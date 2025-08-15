# site/services/stt/stt_service.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from faster_whisper import WhisperModel
import tempfile, os, logging
from threading import Lock
from typing import Optional, List, Dict

# --- Config via env ---
MODEL_NAME = os.getenv("STT_MODEL", "small.en")
DEVICE     = os.getenv("STT_DEVICE", "auto")
COMPUTE    = os.getenv("STT_COMPUTE", "int8")
USE_VAD    = os.getenv("STT_VAD", "1") == "1"
WORDS      = os.getenv("STT_WORDS", "0") == "1"

logger = logging.getLogger("stt")
logger.setLevel(logging.INFO)

app = FastAPI()
logger.info(f"Loading model: {MODEL_NAME} (device={DEVICE}, compute={COMPUTE})")
model_lock = Lock()
model = WhisperModel(MODEL_NAME, device=DEVICE, compute_type=COMPUTE)

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
    compute: Optional[str] = None        # "int8"|"int8_float16"|"float16"|"float32"

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

        segments, info = model.transcribe(
            tmp_path,
            language=language,
            task="translate" if translate else "transcribe",
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
    return {"ok": True, "model": MODEL_NAME, "device": DEVICE, "compute": COMPUTE}

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
    global model, MODEL_NAME, DEVICE, COMPUTE
    new_model = cfg.model or MODEL_NAME
    new_dev   = cfg.device or DEVICE
    new_comp  = cfg.compute or COMPUTE

    logger.info(f"Reload request: model={new_model} device={new_dev} compute={new_comp}")
    with model_lock:
        try:
            m = WhisperModel(new_model, device=new_dev, compute_type=new_comp)
            model = m
            MODEL_NAME, DEVICE, COMPUTE = new_model, new_dev, new_comp
        except Exception as e:
            logger.exception("Reload failed")
            return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})
    return {"ok": True, "model": MODEL_NAME, "device": DEVICE, "compute": COMPUTE}
