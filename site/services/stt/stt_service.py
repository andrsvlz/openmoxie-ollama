# site/services/stt/stt_service.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from faster_whisper import WhisperModel
import tempfile, os, logging
from threading import Lock
from typing import Optional, List, Dict, Tuple

try:
    import ctranslate2  # type: ignore
except ImportError:  # pragma: no cover - faster-whisper bundles this in production
    ctranslate2 = None

# --- Config via env ---
MODEL_NAME = os.getenv("STT_MODEL", "small.en")
REQUESTED_DEVICE = os.getenv("STT_DEVICE", "auto")
REQUESTED_COMPUTE = os.getenv("STT_COMPUTE", "auto")
USE_VAD    = os.getenv("STT_VAD", "1") == "1"
WORDS      = os.getenv("STT_WORDS", "0") == "1"

logger = logging.getLogger("stt")
logger.setLevel(logging.INFO)

VALID_COMPUTE_TYPES = {"int8", "int8_float16", "float16", "float32", "auto"}


def _resolve_device(preferred: str) -> str:
    pref = (preferred or "auto").strip().lower()
    if pref == "auto":
        if ctranslate2 is not None:
            try:
                if ctranslate2.get_device_count("cuda") > 0:
                    logger.info("Auto device selection detected CUDA; using 'cuda'.")
                    return "cuda"
            except Exception as exc:
                logger.warning("Unable to query CUDA device count (%s); defaulting to CPU.", exc)
        return "cpu"
    if pref not in {"cpu", "cuda"}:
        logger.warning("Unknown device '%s'; defaulting to CPU.", pref)
        return "cpu"
    return pref


def _resolve_compute(device: str, preferred: str) -> str:
    pref = (preferred or "auto").strip().lower()
    if pref == "auto" or pref not in VALID_COMPUTE_TYPES:
        fallback = "float16" if device == "cuda" else "int8"
        if pref not in {"", "auto"}:
            logger.warning("Unsupported compute type '%s'; using '%s'.", pref, fallback)
        return fallback
    if device == "cuda" and pref == "int8":
        logger.info("Adjusting compute type 'int8' to 'int8_float16' for CUDA.")
        return "int8_float16"
    if device == "cpu" and pref in {"float16"}:
        logger.info("Compute type '%s' is inefficient on CPU; switching to 'int8'.", pref)
        return "int8"
    return pref


def _load_model(model_name: str, device_pref: str, compute_pref: str) -> Tuple[WhisperModel, str, str]:
    resolved_device = _resolve_device(device_pref)
    resolved_compute = _resolve_compute(resolved_device, compute_pref)
    logger.info(
        "Loading model '%s' (requested device=%s, compute=%s → using device=%s, compute=%s)",
        model_name,
        (device_pref or "auto"),
        (compute_pref or "auto"),
        resolved_device,
        resolved_compute,
    )
    try:
        instance = WhisperModel(model_name, device=resolved_device, compute_type=resolved_compute)
        return instance, resolved_device, resolved_compute
    except Exception as exc:
        if resolved_device == "cuda":
            logger.warning("Failed to initialize model on CUDA (%s); retrying on CPU fallback.", exc)
            fallback_device = "cpu"
            fallback_compute = _resolve_compute(fallback_device, compute_pref)
            try:
                instance = WhisperModel(model_name, device=fallback_device, compute_type=fallback_compute)
                return instance, fallback_device, fallback_compute
            except Exception:
                logger.exception("CPU fallback initialization failed as well.")
                raise
        raise


app = FastAPI()
model_lock = Lock()
model, DEVICE, COMPUTE = _load_model(MODEL_NAME, REQUESTED_DEVICE, REQUESTED_COMPUTE)

class STTSegment(BaseModel):
    start: float
    end: float
    text: str

class STTResponse(BaseModel):
    text: str
    language: str | None = None
    segments: list[STTSegment]

class ReloadConfig(BaseModel):
    model: Optional[str] = None          # e.g. "/models/faster-whisper-small.en"
    device: Optional[str] = None         # "auto"|"cpu"|"cuda"
    compute: Optional[str] = None        # "int8"|"int8_float16"|"float16"|"float32"|"auto"

@app.post("/stt", response_model=STTResponse)
async def stt(
    file: UploadFile = File(...),
    language: str | None = Form(None),
    initial_prompt: str | None = Form(None),
    translate: bool = Form(False),
):
    try:
        suffix = os.path.splitext(file.filename or ".wav")[1]
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            data = await file.read()
            tmp.write(data)
            tmp_path = tmp.name

        logger.info(f"STT request: {file.filename=} size={len(data)} lang={language} vad={USE_VAD}")

        translate = False  # Forzar modo transcripción; ignorar traducción
        with model_lock:
            segments, info = model.transcribe(
                tmp_path,
                language=language,
                task="transcribe",
                vad_filter=USE_VAD,
                word_timestamps=WORDS,
                initial_prompt=initial_prompt,
            )

        out_text, out_segments = [], []
        for s in segments:
            out_text.append(s.text)
            out_segments.append({"start": s.start, "end": s.end, "text": s.text})

        os.remove(tmp_path)

        text = " ".join(out_text).strip()
        logger.info(f"STT result: chars={len(text)} segments={len(out_segments)} lang={info.language}")
        return {"text": text, "language": info.language, "segments": out_segments}

    except Exception as e:
        logger.exception("STT failure")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/health")
def health():
    return {
        "ok": True,
        "model": MODEL_NAME,
        "device": DEVICE,
        "compute": COMPUTE,
        "requested_device": REQUESTED_DEVICE,
        "requested_compute": REQUESTED_COMPUTE,
    }

# ---------- Control API ----------
def _scan_models(roots: List[str]) -> List[Dict[str, str]]:
    seen = set()
    out: List[Dict[str, str]] = []
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        try:
            for name in os.listdir(root):
                path = os.path.join(root, name)
                if not os.path.isdir(path):
                    continue
                if (os.path.isfile(os.path.join(path, "config.json"))
                    and os.path.isfile(os.path.join(path, "model.bin"))):
                    if path in seen:
                        continue
                    seen.add(path)
                    size = 0
                    try:
                        size = os.path.getsize(os.path.join(path, "model.bin"))
                    except Exception:
                        pass
                    out.append({"name": name, "path": path, "size": size})
        except Exception:
            continue
    out.sort(key=lambda m: (m.get("size") or 0, m.get("name") or ""))
    return out

@app.get("/control/models")
def list_models(root: Optional[str] = None):
    """
    Returns available model directories.
    Scans (in order): ?root=..., $STT_MODELS_DIR, /models, ./models (next to this file).
    """
    roots = []
    if root:
        roots.append(root)
    env_root = os.getenv("STT_MODELS_DIR")
    if env_root:
        roots.append(env_root)
    roots.append("/models")
    here_models = os.path.join(os.path.dirname(__file__), "models")
    roots.append(here_models)
    return {"ok": True, "models": _scan_models(roots)}

@app.post("/control/reload")
def reload_model(cfg: ReloadConfig):
    global model, MODEL_NAME, DEVICE, COMPUTE, REQUESTED_DEVICE, REQUESTED_COMPUTE

    new_model = cfg.model or MODEL_NAME
    new_dev_pref = cfg.device or REQUESTED_DEVICE
    new_comp_pref = cfg.compute or REQUESTED_COMPUTE

    logger.info(
        "Reload request received: model=%s device=%s compute=%s",
        new_model,
        new_dev_pref,
        new_comp_pref,
    )

    with model_lock:
        try:
            loaded_model, actual_device, actual_compute = _load_model(new_model, new_dev_pref, new_comp_pref)
            model = loaded_model
            MODEL_NAME = new_model
            DEVICE = actual_device
            COMPUTE = actual_compute
            REQUESTED_DEVICE = new_dev_pref
            REQUESTED_COMPUTE = new_comp_pref
        except Exception as e:
            logger.exception("Reload failed")
            return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

    return {"ok": True, "model": MODEL_NAME, "device": DEVICE, "compute": COMPUTE}
