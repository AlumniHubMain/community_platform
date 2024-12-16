import os
import sys
from pathlib import Path
from datetime import datetime

# Add the microservice root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.model.model_settings import (
    ModelType,
    FilterType,
    DiversificationType,
    CatBoostModelSettings,
    HeuristicModelSettings,
)
from db_common.schemas import (
    SUserProfileRead,
    SLinkedInProfileRead,
    SMeetingIntentRead,
)
from db_common.enums.meeting_intents import (
    EMeetingIntentMeetingType,
    EMeetingIntentLookingForType,
    EMeetingIntentQueryType,
    EMeetingIntentHelpRequestType,
)

# Mock test data
mock_users = [
    SUserProfileRead(
        id=1,
        name="John",
        surname="Doe",
        email="john@example.com",
        meeting_responses=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
    SUserProfileRead(
        id=2,
        name="Jane",
        surname="Smith",
        email="jane@example.com",
        meeting_responses=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ),
]

mock_linkedin = [
    SLinkedInProfileRead(
        user_id=1,
        industry="Technology",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        id=1,
        profile_url="https://www.linkedin.com/in/john-doe-1234567890",
    ),
    SLinkedInProfileRead(
        user_id=2,
        industry="Technology",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        id=2,
        profile_url="https://www.linkedin.com/in/jane-smith-1234567890",
    ),
]

mock_intent = SMeetingIntentRead(
    id=1,
    user_id=1,
    meeting_type=EMeetingIntentMeetingType.online,
    looking_for_type=EMeetingIntentLookingForType.part_time,
    query_type=EMeetingIntentQueryType.looking_for,
    help_request_type=EMeetingIntentHelpRequestType.other,
    text_intent="Looking for part-time work",
    created_at=datetime.now(),
    updated_at=datetime.now(),
)


@pytest.fixture
def client():
    return TestClient(fastapi_app)


@pytest.fixture
def mock_data_loader():
    with patch("app.main.DataLoader") as mock:
        mock.get_all_user_profiles = AsyncMock(return_value=mock_users)
        mock.get_all_linkedin_profiles = AsyncMock(return_value=mock_linkedin)
        mock.get_meeting_intent = AsyncMock(return_value=mock_intent)
        yield mock


@pytest.fixture
def mock_queue_manager():
    with patch("app.main.queue_manager") as mock:
        mock.put_to_queue = AsyncMock()
        yield mock


@pytest.fixture
def mock_ps_client():
    with patch("app.main.psclient") as mock:
        mock.get_file = MagicMock(return_value="mock_model_path")
        yield mock


# @pytest.mark.asyncio
# async def test_get_matches_catboost(client, mock_data_loader, mock_queue_manager, mock_ps_client):
#     """Test matching endpoint with CatBoost model settings"""
#     # Update model settings for CatBoost
#     with patch("app.main.model_settings_presets") as mock_settings:
#         mock_settings["catboost"] = CatBoostModelSettings(
#             model_type=ModelType.CATBOOST,
#             model_path="mock_model.cbm",
#             settings_name="catboost",
#             filters=[],
#             diversifications=[],
#         )

#         response = client.get("/get_matches/1/1/catboost/5")

#         assert response.status_code == 200
#         mock_queue_manager.put_to_queue.assert_called_once()
#         mock_ps_client.get_file.assert_called_once()


@pytest.mark.asyncio
async def test_get_matches_heuristic(client, mock_data_loader, mock_queue_manager):
    """Test matching endpoint with heuristic model settings"""
    # Update model settings for heuristic approach
    with patch("app.main.model_settings_presets") as mock_settings:
        mock_settings.__contains__.return_value = True
        mock_settings.__getitem__.return_value = HeuristicModelSettings(
            model_type=ModelType.HEURISTIC,
            settings_name="heuristic",
            rules=[
                {
                    "column": "industry_user",
                    "operation": "equals",
                    "value": "Technology",
                    "weight": 0.5,
                }
            ],
            filters=[],
            diversifications=[],
        )

        response = client.get("/get_matches/1/1/heuristic/5")

        assert response.status_code == 200
        mock_queue_manager.put_to_queue.assert_called_once()


@pytest.mark.asyncio
async def test_get_matches_with_filters(client, mock_data_loader, mock_queue_manager):
    """Test matching endpoint with filters"""
    with patch("app.main.model_settings_presets") as mock_settings:
        mock_settings.__contains__.return_value = True
        mock_settings.__getitem__.return_value = HeuristicModelSettings(
            model_type=ModelType.HEURISTIC,
            settings_name="filtered",
            rules=[],
            filters=[
                {
                    "filter_type": FilterType.STRICT,
                    "filter_name": "industry_filter",
                    "filter_column": "industry_user",
                    "filter_rule": "Technology",
                }
            ],
            diversifications=[],
        )

        response = client.get("/get_matches/1/1/filtered/5")

        assert response.status_code == 200
        mock_queue_manager.put_to_queue.assert_called_once()


@pytest.mark.asyncio
async def test_get_matches_with_diversification(client, mock_data_loader, mock_queue_manager):
    """Test matching endpoint with diversification settings"""
    with patch("app.main.model_settings_presets") as mock_settings:
        mock_settings.__contains__.return_value = True
        mock_settings.__getitem__.return_value = HeuristicModelSettings(
            model_type=ModelType.HEURISTIC,
            settings_name="diverse",
            rules=[],
            filters=[],
            diversifications=[
                {
                    "diversification_type": DiversificationType.SCORE_BASED,
                    "diversification_name": "industry_div",
                    "diversification_column": "industry_user",
                    "diversification_value": 2,
                }
            ],
        )

        response = client.get("/get_matches/1/1/diverse/5")

        assert response.status_code == 200
        mock_queue_manager.put_to_queue.assert_called_once()


@pytest.mark.asyncio
async def test_get_matches_invalid_user(client, mock_data_loader, mock_queue_manager):
    """Test matching endpoint with invalid user ID"""
    mock_data_loader.get_meeting_intent.side_effect = Exception("Intent not found")

    response = client.get("/get_matches/1/999/heuristic/5")

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_get_matches_invalid_preset(client, mock_data_loader, mock_queue_manager):
    """Test matching endpoint with invalid model settings preset"""
    response = client.get("/get_matches/1/1/invalid_preset/5")

    assert response.status_code == 500
