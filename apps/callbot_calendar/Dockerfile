FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /build/apps/callbot_calendar/

COPY --from=root ./packages /build/packages

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache

COPY src ./src

ENTRYPOINT ["/build/apps/callbot_calendar/.venv/bin/python", "/build/apps/callbot_calendar/src/callbot_calendar/google_calendar.py"]
