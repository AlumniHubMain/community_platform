import pytest
import base64
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from common_db.enums.forms import EFormIntentType
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
def mock_parse_text_for_matching():
    async def mock_process(*args, **kwargs):
        return 1, [2, 3, 4]

    with patch("matching.main.parse_text_for_matching", side_effect=mock_process) as mock:
        yield mock


@pytest.mark.asyncio
async def test_pubsub_push_text_matching(client, mock_parse_text_for_matching):
    """Test Pub/Sub push endpoint with text-based matching"""
    message_data = {
        "user_id": 1,
        "text_description": "I want to connect with people in tech",
        "model_settings_preset": "heuristic",
        "n": 5,
    }
    pubsub_message = create_pubsub_message(message_data)

    response = client.post("/pubsub/push", json=pubsub_message)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "match_id": 1}
    mock_parse_text_for_matching.assert_called_once()

    # Verify the correct arguments were passed
    call_kwargs = mock_parse_text_for_matching.call_args.kwargs
    assert call_kwargs["user_id"] == 1
    assert call_kwargs["text_description"] == "I want to connect with people in tech"
    assert call_kwargs["model_settings_preset"] == "heuristic"
    assert call_kwargs["n"] == 5


@pytest.mark.asyncio
async def test_pubsub_push_text_matching_with_intent(client, mock_parse_text_for_matching):
    """Test Pub/Sub push endpoint with text-based matching and provided intent"""
    message_data = {
        "user_id": 1,
        "text_description": "I want to find a mentor",
        "intent_type": EFormIntentType.mentoring_mentee.value,
        "model_settings_preset": "heuristic",
        "n": 5,
    }
    pubsub_message = create_pubsub_message(message_data)

    response = client.post("/pubsub/push", json=pubsub_message)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "match_id": 1}
    mock_parse_text_for_matching.assert_called_once()

    # Verify the intent type was passed correctly
    call_kwargs = mock_parse_text_for_matching.call_args.kwargs
    assert call_kwargs["intent_type"] == EFormIntentType.mentoring_mentee


@pytest.mark.asyncio
async def test_pubsub_push_text_matching_error(client, mock_parse_text_for_matching):
    """Test error handling in Pub/Sub push endpoint with text-based matching"""
    # Mock an error in the text matching process
    mock_parse_text_for_matching.side_effect = Exception("Matching error")

    message_data = {
        "user_id": 1,
        "text_description": "I want to connect with people",
        "model_settings_preset": "heuristic",
        "n": 5,
    }
    pubsub_message = create_pubsub_message(message_data)

    response = client.post("/pubsub/push", json=pubsub_message)

    assert response.status_code == 500
    assert "Matching error" in response.json()["detail"]
