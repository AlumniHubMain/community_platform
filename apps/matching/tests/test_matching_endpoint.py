import os
import sys
import base64
import json
from pathlib import Path
from datetime import datetime

# Add the microservice root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app as fastapi_app


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
def client():
    return TestClient(fastapi_app)


@pytest.fixture
def mock_ps_client():
    with patch("app.matching.PSClient") as mock:
        mock.get_file = MagicMock(return_value="mock_model_path")
        yield mock


@pytest.fixture
def mock_process_matching_request():
    with patch("app.main.process_matching_request") as mock:
        mock.return_value = (1, [2, 3, 4])  # match_id, predictions
        yield mock


@pytest.mark.asyncio
async def test_pubsub_push_heuristic(client, mock_process_matching_request):
    """Test Pub/Sub push endpoint with heuristic model settings"""
    message_data = {
        "user_id": 1,
        "meeting_intent_id": 1,
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
        "meeting_intent_id": 1,
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
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_pubsub_push_missing_required_field(client):
    """Test Pub/Sub push endpoint with missing required field"""
    message_data = {
        "user_id": 1,
        # missing meeting_intent_id
        "model_settings_preset": "heuristic",
        "n": 5,
    }
    pubsub_message = create_pubsub_message(message_data)
    response = client.post("/pubsub/push", json=pubsub_message)
    assert response.status_code == 400
