# syntax=docker/dockerfile:1.7
FROM python:3.12.11-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy \
    UV_NO_PROGRESS=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /build
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir \
      "uv==0.11.19" "build==1.5.0" "setuptools==83.0.0" \
    && uv sync --locked --no-dev --no-install-project \
    && python -m build --wheel --no-isolation \
    && uv pip install --python /opt/venv/bin/python --no-deps dist/*.whl

FROM python:3.12.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    SUPPORTOPS_ENVIRONMENT=local \
    SUPPORTOPS_LOG_LEVEL=INFO \
    SUPPORTOPS_LLM_ENABLED=false \
    SUPPORTOPS_DB_PATH=/app/data/supportops.db \
    SUPPORTOPS_EXPORT_ROOT=/app/exports \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

RUN groupadd --system --gid 10001 supportops \
    && useradd --system --uid 10001 --gid supportops --home-dir /app supportops \
    && install -d -o supportops -g supportops /app/data /app/exports
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv

USER 10001:10001
EXPOSE 8501
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=2).read()"]
ENTRYPOINT ["python", "-m", "streamlit", "run", "/opt/venv/lib/python3.12/site-packages/supportops/streamlit_app.py"]
CMD ["--server.headless=true", "--server.address=0.0.0.0", "--server.port=8501"]
