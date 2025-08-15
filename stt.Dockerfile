# stt.Dockerfile
FROM python:3.11-slim

# mp3/ogg decoding; harmless for wav-only too
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the service
# (uses your existing FastAPI app at site/services/stt/stt_service.py)
COPY site/services/stt/stt_service.py /app/stt_service.py

# Python deps
RUN pip install --no-cache-dir \
      fastapi \
      "uvicorn[standard]" \
      faster-whisper \
      python-multipart \
      soundfile

# Defaults; can be overridden via docker-compose env
ENV STT_MODEL=/models/faster-whisper-small.en \
    STT_DEVICE=auto \
    STT_COMPUTE=int8 \
    STT_VAD=1

EXPOSE 8001


CMD ["uvicorn", "stt_service:app", "--host", "0.0.0.0", "--port", "8001"]
