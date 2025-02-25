import pytest
from notifications.main import app
from notifications.logic.incoming_message import message_handler

@pytest.mark.asyncio
async def test_message_handler(mock_broker):
    # Test message data
    test_message = {
        "type": "email",
        "recipient": "test@example.com",
        "subject": "Test Notification",
        "body": "This is a test notification"
    }
    
    # Call message handler
    await message_handler(test_message)
    
    # Assert that appropriate methods were called
    mock_broker.process_message.assert_called_once()

@pytest.mark.asyncio
async def test_invalid_message_format(mock_broker, caplog):
    invalid_message = {
        "type": "unknown",
        "data": "invalid"
    }
    
    await message_handler(invalid_message)
    
    # Check that error was logged
    assert "Invalid message format" in caplog.text
    
    # Ensure message wasn't processed
    mock_broker.process_message.assert_not_called()

@pytest.mark.asyncio
async def test_message_processing_error(mock_broker):
    test_message = {
        "type": "email",
        "recipient": "test@example.com",
        "subject": "Test",
        "body": "Test"
    }
    
    # Simulate processing error
    mock_broker.process_message.side_effect = Exception("Processing failed")
    
    with pytest.raises(Exception) as exc_info:
        await message_handler(test_message)
    
    assert str(exc_info.value) == "Processing failed" 