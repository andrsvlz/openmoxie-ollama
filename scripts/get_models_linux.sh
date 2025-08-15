#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${ROOT}/site/services/stt/models"
mkdir -p "${DEST}"

# Supported names → Hugging Face repos (official faster-whisper model dirs)
declare -A HF=(
  ["faster-whisper-small.en"]="https://huggingface.co/Systran/faster-whisper-small.en/resolve/main"
  ["faster-whisper-base.en"]="https://huggingface.co/Systran/faster-whisper-base.en/resolve/main"
)

download_model() {
  local name="$1"
  local base="${HF[$name]}"
  local out="${DEST}/${name}"
  if [[ -z "${base}" ]]; then
    echo "Unknown model name: ${name}"
    exit 1
  fi
  mkdir -p "${out}"
  echo "→ Downloading ${name} to ${out}"
  curl -L -o "${out}/model.bin"      "${base}/model.bin"
  curl -L -o "${out}/config.json"    "${base}/config.json"
  curl -L -o "${out}/tokenizer.json" "${base}/tokenizer.json"
  curl -L -o "${out}/vocabulary.txt" "${base}/vocabulary.txt"
  echo "✓ ${name} done"
}

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 faster-whisper-small.en [faster-whisper-base.en ...]"
  echo "Available:"
  for k in "${!HF[@]}"; do echo "  - $k"; done
  exit 1
fi

for m in "$@"; do
  download_model "$m"
done

echo "All done. Models in: ${DEST}"
