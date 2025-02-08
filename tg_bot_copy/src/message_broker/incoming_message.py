from google.cloud.pubsub_v1.subscriber.message import Message

from .schemas import DTONotificationMessage
from ..tools.safe_msg_send import send


async def message_handler(message: Message) -> None:
    """Processing an incoming message"""

    print(f'Бот получил сообщение из pubsub')

    try:
        # Decode the message
        notification = DTONotificationMessage.model_validate_json(message.data)

        if notification.type == 'general_text':
            await send(telegram_id=notification.user.telegram_id, text=notification.body)

        message.ack()
    except Exception as e:
        message.nack()
        raise Exception(f"telegram send error: {str(e)}")


