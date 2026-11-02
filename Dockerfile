FROM python:3.13-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# dependencies first so they stay cached when only the source changes
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

# static files are collected at build time (the secret key here is for this step only)
RUN SECRET_KEY=build-only STATIC_ROOT=/app/staticfiles python manage.py collectstatic --noinput

RUN useradd -m -u 1000 appuser && mkdir -p /data/media && chown -R appuser:appuser /app /data
USER appuser

ENV DATABASE_PATH=/data/db.sqlite3 \
    MEDIA_ROOT=/data/media

VOLUME /data
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn suffolkcoins.wsgi:application --bind 0.0.0.0:8000 --workers 2"]
