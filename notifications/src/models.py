from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from backend.db_proxy.common_db.db_abstract import ObjectTable, schema


class ORMNotificationSettings(ObjectTable):
    """
    The model of the notification_settings table in Postgres (user settings for notifications)
    """
    __tablename__ = 'notification_settings'

    user_id: Mapped[int] = mapped_column(ForeignKey(column=f'{schema}.users.id'))
    timezone: Mapped[str | None]
    is_tg_notify: Mapped[bool] = False
    is_email_notify: Mapped[bool] = False
    is_telephone_notify: Mapped[bool] = False

    # TODO: наверное стоит эту модельку просто в user добавить (чтобы не плодить связи 1-1)
