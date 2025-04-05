FROM python:3.12-slim

RUN apt-get update && apt-get install -y build-essential
RUN apt-get update && apt-get install -y curl && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc && \
    . "$HOME/.cargo/env" && \
    cargo --version
ENV PATH="/root/.cargo/bin:${PATH}"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY packages/ /build/packages/

WORKDIR /build/apps/matching/

COPY apps/matching/pyproject.toml apps/matching/uv.lock /build/apps/matching/

COPY config/ /build/config/
COPY credentials/ /build/credentials/
COPY ./secrets/ /build/secrets/

COPY apps/matching/ /build/apps/matching/

RUN uv sync --frozen

CMD ["/build/apps/matching/.venv/bin/uvicorn", "matching.main:app", "--host", "0.0.0.0", "--port", "8080"]
 