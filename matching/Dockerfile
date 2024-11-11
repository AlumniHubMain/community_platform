# Используем multi-stage building
FROM python:3.13-slim-bullseye as builder

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --dev

FROM python:3.13-slim-bullseye

RUN useradd -m -u 1000 appuser

COPY --from=builder /.venv /.venv
COPY --chown=appuser:appuser ./app /app

WORKDIR /app
USER appuser

EXPOSE 8080
ENV PATH="/.venv/bin:$PATH"

CMD ["python", "-m", "fastapi", "run", "main.py", "--port", "8080"]