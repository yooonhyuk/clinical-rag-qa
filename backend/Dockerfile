# syntax=docker/dockerfile:1
# FastAPI API image. Build context: repository root.
FROM ghcr.io/astral-sh/uv:0.11.16 AS uv

FROM python:3.12-slim
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR /app/backend

# Dependencies first (cached layer), then the project itself.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ ./
RUN uv sync --frozen --no-dev

COPY samples /app/samples
COPY corpus /app/corpus
RUN useradd --create-home --uid 10001 app && mkdir -p /app/data && chown -R app /app/data
USER app

ENV RAW_DOCS_PATH=/app/data/raw-docs/documents \
    DICOM_PATH=/app/data/raw-docs/dicom \
    SAMPLES_PATH=/app/samples \
    CORPORA_PATH=/app/corpus
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --retries=10 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')"
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
