from setuptools import setup, find_packages

setup(
    name="db_common",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=2.0.36",
        "pydantic>=2.9.2",
        "asyncpg>=0.30.0",
    ],
) 