"""
Models for working with community companies and their services.
"""
from datetime import datetime
from sqlalchemy import Text, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from common_db.models.base import ObjectTable as Base
from common_db.config import schema


class ORMCommunityCompany(Base):
    """Model for storing information about community companies (Yandex, VK, etc.)"""
    __tablename__ = "community_companies"
    __table_args__ = (
        UniqueConstraint('community_company_domain_label', name='uq_community_company_domain_label'),
        {'schema': schema}
    )
    
    # Main fields
    community_company_domain_label: Mapped[str] = mapped_column(
        index=True,
        unique=True,
        doc="Company domain (e.g., vk.com, yandex.ru)"
    )
    
    # Additional information
    description: Mapped[str | None] = mapped_column(
        Text,
        doc="Company description"
    )
    
    logo_url: Mapped[str | None] = mapped_column(
        doc="Company logo URL"
    )
    
    is_active: Mapped[bool] = mapped_column(
        default=True,
        doc="Whether the company is active"
    )
    
    is_custom: Mapped[bool] = mapped_column(
        default=False,
        doc="Manual input from user"
    )
    
    # Relationships
    services: Mapped[list["ORMCompanyService"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        lazy='selectin',
        doc="Company services"
    )


class ORMCompanyService(Base):
    """Model for storing information about company services (Yandex.Food, Yandex.Afisha, etc.)"""
    __tablename__ = "company_services"
    __table_args__ = (
        Index('ix_company_services_company_id', 'company_id'),
        {'schema': schema}
    )
    
    # Main fields
    company_id: Mapped[int] = mapped_column(
        ForeignKey(f"{schema}.community_companies.id", ondelete="CASCADE"),
        index=True,
        doc="Company ID"
    )
    
    service_label: Mapped[str] = mapped_column(
        doc="Company service name (e.g., Food, Afisha)"
    )
    
    # Additional information
    description: Mapped[str | None] = mapped_column(
        Text,
        doc="Service description"
    )
    
    logo_url: Mapped[str | None] = mapped_column(
        doc="Service logo URL"
    )
    
    is_active: Mapped[bool] = mapped_column(
        default=True,
        doc="Whether the service is active"
    )
    
    is_custom: Mapped[bool] = mapped_column(
        default=False,
        doc="Manual input from user"
    )
    
    # Additional service settings (in JSON format)
    settings: Mapped[dict | None] = mapped_column(
        JSONB(none_as_null=True),
        doc="Additional service settings"
    )
    
    # Relationships
    company: Mapped["ORMCommunityCompany"] = relationship(
        back_populates="services",
        lazy='selectin',
        doc="Company that owns the service"
    ) 