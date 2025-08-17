#!/bin/sh
set -eu

OLLAMA_HOST="${OLLAMA_HOST:-http://ollama:11434}"
# Space- or comma-separated list, e.g. "llama3.2:3b deepseek-r1:1.5b"
OLLAMA_MODELS="${OLLAMA_MODELS:-llama3.2:3b}"

# normalize commas to spaces
MODELS=$(printf "%s" "$OLLAMA_MODELS" | tr ',' ' ')

echo "[ollama-init] Host: $OLLAMA_HOST"
echo "[ollama-init] Models: $MODELS"

wait_for() {
  url="$1"; tries="${2:-180}"; nap="${3:-2}"
  i=0
  while [ "$i" -lt "$tries" ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[ollama-init] Ready: $url"
      return 0
    fi
    i=$((i+1))
    sleep "$nap"
  done
  echo "[ollama-init] Timeout waiting for $url" >&2
  return 1
}

pull_one() {
  name="$1"
  echo "→ pulling $name"
  # /api/pull streams JSONL; curl -N to stream till completion
  curl -fsS -N -X POST     -H 'Content-Type: application/json'     -d "{"name":"${name}"}"     "${OLLAMA_HOST%/}/api/pull"     || { echo "pull failed for $name" >&2; exit 1; }
  echo "✓ $name"
}

# Ensure the API is accepting requests before pulling
wait_for "${OLLAMA_HOST%/}/api/tags" 180 2

for m in $MODELS; do
  pull_one "$m"
done

echo "[ollama-init] All models pulled."
