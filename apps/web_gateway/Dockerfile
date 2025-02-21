FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY ./packages /build/packages/

WORKDIR /build/apps/web_gateway/

COPY ./apps/web_gateway/pyproject.toml ./apps/web_gateway/uv.lock ./
RUN uv sync --frozen --no-install-project

# configs for local development
COPY ./config/ /build/config/
COPY ./credentials/ /build/credentials/

COPY ./apps/web_gateway/ /build/apps/web_gateway/

RUN uv sync --frozen

CMD ["/build/apps/web_gateway/.venv/bin/python", ".venv/bin/uvicorn", "--host", "0.0.0.0", "--port", "8080", "main:app"]
