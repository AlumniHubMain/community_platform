from datetime import datetime
from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import Index

from common_db.models.base import ObjectTable as Base
from src.types import LinkedInProviderType


class LinkedInApiLimits(Base):
    """API limits model"""
    __tablename__ = "linkedin_api_limits"

    # Тип провайдера
    provider_type: Mapped[str] = mapped_column(
        SQLEnum(LinkedInProviderType),
        index=True,
        doc="Provider type"
    )
    
    # Идентификатор провайдера (последние 4 символа API ключа или email до @)
    provider_id: Mapped[str] = mapped_column(
        String(50),
        doc="Provider identifier (last 4 chars of API key or email prefix)"
    )
    
    credits_left: Mapped[int] = mapped_column(doc="Remaining API credits")
    rate_limit_left: Mapped[int] = mapped_column(doc="Remaining rate limit")
    updated_at: Mapped[datetime] = mapped_column(doc="Last update timestamp")
    
    __table_args__ = (
        # Уникальность по комбинации тип + идентификатор
        Index('idx_provider_unique', 'provider_type', 'provider_id', unique=True),
        # Индекс для мониторинга лимитов
        Index('idx_limits_status', 'credits_left', 'rate_limit_left'),
    )

    @staticmethod
    def get_provider_id(provider_type: LinkedInProviderType, api_key: str | None = None, email: str | None = None) -> str:
        """Получает идентификатор провайдера на основе его типа и креденшелов"""
        if provider_type == LinkedInProviderType.SCRAPIN and api_key:
            return api_key[-4:]  # Последние 4 символа API ключа
        elif provider_type == LinkedInProviderType.TOMQUIRK and email:
            return email.split('@')[0]  # Email до @
        else:
            raise ValueError("Invalid provider credentials")
