from google.cloud import pubsub_v1
from ..schemas import DTOPreparedNotification
from ..config import settings


class NotificationSender:
    """Class for sending notifications"""

    def __init__(self):
        self.publisher = pubsub_v1.PublisherClient(credentials=settings.ps_credentials)
        self.tg_topic_path = self.publisher.topic_path(settings.ps_project_id, settings.ps_tg_topic)

    async def __send_tg_notification(self, notification: DTOPreparedNotification) -> str:
        """Sending telegram notifications to Pub/Sub"""
        data = notification.model_dump_json().encode('utf-8')
        future = self.publisher.publish(self.tg_topic_path, data=data)
        message_id = future.result()
        return message_id

    async def __send_email_notification(self, notification: DTOPreparedNotification) -> str:
        """Sending email notifications"""
        pass
        # TODO: нужны шаблоны html

    async def __send_telephone_notification(self, notification: DTOPreparedNotification) -> str:
        """Sending telephone notifications"""
        pass
        # TODO: необходимость телефонных уведомлений?

    async def send_notification(self, notification: DTOPreparedNotification):
        """Sending notifications"""
        # TODO: добавить проверку на часовой пояс?
        if notification.settings.is_tg_notify:
            await self.__send_tg_notification(notification)
        if notification.settings.is_email_notify:
            await self.__send_email_notification(notification)
        if notification.settings.is_telephone_notify:
            await self.__send_telephone_notification(notification)
