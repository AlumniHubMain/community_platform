import sys
from pathlib import Path
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)
from matching.matching import process_matching_request
from matching.model.model_settings import (
    ModelType,
    FilterType,
    DiversificationType,
    HeuristicModelSettings,
    DiversificationSettings,
    FilterSettings,
)
from common_db.schemas import (
    SUserProfileRead,
    SMeetingIntentRead,
)
from common_db.enums.meeting_intents import (
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
def mock_session(mock_users, mock_intent):
    class MockAsyncSession:
        def __init__(self):
            self._id_counter = 1
            self._stored_objects = {}
            self.mock_users = mock_users
            self.mock_intent = mock_intent

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

        async def execute(self, statement):
            from sqlalchemy import Select
            from common_db.models import ORMUserProfile, ORMMeetingIntent

            class MockResult:
                def __init__(self, results):
                    self._results = results

                def scalar_one_or_none(self):
                    return self._results[0] if self._results else None

                def scalars(self):
                    class MockScalars:
                        def __init__(self, results):
                            self._results = results

                        def all(self):
                            return self._results

                    return MockScalars(self._results)

            if isinstance(statement, Select):
                # Check the primary entity of the select
                entity = statement.column_descriptions[0]["entity"]
                if entity == ORMUserProfile:
                    return MockResult(self.mock_users)
                elif entity == ORMMeetingIntent:
                    return MockResult([self.mock_intent])
            return MockResult([])

    class AsyncSessionContextManager:
        def __init__(self):
            self.session = MockAsyncSession()

        async def __aenter__(self):
            return self.session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            await self.session.close()

    def session_factory():
        return AsyncSessionContextManager()

    return session_factory  # Return the factory function instead of the class


@pytest.fixture
def mock_data_loader():
    with patch("matching.data_loader.DataLoader", autospec=True) as mock:
        # Remove the mocked methods to let the session handle the data
        yield mock


@pytest.fixture
def mock_model_settings():
    with patch("matching.model.model_settings.model_settings_presets", autospec=True) as mock_settings:
        mock_settings.__contains__.return_value = True
        mock_settings.__getitem__.return_value = HeuristicModelSettings(
            model_type=ModelType.HEURISTIC,
            settings_name="heuristic",
            rules=[],
            filters=[],
            diversifications=[],
        )
        yield mock_settings


@pytest.mark.asyncio
async def test_process_matching_basic(
    mock_session,
    mock_data_loader,
    mock_model_settings,
):
    """Test basic matching process with heuristic preset"""

    settings = HeuristicModelSettings(
        model_type=ModelType.HEURISTIC,
        settings_name="heuristic",
        rules=[],
        filters=[],
        diversifications=[],
    )
    mock_model_settings.__getitem__.return_value = settings

    match_id, predictions = await process_matching_request(
        db_session_callable=mock_session,
        psclient=None,
        logger=MagicMock(),
        user_id=1,
        meeting_intent_id=1,
        model_settings_preset="heuristic",
        n=2,
    )

    # Add debug prints
    print(f"Predictions: {predictions}")

    assert match_id == 1
    assert isinstance(predictions, list)
    assert len(predictions) == 2
    assert 2 in predictions
    assert 3 in predictions


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
    with patch("matching.matching.DataLoader") as mock_dl:
        mock_dl.get_all_user_profiles.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await process_matching_request(
                db_session_callable=mock_session,  # Pass the factory function directly
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


@pytest.mark.asyncio
async def test_process_matching_with_filters_context_manager(mock_session, mock_data_loader):
    """Test matching process with strict filters"""
    with patch("matching.matching.model_settings_presets") as mock_model_settings:
        # Create settings with explicit filter
        settings = HeuristicModelSettings(
            model_type=ModelType.HEURISTIC,
            settings_name="heuristic",
            rules=[],
            filters=[
                FilterSettings(
                    filter_type=FilterType.STRICT,
                    filter_name="expertise_filter",
                    filter_column="expertise_area",
                    filter_rule="development",
                )
            ],
            diversifications=[],
        )
        mock_model_settings.__getitem__.return_value = settings
        mock_model_settings.__contains__.return_value = True

        match_id, predictions = await process_matching_request(
            db_session_callable=mock_session,
            psclient=None,
            logger=MagicMock(),
            user_id=1,
            meeting_intent_id=1,
            model_settings_preset="heuristic",
            n=5,
        )

        assert 3 not in predictions  # User 3 should be filtered out (no development expertise)
