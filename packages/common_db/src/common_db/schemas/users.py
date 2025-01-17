from datetime import datetime
from pydantic import ConfigDict
from common_db.enums.users import (
    EInterests,
    EExpertiseArea,
    ESpecialisation,
    EGrade,
    EIndustry,
    ESkills,
    ELocation,
    ERequestsToCommunity,
    ECompanyServices,
)
from common_db.schemas.base import TimestampedSchema
from common_db.schemas.meetings import MeetingResponseRead


class UserProfile(TimestampedSchema):
    name: str
    surname: str
    email: str
    avatars: list[str] | None = None
    about: str | None = None
    interests: list[EInterests] | None = None
    linkedin_link: str | None = None
    telegram_name: str | None = None
    telegram_id: int | None = None
    expertise_area: list[EExpertiseArea] | None = None
    specialisation: list[ESpecialisation] | None = None
    grade: EGrade | None = None
    industry: list[EIndustry] | None = None
    skills: list[ESkills] | None = None
    current_company: str | None = None
    company_services: list[ECompanyServices] | None = None
    location: ELocation | None = None
    referral: bool | None = None
    requests_to_community: list[ERequestsToCommunity] | None = None
    is_tg_bot_blocked: bool | None = None
    blocked_status_update_date: datetime | None = None
    meeting_responses: list[MeetingResponseRead] | None = None


class SUserProfileUpdate(UserProfile):
    id: int


class SUserProfileRead(SUserProfileUpdate):
    model_config = ConfigDict(from_attributes=True)
