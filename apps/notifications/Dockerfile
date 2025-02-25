# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc && \
    . "$HOME/.cargo/env"
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy UV binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /build/apps/notifications/

# Copy shared packages and configurations
COPY packages/ /build/packages/
COPY config/ /build/config/
COPY credentials/ /build/credentials/

# Copy project files
COPY pyproject.toml uv.lock /build/apps/notifications/
COPY src/ /build/apps/notifications/src/

# Install dependencies with frozen lock file
RUN uv sync --frozen

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/build/apps/notifications/src

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the service using uvicorn
CMD ["/build/apps/notifications/.venv/bin/uvicorn", "notifications.main:app", "--host", "0.0.0.0", "--port", "8080"] 