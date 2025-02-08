from datetime import datetime
from pydantic import BaseModel

from common_db.schemas.base import BaseSchema, TimestampedSchema
from common_db.enums.forms import (
    EFormIntentType,
    EFormSocialExpansionQueryType,
    EFormProfessionalNetworkingQueryType,
    EFormProfessionalNetworkingSpecializationType,
    EFormExperienceExchangeQueryType,
    EFormMentoringRole,
    EFormMentoringHelpRequest, 
    EFormMentoringSpecialozations,
    EFormReferralsCompanies,
    EFormEnglishLevel,
)

# ============================ Connects form schema ============================
class FormFieldSocialSircleExpansion(BaseModel):
    query_type: list[EFormSocialExpansionQueryType]


class FormFieldProfessionalNetworking(BaseModel):
    query_type: list[EFormProfessionalNetworkingQueryType]
    target_specialization: list[EFormProfessionalNetworkingSpecializationType]

    
class FormFieldExperienceExchange(BaseModel):
    query_type: list[EFormExperienceExchangeQueryType]

  
class FormConnects(BaseModel):
    social_circle_expansion: FormFieldSocialSircleExpansion | None = None
    professional_networking: FormFieldProfessionalNetworking | None = None
    experience_exchange: FormFieldExperienceExchange | None = None
    details: str | None = None
# ==============================================================================

# ============================ Mentoring form schema ===========================
class FormMentoring(BaseModel):
    role: EFormMentoringRole
    help_request: list[EFormMentoringHelpRequest]
    custom_query: str | None = None
    specialization: list[EFormMentoringSpecialozations]
    details: str | None = None


# ==============================================================================

# ============================ Refferals form schema ===========================

class FormReferralsFind(BaseModel):
    selected_companies: list[EFormReferralsCompanies]
    resume_s3_link: str
    english_level: EFormEnglishLevel
    english_sertificat_s3_link: str | None = None


class FormReferralsRecommendation(BaseModel):
    is_all_experts_type: bool
    is_need_call: bool
    required_english_level: EFormEnglishLevel
    job_link: str

# ==============================================================================

INTENT_TO_SCHEMA = {
    EFormIntentType.connects: FormConnects,
    EFormIntentType.mentoring: FormMentoring,
    EFormIntentType.referrals_find: FormReferralsFind,
    EFormIntentType.referrals_recommendation: FormReferralsRecommendation,
}

class FormBase(BaseSchema):
    """Base schema for forms"""
    user_id: int
    intent: EFormIntentType
    content: dict
    calendar: str


class FormCreate(FormBase):
    """Schema for creating a form"""
    pass


class FormRead(FormBase, TimestampedSchema):
    """Schema for reading a form"""
    pass
