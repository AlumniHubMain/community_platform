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


class EFormSpecialization(Enum):
    """
    Warning! __ separator must be user for construction of tree structure.
    For example: 
        development__data_science__deep_learning means this tree -> [development -> data science -> deep learning]
    """
    development__frontend__react = "development__frontend__react"
    development__frontend__vue = "development__frontend__vue"
    development__backend__cpp = "development__backend__cpp"
    development__backend__python = "development__backend__python"
    development__data_science__deep_learning = "development__data_science__deep_learning"
    # TODO: Fill me


class EFormSkills(Enum):
    development__frontend = "development__frontend"
    design_ui_ux = "design_ui_ux"
    # TODO: Fill me


class EFormCompanies(Enum):
    any = "any"
    vk = "vk"
    yandex = "yandex"


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


class EFormConnectsSocialExpansionTopic(Enum):
    """
    Warning! __ separator must be user for construction of tree structure.
    For example: 
        development__data_science__deep_learning means this tree -> [development -> data science -> deep learning]
    """
    development__web_development = "development__web_development"
    development__mobile_development = "development__mobile_development"
    design__design_system_development = "design__design_system_development"
    custom = "custom"
    # TODO: Fill me


class EFormProfessionalNetworkingTopic(Enum):
    development = "development"
    analytics = "analytics"
    # TODO: Fill me


class EFormMentoringHelpRequest(Enum):
    adaptation_after_relocate = "adaptation_after_relocate"
    process_and_teams_management = "process_and_teams_management"
    custom = "custom"
    # TODO: Fill me


class EFormMentoringGrade(Enum):
    junior = "junior"
    middle = "middle"
    senior = "senior"
    lead = "lead"
    head = "head"
    executive = "executive"


class EFormRefferalsCompanyType(Enum):
    dummy = "dummy"
    # TODO: Fill me


class EFormMockInterviewType(Enum):
    technical = "technical"
    behavioral = "behavioral"
    role_playing = "role_playing"


class EFormMockInterviewLangluages(Enum):
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
