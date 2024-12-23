FROM python:3.12-slim as build

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

VOLUME ../../:/build/

WORKDIR /build/apps/db_proxy/
RUN uv sync --frozen --no-cache

FROM python:3.12-slim

COPY --from=build /build/apps/db_proxy/.venv /
COPY main.py /main.py

CMD ["/.venv/bin/uvicorn", "--host", "0.0.0.0", "--port", "8080", "main:app"]
