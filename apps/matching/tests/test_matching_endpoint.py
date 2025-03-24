import os
import sys
import base64
import json
from pathlib import Path
from datetime import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from matching.main import app as fastapi_app


def create_pubsub_message(data: dict) -> dict:
    """Helper function to create a Pub/Sub message"""
    encoded_data = base64.b64encode(json.dumps(data).encode()).decode()
    return {
        "message": {
            "data": encoded_data,
            "messageId": "test_message_id",
            "publishTime": "2024-01-01T00:00:00.000Z",
        },
        "subscription": "test-subscription",
    }


@pytest.fixture
def mock_db_manager():
    with patch("matching.main.db_manager") as mock:
        # Create a mock session context manager
        async def async_session():
            class AsyncSessionContext:
                async def __aenter__(self):
                    return AsyncMock()

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

            return AsyncSessionContext()

        mock.session = async_session
        yield mock


@pytest.fixture
def mock_storage():
    with patch("matching.main.CloudStorageAdapter") as mock:
        instance = mock.return_value
        instance.initialize = AsyncMock()
        yield instance


@pytest.fixture
def client(mock_db_manager, mock_storage):
    return TestClient(fastapi_app)


@pytest.fixture
def mock_ps_client():
    with patch("matching.transport.PSClient") as mock:
        mock.get_file = MagicMock(return_value="mock_model_path")
        yield mock


@pytest.fixture
def mock_process_matching_request():
    async def mock_process(*args, **kwargs):
        return 1, [2, 3, 4]

    with patch("matching.main.process_matching_request", side_effect=mock_process) as mock:
        yield mock


@pytest.mark.asyncio
async def test_pubsub_push_heuristic(client, mock_process_matching_request):
    """Test Pub/Sub push endpoint with heuristic model settings"""
    message_data = {
        "user_id": 1,
        "form_id": 1,
        "model_settings_preset": "heuristic",
        "n": 5,
    }
    pubsub_message = create_pubsub_message(message_data)

    response = client.post("/pubsub/push", json=pubsub_message)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "match_id": 1}
    mock_process_matching_request.assert_called_once()


@pytest.mark.asyncio
async def test_pubsub_push_with_filters(client, mock_process_matching_request):
    """Test Pub/Sub push endpoint with filters"""
    message_data = {
        "user_id": 1,
        "form_id": 1,
        "model_settings_preset": "filtered",
        "n": 5,
    }
    pubsub_message = create_pubsub_message(message_data)

    response = client.post("/pubsub/push", json=pubsub_message)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "match_id": 1}
    mock_process_matching_request.assert_called_once()


@pytest.mark.asyncio
async def test_pubsub_push_invalid_message(client):
    """Test Pub/Sub push endpoint with invalid message format"""
    response = client.post("/pubsub/push", json={"invalid": "message"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_pubsub_push_invalid_data(client):
    """Test Pub/Sub push endpoint with invalid data format"""
    pubsub_message = {
        "message": {
            "data": "invalid_base64",
            "messageId": "test_message_id",
        }
    }
    response = client.post("/pubsub/push", json=pubsub_message)
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_pubsub_push_missing_required_field(client):
    """Test Pub/Sub push endpoint with missing required field"""
    message_data = {
        "user_id": 1,
        # missing form_id
        "model_settings_preset": "heuristic",
        "n": 5,
    }
    pubsub_message = create_pubsub_message(message_data)
    response = client.post("/pubsub/push", json=pubsub_message)
    assert response.status_code == 500
