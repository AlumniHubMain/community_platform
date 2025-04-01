import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import logging
import datetime

from common_db.enums.forms import EFormIntentType
from common_db.models import ORMMatchingResult
from matching.matching import parse_text_for_matching


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
def mock_form_parser_service():
    """Mock the FormParserService"""
    with patch("matching.matching.form_parser_service") as mock:
        # Don't use async properties directly as they are coroutines that must be awaited
        # Instead, set attributes directly on the mock
        mock.initialized = True  # Set as already initialized to avoid await
        mock.initialize = AsyncMock()
        mock.parse_text_to_form_content = AsyncMock()
        yield mock


@pytest.fixture
def mock_form_read():
    """Mock the FormRead pydantic model"""
    with patch("matching.matching.FormRead", MockFormRead):
        yield


@pytest.fixture
def mock_data_loader():
    """Mock the DataLoader class"""
    with patch("matching.matching.DataLoader") as mock:
        mock.get_all_user_profiles = AsyncMock(return_value=[])
        mock.get_all_linkedin_profiles = AsyncMock(return_value=[])
        
        # For the get_form method, return None by default (no form exists)
        mock.get_form = AsyncMock(return_value=None)
        
        yield mock


@pytest.fixture
def mock_form():
    """Create a mock form object with required properties"""
    form = MagicMock()
    form.id = 1
    form.user_id = 1
    form.intent = EFormIntentType.connects
    form.content = {
        "is_local_community": True,
        "social_circle_expansion": {
            "meeting_formats": ["online"],
            "topics": ["general_networking"],
            "details": "Looking to meet new people in tech",
        }
    }
    form.created_at = datetime.datetime.now()
    form.updated_at = datetime.datetime.now()
    return form


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

    class AsyncSessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # Return the context manager directly, not a factory function
    return AsyncSessionContext()


@pytest.mark.asyncio
async def test_parse_text_for_matching(
    mock_session, mock_form_parser_service, mock_data_loader, mock_model, mock_limits_manager, mock_model_settings, mock_form_read
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

    # Mock the ORMMatchingResult creation
    with patch("matching.matching.ORMMatchingResult") as mock_orm:
        # Configure the mock to store the additional_data as an attribute
        mock_instance = MagicMock()
        mock_orm.return_value = mock_instance
        
        # Call the function
        match_id, predictions = await parse_text_for_matching(
            db_session_callable=lambda: mock_session,  # Pass the session directly as a callable
            psclient=MagicMock(),
            logger=logging.getLogger(),
            user_id=1,
            text_description="I want to connect with people in tech",
            intent_type=None,  # Auto-detect intent
            model_settings_preset="heuristic",
            n=5,
        )

        # Verify the parser was initialized (since we set initialized=True, this shouldn't be called)
        mock_form_parser_service.initialize.assert_not_called()
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
        session = await mock_session.__aenter__()
        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

        # Verify the saved result has the correct structure
        saved_result = session.add.call_args[0][0]
        assert saved_result is mock_instance
        assert mock_orm.call_args.kwargs["user_id"] == 1
        assert mock_orm.call_args.kwargs["form_id"] is None  # No form ID for text-based matching
        assert mock_orm.call_args.kwargs["matching_result"] == [2, 3]
        
        # Check that additional_data was passed to the constructor
        assert "additional_data" in mock_orm.call_args.kwargs
        additional_data = mock_orm.call_args.kwargs["additional_data"]
        assert "parsed_content" in additional_data
        assert "text_description" in additional_data
        assert "intent_type" in additional_data


@pytest.mark.asyncio
async def test_parse_text_for_matching_with_provided_intent(
    mock_session, mock_form_parser_service, mock_data_loader, mock_model, mock_limits_manager, mock_model_settings, mock_form, mock_form_read
):
    """Test the text-based matching process with provided intent type"""
    # Configure the mock to return a tuple of (intent_type, content)
    intent_type = EFormIntentType.mentoring_mentee
    form_content = {
        "grade": ["junior"],
        "mentor_specialization": ["development__backend"],
        "help_request": {
            "request": ["career_growth"],
        },
        "details": "Looking for a mentor to help with career growth",
    }
    mock_form_parser_service.parse_text_to_form_content.return_value = (intent_type, form_content)
    
    # Mock the ORMMatchingResult creation
    with patch("matching.matching.ORMMatchingResult") as mock_orm:
        # Configure the mock to store the additional_data as an attribute
        mock_instance = MagicMock()
        mock_orm.return_value = mock_instance
        
        # Call the function with provided intent
        match_id, predictions = await parse_text_for_matching(
            db_session_callable=lambda: mock_session,
            psclient=MagicMock(),
            logger=logging.getLogger(),
            user_id=1,
            text_description="I want a mentor",
            intent_type=intent_type,
            model_settings_preset="heuristic",
            n=5,
        )

        # Verify the parser was called with the provided intent
        mock_form_parser_service.parse_text_to_form_content.assert_called_once_with(
            "I want a mentor", intent_type
        )

        # Verify the saved result has the correct intent type
        session = await mock_session.__aenter__()
        saved_result = session.add.call_args[0][0]
        assert saved_result is mock_instance
        
        # Check that additional_data was passed to the constructor
        assert "additional_data" in mock_orm.call_args.kwargs
        additional_data = mock_orm.call_args.kwargs["additional_data"]
        assert "intent_type" in additional_data
        assert additional_data["intent_type"] == intent_type.value


@pytest.mark.asyncio
async def test_parse_text_for_matching_error_handling(mock_session, mock_form_parser_service, mock_data_loader, mock_form_read):
    """Test error handling in the text-based matching process"""
    # Mock a parser error
    mock_form_parser_service.parse_text_to_form_content.side_effect = Exception("Parser error")

    # Mock the ORMMatchingResult creation
    with patch("matching.matching.ORMMatchingResult") as mock_orm:
        # Configure the mock to store error details as attributes
        mock_instance = MagicMock()
        mock_orm.return_value = mock_instance
        
        # Call the function
        with pytest.raises(Exception):
            await parse_text_for_matching(
                db_session_callable=lambda: mock_session,  # Pass the session directly as a callable
                psclient=MagicMock(),
                logger=logging.getLogger(),
                user_id=1,
                text_description="I want to connect with people",
                intent_type=None,
                model_settings_preset="heuristic",
                n=5,
            )

        # Verify error result was saved
        session = await mock_session.__aenter__()
        saved_result = session.add.call_args[0][0]
        assert saved_result is mock_instance
        
        # Check constructor arguments
        assert mock_orm.call_args.kwargs["user_id"] == 1
        assert mock_orm.call_args.kwargs["form_id"] is None
        assert mock_orm.call_args.kwargs["error_code"] == "TEXT_MATCHING_ERROR"
        
        # Check error details
        error_details = mock_orm.call_args.kwargs["error_details"]
        assert "error" in error_details
        assert error_details["text_description"] == "I want to connect with people"
