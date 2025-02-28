from datetime import datetime, UTC
from loguru import logger
from zoneinfo import ZoneInfo

from common_db.managers.user import UserManager
from common_db.schemas import DTOGeneralNotification, DTOUserNotification, DTONotifiedUserProfile
from notifications.config import settings
from notifications.loader import broker
from notifications.smtp_mailing.client import email_client


class NotificationSender:
    """Class for sending notifications"""

    @staticmethod
    async def __get_html_kwargs(notification: DTOUserNotification) -> dict[str, str]:
        """getting the necessary arguments for html template from the user's schema (DTONotifiedUserProfile)"""
        pass
        # TODO: утвердить типы html шаблонов

    @staticmethod
    async def __send_tg_notification(notification: DTOUserNotification) -> str:
        """Sending telegram notifications to Pub/Sub"""
        # проверяем заблокировал ли человек бота
        if notification.user.is_tg_bot_blocked:
            return "Пользователь заблокировал бота"
        # TODO: обработка случая блокировки человеком бота

        return await broker.publish(settings.ps_notification_tg_topic, notification)

    @staticmethod
    async def __send_email_notification(notification: DTOUserNotification,
                                        html_kwargs: dict[str, str] | None = None) -> str:
        """Sending email notifications"""
        if html_kwargs is not None:
            return await email_client.send_html_email(recipient=notification.user.email,
                                                      subject=notification.params.subject,
                                                      template_name=notification.params.template_name,
                                                      **html_kwargs)
        else:
            return await email_client.send_text_email(recipient=notification.user.email,
                                                      subject=notification.params.subject,
                                                      body=notification.params.text)

    @staticmethod
    async def __send_push_notification(notification: DTOUserNotification) -> str:
        """Sending push notifications"""
        pass

    @classmethod
    async def __send_user_notification(cls, notification: DTOUserNotification):
        """Sending notifications"""
        # getting the current time of the user
        user_timezone: str = notification.user.timezone
        user_time = datetime.now(ZoneInfo(user_timezone)) if user_timezone else datetime.now(UTC)

        # TODO: логика по обработке времени отправки

        if notification.user.is_tg_notify:
            info: str = await cls.__send_tg_notification(notification)
            logger.info(f'в pubsub отправлено сообщение # {info}')
        if notification.user.is_email_notify:
            html_kwargs = await cls.__get_html_kwargs(notification)
            await cls.__send_email_notification(notification, html_kwargs)
        if notification.user.is_push_notify:
            await cls.__send_push_notification(notification)

    @classmethod
    async def send_notification(cls, notification: DTOGeneralNotification):
        """Sending notifications"""
        if notification.notification_type.value.casefold().startswith('user'):
            # getting notified user
            notified_user: DTONotifiedUserProfile = DTONotifiedUserProfile(
                **(await UserManager.get_user_by_id(user_id=notification.params.user_id)).model_dump())

            # preparing notification
            prepared_notification = DTOUserNotification(**notification.model_dump(), user=notified_user)

            # sending the prepared notification to the mailing module
            await cls.__send_user_notification(prepared_notification)
