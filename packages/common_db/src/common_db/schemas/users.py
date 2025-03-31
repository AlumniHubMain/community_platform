from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from common_db.enums.users import (
    EExpertiseArea,
    EGrade,
    EIndustry,
    ESkillsArea,
    ERequestsArea,
    EInterestsArea,
    EWithWhom,
    EVisibilitySettings,
    EProfileType,
    ELocation,
)
from common_db.schemas.forms import EFormSpecialization, EFormSkills
from common_db.schemas.base import BaseSchema, TimestampedSchema
from common_db.schemas.meetings import MeetingResponseRead
from common_db.schemas.linkedin import LinkedInProfileRead
from pydantic_extra_types.country import CountryAlpha2, CountryAlpha3
from pydantic_extra_types.timezone_name import TimeZoneName


class DTOSpecialisation(BaseSchema):
    label: str | None = None
    description: str | None = None
    is_custom: bool | None = None
    expertise_area: EExpertiseArea | None = None


class DTOSpecialisationRead(DTOSpecialisation):
    id: int | None = None


class DTOUserSpecialisation(BaseSchema):
    user_id: int = None
    specialisation_id: int
    grade: EGrade | None = None


class DTOUserSpecialisationRead(DTOUserSpecialisation):
    specialisation: DTOSpecialisationRead


class DTOInterest(BaseSchema):
    label: str | None = None
    description: str | None = None
    is_custom: bool | None = None
    interest_area: EInterestsArea | None = None


class DTOInterestRead(DTOInterest):
    id: int | None = None


class DTOIndustry(BaseSchema):
    label: EIndustry | None = None


class DTOSkill(BaseSchema):
    label: str | None = None
    description: str | None = None
    is_custom: bool | None = None
    skill_area: ESkillsArea | None = None


class DTOSkillRead(DTOSkill):
    id: int | None = None


class DTORequestsCommunity(BaseSchema):
    label: str | None = None
    description: str | None = None
    is_custom: bool | None = None
    requests_area: ERequestsArea | None = None


class DTORequestsCommunityRead(DTORequestsCommunity):
    id: int | None = None


class DTOUserProfile(BaseSchema):
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
    referrer_id: int | None = None
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
    profile_type: EProfileType | None = None

    is_verified: bool = False  # verification flag via linkedin_parser
    verified_datetime: datetime | None = None

    linkedin_profile: LinkedInProfileRead | None = None

    communities_companies_domains: list[str] | None = None
    communities_companies_services: list[str] | None = None
    
    # fields for company recommendations and vacancies - referral block
    recommender_companies: list[str] | None = None  # list of companies where user is a recommender
    vacancy_pages: list[str] | None = None  # list of vacancy pages


class DTOUserProfileUpdate(DTOUserProfile):
    id: int


class SUserProfileRead(DTOUserProfile, TimestampedSchema):
    expertise_area: list[str] | None = None
    industries: list[str] | None = None
    grade: str | None = None
    location: str | None = None
    specialisations: list[str] | None = None
    skills: list[str] | None = None
    languages: list[str] | None = None
    current_position_title: str | None = None
    is_currently_employed: bool = False
    linkedin_profile: dict | None = None

    # Additional fields
    interests: list[str] | None = None
    requests_to_community: list[str] | None = None
    requests_community: list[str] | None = None

    @classmethod
    def from_orm(cls, profile: "ORMUserProfile") -> "SUserProfileRead":
        """Create SUserProfileRead from ORM model"""
        return cls(
            id=profile.id,
            name=profile.name,
            surname=profile.surname,
            email=profile.email,
            expertise_area=[
                spec.expertise_area.value
                for spec in profile.specialisations
                if spec.expertise_area
            ] if profile.specialisations else None,
            industries=[
                ind.label.value
                for ind in profile.industries
                if ind.label
            ] if profile.industries else None,
            grade=profile.grade.value if hasattr(profile.grade, 'value') else profile.grade,
            location=profile.location.value if hasattr(profile.location, 'value') else profile.location,
            specialisations=[
                spec.label
                for spec in profile.specialisations
                if spec.label
            ] if profile.specialisations else None,
            skills=[
                skill.label
                for skill in profile.skills
                if skill.label
            ] if profile.skills else None,
            languages=(
                profile.linkedin_profile.languages
                if profile.linkedin_profile and profile.linkedin_profile.languages
                else None
            ),
            current_position_title=(
                profile.linkedin_profile.current_position_title
                if profile.linkedin_profile
                else None
            ),
            is_currently_employed=(
                profile.linkedin_profile.is_currently_employed
                if profile.linkedin_profile
                else False
            ),
            linkedin_profile=({
                                  "skills": profile.linkedin_profile.skills,
                                  "languages": profile.linkedin_profile.languages,
                                  "follower_count": profile.linkedin_profile.follower_count,
                                  "summary": profile.linkedin_profile.summary,
                                  "work_experience": [
                                      exp.model_dump()
                                      for exp in profile.linkedin_profile.work_experience
                                      if exp is not None
                                  ]
                              } if profile.linkedin_profile else None),
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )


class DTOUserProfileRead(DTOUserProfileUpdate):
    specialisations: list[DTOUserSpecialisationRead] | None = None
    interests: list[DTOInterestRead] | None = None
    industry: list[DTOIndustry] | None = None
    skills: list[DTOSkillRead] | None = None
    requests_to_community: list[DTORequestsCommunityRead] | None = None
    referrer: DTOUserProfileUpdate | None = None
    referred: list[DTOUserProfileUpdate] | None = None

    def to_old_schema(self) -> SUserProfileRead:
        old_schema: SUserProfileRead = SUserProfileRead(**self.model_dump(
            exclude={
                'specialisations',
                'interests',
                'industry',
                'skills',
                'requests_to_community',
                'referrer',
                'referred'
            }
        ))
        old_schema.specialisations = [x.specialisation.label for x in self.specialisations] \
            if self.specialisations else None
        old_schema.expertise_area = list({x.specialisation.expertise_area.name for x in self.specialisations}) \
            if self.specialisations else None
        old_schema.interests = [x.label for x in self.interests] if self.interests else None
        old_schema.industry = [x.label for x in self.industry] if self.industry else None
        old_schema.skills = [x.label for x in self.skills] if self.skills else None
        old_schema.requests_to_community = [x.label for x in self.requests_to_community] \
            if self.requests_to_community else None
        return old_schema


class DTOSearchUser(BaseSchema):
    name: str | None = None
    surname: str | None = None
    country: str | None = None
    city: str | None = None
    expertise_area: str | None = None
    specialisation: str | None = None
    skill: str | None = None
    limit: int | None = 30


class DTOAllProperties(BaseSchema):
    specialisations: list[DTOSpecialisationRead] | None = None
    interests: list[DTOInterestRead] | None = None
    skills: list[DTOSkillRead] | None = None
    requests_to_community: list[DTORequestsCommunityRead] | None = None
