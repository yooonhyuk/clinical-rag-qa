# syntax=docker/dockerfile:1
# Streamlit UI image. Build context: repository root.
FROM ghcr.io/astral-sh/uv:0.11.16 AS uv

FROM python:3.12-slim
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --only-group ui --no-install-project
COPY frontend/streamlit_app.py frontend/no_egress_entrypoint.py ./

RUN useradd --create-home --uid 10001 app
USER app
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
