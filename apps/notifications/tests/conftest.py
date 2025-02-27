import pytest
from fastapi.testclient import TestClient
from notifications.main import app

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_broker(mocker):
    # Mock the broker for tests
    return mocker.patch('notifications.main.broker') 