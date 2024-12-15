from common_db import *

from typing import List

from pydantic import BaseModel


class UserProfile(BaseModel):
    name: str
    surname: str
    email: str

    avatars: List[str] | None

    about: str | None
    interests: List[EInterests] | None

    linkedin_link: str | None
    telegram_name: str | None
    telegram_id: int | None

    # ToDo(evseev.dmsr) Validate specialisation as subpart of expertise
    expertise_area: List[EExpertiseArea] | None
    specialisation: List[ESpecialisation] | None
    grade: EGrade | None
    industry: List[EIndustry] | None
    skills: List[ESkills] | None

    current_company: str | None
    company_services: List[ECompanyServices] | None

    location: ELocation | None
    referral: bool | None
    requests_to_community: List[ERequestsToCommunity]
    
    available_meetings_pendings_count: int | None
    available_meetings_confirmations_count: int | None


class SUserProfileUpdate(UserProfile):
    id: int


class SUserProfileRead(SUserProfileUpdate):
    class Config:
        from_attributes = True
