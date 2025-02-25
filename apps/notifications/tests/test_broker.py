import pytest
from notifications.main import app

@pytest.mark.asyncio
async def test_broker_subscription(mock_broker):
    # Test that broker.subscribe is called during startup
    async with app.router.lifespan_context(app):
        mock_broker.subscribe.assert_called_once_with(
            app.state.settings.ps_notification_sub_name,
            app.state.message_handler
        )

@pytest.mark.asyncio
async def test_broker_error_handling(mock_broker):
    # Test handling of broker subscription error
    mock_broker.subscribe.side_effect = Exception("Connection error")
    
    with pytest.raises(Exception) as exc_info:
        async with app.router.lifespan_context(app):
            pass
    
    assert str(exc_info.value) == "Connection error" 