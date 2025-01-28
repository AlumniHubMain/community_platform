from datetime import datetime
from typing import Any
from sqlalchemy import JSON, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common_db.models.base import ObjectTable as Base
from common_db.models.users import ORMUserProfile
from common_db.config import schema


class ORMLinkedInRawData(Base):
    """Модель для хранения сырых данных профиля LinkedIn"""
    __tablename__ = "linkedin_raw_data"
    
    __table_args__ = (
        # Уникальность по URL и дате парсинга
        UniqueConstraint('target_linkedin_url', 'parsed_date', name='uq_linkedin_raw_data_url_date'),
        {'schema': schema}
    )
    
    # URL профиля, который парсили
    target_linkedin_url: Mapped[str] = mapped_column(
        index=True,  # Для быстрого поиска
        doc="LinkedIn profile URL that was parsed"
    )
    
    # Сырые данные от API
    raw_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        doc="Raw API response data"
    )
    
    # Дата и время парсинга
    parsed_date: Mapped[datetime] = mapped_column(
        DateTime,
        index=True,  # Для быстрого поиска по дате
        doc="Profile parsing date"
    )


class ORMLinkedInProfile(Base):
    """LinkedIn profile model"""
    __tablename__ = "linkedin_profiles"

    # Индексы для оптимизации поиска и сортировки
    # TODO: добавить индекс users_id_fk после согласования
    # __table_args__ = (
    #     {'schema': schema}  # Указываем схему для таблицы
    # )

    # Связь с основным профилем
    # TODO: пока нет возможности сделать индексом, т.к. будут парситься профили сообществ,
    #  а они не Users данной платформы
    users_id_fk: Mapped[int | None] = mapped_column(
        ForeignKey(f"{schema}.users.id"),
        unique=True,  # one-to-one
        nullable=True,  # т.к. профили из Сообществ можем лить, а их нет в Users
        doc="ID профиля в основной системе"
    )

    # Basic Info
    public_identifier: Mapped[str | None] = mapped_column(doc="Public identifier")
    linkedin_identifier: Mapped[str | None] = mapped_column(doc="LinkedIn identifier")
    member_identifier: Mapped[str | None] = mapped_column(doc="Member identifier")
    linkedin_url: Mapped[str | None] = mapped_column(doc="LinkedIn profile URL")
    first_name: Mapped[str | None] = mapped_column(doc="First name")
    last_name: Mapped[str | None] = mapped_column(doc="Last name")
    headline: Mapped[str | None] = mapped_column(Text, doc="Profile headline")
    location: Mapped[str | None] = mapped_column(doc="Location")

    summary: Mapped[str | None] = mapped_column(Text, doc="Profile summary")
    photo_url: Mapped[str | None] = mapped_column(doc="Profile photo URL")
    background_url: Mapped[str | None] = mapped_column(doc="Profile background URL")
    is_open_to_work: Mapped[bool | None] = mapped_column(doc="Open to work flag")
    is_premium: Mapped[bool | None] = mapped_column(doc="Premium account flag")
    pronoun: Mapped[str | None] = mapped_column(doc="Pronoun")
    is_verification_badge_shown: Mapped[bool | None] = mapped_column(doc="Show verification badge flag")
    creation_date: Mapped[datetime | None] = mapped_column(DateTime, doc="Profile creation date")
    follower_count: Mapped[int | None] = mapped_column(doc="Follower count")
    parsed_date: Mapped[datetime] = mapped_column(DateTime, doc="Profile parsing date")

    # Professional Info
    skills: Mapped[list[str] | None] = mapped_column(
        JSONB(none_as_null=True),  # JSONB хранит в бинарном формате, без escape-последовательностей
        doc="Skills"
    )
    languages: Mapped[list[str] | None] = mapped_column(
        JSONB(none_as_null=True),
        doc="Languages"
    )
    recommendations: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(none_as_null=True),
        doc="Recommendations"
    )
    certifications: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(none_as_null=True),
        doc="Certifications"
    )

    # Current Job Info
    # TODO: Возможно вынести в головную таблицу User?
    # Инфа о текущем месте работы, вынесено из work_experience history
    # (последняя запись с откр. датой завершения работы)
    is_currently_employed: Mapped[bool | None] = mapped_column(doc="Whether person is currently employed "
                                                                   "(has at least one job without end_date)")
    current_jobs_count: Mapped[int | None] = mapped_column(doc="Number of current jobs (count of records "
                                                               "without end_date)")
    current_company_label: Mapped[str | None] = mapped_column(doc="Latest active company name")
    current_company_linkedin_id: Mapped[str | None] = mapped_column(doc="Latest active company LinkedIn ID")
    current_position_title: Mapped[str | None] = mapped_column(doc="Latest active job title")
    current_company_linkedin_url: Mapped[str | None] = mapped_column(doc="Latest active company LinkedIn URL")

    # Target Company Info
    # TODO: Возможно вынести в головную таблицу User?
    # Target Company Info - посл. место работы в легитимных компаниях (с точки зрения продуктовой верификации)
    is_target_company_found: Mapped[bool | None] = mapped_column(doc="Whether target company was found "
                                                                     "in work experience")
    target_company_positions_count: Mapped[int | None] = mapped_column(doc="Number of positions in target company")
    target_company_label: Mapped[str | None] = mapped_column(doc="Target company name from work experience")
    target_company_linkedin_id: Mapped[str | None] = mapped_column(doc="Target company LinkedIn ID")
    target_position_title: Mapped[str | None] = mapped_column(doc="Latest position in target company")
    target_company_linkedin_url: Mapped[str | None] = mapped_column(doc="Target company LinkedIn URL")
    is_employee_in_target_company: Mapped[bool | None] = mapped_column(doc="Whether person is currently "
                                                                           "employed in target company")

    # Relationships
    education: Mapped[list["ORMEducation"]] = relationship(
        back_populates="profile",
        # cascade="all, delete-orphan",
        lazy='selectin'
    )
    work_experience: Mapped[list["ORMWorkExperience"]] = relationship(
        back_populates="profile",
        # cascade="all, delete-orphan",
        lazy='selectin'
    )
    user: Mapped["ORMUserProfile"] = relationship(back_populates="linkedin_profile", doc="Связанный основной профиль")


class ORMEducation(Base):
    """Stores education entries"""
    __tablename__ = "linkedin_education"

    # Индексы для оптимизации поиска и сортировки
    # TODO: добавить индексы
    __table_args__ = (
        # Уникальный индекс для предотвращения дублей - чтобы сохранять только новые записи
        UniqueConstraint('profile_id', 'school', 'degree', name='uq_education_profile_url'),
        {'schema': schema}  # Указываем схему для таблицы
    )
    # 'profile_id', 'school', 'degree' - пока предполагаем, что так будут уникальны,
    # но смотреть на распределение реальных данных

    # Main fields
    profile_id: Mapped[int] = mapped_column(ForeignKey(f"{schema}.linkedin_profiles.id"),
                                            doc="Profile reference", index=True)

    school: Mapped[str] = mapped_column(doc="School name")
    degree: Mapped[str | None] = mapped_column(doc="Degree")
    field_of_study: Mapped[str | None] = mapped_column(doc="Field of study")
    start_date: Mapped[datetime | None] = mapped_column(DateTime, doc="Start date")
    end_date: Mapped[datetime | None] = mapped_column(DateTime, doc="End date")
    description: Mapped[str | None] = mapped_column(Text, doc="Description")
    linkedin_url: Mapped[str | None] = mapped_column(doc="LinkedIn URL")
    school_logo: Mapped[str | None] = mapped_column(doc="School logo URL")

    # Relationship
    profile: Mapped["ORMLinkedInProfile"] = relationship(
        back_populates="education",
        lazy='selectin'
    )


class ORMWorkExperience(Base):
    """Stores work experience entries"""
    __tablename__ = "linkedin_experience"

    # Индексы для оптимизации поиска и сортировки
    __table_args__ = (
        # Уникальный индекс для предотвращения дублей - чтобы сохранять только новые записи
        UniqueConstraint('profile_id', 'company_label', 'title', name='uq_work_experience_profile_url'),
        {'schema': schema}  # Указываем схему для таблицы
    )
    # 'profile_id', 'company_label', 'title' - пока предполагаем, что так будут уникальны,
    # но смотреть на распределение реальных данных (company_id - зачастую null)

    # Main fields
    profile_id: Mapped[int] = mapped_column(ForeignKey(f"{schema}.linkedin_profiles.id"), doc="Profile reference",
                                            index=True)

    company_label: Mapped[str | None] = mapped_column(doc="Company name")
    title: Mapped[str] = mapped_column(doc="Job title")
    company_linkedin_url: Mapped[str | None] = mapped_column(doc="Company LinkedIn URL")
    location: Mapped[str | None] = mapped_column(doc="Job location")
    start_date: Mapped[datetime | None] = mapped_column(DateTime, doc="Start date")
    end_date: Mapped[datetime | None] = mapped_column(DateTime, doc="End date")
    description: Mapped[str | None] = mapped_column(Text, doc="Job description")
    duration: Mapped[str | None] = mapped_column(doc="Job duration")
    employment_type: Mapped[str | None] = mapped_column(doc="Employment type")
    company_logo: Mapped[str | None] = mapped_column(doc="Company logo URL")
    linkedin_url: Mapped[str | None] = mapped_column(doc="LinkedIn URL")
    linkedin_id: Mapped[str | None] = mapped_column(doc="LinkedIn ID")

    # Relationship
    profile: Mapped["ORMLinkedInProfile"] = relationship(
        back_populates="work_experience",
        lazy='selectin'
    )

    # TODO: Вынести raw_data в отдельную таблицу LinkedinRawData со связью на users.id
    # TODO: Сделать отдельную таблицу профилей компаний LinkedinCompanies - пригодится в будущем как реестр с описанием
