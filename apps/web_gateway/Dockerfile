FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=root ./ /build/

WORKDIR /build/apps/web_gateway/
RUN uv sync --frozen --no-cache --reinstall
RUN uv pip install python-multipart alembic
COPY main.py /main.py

ENV PYTHONPATH=${PYTHONPATH}:/build

CMD ["/build/apps/web_gateway/.venv/bin/python", ".venv/bin/uvicorn", "--host", "0.0.0.0", "--port", "8080", "main:app"]