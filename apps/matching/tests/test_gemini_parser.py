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
        
        # Instead of using AsyncMock directly, create a method that returns the mock response
        async def mock_generate_content(*args, **kwargs):
            # Default mock response - will be overridden in tests
            return MagicMock(text="mocked response")
        
        # Set the generate_content method to our async function
        model_instance.generate_content = mock_generate_content
        yield model_instance


@pytest.fixture
def mock_vertexai():
    """Mock the vertexai initialization"""
    with patch("matching.parser.gemini_parser.vertexai") as mock:
        mock.init = MagicMock()
        yield mock


@pytest.fixture
def gemini_parser(mock_vertexai, mock_generative_model):
    """Create a GeminiParser instance with mocked dependencies"""
    parser = GeminiParser(project_id="test-project")
    # Set initialized directly instead of calling async initialize
    parser.initialized = True
    parser.model = mock_generative_model
    return parser


@pytest.mark.asyncio
async def test_initialize(mock_vertexai, mock_generative_model):
    """Test parser initialization"""
    # Create a new mock for GenerativeModel to verify the call
    with patch("matching.parser.gemini_parser.GenerativeModel") as mock_generative_model_class:
        # Set up the mock to return our mock instance
        mock_generative_model_class.return_value = mock_generative_model
        
        # Create a new parser instance
        parser = GeminiParser(project_id="test-project")
        
        # Verify initial state
        assert not parser.initialized
        
        # Initialize the parser
        await parser.initialize()
        
        # Verify final state and mock calls
        assert parser.initialized
        mock_vertexai.init.assert_called_once_with(project="test-project", location="us-central1")
        mock_generative_model_class.assert_called_once_with("gemini-1.5-pro")


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
        # Create a fresh mock for each iteration
        mock_response = mock_gemini_response(intent_str)
        
        # Override the generate_content method for this test
        async def mock_generate_intent(*args, **kwargs):
            return mock_response
            
        # Replace the method temporarily
        original_method = mock_generative_model.generate_content
        mock_generative_model.generate_content = mock_generate_intent
        
        try:
            result = await gemini_parser.detect_intent_type("I want to " + intent_str.replace("_", " "))
            assert result == expected_enum
        finally:
            # Restore the original method
            mock_generative_model.generate_content = original_method


@pytest.mark.asyncio
async def test_detect_intent_type_error_handling(gemini_parser, mock_generative_model):
    """Test error handling in intent type detection"""
    # Override the generate_content method to raise an exception
    async def mock_generate_error(*args, **kwargs):
        raise Exception("API error")
        
    # Replace the method temporarily
    original_method = mock_generative_model.generate_content
    mock_generative_model.generate_content = mock_generate_error
    
    try:
        # Should default to connects on error
        result = await gemini_parser.detect_intent_type("Some text")
        assert result == EFormIntentType.connects
    finally:
        # Restore the original method
        mock_generative_model.generate_content = original_method


@pytest.mark.asyncio
async def test_detect_intent_type_unknown_response(gemini_parser, mock_generative_model, mock_gemini_response):
    """Test handling of unknown intent type responses"""
    # Create a mock response with an unknown intent type
    mock_response = mock_gemini_response("unknown_intent_type")
    
    # Override the generate_content method for this test
    async def mock_generate_unknown(*args, **kwargs):
        return mock_response
        
    # Replace the method temporarily
    original_method = mock_generative_model.generate_content
    mock_generative_model.generate_content = mock_generate_unknown
    
    try:
        # Should default to connects for unknown intent
        result = await gemini_parser.detect_intent_type("Some text")
        assert result == EFormIntentType.connects
    finally:
        # Restore the original method
        mock_generative_model.generate_content = original_method


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

    # Create a mock response with JSON content
    mock_response = mock_gemini_response(f"```json\n{json.dumps(valid_json)}\n```")
    
    # Override the generate_content method for this test
    async def mock_generate_json(*args, **kwargs):
        return mock_response
        
    # Replace the method temporarily
    original_method = mock_generative_model.generate_content
    mock_generative_model.generate_content = mock_generate_json
    
    try:
        # Test with provided intent type
        intent_type, content = await gemini_parser.parse_text_to_form_content(
            "I want to connect with people", EFormIntentType.connects
        )

        assert intent_type == EFormIntentType.connects
        assert content == valid_json
        assert content["is_local_community"] is True
        assert "social_circle_expansion" in content
    finally:
        # Restore the original method
        mock_generative_model.generate_content = original_method
    
    # Test with auto-detected intent type - need to mock two responses
    # First for intent detection, second for content parsing
    mock_response_intent = mock_gemini_response("connects")
    mock_response_content = mock_gemini_response(f"```json\n{json.dumps(valid_json)}\n```")
    
    # Track which call is being made
    call_count = 0
    
    async def mock_sequential_responses(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_response_intent
        else:
            return mock_response_content
    
    # Replace the method temporarily
    mock_generative_model.generate_content = mock_sequential_responses
    
    try:
        intent_type, content = await gemini_parser.parse_text_to_form_content("I want to connect with people")

        assert intent_type == EFormIntentType.connects
        assert content == valid_json
        assert call_count == 2  # Verify both calls were made
    finally:
        # Restore the original method
        mock_generative_model.generate_content = original_method


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
    mock_response = mock_gemini_response("This is not JSON")
    
    # Override the generate_content method to return invalid JSON
    async def mock_generate_invalid_json(*args, **kwargs):
        return mock_response
        
    # Replace the method temporarily
    original_method = mock_generative_model.generate_content
    mock_generative_model.generate_content = mock_generate_invalid_json
    
    try:
        with pytest.raises(ValueError):
            await gemini_parser.parse_text_to_form_content("Some text", EFormIntentType.connects)
    finally:
        # Restore the original method
        mock_generative_model.generate_content = original_method
    
    # Now test with API error by raising an exception
    async def mock_generate_api_error(*args, **kwargs):
        raise Exception("API error")
    
    # Replace the method again
    mock_generative_model.generate_content = mock_generate_api_error
    
    try:
        with pytest.raises(Exception):
            await gemini_parser.parse_text_to_form_content("Some text", EFormIntentType.connects)
    finally:
        # Restore the original method
        mock_generative_model.generate_content = original_method


def test_process_special_data_types():
    """Test processing of special data types for compatibility with new schemas"""
    
    # Create parser instance directly (no async here)
    parser = GeminiParser(project_id="test-project")
    
    # Test case 1: Handling different object types
    class MockObject:
        def __init__(self, value=None, label=None):
            self.value = value
            self.label = label
    
    # Create test data with mixed object types
    content = {
        "expertise_area": [MockObject(value="backend"), MockObject(value="frontend")],
        "grade": MockObject(value="senior"),
        "interests": [MockObject(label="technology"), MockObject(label="design")],
        "skills": [MockObject(label="python"), "javascript"],
        "specialisations": [MockObject(label="web_development")],
        "industries": [MockObject(label="software")],
        "nested": {
            "skills": [MockObject(label="react")]
        },
        "list_of_objects": [
            {"languages": [MockObject(label="english")]},
            {"skills": "python"}
        ]
    }
    
    # Process the content
    parser._process_special_data_types(content)
    
    # Verify transformations
    assert content["expertise_area"] == ["backend", "frontend"]
    assert content["grade"] == "senior"
    assert content["interests"] == ["technology", "design"]
    assert content["skills"] == ["python", "javascript"]  # Mixed types correctly handled
    assert content["specialisations"] == ["web_development"]
    assert content["industries"] == ["software"]
    
    # Verify nested transformations
    assert content["nested"]["skills"] == ["react"]
    assert content["list_of_objects"][0]["languages"] == ["english"]
    assert content["list_of_objects"][1]["skills"] == "python"
    
    # Test case 2: Handling None or empty values
    content2 = {
        "expertise_area": None,
        "interests": [],
        "nested": {
            "skills": None
        }
    }
    
    parser._process_special_data_types(content2)
    
    assert content2["expertise_area"] == []
    assert content2["interests"] == []
    assert content2["nested"]["skills"] == []
    
    # Test case 3: Handling non-list values
    content3 = {
        "expertise_area": "backend",
        "nested": {
            "specialisations": "web"
        }
    }
    
    parser._process_special_data_types(content3)
    
    assert content3["expertise_area"] == "backend"
    assert content3["nested"]["specialisations"] == "web"
