# Используем multi-stage building
FROM python:3.12.7-slim-bullseye as builder

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN apt-get update && apt-get install -y build-essential
RUN apt-get update && apt-get install -y curl && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc && \
    . "$HOME/.cargo/env" && \
    cargo --version
ENV PATH="/root/.cargo/bin:${PATH}"

# Create and set the virtual environment path
ENV VIRTUAL_ENV=/.venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY db_common /db_common/

COPY matching/pyproject.toml ./
RUN uv lock
RUN uv add /db_common/
RUN uv sync --frozen --no-cache --dev

FROM python:3.12.7-slim-bullseye

RUN useradd -m -u 1000 appuser

# Copy the virtual environment
COPY --from=builder /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Copy the application code and db_common
COPY --chown=appuser:appuser matching/app /app
COPY --from=builder /db_common /db_common

WORKDIR /app
USER appuser

# Ensure Python can find the packages
ENV PYTHONPATH="/:/db_common:${PYTHONPATH}"

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]