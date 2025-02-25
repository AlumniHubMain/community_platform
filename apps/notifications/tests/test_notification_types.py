import pytest
from notifications.main import app
from notifications.logic.incoming_message import message_handler

@pytest.mark.asyncio
async def test_email_notification(mock_broker):
    """Test handling of email notifications"""
    email_message = {
        "type": "email",
        "recipient": "user@example.com",
        "subject": "Test Email",
        "body": "Test email content",
        "metadata": {
            "priority": "high",
            "template_id": "welcome_email"
        }
    }
    
    await message_handler(email_message)
    mock_broker.process_message.assert_called_once_with(email_message)

@pytest.mark.asyncio
async def test_push_notification(mock_broker):
    """Test handling of push notifications"""
    push_message = {
        "type": "push",
        "recipient_token": "device_token_123",
        "title": "New Message",
        "body": "You have a new message",
        "metadata": {
            "action": "open_chat",
            "chat_id": "123"
        }
    }
    
    await message_handler(push_message)
    mock_broker.process_message.assert_called_once_with(push_message)

@pytest.mark.asyncio
async def test_sms_notification(mock_broker):
    """Test handling of SMS notifications"""
    sms_message = {
        "type": "sms",
        "phone_number": "+1234567890",
        "text": "Your verification code: 123456",
        "metadata": {
            "verification_id": "ver_123",
            "expires_in": 300
        }
    }
    
    await message_handler(sms_message)
    mock_broker.process_message.assert_called_once_with(sms_message)

@pytest.mark.asyncio
async def test_batch_notifications(mock_broker):
    """Test handling of batch notifications"""
    batch_message = {
        "type": "batch",
        "notifications": [
            {
                "type": "email",
                "recipient": "user1@example.com",
                "subject": "Update",
                "body": "Update content"
            },
            {
                "type": "push",
                "recipient_token": "token_456",
                "title": "New Feature",
                "body": "Check out our new feature"
            }
        ],
        "metadata": {
            "campaign_id": "camp_123",
            "batch_id": "batch_456"
        }
    }
    
    await message_handler(batch_message)
    mock_broker.process_message.assert_called_once_with(batch_message) 