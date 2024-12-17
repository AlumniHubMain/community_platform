import asyncio
from google.cloud import pubsub_v1

from ..config import settings
from ..tools.safe_msg_send import send
from .schemas import DTONotificationMessage


class NotificationReceiver:
    """Class for receiving and processing notifications from Pub/Sub"""

    def __init__(self):
        self.subscriber = pubsub_v1.SubscriberClient(credentials=settings.credentials())
        self.subscription_path = self.subscriber.subscription_path(settings.ps_project_id,
                                                                   settings.ps_notification_tg_sub_name)

    @staticmethod
    async def process_message(message: pubsub_v1.subscriber.message.Message):
        """Processing an incoming message"""

        # Decode the message
        notification = DTONotificationMessage.model_validate_json(message.data)

        # TODO: обсудить типы уведомлений (общие текстовые, с картинками, ссылками, кнопками и пр.)
        # случай обычного текстового уведомления
        if notification.type == 'general':
            await send(telegram_id=notification.user.telegram_id, text=notification.body)

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
