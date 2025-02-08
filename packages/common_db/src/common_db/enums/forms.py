from enum import Enum
from sqlalchemy import Enum as PGEnum


class EFormIntentType(Enum):
    connects = "connects"
    referrals_recommendation = "referrals_recommendation"
    referrals_find = "referrals_find"
    mentoring = "mentoring"


class EFormSocialExpansionQueryType(Enum):
    interest_discussion = "interest_discussion"
    offline_meetings = "offline_meetings"


class EFormProfessionalNetworkingQueryType(Enum):
    trends_discussion = "trends_discussion"
    startup_ideas = "startup_ideas"


class EFormProfessionalNetworkingSpecializationType(Enum):
    # TODO: Fill it
    ml = "ml"
    development = "development"
    frontend = "frontend"


class EFormExperienceExchangeQueryType(Enum):
    product_feedback = "product_feedback"
    coeducation = "coeducation"
    best_practies_discussion = "best_practies_discussion"
    new_technologies_discussion = "new_technologies_discussion"
    exam_preparation = "exam_preparation"


class EFormMentoringRole(Enum):
    mentor = "mentor"
    mentee = "mentee"


class EFormMentoringHelpRequest(Enum):
    adaptation_after_relocate = "adaptation_after_relocate"
    process_and_teams_management = "process_and_teams_management"
    custom = "custom"
    # TODO: Fill me


class EFormMentoringSpecialozations(Enum):
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


class EFormReferralsCompanies(Enum):
    vk = "vk"
    yandex = "yandex"


class EFormEnglishLevel(Enum):
    unknown = "unknown"
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


# PostgreSQL Enum types
FormIntentTypePGEnum = PGEnum(
    EFormIntentType,
    name="form_intent_type_enum",
    inherit_schema=True,
)

FormSocialExpansionQueryTypePGEnum = PGEnum(
    EFormSocialExpansionQueryType,
    name="form_social_expansion_query_type_enum",
    inherit_schema=True,
)

FormProfessionalNetworkingQueryTypePGEnum = PGEnum(
    EFormProfessionalNetworkingQueryType,
    name="form_professional_networking_query_type_enum",
    inherit_schema=True,
)

FormProfessionalNetworkingSpecializationTypePGEnum = PGEnum(
    EFormProfessionalNetworkingSpecializationType,
    name="form_professional_networking_specialization_type_enum",
    inherit_schema=True,
)

FormExperienceExchangeQueryTypePGEnum = PGEnum(
    EFormExperienceExchangeQueryType,
    name="form_experience_exchange_query_type_enum",
    inherit_schema=True,
)

FormMentoringRolePGEnum = PGEnum(
    EFormMentoringRole,
    name="form_mentoring_role_enum",
    inherit_schema=True,
)

FormMentoringHelpRequestPGEnum = PGEnum(
    EFormMentoringHelpRequest,
    name="form_mentoring_help_request_enum",
    inherit_schema=True,
)

FormMentoringSpecialozationsPGEnum = PGEnum(
    EFormMentoringSpecialozations,
    name="form_mentoring_specializations_enum",
    inherit_schema=True,
)

FormReferralsCompaniesPGEnum = PGEnum(
    EFormReferralsCompanies,
    name="form_refferals_companies_enum",
    inherit_schema=True,
)

FormEnglishLevelPGEnum = PGEnum(
    EFormEnglishLevel,
    name="form_english_level_enum",
    inherit_schema=True,
)
