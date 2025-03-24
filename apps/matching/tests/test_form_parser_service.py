import pytest
from unittest.mock import AsyncMock, patch

from common_db.enums.forms import EFormIntentType
from matching.parser.form_parser_service import FormParserService


@pytest.fixture
def mock_gemini_parser():
    """Create a mock GeminiParser"""
    with patch("matching.parser.form_parser_service.GeminiParser") as mock:
        parser_instance = mock.return_value
        parser_instance.initialize = AsyncMock()
        parser_instance.parse_text_to_form_content = AsyncMock()
        yield parser_instance


@pytest.fixture
def mock_matching_settings():
    """Mock the matching settings"""
    with patch("matching.parser.form_parser_service.matching_settings") as mock:
        mock.matching.project_id = "test-project"
        yield mock


@pytest.fixture
def form_parser_service(mock_gemini_parser, mock_matching_settings):
    """Create a FormParserService instance with mocked dependencies"""
    service = FormParserService()
    # Set initialized directly instead of waiting
    service.initialized = True
    service.parser = mock_gemini_parser
    # Return the actual service object, not the coroutine
    return service


@pytest.mark.asyncio
async def test_initialize(mock_matching_settings):
    """Test service initialization"""
    # Create a new mock for GeminiParser to verify the call
    with patch("matching.parser.form_parser_service.GeminiParser") as mock_gemini_parser_class:
        # Create a mock parser instance
        parser_instance = mock_gemini_parser_class.return_value
        parser_instance.initialize = AsyncMock()
        
        # Create a new service instance
        service = FormParserService()
        
        # Verify initial state
        assert not service.initialized
        
        # Initialize the service
        await service.initialize()
        
        # Verify final state and mock calls
        assert service.initialized
        mock_gemini_parser_class.assert_called_once_with(project_id="test-project")
        parser_instance.initialize.assert_called_once()


@pytest.mark.asyncio
async def test_parse_text_to_form_content(form_parser_service, mock_gemini_parser):
    """Test parsing text to form content"""
    # Mock successful parsing
    mock_content = {"key": "value"}
    mock_gemini_parser.parse_text_to_form_content.return_value = (EFormIntentType.connects, mock_content)

    # Test with provided intent type
    intent_type, content = await form_parser_service.parse_text_to_form_content(
        "I want to connect with people", EFormIntentType.connects
    )

    assert intent_type == EFormIntentType.connects
    assert content == mock_content
    mock_gemini_parser.parse_text_to_form_content.assert_called_once_with(
        "I want to connect with people", EFormIntentType.connects
    )

    # Test with auto-detected intent type
    mock_gemini_parser.parse_text_to_form_content.reset_mock()
    mock_gemini_parser.parse_text_to_form_content.return_value = (EFormIntentType.mentoring_mentee, mock_content)

    intent_type, content = await form_parser_service.parse_text_to_form_content("I want to find a mentor")

    assert intent_type == EFormIntentType.mentoring_mentee
    assert content == mock_content
    mock_gemini_parser.parse_text_to_form_content.assert_called_once_with("I want to find a mentor", None)


@pytest.mark.asyncio
async def test_parse_text_to_form_content_error_handling(form_parser_service, mock_gemini_parser):
    """Test error handling in form content parsing"""
    # Test with parser error
    mock_gemini_parser.parse_text_to_form_content.side_effect = Exception("Parser error")

    # Should return fallback content for the specified intent type
    intent_type, content = await form_parser_service.parse_text_to_form_content("Some text", EFormIntentType.connects)

    assert intent_type == EFormIntentType.connects
    assert "is_local_community" in content
    assert "social_circle_expansion" in content

    # Test with parser error and no intent type
    mock_gemini_parser.parse_text_to_form_content.side_effect = Exception("Parser error")

    # Should default to connects and return fallback content
    intent_type, content = await form_parser_service.parse_text_to_form_content("Some text")

    assert intent_type == EFormIntentType.connects
    assert "is_local_community" in content
    assert "social_circle_expansion" in content


@pytest.mark.parametrize(
    "intent_type",
    [
        EFormIntentType.connects,
        EFormIntentType.mentoring_mentor,
        EFormIntentType.mentoring_mentee,
        EFormIntentType.referrals_recommendation,
        EFormIntentType.mock_interview,
        EFormIntentType.projects_find_cofounder,
        EFormIntentType.projects_find_contributor,
        EFormIntentType.projects_pet_project,
    ],
)
def test_create_fallback_content(form_parser_service, intent_type):
    """Test fallback content creation for each intent type"""
    content = form_parser_service._create_fallback_content(intent_type)

    # Verify content structure based on intent type
    if intent_type == EFormIntentType.connects:
        assert "is_local_community" in content
        assert "social_circle_expansion" in content
    elif intent_type == EFormIntentType.mentoring_mentor:
        assert "required_grade" in content
        assert "specialization" in content
        assert "help_request" in content
    elif intent_type == EFormIntentType.mentoring_mentee:
        assert "grade" in content
        assert "mentor_specialization" in content
        assert "help_request" in content
    elif intent_type == EFormIntentType.referrals_recommendation:
        assert "is_local_community" in content
        assert "is_all_experts_type" in content
        assert "company_type" in content
    elif intent_type == EFormIntentType.mock_interview:
        assert "interview_type" in content
        assert "language" in content
        assert "resume" in content
    elif intent_type in [EFormIntentType.projects_find_cofounder, EFormIntentType.projects_find_contributor]:
        assert "project_description" in content
        assert "specialization" in content
        assert "project_state" in content
    elif intent_type == EFormIntentType.projects_pet_project:
        assert "project_description" in content
        assert "specialization" in content
        assert "role" in content

    # Test unknown intent type
    unknown_content = form_parser_service._create_fallback_content("unknown_intent")
    assert "note" in unknown_content
    assert unknown_content["note"] == "Fallback content - parsing failed"


def test_normalize_object_types():
    """Test normalization of object types for compatibility with old and new schemas"""
    # Create a service instance directly (no async here)
    service = FormParserService()
    
    # Test with different data types and structures
    
    # Test case 1: Simple fields that should be arrays
    content1 = {
        "expertise_area": "development",
        "specialization": "backend",
        "skills": "python",
    }
    
    normalized1 = service._normalize_object_types(content1)
    
    # Verify normalization worked
    assert normalized1 is content1  # Should modify in place
    assert isinstance(normalized1["expertise_area"], list)
    assert normalized1["expertise_area"] == ["development"]
    assert isinstance(normalized1["specialization"], list)
    assert normalized1["specialization"] == ["backend"]
    assert isinstance(normalized1["skills"], list)
    assert normalized1["skills"] == ["python"]
    
    # Test case 2: Already correct array fields
    content2 = {
        "expertise_area": ["development", "design"],
        "skills": ["python", "javascript"],
    }
    
    normalized2 = service._normalize_object_types(content2)
    
    # Verify normalization preserves existing lists
    assert normalized2 is content2  # Should modify in place
    assert normalized2["expertise_area"] == ["development", "design"]
    assert normalized2["skills"] == ["python", "javascript"]
    
    # Test case 3: None/missing fields
    content3 = {
        "expertise_area": None,
        "other_field": "value",
    }
    
    normalized3 = service._normalize_object_types(content3)
    
    # Verify None becomes empty list
    assert normalized3 is content3  # Should modify in place
    assert normalized3["expertise_area"] == []
    assert normalized3["other_field"] == "value"  # Non-list field untouched
    
    # Test case 4: Nested objects
    content4 = {
        "social_circle_expansion": {
            "topics": "networking",
            "meeting_formats": ["online"],
        },
        "skills": ["python"],
    }
    
    normalized4 = service._normalize_object_types(content4)
    
    # Verify nested objects get normalized
    assert normalized4 is content4  # Should modify in place
    assert isinstance(normalized4["social_circle_expansion"]["topics"], list)
    assert normalized4["social_circle_expansion"]["topics"] == ["networking"]
    assert normalized4["social_circle_expansion"]["meeting_formats"] == ["online"]
    assert normalized4["skills"] == ["python"]
    
    # Test case 5: Nested objects in lists
    content5 = {
        "custom_objects": [
            {"specialization": "frontend"},
            {"specialization": ["backend"]},
        ]
    }
    
    normalized5 = service._normalize_object_types(content5)
    
    # Verify objects in lists get normalized
    assert normalized5 is content5  # Should modify in place
    assert isinstance(normalized5["custom_objects"][0]["specialization"], list)
    assert normalized5["custom_objects"][0]["specialization"] == ["frontend"]
    assert normalized5["custom_objects"][1]["specialization"] == ["backend"]
    
    # Verify that all of the above assertions have run
    assert True
