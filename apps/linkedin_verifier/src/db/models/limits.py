# from datetime import datetime
# from enum import Enum
# from sqlalchemy import String
# from sqlalchemy.orm import Mapped, mapped_column
# from sqlalchemy.schema import Index
#
# from common_db.models.base import ObjectTable
# from common_db.config import schema
#
#
# class LinkedInProvider(str, Enum):
#     """Типы провайдеров LinkedIn"""
#     SCRAPIN = "scrapin"
#     TOMQUIRK = "tomquirk"
#
#
# class ORMLinkedInApiLimits(ObjectTable):
#     """API limits model"""
#     __tablename__ = "linkedin_api_limits"
#
#     __table_args__ = (
#         # Уникальность по комбинации тип + идентификатор
#         Index('idx_provider_unique', 'provider_type', 'provider_id', unique=True),
#         # Индекс для мониторинга лимитов
#         Index('idx_limits_status', 'credits_left', 'rate_limit_left'),
#         {'schema': schema}  # Указываем схему для таблицы
#     )
#
#     # Тип провайдера
#     provider_type: Mapped[str] = mapped_column(
#         String,
#         index=True,
#         doc="Provider type"
#     )
#
#     # Идентификатор провайдера (последние 4 символа API ключа или email до @)
#     provider_id: Mapped[str] = mapped_column(
#         String,
#         doc="Provider identifier (last 4 chars of API key or email prefix)"
#     )
#
#     credits_left: Mapped[int] = mapped_column(doc="Remaining API credits")
#     rate_limit_left: Mapped[int] = mapped_column(doc="Remaining rate limit")
#     updated_at: Mapped[datetime] = mapped_column(doc="Last update timestamp")
#
#     @staticmethod
#     def get_provider_id(provider_type: LinkedInProvider, api_key: str | None = None,
#                         email: str | None = None) -> str:
#         """Получает идентификатор провайдера на основе его типа и креденшелов"""
#         if provider_type == LinkedInProvider.SCRAPIN and api_key:
#             return api_key[-4:]  # Последние 4 символа API ключа
#         elif provider_type == LinkedInProvider.TOMQUIRK and email:
#             return email.split('@')[0]  # Email до @
#         else:
#             raise ValueError("Invalid provider credentials")
