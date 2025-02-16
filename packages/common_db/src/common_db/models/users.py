from datetime import datetime
from sqlalchemy import String, ARRAY, BIGINT, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common_db.enums.users import (
    ExpertiseAreaPGEnum,
    SpecialisationPGEnum,
    GradePGEnum,
    CompanyServicesPGEnum,
    IndustryPGEnum,
    SkillsPGEnum,
    LocationPGEnum,
    RequestsToCommunityPGEnum,
    InterestsPGEnum,
    WithWhomEnumPGEnum,
    VisibilitySettingsPGEnum,
    ProfileTypePGEnum,
    EInterests,
    EExpertiseArea,
    ESpecialisation,
    EGrade,
    EIndustry,
    ESkills,
    ELocation,
    ERequestsToCommunity,
    ECompanyServices,
    EWithWhom,
    EVisibilitySettings,
    EProfileType,
)
from common_db.config import schema
from common_db.models.base import ObjectTable


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
    interests: Mapped[list[EInterests] | None] = mapped_column(ARRAY(InterestsPGEnum))

    linkedin_link: Mapped[str | None] = mapped_column(String(100))

    telegram_name: Mapped[str | None] = mapped_column(String(200))
    telegram_id: Mapped[int | None] = mapped_column(BIGINT)

    expertise_area: Mapped[list[EExpertiseArea] | None] = mapped_column(ARRAY(ExpertiseAreaPGEnum))
    specialisation: Mapped[list[ESpecialisation] | None] = mapped_column(ARRAY(SpecialisationPGEnum))
    grade: Mapped[EGrade | None] = mapped_column(GradePGEnum)
    industry: Mapped[list[EIndustry] | None] = mapped_column(ARRAY(IndustryPGEnum))
    skills: Mapped[list[ESkills] | None] = mapped_column(ARRAY(SkillsPGEnum))

    current_company: Mapped[str | None] = mapped_column(String(200))
    company_services: Mapped[list[ECompanyServices] | None] = mapped_column(ARRAY(CompanyServicesPGEnum))

    location: Mapped[ELocation | None] = mapped_column(LocationPGEnum)
    referral: Mapped[bool] = mapped_column(default=False)
    requests_to_community: Mapped[list[ERequestsToCommunity] | None] = mapped_column(ARRAY(RequestsToCommunityPGEnum))

    is_tg_bot_blocked: Mapped[bool] = mapped_column(default=False)
    blocked_status_update_date: Mapped[datetime | None]

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
