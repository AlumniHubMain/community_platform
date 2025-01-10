from typing import Any
from sqlalchemy import JSON, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.common_db.src.common_db.db_abstract import ObjectTable as Base
from packages.common_db.src.common_db.user_model import ORMUserProfile


class LinkedInProfile(Base):
    """LinkedIn profile model"""
    __tablename__ = "linkedin_profiles"

    # Основные поля с индексами
    username: Mapped[str] = mapped_column(
        unique=True,
        index=True,  # Индекс для поиска по username
        doc="LinkedIn username"
    )
    profile_id: Mapped[str] = mapped_column(
        index=True,  # Индекс для поиска по profile_id
        doc="Profile ID"
    )

    # Индекс для часто используемых полей - TODO: для поиска потом добавить
    __table_args__ = (
        Index('idx_profile_name_location', 'full_name', 'country', 'city'),  # Пример: Композит. индекс
        Index('idx_profile_created', 'created_at'),  # Для сортировки/фильтрации по дате
    )

    # Основные поля
    full_name: Mapped[str] = mapped_column(doc="Full name")
    first_name: Mapped[str] = mapped_column(doc="First name")
    last_name: Mapped[str] = mapped_column(doc="Last name")
    headline: Mapped[str | None] = mapped_column(Text, doc="Profile headline")
    summary: Mapped[str | None] = mapped_column(Text, doc="Profile summary")

    # Location
    country: Mapped[str | None] = mapped_column(doc="Country")
    city: Mapped[str | None] = mapped_column(doc="City")

    # Professional Info
    occupation: Mapped[str | None] = mapped_column(doc="Occupation")
    industry: Mapped[str | None] = mapped_column(doc="Industry")

    # URLs
    profile_url: Mapped[str] = mapped_column(doc="LinkedIn profile URL")
    profile_picture: Mapped[str | None] = mapped_column(doc="Profile picture URL")

    # Stats
    connections_count: Mapped[int | None] = mapped_column(doc="Number of connections")

    # Contact Info
    email: Mapped[str | None] = mapped_column(doc="Email")
    phone: Mapped[str | None] = mapped_column(doc="Phone")
    twitter: Mapped[str | None] = mapped_column(doc="Twitter")

    # Additional Info as JSON
    languages: Mapped[list[str]] = mapped_column(JSON, default=list, doc="Languages")
    skills: Mapped[list[str]] = mapped_column(JSON, default=list, doc="Skills")
    endorsements: Mapped[dict[str, int]] = mapped_column(JSON, default=dict, doc="Skill endorsements")
    certifications: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, doc="Certifications")
    volunteer_work: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, doc="Volunteer work")
    publications: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, doc="Publications")

    # Raw data
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSON, doc="Raw profile data")

    # Связь с основным профилем
    users_id_fk: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,  # one-to-one
        doc="ID профиля в основной системе"
    )

    # Relationships
    education: Mapped[list["Education"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    experience: Mapped[list["Experience"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    user: Mapped["ORMUserProfile"] = relationship(back_populates="linkedin_profile", doc="Связанный основной профиль")


class Education(Base):
    """Stores education entries"""
    __tablename__ = "linkedin_education"

    # Main fields
    profile_id: Mapped[int] = mapped_column(ForeignKey("linkedin_profiles.id"), doc="Profile reference")

    school: Mapped[str] = mapped_column(doc="School name")
    degree: Mapped[str | None] = mapped_column(doc="Degree")
    field_of_study: Mapped[str | None] = mapped_column(doc="Field of study")
    start_date: Mapped[str | None] = mapped_column(doc="Start date")
    end_date: Mapped[str | None] = mapped_column(doc="End date")
    description: Mapped[str | None] = mapped_column(Text, doc="Description")

    # Relationship
    profile: Mapped["LinkedInProfile"] = relationship(back_populates="education")


class Experience(Base):
    """Stores work experience entries"""
    __tablename__ = "linkedin_experience"

    # Main fields
    profile_id: Mapped[int] = mapped_column(ForeignKey("linkedin_profiles.id"), doc="Profile reference")

    company: Mapped[str] = mapped_column(doc="Company name")
    title: Mapped[str] = mapped_column(doc="Job title")
    company_linkedin_url: Mapped[str | None] = mapped_column(doc="Company LinkedIn URL")
    location: Mapped[str | None] = mapped_column(doc="Job location")
    start_date: Mapped[str | None] = mapped_column(doc="Start date")
    end_date: Mapped[str | None] = mapped_column(doc="End date")
    description: Mapped[str | None] = mapped_column(Text, doc="Job description")
    duration: Mapped[str | None] = mapped_column(doc="Job duration")
    employment_type: Mapped[str | None] = mapped_column(doc="Employment type")

    # Relationship
    profile: Mapped["LinkedInProfile"] = relationship(back_populates="experience")
