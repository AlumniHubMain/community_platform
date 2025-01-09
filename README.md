# community_platform
python version = 3.13

## Setup

To setup db you need to run the following commands:

docker compose up -d db

Install dependencies of db_common:

pip install -e db_common

Run setup_db.py:

python -m db_common.setup_db

To run migrations you need to run the following command:

alembic upgrade head

To insert test data you need to run the following command:

python -m scripts.insert_test_data

If you do not want to mess with the requirements, you can use the following command to set it up via docker:

docker compose up -d matching --build

docker compose exec matching sh -c 'export DB_HOST=db && python -m db_common.setup_db && alembic upgrade head'

docker compose exec matching python -m scripts.insert_test_data


## Setup
### Local Dev
#### MacOs & Linux Install UV
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
#### Install Python 
```bash
uv python install 3.12 3.13
```
