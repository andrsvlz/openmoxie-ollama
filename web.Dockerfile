# web.Dockerfile
FROM python:3.11-slim

# System deps for your entrypoint and runtime
RUN apt-get update \
 && apt-get install -y --no-install-recommends bash curl \
 && rm -rf /var/lib/apt/lists/*

# Workdir and app
WORKDIR /app
COPY . /app

# Python deps (make sure requirements.txt includes gunicorn & Django)
# e.g. lines in requirements.txt:
#   Django>=5.1
#   gunicorn>=21.2
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint; strip CRLF if edited on Windows; make executable
# adjust the source path to wherever your script lives in the repo
COPY docker/web-entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENV DJANGO_SETTINGS_MODULE=openmoxie.settings
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
