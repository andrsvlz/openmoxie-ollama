#!/usr/bin/env bash
set -euo pipefail
cd /app/site

# Apply migrations
python manage.py migrate --noinput

# Collect static (ignore if not configured)
python manage.py collectstatic --noinput || true

# Default internal service URLs if not provided
export STT_URL="${STT_URL:-http://stt:8001/stt}"

# Run the app
exec gunicorn openmoxie.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${WEB_WORKERS:-3}" \
  --timeout "${WEB_TIMEOUT:-120}"
