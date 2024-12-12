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

docker compose exec matching python -m db_common.setup_db

docker compose exec matching alembic upgrade head

docker compose exec matching python -m scripts.insert_test_data

