# ---------------------------------------------------------------------------
# Stage 1 — Python base
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ---------------------------------------------------------------------------
# Stage 2 — Install dependencies
# ---------------------------------------------------------------------------
FROM base AS deps

COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Stage 3 — Application image
# ---------------------------------------------------------------------------
FROM deps AS app

COPY . .

# Collect static files (do not fail if DB is not available at build time)
RUN python manage.py collectstatic --noinput || true

# Create non-root user for security
RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app
USER app

EXPOSE 8000

# Entrypoint: apply migrations then start Gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120 --access-logfile - --error-logfile -"]
