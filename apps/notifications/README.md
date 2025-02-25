# Notifications Service

A notification service that connects different services and platform users through a message broker. The service handles various types of notifications, ensuring reliable message delivery and proper user notification through different channels.

## Features
- Asynchronous message processing
- Integration with message broker for inter-service communication
- Email notifications support
- Scalable architecture
- Reliable message delivery

## Setup
### Local Dev
#### MacOs & Linux Install UV
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Setup venv
```bash
uv sync
```
#### Run tests

```bash
uv run pytest --cov=notifications tests/
```

## Docker
### Build
```bash
docker build -t notifications .
```

### Run
```bash
docker run -d -p 8080:8080 notifications
```

### Compose
```bash
docker compose up -d --build
```

## Architecture
The service listens for events from the message broker and processes them according to notification rules. It supports various notification channels and can be easily extended to support new ones.

## Dependencies
- aiosmtplib - for async email handling
- common-db - shared database utilities
- message-broker - message queue integration
- loguru - for structured logging
- fastapi - for REST API and application framework
- uvicorn - ASGI server implementation

### Development Dependencies
- pytest - testing framework
- pytest-asyncio - async test support
- pytest-mock - mocking support
- pytest-cov - code coverage reporting
- debugpy - debugging support
- pylint - code linting
- ruff - fast Python linter
- httpx - HTTP client for testing