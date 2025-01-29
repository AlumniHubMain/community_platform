FROM mcr.microsoft.com/playwright/python:v1.49.1-noble

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache
COPY app /app

ENV PATH="/.venv/bin:$PATH"

CMD ["python3", "-m", "app.main"]