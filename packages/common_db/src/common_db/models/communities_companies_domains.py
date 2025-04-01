"""
Models for working with community companies and their services.
"""
from sqlalchemy import Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common_db.models.base import ObjectTable as Base
from common_db.config import schema


class ORMCommunityCompany(Base):
    """Model for storing information about community companies (Yandex, VK, etc.)"""
    __tablename__ = "community_companies"
    
    # Main fields
    community_company_domain_label: Mapped[str] = mapped_column(
        index=True,
        unique=True,
        doc="Community company domain (e.g., vk, yandex)"
    )
    
    # Additional information
    description: Mapped[str | None] = mapped_column(
        Text,
        doc="Company description"
    )
    
    logo_url: Mapped[str | None] = mapped_column(
        doc="Company logo URL"
    )

    is_custom: Mapped[bool] = mapped_column(
        default=False,
        doc="Is manual input from user"
    )
    
    # Relationships
    services: Mapped[list["ORMCommunityCompanyService"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        lazy='selectin',
        doc="Company services"
    )


class ORMCommunityCompanyService(Base):
    """Model for storing information about company services (Yandex: Food, Afisha, etc.)"""
    __tablename__ = "community_company_services"
    
    # Main fields
    company_id_fk: Mapped[int] = mapped_column(
        ForeignKey(f"{schema}.community_companies.id", ondelete="CASCADE"),
        index=True
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
        doc="Whether the service is active (= verified by community_managers)"
    )
    
    is_custom: Mapped[bool] = mapped_column(
        default=False,
        doc="Manual input from user"
    )

    # Relationships
    company: Mapped["ORMCommunityCompany"] = relationship(
        back_populates="services",
        lazy='selectin',
        doc="Company that owns the service"
    )
