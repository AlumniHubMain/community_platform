import pytest
import base64
import json
import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from common_db.enums.forms import EFormIntentType
from matching.main import app as fastapi_app


# Create a mock class to replace FormRead
class MockFormRead:
    """Mock implementation of FormRead for testing"""
    def __init__(self, id, user_id, intent, content, created_at=None, updated_at=None, description=None):
        self.id = id
        self.user_id = user_id
        self.intent = intent
        self.content = content
        self.created_at = created_at or datetime.datetime.now()
        self.updated_at = updated_at or datetime.datetime.now()
        self.description = description
        
    @property
    def meeting_format(self):
        """Mock implementation of meeting_format property"""
        if self.intent == EFormIntentType.connects:
            if 'social_circle_expansion' in self.content:
                formats = self.content['social_circle_expansion'].get('meeting_formats', [])
                return formats[0] if formats else None
        return self.content.get('meeting_format', 'any')
    
    @property
    def specialization(self):
        """Mock implementation of specialization property"""
        return self.content.get('specialization', [])
    
    @property
    def required_grade(self):
        """Mock implementation of required_grade property"""
        return self.content.get('required_grade', [])


@pytest.fixture
def mock_form_read():
    """Mock the FormRead pydantic model"""
    with patch("matching.matching.FormRead", MockFormRead):
        yield


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
        # Create a fixed session context manager
        class AsyncSessionContext:
            async def __aenter__(self):
                return AsyncMock()

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
                
        # Set the session attribute to return the context manager directly
        mock.session = lambda: AsyncSessionContext()
        yield mock


@pytest.fixture
def mock_storage():
    with patch("matching.main.CloudStorageAdapter") as mock:
        instance = mock.return_value
        instance.initialize = AsyncMock()
        yield instance


@pytest.fixture
def mock_orm_matching_result():
    """Mock the ORMMatchingResult model to avoid validation errors"""
    with patch("matching.matching.ORMMatchingResult") as mock:
        # Return a MagicMock instance that can have any attributes
        instance = MagicMock()
        instance.id = 1  # Default ID to return
        mock.return_value = instance
        yield mock


@pytest.fixture
def client(mock_db_manager, mock_storage, mock_form_read, mock_orm_matching_result):
    return TestClient(fastapi_app)


@pytest.fixture
def mock_parse_text_for_matching():
    """Create a mock for parse_text_for_matching that handles async correctly"""
    mock = AsyncMock()
    mock.return_value = (1, [2, 3, 4])
    
    with patch("matching.main.parse_text_for_matching", mock):
        yield mock


@pytest.mark.asyncio
async def test_pubsub_push_text_matching(client, mock_parse_text_for_matching, mock_form_read):
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
async def test_pubsub_push_text_matching_with_intent(client, mock_parse_text_for_matching, mock_form_read):
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
async def test_pubsub_push_text_matching_error(client, mock_parse_text_for_matching, mock_form_read):
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
