import asyncio
from google.cloud import pubsub_v1

from .db_manager import NotificationManager
from .publisher import NotificationSender
from ..schemas import DTONotificationMessage, DTONotificationSettings, DTOPreparedNotification
from ..config import settings


class NotificationReceiver:
    """Class for receiving and processing notifications from Pub/Sub"""

    def __init__(self):
        self.subscriber = pubsub_v1.SubscriberClient(credentials=settings.credentials())
        self.subscription_path = self.subscriber.subscription_path(settings.ps_project_id,
                                                                   settings.ps_notification_sub_name)
        self.sender = NotificationSender()

    async def process_message(self, message: pubsub_v1.subscriber.message.Message):
        """Обработка входящего сообщения"""

        # Decode the message
        notification = DTONotificationMessage.model_validate_json(message.data)

        # Getting the user's notification settings
        user_settings: DTONotificationSettings = \
            await NotificationManager.get_user_notification_settings(notification.user_id)

        if not user_settings:
            pass
            # TODO: обработка отсутствия настроек

        # Preparing a notification
        prepared_notification = DTOPreparedNotification(**notification.model_dump(), settings=user_settings)

        # Sending a prepared notification
        await self.sender.send_notification(prepared_notification)

        message.ack()

    async def start_receiving(self):
        """Запуск получения сообщений"""

        def callback(message: pubsub_v1.subscriber.message.Message):
            asyncio.run(self.process_message(message))

        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=callback
        )

        streaming_pull_future.result()
