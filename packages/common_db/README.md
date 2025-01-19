# common_db

Common DB package for all services.

## How to run migrations

1. Run local DB container or change settings in `config/db.json`

```bash
docker compose up -d db
```

2. Cd to this directory

```bash
cd packages/common_db
```
3. Setup env

```bash
uv venv -p 3.12 .venv
source .venv/bin/activate
uv sync
uv pip install -e .
```

4. Create/Run migrations

Create your models, schemes, enums, etc.
Export models in src/common_db/models/__init__.py

```bash
alembic revision --autogenerate -m "Migration message"
alembic upgrade head
```