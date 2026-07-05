# syntax=docker/dockerfile:1
#
# Prolane API (FastAPI). Part of a DELIBERATELY-VULNERABLE training target.
# For local, educational use only - never expose this on a network.
#
# Build context is the repo root (see docker-compose.yml).

FROM python:3.11-slim AS api

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first so this layer caches across code changes.
COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

# Application code + the deterministic SQL the API loads on first boot.
# init_db() seeds SQLite from db/schema.sql + seed.sql + seed_bulk.sql the first
# time it starts, and writes the db file + uploads/ under /app at runtime.
COPY api ./api
COPY db ./db

EXPOSE 8081

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8081/health', timeout=2)"

# Binds 0.0.0.0 INSIDE the container only; compose publishes the port to the
# host's loopback (127.0.0.1) so it is never reachable off the machine.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8081"]
