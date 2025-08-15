# site/hive/stt.py
from __future__ import annotations
import requests
from typing import Optional, Tuple
from django.conf import settings
from .models import HiveConfiguration
from .mqtt.ai_factory import create_openai

# site/hive/stt.py

def get_stt_config():
    """Public helper: returns (backend, url, lang)."""
    return _get_stt_config()

def stt_health(timeout=2):
    """
    Returns a dict with backend/url/lang and, if local, health info from the STT service.
    {
      "backend": "local"|"openai",
      "url": "...",
      "lang": "en",
      "service": {"ok": true, "model": "...", "device": "cuda|cpu", "compute": "..."} | {"error": "..."}
    }
    """
    backend, url, lang = _get_stt_config()
    info = {}
    if backend == "local":
        try:
            hurl = url.replace("/stt", "/health")
            r = requests.get(hurl, timeout=timeout)
            r.raise_for_status()
            info = r.json()
        except Exception as e:
            info = {"error": str(e)}
    return {"backend": backend, "url": url, "lang": lang, "service": info}


def _get_stt_config() -> tuple[str, str, str]:
    """
    Returns (backend, url, lang).
    backend: "local" or "openai"
    url:     e.g. http://127.0.0.1:8001/stt
    lang:    e.g. "en"
    """
    cfg = HiveConfiguration.objects.filter(name='default').first()
    backend = (getattr(cfg, "stt_backend", None) or getattr(settings, "STT_BACKEND", "openai")).lower()
    url     = getattr(cfg, "stt_url", None) or getattr(settings, "STT_URL", "http://127.0.0.1:8001/stt")
    lang    = getattr(cfg, "stt_lang", None) or getattr(settings, "STT_LANG", "en")
    return backend, url, lang

def transcribe_wav_bytes(wav_bytes: bytes, language: Optional[str] = None) -> Tuple[str, float, float]:
    """
    Returns (text, start_sec, end_sec). Start/end are relative to the start of this utterance.
    """
    backend, url, default_lang = _get_stt_config()
    lang = language or default_lang

    if backend == "local":
        # Call your faster-whisper microservice
        r = requests.post(
            url,
            files={"file": ("speech.wav", wav_bytes, "audio/wav")},
            data={"language": lang},
            timeout=120
        )
        r.raise_for_status()
        j = r.json()
        text = j.get("text", "")
        segs = j.get("segments") or []
        if segs:
            start = float(segs[0].get("start", 0.0))
            end   = float(segs[-1].get("end", 0.0))
        else:
            start = end = 0.0
        return text, start, end

    # Remote OpenAI Whisper (legacy)
    # NOTE: ai_factory is under hive/mqtt/
    from .mqtt.ai_factory import create_openai
    client = create_openai()
    resp = client.audio.transcriptions.create(
        file=("speech.wav", wav_bytes),
        model="whisper-1",
        response_format="verbose_json",
        timestamp_granularities=["word"]
    )
    text = getattr(resp, "text", "") or ""
    words = getattr(resp, "words", []) or []
    if words:
        start = min(w.start for w in words)
        end   = max(w.end for w in words)
    else:
        start = end = 0.0
    return text, float(start), float(end)
