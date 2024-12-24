from datetime import datetime, UTC
from google.cloud import pubsub_v1
from zoneinfo import ZoneInfo

from ..schemas import DTOPreparedNotification
from ..smtp_mailing.client import email_client
from ..config import settings


class NotificationSender:
    """Class for sending notifications"""

    def __init__(self):
        self.smtp_client = email_client
        self.publisher = pubsub_v1.PublisherClient(credentials=settings.ps_credentials)
        self.tg_topic_path = self.publisher.topic_path(settings.ps_project_id, settings.ps_tg_topic)

    async def __get_html_kwargs(self, notification: DTOPreparedNotification) -> dict[str, str]:
        """getting the necessary arguments for html template from the user's schema (DTONotifiedUserProfile)"""
        pass
        # TODO: утвердить типы html шаблонов

    async def __send_tg_notification(self, notification: DTOPreparedNotification) -> str:
        """Sending telegram notifications to Pub/Sub"""
        # проверяем заблокировал ли человек бота
        if notification.user.is_tg_bot_blocked:
            return 'User is blocked bot'
        # TODO: обработка случая блокировки человеком бота

        data = notification.model_dump_json().encode('utf-8')
        future = self.publisher.publish(self.tg_topic_path, data=data)
        message_id = future.result()
        return message_id

    async def __send_email_notification(self, notification: DTOPreparedNotification) -> str:
        """Sending email notifications"""
        if notification.type.startswith('html'):
            html_kwargs: dict[str, str] = await self.__get_html_kwargs(notification)
            return await self.smtp_client.send_html_email(recipient=notification.user.email,
                                                          subject=notification.head,
                                                          template_name=notification.body,
                                                          **html_kwargs)
        else:
            return await email_client.send_text_email(recipient=notification.user.email,
                                                      subject=notification.head,
                                                      body=notification.body)

    async def __send_push_notification(self, notification: DTOPreparedNotification) -> str:
        """Sending push notifications"""
        pass
        # TODO: куда именно посылать?

    async def __send_telephone_notification(self, notification: DTOPreparedNotification) -> str:
        """Sending telephone notifications"""
        pass
        # TODO: необходимость телефонных уведомлений?

    async def send_notification(self, notification: DTOPreparedNotification):
        """Sending notifications"""
        # getting the current time of the user
        user_timezone: str = notification.user.settings.timezone
        user_time = datetime.now(ZoneInfo(user_timezone)) if user_timezone else datetime.now(UTC)

        # TODO: логика по обработке времени отправки

        if notification.settings.is_tg_notify:
            await self.__send_tg_notification(notification)
        if notification.settings.is_email_notify:
            await self.__send_email_notification(notification)
        if notification.settings.is_push_notify:
            await self.__send_push_notification(notification)
        if notification.settings.is_telephone_notify:
            await self.__send_telephone_notification(notification)
