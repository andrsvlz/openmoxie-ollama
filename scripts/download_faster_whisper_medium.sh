#!/usr/bin/env bash

set -euo pipefail

MODEL_DIR=${MODEL_DIR:-"$HOME/models/faster-whisper-medium"}

mkdir -p "$MODEL_DIR"
cd "$MODEL_DIR"

function fetch() {
  local url="$1" fname="$2"
  if [ -f "$fname" ]; then
    echo "[download] $fname ya existe; omitiendo"
  else
    echo "[download] descargando $fname"
    curl -L -o "$fname" "$url"
  fi
}

BASE_URL="https://huggingface.co/Systran/faster-whisper-medium/resolve/main"

fetch "$BASE_URL/model.bin" model.bin
fetch "$BASE_URL/config.json" config.json
fetch "$BASE_URL/tokenizer.json" tokenizer.json
fetch "$BASE_URL/vocabulary.json" vocabulary.json

echo "[download] Modelo almacenado en $MODEL_DIR"
