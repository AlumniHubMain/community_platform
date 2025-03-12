import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from common_db.enums.forms import EFormIntentType
from matching.parser.gemini_parser import GeminiParser


@pytest.fixture
def mock_gemini_response():
    """Create a mock Gemini response"""

    class MockResponse:
        def __init__(self, text):
            self.text = text

    return MockResponse


@pytest.fixture
def mock_generative_model():
    """Mock the GenerativeModel class"""
    with patch("matching.parser.gemini_parser.GenerativeModel") as mock:
        model_instance = mock.return_value
        model_instance.generate_content = AsyncMock()
        yield model_instance


@pytest.fixture
def mock_vertexai():
    """Mock the vertexai initialization"""
    with patch("matching.parser.gemini_parser.vertexai") as mock:
        mock.init = MagicMock()
        yield mock


@pytest.fixture
async def gemini_parser(mock_vertexai, mock_generative_model):
    """Create a GeminiParser instance with mocked dependencies"""
    parser = GeminiParser(project_id="test-project")
    await parser.initialize()
    return parser


@pytest.mark.asyncio
async def test_initialize(mock_vertexai, mock_generative_model):
    """Test parser initialization"""
    parser = GeminiParser(project_id="test-project")

    assert not parser.initialized
    await parser.initialize()
    assert parser.initialized

    mock_vertexai.init.assert_called_once_with(project="test-project", location="us-central1")
    mock_generative_model.assert_called_once_with("gemini-1.5-pro")


@pytest.mark.asyncio
async def test_detect_intent_type(gemini_parser, mock_generative_model, mock_gemini_response):
    """Test intent type detection"""
    # Test each intent type
    intent_types = {
        "connects": EFormIntentType.connects,
        "mentoring_mentor": EFormIntentType.mentoring_mentor,
        "mentoring_mentee": EFormIntentType.mentoring_mentee,
        "referrals_recommendation": EFormIntentType.referrals_recommendation,
        "mock_interview": EFormIntentType.mock_interview,
        "projects_find_cofounder": EFormIntentType.projects_find_cofounder,
        "projects_find_contributor": EFormIntentType.projects_find_contributor,
        "projects_pet_project": EFormIntentType.projects_pet_project,
    }

    for intent_str, expected_enum in intent_types.items():
        mock_generative_model.generate_content.reset_mock()
        mock_generative_model.generate_content.return_value = mock_gemini_response(intent_str)

        result = await gemini_parser.detect_intent_type("I want to " + intent_str.replace("_", " "))

        assert result == expected_enum
        mock_generative_model.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_detect_intent_type_error_handling(gemini_parser, mock_generative_model):
    """Test error handling in intent type detection"""
    # Test with exception
    mock_generative_model.generate_content.side_effect = Exception("API error")

    # Should default to connects on error
    result = await gemini_parser.detect_intent_type("Some text")
    assert result == EFormIntentType.connects


@pytest.mark.asyncio
async def test_detect_intent_type_unknown_response(gemini_parser, mock_generative_model, mock_gemini_response):
    """Test handling of unknown intent type responses"""
    # Test with unknown intent type
    mock_generative_model.generate_content.return_value = mock_gemini_response("unknown_intent_type")

    # Should default to connects for unknown intent
    result = await gemini_parser.detect_intent_type("Some text")
    assert result == EFormIntentType.connects


@pytest.mark.asyncio
async def test_parse_text_to_form_content(gemini_parser, mock_generative_model, mock_gemini_response):
    """Test parsing text to form content"""
    # Mock a valid JSON response for connects form
    valid_json = {
        "is_local_community": True,
        "social_circle_expansion": {
            "meeting_formats": ["online"],
            "topics": ["general_networking"],
            "details": "Looking to meet new people in tech",
        },
    }

    mock_generative_model.generate_content.return_value = mock_gemini_response(
        f"```json\n{json.dumps(valid_json)}\n```"
    )

    # Test with provided intent type
    intent_type, content = await gemini_parser.parse_text_to_form_content(
        "I want to connect with people", EFormIntentType.connects
    )

    assert intent_type == EFormIntentType.connects
    assert content == valid_json
    assert content["is_local_community"] is True
    assert "social_circle_expansion" in content

    # Test with auto-detected intent type
    mock_generative_model.generate_content.reset_mock()
    # First call for intent detection, second for content parsing
    mock_generative_model.generate_content.side_effect = [
        mock_gemini_response("connects"),
        mock_gemini_response(f"```json\n{json.dumps(valid_json)}\n```"),
    ]

    intent_type, content = await gemini_parser.parse_text_to_form_content("I want to connect with people")

    assert intent_type == EFormIntentType.connects
    assert content == valid_json
    assert mock_generative_model.generate_content.call_count == 2


@pytest.mark.asyncio
async def test_extract_json_from_response(gemini_parser):
    """Test JSON extraction from different response formats"""
    # Test with JSON in code block
    json_in_block = 'Here\'s the parsed form:\n```json\n{"key": "value"}\n```'
    result = gemini_parser._extract_json_from_response(json_in_block)
    assert result == {"key": "value"}

    # Test with JSON without code block markers
    json_without_block = '{\n  "key": "value"\n}'
    result = gemini_parser._extract_json_from_response(json_without_block)
    assert result == {"key": "value"}

    # Test with JSON embedded in text
    json_in_text = 'I\'ve analyzed the form and here\'s the result: {"key": "value"} Hope this helps!'
    result = gemini_parser._extract_json_from_response(json_in_text)
    assert result == {"key": "value"}

    # Test with invalid JSON
    with pytest.raises(ValueError):
        gemini_parser._extract_json_from_response("This is not JSON")


@pytest.mark.asyncio
async def test_parse_text_to_form_content_error_handling(gemini_parser, mock_generative_model, mock_gemini_response):
    """Test error handling in form content parsing"""
    # Test with invalid JSON response
    mock_generative_model.generate_content.return_value = mock_gemini_response("This is not JSON")

    with pytest.raises(ValueError):
        await gemini_parser.parse_text_to_form_content("Some text", EFormIntentType.connects)

    # Test with API error
    mock_generative_model.generate_content.side_effect = Exception("API error")

    with pytest.raises(Exception):
        await gemini_parser.parse_text_to_form_content("Some text", EFormIntentType.connects)
