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

## Build
### Docker 
```bash
docker build . --build-context root='../../'
```