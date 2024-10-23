import logging

from functools import wraps

import click
import psycopg2 as pg

from flask import current_app, g

from app import consts

logger = logging.getLogger(__name__)


def get_db():
    if "db" not in g:
        # TODO: user gcloud secret-manager
        g.db = pg.connect(
            dbname=consts.DB_NAME,
            user="user",
            password="",
            host="localhost",
            port="9999",
            async_=False,
        )
        g.db.set_session(
            isolation_level=pg.extensions.ISOLATION_LEVEL_READ_COMMITTED,
            readonly=False,
            autocommit=True,
        )

    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def with_cursor(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        with get_db().cursor() as curs:
            return func(curs, *args, **kwargs)
    return decorated


def reinit_db():
    db = get_db()

    with db.cursor() as curs:
        logger.info("clearing db '%s'", consts.DB_NAME)

        curs.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public';
        """)
        tables = curs.fetchall()
        for table in tables:
            table_name = table[0]
            logger.debug("removing table '%s'", table_name)
            curs.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")

        logger.info("creating new tables...")
        with current_app.open_resource("schema.sql", "r") as f:
            curs.execute(f.read())


@click.command("reinit-db")
def reinit_db_command():
    """Clear the existing data and create new tables."""
    reinit_db()


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(reinit_db_command)
