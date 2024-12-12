from setuptools import setup, find_packages

setup(
    name="db_common",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=2.0.36",
        "pydantic>=2.9.2",
        "pydantic-settings>=2.6.0",
        "asyncpg>=0.30.0",
        "alembic>=1.14.0",
        "psycopg2-binary>=2.9.9",
        "black>=24.10.0",
        "greenlet>=2.0.0",
    ],
)
