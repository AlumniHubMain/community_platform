from enum import Enum
from sqlalchemy import Enum as PGEnum


class EFormIntentType(Enum):
    connects = "connects"
    referrals_recommendation = "referrals_recommendation"
    mentoring_mentor = "mentoring_mentor"
    mentoring_mentee = "mentoring_mentee"
    mock_interview = "mock_interview"
    projects_find_contributor = "projects_find_contributor"
    projects_find_cofounder = "projects_find_cofounder"
    projects_pet_project = "projects_pet_project"


class EFormEnglishLevel(Enum):
    not_required = "not_required"
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"
    native = "Native"


class EFormConnectsMeetingFormat(Enum):
    offline = "offline"
    online = "online"


class EFormMentoringHelpRequest(Enum):
    career_trainsition = "career_trainsition"
    professional_development = "professional_development"
    people_and_process_management = "people_and_process_management"
    personal_brand_creation = "personal_brand_creation"
    public_speaking_and_presentation = "public_speaking_and_presentation"
    entrepreneurship = "entrepreneurship"
    relocation_and_adaptation = "relocation_and_adaptation"
    work_life_balance = "work_life_balance"
    overcoming_impostor_syndrome = "overcoming_impostor_syndrome"
    overcoming_fear_of_uncertainty = "overcoming_fear_of_uncertainty"
    reducing_anxiety_and_procrastination = "reducing_anxiety_and_procrastination"
    foreign_univercity_admission_and_study_assistance = "foreign_univercity_admission_and_study_assistance"
    conflict_resolution = "conflict_resolution"
    preparation_for_interview = "preparation_for_interview"
    finding_job_help = "finding_job_help"
    custom = "custom"


class EFormRefferalsCompanyType(Enum):
    startup = "startup"
    growing_company = "growing_company"
    mature_company = "mature_company"


class EFormMockInterviewType(Enum):
    technical_algorithms = "technical_algorithms"
    technical_system_design = "technical_system_design"
    behavioral = "behavioral"
    case = "case"
    custom = "custom"


class EFormLangluage(Enum):
    english = "english"
    russian = "russian"
    custom = "custom"


class EFormProjectProjectState(Enum):
    idea = "idea"
    prototype = "prototype"
    mvp = "mvp"
    scaling = "scaling"


class EFormProjectUserRole(Enum):
    contributor = "contributor"
    cofounder = "cofounder"


# PostgreSQL Enum types
FormIntentTypePGEnum = PGEnum(
    EFormIntentType,
    name="form_intent_type_enum",
    inherit_schema=True,
)
