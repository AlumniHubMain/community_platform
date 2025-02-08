from datetime import datetime
from pydantic import BaseModel, EmailStr
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

from common_db.schemas.meetings import MeetingResponseRead
from pydantic_extra_types.country import CountryAlpha2, CountryAlpha3
from pydantic_extra_types.timezone_name import TimeZoneName


class DTOSpecialisation(BaseModel):
    label: str | None = None
    description: str | None = None
    is_custom: bool | None = None
    expertise_area: EExpertiseArea | None = None


class DTOSpecialisationRead(DTOSpecialisation):
    id: int | None = None

    class Config:
        from_attributes = True


class DTOUserSpecialisation(BaseModel):
    user_id: int = None
    specialisation_id: int
    grade: EGrade | None = None


class DTOUserSpecialisationRead(DTOUserSpecialisation):
    specialisation: DTOSpecialisationRead

    class Config:
        from_attributes = True


class DTOInterest(BaseModel):
    label: str | None = None
    description: str | None = None
    is_custom: bool | None = None
    interest_area: EInterestsArea | None = None


class DTOInterestRead(DTOInterest):
    id: int | None = None

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


class DTOSkillRead(DTOSkill):
    id: int | None = None

    class Config:
        from_attributes = True


class DTORequestsCommunity(BaseModel):
    label: str | None = None
    description: str | None = None
    is_custom: bool | None = None
    requests_area: ERequestsArea | None = None


class DTORequestsCommunityRead(DTORequestsCommunity):
    id: int | None = None

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


class SUserProfileRead(DTOUserProfile):
    specialisations: list[str] | None = None
    interests: list[str] | None = None
    industry: list[str] | None = None
    skills: list[str] | None = None
    requests_to_community: list[str] | None = None


class DTOUserProfileRead(DTOUserProfileUpdate):
    specialisations: list[DTOUserSpecialisationRead] | None = None
    interests: list[DTOInterestRead] | None = None
    industry: list[DTOIndustry] | None = None
    skills: list[DTOSkillRead] | None = None
    requests_to_community: list[DTORequestsCommunityRead] | None = None

    class Config:
        from_attributes = True

    def to_old_schema(self) -> SUserProfileRead:
        old_schema: SUserProfileRead = SUserProfileRead(**self.model_dump(
            exclude={
                'specialisations',
                'interests',
                'industry',
                'skills',
                'requests_to_community'
            }
        ))
        old_schema.specialisation = [x.specialisation.label for x in self.specialisations] \
            if self.specialisations else None
        old_schema.expertise_area = list({x.specialisation.expertise_area.name for x in self.specialisations}) \
            if self.specialisations else None
        old_schema.interests = [x.label for x in self.interests] if self.interests else None
        old_schema.industry = [x.label for x in self.industry] if self.industry else None
        old_schema.skills = [x.label for x in self.skills] if self.skills else None
        old_schema.requests_to_community = [x.label for x in self.requests_to_community] \
            if self.requests_to_community else None
        return old_schema


class DTOSearchUser(BaseModel):
    name: str | None = None
    surname: str | None = None
    country: str | None = None
    city: str | None = None
    expertise_area: str | None = None
    specialisation: str | None = None
    skill: str | None = None
    limit: int | None = 30


class DTOAllProperties(BaseModel):
    specialisations: list[DTOSpecialisationRead] | None = None
    interests: list[DTOInterestRead] | None = None
    skills: list[DTOSkillRead] | None = None
    requests_to_community: list[DTORequestsCommunityRead] | None = None
