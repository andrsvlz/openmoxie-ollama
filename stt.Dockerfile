# stt.Dockerfile
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# System deps for audio decoding + Python tooling
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 \
      python3-pip \
      python3-venv \
      python3-dev \
      ffmpeg \
      libsndfile1 \
      curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/local/bin/python \
    && ln -sf /usr/bin/pip3 /usr/local/bin/pip

RUN python -m pip install --upgrade pip

WORKDIR /app

# Copy the service code
COPY site/services/stt/stt_service.py /app/stt_service.py

# Install CUDA-enabled CTranslate2 first so faster-whisper keeps the GPU build
RUN pip install --no-cache-dir --upgrade --extra-index-url https://download.pytorch.org/whl/cu121 \
      'ctranslate2>=4.2,<5' \
    && pip install --no-cache-dir \
      fastapi \
      "uvicorn[standard]" \
      faster-whisper \
      python-multipart \
      soundfile

# Defaults; override via docker-compose env as needed
ENV STT_MODEL=/models/faster-whisper-small \
    STT_DEVICE=auto \
    STT_COMPUTE=auto \
    STT_VAD=1

EXPOSE 8001

CMD ["uvicorn", "stt_service:app", "--host", "0.0.0.0", "--port", "8001"]
