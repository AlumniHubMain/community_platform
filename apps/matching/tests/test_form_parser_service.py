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
async def form_parser_service(mock_gemini_parser, mock_matching_settings):
    """Create a FormParserService instance with mocked dependencies"""
    service = FormParserService()
    await service.initialize()
    return service


@pytest.mark.asyncio
async def test_initialize(mock_gemini_parser, mock_matching_settings):
    """Test service initialization"""
    service = FormParserService()

    assert not service.initialized
    await service.initialize()
    assert service.initialized

    mock_gemini_parser.assert_called_once_with(project_id="test-project")
    mock_gemini_parser.return_value.initialize.assert_called_once()


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
        assert "langluage" in content
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
