#!/usr/bin/env bash
set -euo pipefail
cd /app/site

# --- Django prep ---
python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

# --- Service endpoints (defaults if not provided) ---
export STT_URL="${STT_URL:-http://stt:8001/stt}"
export OLLAMA_HOST="${OLLAMA_HOST:-http://ollama:11434}"

echo "[web-entrypoint] STT_URL=${STT_URL}"
echo "[web-entrypoint] OLLAMA_HOST=${OLLAMA_HOST}"

# --- Optional wait for dependencies to be ready ---
wait_for() {  # usage: wait_for URL [retries] [sleep_seconds]
  local url="${1}"; local tries="${2:-30}"; local nap="${3:-1}"
  for i in $(seq 1 "${tries}"); do
    if curl -fsS "${url}" >/dev/null 2>&1; then
      echo "[web-entrypoint] Ready: ${url}"
      return 0
    fi
    echo "[web-entrypoint] Waiting (${i}/${tries}) for ${url} ..."
    sleep "${nap}"
  done
  echo "[web-entrypoint] Timed out waiting for ${url}" >&2
  return 1
}

if [[ "${SKIP_WAIT_FOR:-0}" != "1" ]]; then
  # STT health endpoint inferred from STT_URL
  STT_HEALTH="${STT_URL%/stt}/health"
  wait_for "${STT_HEALTH}" 40 1 || true   # soft wait

  # Ollama simple endpoint that lists tags
  wait_for "${OLLAMA_HOST}/api/tags" 40 1 || true
fi

# --- Run the app ---
exec gunicorn openmoxie.wsgi:application   --bind 0.0.0.0:8000   --workers "${WEB_WORKERS:-3}"   --timeout "${WEB_TIMEOUT:-120}"