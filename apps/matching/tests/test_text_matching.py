import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import logging

from common_db.enums.forms import EFormIntentType
from common_db.models import ORMMatchingResult
from matching.matching import parse_text_for_matching


@pytest.fixture
def mock_form_parser_service():
    """Mock the FormParserService"""
    with patch("matching.matching.form_parser_service") as mock:
        mock.initialized = False
        mock.initialize = AsyncMock()
        mock.parse_text_to_form_content = AsyncMock()
        yield mock


@pytest.fixture
def mock_data_loader():
    """Mock the DataLoader class"""
    with patch("matching.matching.DataLoader") as mock:
        mock.get_all_user_profiles = AsyncMock(return_value=[])
        mock.get_all_linkedin_profiles = AsyncMock(return_value=[])
        yield mock


@pytest.fixture
def mock_model():
    """Mock the Model class"""
    with patch("matching.matching.Model") as mock:
        model_instance = mock.return_value
        model_instance.load_model = MagicMock()
        model_instance.predict = MagicMock(return_value=[2, 3, 4])
        yield model_instance


@pytest.fixture
def mock_limits_manager():
    """Mock the LimitsManager class"""
    with patch("matching.matching.LimitsManager") as mock:
        mock.filter_users_by_limits = AsyncMock(return_value=[2, 3])
        yield mock


@pytest.fixture
def mock_model_settings():
    """Mock the model settings"""
    with patch("matching.matching.model_settings_presets") as mock:
        mock_settings = MagicMock()
        mock_settings.model_type = "heuristic"
        mock.__getitem__.return_value = mock_settings
        mock.__contains__.return_value = True
        yield mock


@pytest.fixture
def mock_session():
    """Create a mock database session"""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    async def session_factory():
        class AsyncSessionContext:
            async def __aenter__(self):
                return session

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        return AsyncSessionContext()

    return session_factory


@pytest.mark.asyncio
async def test_parse_text_for_matching(
    mock_session, mock_form_parser_service, mock_data_loader, mock_model, mock_limits_manager, mock_model_settings
):
    """Test the text-based matching process"""
    # Mock the form parser response
    mock_form_parser_service.parse_text_to_form_content.return_value = (
        EFormIntentType.connects,
        {
            "is_local_community": True,
            "social_circle_expansion": {
                "meeting_formats": ["online"],
                "topics": ["general_networking"],
                "details": "Looking to meet new people in tech",
            },
        },
    )

    # Call the function
    match_id, predictions = await parse_text_for_matching(
        db_session_callable=mock_session,
        psclient=MagicMock(),
        logger=logging.getLogger(),
        user_id=1,
        text_description="I want to connect with people in tech",
        intent_type=None,  # Auto-detect intent
        model_settings_preset="heuristic",
        n=5,
    )

    # Verify the parser was initialized and called
    mock_form_parser_service.initialize.assert_called_once()
    mock_form_parser_service.parse_text_to_form_content.assert_called_once_with(
        "I want to connect with people in tech", None
    )

    # Verify the model was used correctly
    mock_model.predict.assert_called_once()

    # Verify limits were applied
    mock_limits_manager.filter_users_by_limits.assert_called_once()

    # Verify results
    assert predictions == [2, 3]  # Filtered predictions

    # Verify matching result was saved
    session = await mock_session().__aenter__()
    session.add.assert_called_once()
    session.commit.assert_called_once()
    session.refresh.assert_called_once()

    # Verify the saved result has the correct structure
    saved_result = session.add.call_args[0][0]
    assert isinstance(saved_result, ORMMatchingResult)
    assert saved_result.user_id == 1
    assert saved_result.form_id is None  # No form ID for text-based matching
    assert saved_result.matching_result == [2, 3]
    assert "parsed_content" in saved_result.additional_data
    assert "text_description" in saved_result.additional_data
    assert "intent_type" in saved_result.additional_data


@pytest.mark.asyncio
async def test_parse_text_for_matching_with_provided_intent(
    mock_session, mock_form_parser_service, mock_data_loader, mock_model, mock_limits_manager, mock_model_settings
):
    """Test the text-based matching process with provided intent type"""
    # Mock the form parser response
    mock_form_parser_service.parse_text_to_form_content.return_value = (
        EFormIntentType.mentoring_mentee,  # Should use this despite provided intent
        {
            "grade": ["junior"],
            "mentor_specialization": ["development__backend"],
            "help_request": {
                "request": ["career_growth"],
            },
            "details": "Looking for a mentor to help with career growth",
        },
    )

    # Call the function with provided intent
    match_id, predictions = await parse_text_for_matching(
        db_session_callable=mock_session,
        psclient=MagicMock(),
        logger=logging.getLogger(),
        user_id=1,
        text_description="I want a mentor",
        intent_type=EFormIntentType.mentoring_mentee,  # Provide intent
        model_settings_preset="heuristic",
        n=5,
    )

    # Verify the parser was called with the provided intent
    mock_form_parser_service.parse_text_to_form_content.assert_called_once_with(
        "I want a mentor", EFormIntentType.mentoring_mentee
    )

    # Verify the saved result has the correct intent type
    session = await mock_session().__aenter__()
    saved_result = session.add.call_args[0][0]
    assert saved_result.additional_data["intent_type"] == EFormIntentType.mentoring_mentee.value


@pytest.mark.asyncio
async def test_parse_text_for_matching_error_handling(mock_session, mock_form_parser_service, mock_data_loader):
    """Test error handling in the text-based matching process"""
    # Mock a parser error
    mock_form_parser_service.parse_text_to_form_content.side_effect = Exception("Parser error")

    # Call the function
    with pytest.raises(Exception):
        await parse_text_for_matching(
            db_session_callable=mock_session,
            psclient=MagicMock(),
            logger=logging.getLogger(),
            user_id=1,
            text_description="I want to connect with people",
            intent_type=None,
            model_settings_preset="heuristic",
            n=5,
        )

    # Verify error result was saved
    session = await mock_session().__aenter__()
    saved_result = session.add.call_args[0][0]
    assert isinstance(saved_result, ORMMatchingResult)
    assert saved_result.error_code == "TEXT_MATCHING_ERROR"
    assert "error" in saved_result.error_details
    assert "text_description" in saved_result.error_details
