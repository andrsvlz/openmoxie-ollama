#!/usr/bin/env zsh
set -e
set -u
set -o pipefail

# Support CSV flag: -Models "a,b"
if [[ ${1:-} == "-Models" && -n ${2:-} ]]; then
  models=(${(s:,:)2})
  shift 2
  set -- $models
fi

# Script dir (absolute), project root = parent of scripts/
SCRIPT_DIR="${0:A:h}"
ROOT="${SCRIPT_DIR:h}"
DEST="${ROOT}/site/services/stt/models"
mkdir -p "$DEST"

typeset -A HF
HF=(
  faster-whisper-small.en https://huggingface.co/Systran/faster-whisper-small.en/resolve/main
  faster-whisper-base.en  https://huggingface.co/Systran/faster-whisper-base.en/resolve/main
)

download_model() {
  local name="$1"
  local base="${HF[$name]-}"
  if [[ -z "$base" ]]; then
    print -u2 "Unknown model: $name"
    exit 1
  fi
  local out="$DEST/$name"
  mkdir -p "$out"
  print "→ Downloading $name to $out"
  curl -fSL "$base/model.bin"      -o "$out/model.bin"
  curl -fSL "$base/config.json"    -o "$out/config.json"
  curl -fSL "$base/tokenizer.json" -o "$out/tokenizer.json"
  curl -fSL "$base/vocabulary.txt" -o "$out/vocabulary.txt"
  print "✓ $name done"
}

if (( $# == 0 )); then
  print "Usage: $0 <model...>"
  print "Available:"
  for k in ${(k)HF}; do print "  - $k"; done
  exit 1
fi

for m in "$@"; do download_model "$m"; done
print "All done. Models in: $DEST"
