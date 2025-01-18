FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY ./ /build/

WORKDIR /build/apps/web_gateway/
RUN uv sync --frozen --no-cache
RUN uv pip install python-multipart
COPY main.py /main.py

CMD ["/build/apps/web_gateway/.venv/bin/python", ".venv/bin/uvicorn", "--host", "0.0.0.0", "--port", "8080", "main:app"]
 
