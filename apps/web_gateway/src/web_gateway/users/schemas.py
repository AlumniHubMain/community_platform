from common_db.enums.users import *

from pydantic import BaseModel, ConfigDict

# TODO: use from common_db.schemas.users
class UserProfile(BaseModel):
    name: str
    surname: str
    email: str

    avatars: list[str] | None

    about: str | None
    interests: list[EInterests] | None

    linkedin_link: str | None
    telegram_name: str | None
    telegram_id: int | None

    # ToDo(evseev.dmsr) Validate specialisation as subpart of expertise
    expertise_area: list[EExpertiseArea] | None
    specialisation: list[ESpecialisation] | None
    grade: EGrade | None
    industry: list[EIndustry] | None
    skills: list[ESkills] | None

    current_company: str | None
    company_services: list[ECompanyServices] | None

    location: ELocation | None
    referral: bool | None
    requests_to_community: list[ERequestsToCommunity]
    
    available_meetings_pendings_count: int | None
    available_meetings_confirmations_count: int | None

    who_to_date_with: EWithWhom | None
    who_sees_profile: EVisibilitySettings
    who_sees_current_job: EVisibilitySettings
    who_sees_contacts: EVisibilitySettings
    who_sees_calendar: EVisibilitySettings

    profile_type: EProfileType


class SUserProfileUpdate(UserProfile):
    id: int


class SUserProfileRead(SUserProfileUpdate):
    model_config = ConfigDict(from_attributes=True)
