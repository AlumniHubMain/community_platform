from datetime import datetime
from pydantic import ConfigDict, BaseModel, EmailStr
from common_db.enums.users import (
    EExpertiseArea,
    EGrade,
    EIndustry,
    ESkillsArea,
    ERequestsArea,
    EInterestsArea,
    EWithWhom,
    EVisibilitySettings,
)

from common_db.schemas.base import TimestampedSchema
from common_db.schemas.meetings import MeetingResponseRead
from pydantic_extra_types.country import CountryAlpha2, CountryAlpha3
from pydantic_extra_types.timezone_name import TimeZoneName


class UserProfile(TimestampedSchema):
    name: str
    surname: str
    email: str
    avatars: list[str] | None = None
    about: str | None = None
    interests: list[str] | None = None
    linkedin_link: str | None = None
    telegram_name: str | None = None
    telegram_id: int | None = None
    expertise_area: list[str] | None = None
    specialisation: list[str] | None = None
    grade: EGrade | None = None
    industry: list[str] | None = None
    skills: list[str] | None = None
    country: str | None = None
    city: str | None = None
    referral: bool | None = None
    requests_to_community: list[str] | None = None
    is_tg_bot_blocked: bool | None = None
    blocked_status_update_date: datetime | None = None
    meeting_responses: list[MeetingResponseRead] | None = None


class SUserProfileUpdate(UserProfile):
    id: int


class SUserProfileRead(SUserProfileUpdate):
    model_config = ConfigDict(from_attributes=True)


class DTOSpecialisation(BaseModel):
    label: str | None = None
    description: str | None = None
    is_custom: bool | None = None
    expertise_area: EExpertiseArea | None = None

    class Config:
        from_attributes = True


class DTOInterest(BaseModel):
    label: str | None = None
    description: str | None = None
    is_custom: bool | None = None
    interest_area: EInterestsArea | None = None

    class Config:
        from_attributes = True


class DTOIndustry(BaseModel):
    label: EIndustry | None = None

    class Config:
        from_attributes = True


class DTOSkill(BaseModel):
    label: str | None = None
    description: str | None = None
    is_custom: bool | None = None
    skill_area: ESkillsArea | None = None

    class Config:
        from_attributes = True


class DTORequestsCommunity(BaseModel):
    label: str | None = None
    description: str | None = None
    is_custom: bool | None = None
    requests_area: ERequestsArea | None = None

    class Config:
        from_attributes = True


class DTOUserProfile(BaseModel):
    name: str
    surname: str
    email: EmailStr
    avatars: list[str] | None = None
    about: str | None = None
    linkedin_link: str | None = None
    telegram_name: str | None = None
    telegram_id: int | None = None
    is_tg_bot_blocked: bool = False
    blocked_status_update_date: datetime | None = None
    country: CountryAlpha2 | CountryAlpha3 | None = None
    city: str | None = None
    timezone: TimeZoneName | None = None
    referral: bool | None = None
    is_tg_notify: bool | None = None
    is_email_notify: bool | None = None
    is_push_notify: bool | None = None
    who_to_date_with: EWithWhom | None = None
    who_sees_profile: EVisibilitySettings | None = None
    who_sees_current_job: EVisibilitySettings | None = None
    who_sees_contacts: EVisibilitySettings | None = None
    who_sees_calendar: EVisibilitySettings | None = None
    available_meetings_pendings_count: int | None = None
    available_meetings_confirmations_count: int | None = None
    meeting_responses: list[MeetingResponseRead] | None = None


class DTOUserProfileUpdate(DTOUserProfile):
    id: int


class DTOUserProfileRead(DTOUserProfileUpdate):
    specialisations: list[DTOSpecialisation] | None = None
    interests: list[DTOInterest] | None = None
    industry: list[DTOIndustry] | None = None
    skills: list[DTOSkill] | None = None
    requests_to_community: list[DTORequestsCommunity] | None = None

    class Config:
        from_attributes = True

    def to_lazy_schema(self) -> SUserProfileRead:
        lazy_schema: SUserProfileRead = SUserProfileRead(**self.model_dump(
            exclude={
                'specialisations',
                'interests',
                'industry',
                'skills',
                'requests_to_community'
            }
        ))
        lazy_schema.specialisation = [x.label for x in self.specialisation] if self.specialisation else None
        lazy_schema.expertise_area = list({x.expertise_area.name for x in self.specialisation}) \
            if self.specialisation else None
        lazy_schema.interests = [x.label for x in self.interests] if self.interests else None
        lazy_schema.industry = [x.label for x in self.industry] if self.industry else None
        lazy_schema.skills = [x.label for x in self.skills] if self.skills else None
        lazy_schema.requests_to_community = [x.label for x in self.requests_to_community] \
            if self.requests_to_community else None
        return lazy_schema


class DTOSearchUser(BaseModel):
    name: str | None = None
    surname: str | None = None
    country: str | None = None
    city: str | None = None
    expertise_area: str | None = None
    specialisation: str | None = None
    skill: str | None = None
    limit: int | None = 30
