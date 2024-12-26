from datetime import datetime, UTC
from zoneinfo import ZoneInfo

from notifications.loader import broker
from ..schemas import DTOPreparedNotification
from ..smtp_mailing.client import email_client
from notifications.config import settings


class NotificationSender:
    """Class for sending notifications"""

    @staticmethod
    async def __get_html_kwargs(notification: DTOPreparedNotification) -> dict[str, str]:
        """getting the necessary arguments for html template from the user's schema (DTONotifiedUserProfile)"""
        pass
        # TODO: утвердить типы html шаблонов

    @staticmethod
    async def __send_tg_notification(notification: DTOPreparedNotification) -> str:
        """Sending telegram notifications to Pub/Sub"""
        # проверяем заблокировал ли человек бота
        if notification.user.is_tg_bot_blocked:
            return "Пользователь заблокировал бота"
        # TODO: обработка случая блокировки человеком бота

        return await broker.publish(settings.ps_notification_tg_topic, notification)

    @staticmethod
    async def __send_email_notification(notification: DTOPreparedNotification,
                                        html_kwargs: dict[str, str] | None = None) -> str:
        """Sending email notifications"""
        if html_kwargs is not None:
            return await email_client.send_html_email(recipient=notification.user.email,
                                                      subject=notification.head,
                                                      template_name=notification.body,
                                                      **html_kwargs)
        else:
            return await email_client.send_text_email(recipient=notification.user.email,
                                                      subject=notification.head,
                                                      body=notification.body)

    @staticmethod
    async def __send_push_notification(notification: DTOPreparedNotification) -> str:
        """Sending push notifications"""
        pass

    @classmethod
    async def send_notification(cls, notification: DTOPreparedNotification):
        """Sending notifications"""
        # getting the current time of the user
        user_timezone: str = notification.user.timezone
        user_time = datetime.now(ZoneInfo(user_timezone)) if user_timezone else datetime.now(UTC)

        # TODO: логика по обработке времени отправки

        if notification.user.is_tg_notify:
            info: str = await cls.__send_tg_notification(notification)
            print(f'в pubsub отправлено сообщение # {info}')
        if notification.user.is_email_notify:
            html_kwargs = await cls.__get_html_kwargs(notification) if notification.type.startswith('html') else None
            await cls.__send_email_notification(notification, html_kwargs)
        if notification.user.is_push_notify:
            await cls.__send_push_notification(notification)
