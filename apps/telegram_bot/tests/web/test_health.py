import pytest

from fastapi.testclient import TestClient


@pytest.fixture()
def telegram_bot_app():
    from telegram_bot.main import app
    return app


@pytest.fixture()
def telegram_bot_client(telegram_bot_app):
    yield TestClient(telegram_bot_app)
