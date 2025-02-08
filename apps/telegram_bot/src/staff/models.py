from enum import Enum as BaseEnum

from sqlalchemy import Enum, BigInteger
from sqlalchemy.orm import mapped_column, Mapped

from backend.db_proxy.common_db.db_abstract import ObjectTable


class TgBotStaffRole(BaseEnum):
    admin: str = 'admin'
    manager: str = 'manager'
    community_manager: str = 'community_manager'
    activists_manager: str = 'activists_manager'
    recruitment_manager: str = 'recruitment_manager'
    mentoring_manager: str = 'mentoring_manager'


class ORMTgBotStaff(ObjectTable):
    """
    Модель таблицы tg_bot_staff в Postgres (персонал alh, взаимодействующий с ботом)
    """
    __tablename__ = 'tg_bot_staff'

    telegram_name: Mapped[str]
    telegram_id: Mapped[int | None] = mapped_column(BigInteger)
    name: Mapped[str | None]
    surname: Mapped[str | None]
    bio: Mapped[str | None]
    email: Mapped[str | None]
    phone_number: Mapped[str | None]
    role: Mapped[TgBotStaffRole] = mapped_column(
        Enum(TgBotStaffRole, name='tg_staff_role', inherit_schema=True),
        default=TgBotStaffRole.manager
    )
