# Matching

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
uv run pytest
```

## Docker
### Build 
```bash
docker build -t matching .
```

### Run
```bash
docker run -d -p 8080:8080 matching
```

### Compose
```bash
docker compose up -d --build
```