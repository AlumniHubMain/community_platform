FROM python:3.12-slim AS build

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY --from=root ./ /build/

WORKDIR /build/apps/telegram_bot/

RUN uv sync --frozen --no-cache

FROM python:3.12-slim

COPY --from=build /build/apps/telegram_bot/.venv /.venv

CMD ["/.venv/bin/uvicorn", "--host", "0.0.0.0", "--port", "8080", "telegram_bot.main:app"]