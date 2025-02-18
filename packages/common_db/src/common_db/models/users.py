from datetime import datetime
from sqlalchemy import String, ARRAY, BIGINT, Index, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common_db.enums.users import (
    ExpertiseAreaPGEnum,
    GradePGEnum,
    CompanyServicesPGEnum,
    IndustryPGEnum,
    SkillsAreaPGEnum,
    RequestsAreaPGEnum,
    InterestsAreaPGEnum,
    WithWhomEnumPGEnum,
    VisibilitySettingsPGEnum,
    EInterestsArea,
    ProfileTypePGEnum,
    EExpertiseArea,
    EGrade,
    EIndustry,
    ESkillsArea,
    ERequestsArea,
    ECompanyServices,
    EWithWhom,
    EVisibilitySettings,
    EProfileType,
)
from common_db.config import schema
from common_db.models.base import Base, ObjectTable, PropertyTable


class ORMUserProfile(ObjectTable):
    """
    Модель таблицы (шаблон) пользователей.
    """

    __tablename__ = 'users'

    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)

    avatars: Mapped[list[str] | None] = mapped_column(ARRAY(String(300)))
    about: Mapped[str | None] = mapped_column(String(300))
    linkedin_link: Mapped[str | None] = mapped_column(String(100))

    telegram_name: Mapped[str | None] = mapped_column(String(200))
    telegram_id: Mapped[int | None] = mapped_column(BIGINT)
    is_tg_bot_blocked: Mapped[bool] = mapped_column(default=False)
    blocked_status_update_date: Mapped[datetime | None]

    country: Mapped[str | None]
    city: Mapped[str | None]
    timezone: Mapped[str | None]
    referral: Mapped[bool] = mapped_column(default=False)

    is_tg_notify: Mapped[bool] = mapped_column(default=False)
    is_email_notify: Mapped[bool] = mapped_column(default=False)
    is_push_notify: Mapped[bool] = mapped_column(default=False)

    # relationships for basic user properties
    specialisations: Mapped[list["ORMSpecialisation"]] = relationship(
        "ORMSpecialisation",
        secondary=f"{schema}.users_specialisations",
        back_populates="users"
    )

    user_specialisations: Mapped[list["ORMUserSpecialisation"]] = relationship(
        "ORMUserSpecialisation",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    interests: Mapped[list["ORMInterest"]] = relationship(
        "ORMInterest",
        secondary=f"{schema}.users_interests",
        back_populates="users"
    )

    industries: Mapped[list["ORMUserIndustry"]] = relationship(
        "ORMUserIndustry",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    skills: Mapped[list["ORMSkill"]] = relationship(
        "ORMSkill",
        secondary=f"{schema}.users_skills",
        back_populates="users"
    )

    requests_to_community: Mapped[list["ORMRequestsCommunity"]] = relationship(
        "ORMRequestsCommunity",
        secondary=f"{schema}.users_requests_to_community",
        back_populates="users"
    )

    who_to_date_with: Mapped[EWithWhom | None] = mapped_column(WithWhomEnumPGEnum)
    who_sees_profile: Mapped[EVisibilitySettings] = mapped_column(
        VisibilitySettingsPGEnum,
        default=EVisibilitySettings.anyone)
    who_sees_current_job: Mapped[EVisibilitySettings] = mapped_column(
        VisibilitySettingsPGEnum,
        default=EVisibilitySettings.anyone)
    who_sees_contacts: Mapped[EVisibilitySettings] = mapped_column(
        VisibilitySettingsPGEnum,
        default=EVisibilitySettings.anyone)
    who_sees_calendar: Mapped[EVisibilitySettings] = mapped_column(
        VisibilitySettingsPGEnum,
        default=EVisibilitySettings.anyone)

    # Relationship for user_meetings, linking the user to their meetings with roles and responses
    # meeting_responses: Mapped[list["ORMMeetingResponse"]] = relationship(
    #     "ORMMeetingResponse", back_populates="user", cascade="all, delete-orphan"
    # )

    linkedin_profile: Mapped["ORMLinkedInProfile"] = relationship(back_populates="user", doc="Профиль linkedIn")

    available_meetings_pendings_count: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    available_meetings_confirmations_count: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)

    # Add this to the existing relationships in ORMUserProfile
    linkedin_profile: Mapped["ORMLinkedInProfile"] = relationship(
        "ORMLinkedInProfile",
        back_populates="user",
        uselist=False,  # one-to-one relationship
        cascade="all, delete-orphan"
    )
    profile_type: Mapped[EProfileType] = mapped_column(ProfileTypePGEnum, default=EProfileType.New)

    __table_args__ = (Index('ix_users_telegram_id', 'telegram_id'),
                      {'schema': f"{schema}"}
                      )


class ORMSpecialisation(PropertyTable):
    """
    The specializations table model.
    """

    __tablename__ = 'specialisations'

    expertise_area: Mapped[EExpertiseArea | None] = mapped_column(ExpertiseAreaPGEnum)

    users: Mapped[list["ORMUserProfile"]] = relationship(
        "ORMUserProfile",
        secondary=f"{schema}.users_specialisations",
        back_populates="specialisations"
    )

    user_specialisations: Mapped[list["ORMUserSpecialisation"]] = relationship(
        "ORMUserSpecialisation",
        back_populates="specialisation",
        cascade="all, delete-orphan"
    )


class ORMUserSpecialisation(Base):
    """
    The users specializations table model.
    """

    __tablename__ = 'users_specialisations'

    user_id: Mapped[int] = mapped_column(ForeignKey(column=f'{schema}.users.id'), primary_key=True, index=True)
    specialisation_id: Mapped[int] = mapped_column(ForeignKey(column=f'{schema}.specialisations.id'),
                                                   primary_key=True,
                                                   index=True)

    grade: Mapped[EGrade | None] = mapped_column(GradePGEnum)

    user: Mapped["ORMUserProfile"] = relationship("ORMUserProfile", back_populates="user_specialisations")
    specialisation: Mapped["ORMSpecialisation"] = relationship(
        "ORMSpecialisation",
        back_populates="user_specialisations"
    )


class ORMInterest(PropertyTable):
    """
    The interests table model.
    """

    __tablename__ = 'interests'

    interest_area: Mapped[EInterestsArea | None] = mapped_column(InterestsAreaPGEnum)

    users: Mapped[list["ORMUserProfile"]] = relationship(
        "ORMUserProfile",
        secondary=f"{schema}.users_interests",
        back_populates="interests"
    )


class ORMUserInterest(Base):
    """
    The users interests table model.
    """

    __tablename__ = 'users_interests'

    user_id: Mapped[int] = mapped_column(ForeignKey(column=f'{schema}.users.id'), primary_key=True, index=True)
    interest_id: Mapped[int] = mapped_column(ForeignKey(column=f'{schema}.interests.id'),
                                             primary_key=True,
                                             index=True)


class ORMUserIndustry(ObjectTable):
    """
    The users industries table model.
    """

    __tablename__ = 'users_industries'

    user_id: Mapped[int] = mapped_column(ForeignKey(column=f'{schema}.users.id'), index=True)
    label: Mapped[EIndustry | None] = mapped_column(IndustryPGEnum)

    user: Mapped["ORMUserProfile"] = relationship("ORMUserProfile", back_populates="industries")


class ORMSkill(PropertyTable):
    """
    The skills table model.
    """

    __tablename__ = 'skills'

    skill_area: Mapped[ESkillsArea | None] = mapped_column(SkillsAreaPGEnum)
    users: Mapped[list["ORMUserProfile"]] = relationship(
        "ORMUserProfile",
        secondary=f"{schema}.users_skills",
        back_populates="skills"
    )


class ORMUserSkill(Base):
    """
    The users skills table model.
    """

    __tablename__ = 'users_skills'

    user_id: Mapped[int] = mapped_column(ForeignKey(column=f'{schema}.users.id'), primary_key=True, index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey(column=f'{schema}.skills.id'),
                                          primary_key=True,
                                          index=True)


class ORMRequestsCommunity(PropertyTable):
    """
    The requests to community table model.
    """

    __tablename__ = 'requests_to_community'

    requests_area: Mapped[ERequestsArea | None] = mapped_column(RequestsAreaPGEnum)

    users: Mapped[list["ORMUserProfile"]] = relationship(
        "ORMUserProfile",
        secondary=f"{schema}.users_requests_to_community",
        back_populates="requests_community"
    )


class ORMUserRequestsCommunity(Base):
    """
    The users skills table model.
    """

    __tablename__ = 'users_requests_to_community'

    user_id: Mapped[int] = mapped_column(ForeignKey(column=f'{schema}.users.id'), primary_key=True, index=True)
    requests_id: Mapped[int] = mapped_column(ForeignKey(column=f'{schema}.requests_to_community.id'),
                                             primary_key=True,
                                             index=True)
