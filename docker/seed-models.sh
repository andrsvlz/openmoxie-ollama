#!/bin/sh
set -eu

MODELS_DIR="${MODELS_DIR:-/models}"
MODEL_NAMES="${MODEL_NAMES:-faster-whisper-small.en}"

echo "[model-init] MODELS_DIR=$MODELS_DIR"
echo "[model-init] MODEL_NAMES=$MODEL_NAMES"

url() {
  case "$1" in
    faster-whisper-small.en) echo "https://huggingface.co/Systran/faster-whisper-small.en/resolve/main" ;;
    faster-whisper-base.en)  echo "https://huggingface.co/Systran/faster-whisper-base.en/resolve/main" ;;
    faster-whisper-medium)   echo "https://huggingface.co/Systran/faster-whisper-medium/resolve/main" ;;
    faster-whisper-large)    echo "https://huggingface.co/Systran/faster-whisper-large-v3/resolve/main" ;;
    faster-whisper-large-v3) echo "https://huggingface.co/Systran/faster-whisper-large-v3/resolve/main" ;;
    *) echo "" ;;
  esac
}

fetch() {
  name="$1"; base="$2"; out="${MODELS_DIR}/${name}"
  mkdir -p "$out"
  if [ -f "$out/model.bin" ] && [ -f "$out/config.json" ] && \
     [ -f "$out/tokenizer.json" ] && \
     { [ -f "$out/vocabulary.txt" ] || [ -f "$out/vocabulary.json" ]; }; then
    echo "✓ $name already present"
    return 0
  fi
  echo "→ downloading $name to $out"
  curl -fSL "$base/model.bin"      -o "$out/model.bin"
  curl -fSL "$base/config.json"    -o "$out/config.json"
  curl -fSL "$base/tokenizer.json" -o "$out/tokenizer.json"
  if curl -fSL "$base/vocabulary.json" -o "$out/vocabulary.json"; then
    :
  else
    curl -fSL "$base/vocabulary.txt" -o "$out/vocabulary.txt"
  fi
  echo "✓ $name done"
}

# turn comma-separated list into words
OLDIFS="$IFS"
IFS=','
set -- $MODEL_NAMES
IFS="$OLDIFS"

for m in "$@"; do
  base="$(url "$m")"
  if [ -z "$base" ]; then
    echo "Unknown model $m" >&2
    exit 1
  fi
  fetch "$m" "$base"
done

echo "[model-init] All models ready in $MODELS_DIR"
