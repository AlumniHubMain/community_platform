import pytest

from fastapi.testclient import TestClient


@pytest.fixture()
def web_gateway_app():
    from apps.web_gateway.main import app
    return app


@pytest.fixture()
def web_gateway_client(web_gateway_app):
    yield TestClient(web_gateway_app)


@pytest.fixture()
def authorized_client(web_gateway_client):
    auth_response = web_gateway_client.get("/auth/auth_for_development")
    status_code = auth_response.status_code
    assert status_code == 200, f"Auth failed with status {status_code}. Details: {auth_response.json()['detail']}"
    return web_gateway_client
