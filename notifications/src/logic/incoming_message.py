from google.cloud.pubsub_v1.subscriber.message import Message

from .outgoing_message import NotificationSender
from ..db_manager import NotificationManager
from ..schemas import DTONotificationMessage, DTONotifiedUserProfile, DTOPreparedNotification


async def message_handler(message: Message) -> None:
    """Processing an incoming message"""

    # decode the message
    notification = DTONotificationMessage.model_validate_json(message.data)

    # getting notified user
    notified_user: DTONotifiedUserProfile = \
        await NotificationManager.get_notified_user_profile(notification.user_id)

    # preparing notification
    prepared_notification = DTOPreparedNotification(**notification.model_dump(), user=notified_user)

    # sending the prepared notification to the mailing module
    await NotificationSender.send_notification(prepared_notification)

    message.ack()
