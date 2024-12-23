import sys
from pathlib import Path
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch


# Add the microservice root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)
from app.matching import process_matching_request
from app.model.model_settings import (
    ModelType,
    FilterType,
    DiversificationType,
    HeuristicModelSettings,
    DiversificationSettings,
    FilterSettings,
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


# Test data fixtures
@pytest.fixture
def mock_users():
    return [
        SUserProfileRead(
            id=1,
            name="John",
            surname="Doe",
            email="john@example.com",
            expertise_area=["development"],
            industry=["industry1"],
            meeting_responses=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        SUserProfileRead(
            id=2,
            name="Jane",
            surname="Smith",
            email="jane@example.com",
            expertise_area=["development"],
            industry=["industry1"],
            meeting_responses=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        SUserProfileRead(
            id=3,
            name="Bob",
            surname="Wilson",
            email="bob@example.com",
            expertise_area=["marketing"],
            industry=["industry2"],
            meeting_responses=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]


@pytest.fixture
def mock_linkedin():
    return [
        SLinkedInProfileRead(
            user_id=1,
            industry="Technology",
            skills={"python": 5, "java": 3},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            id=1,
            profile_url="https://linkedin.com/john",
        ),
        SLinkedInProfileRead(
            user_id=2,
            industry="Technology",
            skills={"python": 4, "javascript": 5},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            id=2,
            profile_url="https://linkedin.com/jane",
        ),
        SLinkedInProfileRead(
            user_id=3,
            industry="Marketing",
            skills={"marketing": 5, "social media": 4},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            id=3,
            profile_url="https://linkedin.com/bob",
        ),
    ]


@pytest.fixture
def mock_intent():
    return SMeetingIntentRead(
        id=1,
        user_id=1,
        meeting_type=EMeetingIntentMeetingType.online,
        looking_for_type=EMeetingIntentLookingForType.part_time,
        query_type=EMeetingIntentQueryType.looking_for,
        help_request_type=EMeetingIntentHelpRequestType.development,
        text_intent="Looking for Python developers",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_session():
    class MockAsyncSession:
        def __init__(self):
            self._id_counter = 1
            self._stored_objects = {}

        def add(self, obj):
            self._stored_objects[id(obj)] = obj

        async def commit(self):
            for obj in self._stored_objects.values():
                if not hasattr(obj, "id"):
                    setattr(obj.__class__, "id", property(lambda self: self._id))
                    setattr(obj, "_id", self._id_counter)
                    self._id_counter += 1

        async def refresh(self, obj):
            stored_obj = self._stored_objects.get(id(obj))
            if stored_obj is not None and not hasattr(stored_obj, "_id"):
                setattr(obj.__class__, "id", property(lambda self: self._id))
                setattr(stored_obj, "_id", self._id_counter)
                self._id_counter += 1

        async def close(self):
            pass

    class AsyncSessionContextManager:
        def __init__(self):
            self.session = MockAsyncSession()

        async def __aenter__(self):
            return self.session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            await self.session.close()

    def session_factory():
        return AsyncSessionContextManager()

    return session_factory


@pytest.fixture
def mock_data_loader(mock_users, mock_linkedin, mock_intent):
    with patch("app.matching.DataLoader", autospec=True) as mock:
        mock.get_all_user_profiles = AsyncMock(return_value=mock_users)
        mock.get_all_linkedin_profiles = AsyncMock(return_value=mock_linkedin)
        mock.get_meeting_intent = AsyncMock(return_value=mock_intent)
        yield mock


@pytest.fixture
def mock_model_settings():
    with patch("app.matching.model_settings_presets", autospec=True) as mock_settings:
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
                },
                {
                    "column": "skills_linkedin",
                    "operation": "contains",
                    "value": "python",
                    "weight": 0.3,
                },
            ],
            filters=[
                FilterSettings(
                    filter_type=FilterType.STRICT,
                    filter_name="expertise_filter",
                    filter_column="expertise_area",
                    filter_rule="development",
                )
            ],
            diversifications=[
                DiversificationSettings(
                    diversification_type=DiversificationType.SCORE_BASED,
                    diversification_name="industry_div",
                    diversification_column="industry_user",
                    diversification_value=2,
                )
            ],
        )
        yield mock_settings


@pytest.mark.asyncio
async def test_process_matching_basic(
    mock_session,
    mock_data_loader,
    mock_model_settings,
):
    """Test basic matching process with heuristic preset"""
    match_id, predictions = await process_matching_request(
        db_session_callable=mock_session,
        psclient=None,  # Not needed for heuristic
        logger=MagicMock(),
        user_id=1,
        meeting_intent_id=1,
        model_settings_preset="heuristic",
        n=2,
    )

    assert match_id == 1  # First ID from counter
    assert isinstance(predictions, list)
    assert len(predictions) <= 2  # Should not exceed n
    assert 2 in predictions  # User 2 should be matched (similar profile)
    assert 3 not in predictions  # User 3 should be filtered out (different expertise)


@pytest.mark.asyncio
async def test_process_matching_with_filters(
    mock_session,
    mock_data_loader,
    mock_model_settings,
):
    """Test matching process with strict filters"""
    # Modify the mock settings to use strict filtering
    mock_model_settings.__getitem__.return_value.filters = [
        FilterSettings(
            filter_type=FilterType.STRICT,
            filter_name="industry_filter",
            filter_column="industry_user",
            filter_rule="Technology",
        )
    ]

    match_id, predictions = await process_matching_request(
        db_session_callable=mock_session,
        psclient=None,
        logger=MagicMock(),
        user_id=1,
        meeting_intent_id=1,
        model_settings_preset="heuristic",
        n=5,
    )

    assert 3 not in predictions  # User 3 should be filtered out (different industry)


@pytest.mark.asyncio
async def test_process_matching_with_diversification(
    mock_session,
    mock_data_loader,
    mock_model_settings,
):
    """Test matching process with diversification"""
    # Modify the mock settings to use diversification
    mock_model_settings.__getitem__.return_value.diversifications = [
        DiversificationSettings(
            diversification_type=DiversificationType.PROPORTIONAL,
            diversification_name="industry_div",
            diversification_column="industry_user",
            diversification_value=2,
        )
    ]

    match_id, predictions = await process_matching_request(
        db_session_callable=mock_session,
        psclient=None,
        logger=MagicMock(),
        user_id=1,
        meeting_intent_id=1,
        model_settings_preset="heuristic",
        n=3,
    )

    assert len(predictions) <= 3
    # Should include at least one user from a different industry for diversity
    assert any(uid in predictions for uid in [2, 3])


@pytest.mark.asyncio
async def test_process_matching_error_handling(
    mock_session,
    mock_data_loader,
    mock_model_settings,
):
    """Test error handling in matching process"""
    # Simulate an error in data loading
    mock_data_loader.get_all_user_profiles.side_effect = Exception("Database error")

    with pytest.raises(Exception):
        await process_matching_request(
            db_session_callable=mock_session,
            psclient=None,
            logger=MagicMock(),
            user_id=1,
            meeting_intent_id=1,
            model_settings_preset="heuristic",
            n=2,
        )


@pytest.mark.asyncio
async def test_process_matching_invalid_preset(
    mock_session,
    mock_data_loader,
):
    """Test handling of invalid model preset"""
    with pytest.raises(ValueError, match="Invalid model settings preset"):
        await process_matching_request(
            db_session_callable=mock_session,
            psclient=None,
            logger=MagicMock(),
            user_id=1,
            meeting_intent_id=1,
            model_settings_preset="invalid_preset",
            n=2,
        )
