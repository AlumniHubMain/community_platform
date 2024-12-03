# Используем multi-stage building
FROM python:3.13-slim-bullseye as builder

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml ./
COPY db_common ./db_common/

RUN uv sync --frozen --no-cache --dev

FROM python:3.13-slim-bullseye

RUN useradd -m -u 1000 appuser

COPY --from=builder /.venv /.venv
COPY --from=builder /db_common /usr/local/lib/python3.13/site-packages/db_common
COPY --from=builder /db_common /.venv/lib/python3.13/site-packages/db_common
COPY --chown=appuser:appuser ./matching/app /app

WORKDIR /app
USER appuser

ENV PATH="/.venv/bin:$PATH"

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]