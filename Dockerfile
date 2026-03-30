FROM ghcr.io/astral-sh/uv:0.6-python3.12-slim AS builder

WORKDIR /app

# 安裝依賴（利用 layer cache，只有 pyproject.toml 變動才重跑）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# ---- runtime image ----
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY sidecar/ ./sidecar/
COPY skills/ ./skills/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["uvicorn", "sidecar.router:app", "--host", "127.0.0.1", "--port", "8080"]
