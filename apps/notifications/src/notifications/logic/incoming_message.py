from google.cloud.pubsub_v1.subscriber.message import Message

from common_db.schemas.notifications import DTOGeneralNotification
from .outgoing_message import NotificationSender


async def message_handler(message: Message) -> None:
    """Processing an incoming message"""

    await NotificationSender.send_notification(DTOGeneralNotification.model_validate_json(message.data))

    message.ack()
