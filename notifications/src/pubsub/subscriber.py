import asyncio
from google.cloud import pubsub_v1

from .publisher import NotificationSender
from ..db_manager import NotificationManager
from ..config import settings
from ..schemas import DTONotificationMessage, DTONotifiedUserProfile, DTOPreparedNotification


class NotificationReceiver:
    """Class for receiving and processing notifications from Pub/Sub"""

    def __init__(self):
        self.subscriber = pubsub_v1.SubscriberClient(credentials=settings.credentials())
        self.subscription_path = self.subscriber.subscription_path(settings.ps_project_id,
                                                                   settings.ps_notification_sub_name)
        self.sender = NotificationSender()

    async def process_message(self, message: pubsub_v1.subscriber.message.Message):
        """Processing an incoming message"""

        # Decode the message
        notification = DTONotificationMessage.model_validate_json(message.data)

        # Getting notified user
        notified_user: DTONotifiedUserProfile = \
            await NotificationManager.get_notified_user_profile(notification.user_id)

        # Preparing a notification
        prepared_notification = DTOPreparedNotification(**notification.model_dump(), user=notified_user)

        # Sending a prepared notification
        await self.sender.send_notification(prepared_notification)

        message.ack()

    async def start_receiving(self):
        """Starting receiving messages"""

        def callback(message: pubsub_v1.subscriber.message.Message):
            asyncio.run(self.process_message(message))

        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=callback
        )

        streaming_pull_future.result()
