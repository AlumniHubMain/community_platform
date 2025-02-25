import pytest
from notifications.main import app
from notifications.logic.incoming_message import message_handler

@pytest.mark.asyncio
async def test_email_validation(mock_broker, caplog):
    """Test email notification validation"""
    # Missing required fields
    invalid_email = {
        "type": "email",
        "subject": "Test"
        # missing recipient and body
    }
    
    await message_handler(invalid_email)
    assert "Missing required fields for email notification" in caplog.text
    mock_broker.process_message.assert_not_called()
    
    # Invalid email format
    invalid_email = {
        "type": "email",
        "recipient": "invalid_email",
        "subject": "Test",
        "body": "Test"
    }
    
    await message_handler(invalid_email)
    assert "Invalid email format" in caplog.text
    mock_broker.process_message.assert_not_called()

@pytest.mark.asyncio
async def test_push_validation(mock_broker, caplog):
    """Test push notification validation"""
    # Invalid token format
    invalid_push = {
        "type": "push",
        "recipient_token": "",  # empty token
        "title": "Test",
        "body": "Test"
    }
    
    await message_handler(invalid_push)
    assert "Invalid recipient token" in caplog.text
    mock_broker.process_message.assert_not_called()

@pytest.mark.asyncio
async def test_sms_validation(mock_broker, caplog):
    """Test SMS notification validation"""
    # Invalid phone number
    invalid_sms = {
        "type": "sms",
        "phone_number": "123",  # invalid format
        "text": "Test"
    }
    
    await message_handler(invalid_sms)
    assert "Invalid phone number format" in caplog.text
    mock_broker.process_message.assert_not_called()

@pytest.mark.asyncio
async def test_batch_validation(mock_broker, caplog):
    """Test batch notification validation"""
    # Empty notifications list
    invalid_batch = {
        "type": "batch",
        "notifications": []
    }
    
    await message_handler(invalid_batch)
    assert "Empty batch notifications list" in caplog.text
    mock_broker.process_message.assert_not_called()
    
    # Invalid notification in batch
    invalid_batch = {
        "type": "batch",
        "notifications": [
            {
                "type": "email",
                "recipient": "invalid_email"
            }
        ]
    }
    
    await message_handler(invalid_batch)
    assert "Invalid notification in batch" in caplog.text
    mock_broker.process_message.assert_not_called() 