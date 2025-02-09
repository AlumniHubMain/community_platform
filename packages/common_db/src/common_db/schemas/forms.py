from datetime import datetime
from pydantic import BaseModel, model_validator

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
    EFormMockInterviewType,
    EFormHelpRequestSubtype,
    EFormHelpRequestQueryArea,
)

# ============================ Connects form schema ============================
class FormFieldSocialSircleExpansion(BaseModel):
    query_type: list[EFormSocialExpansionQueryType]

    @model_validator(mode='after')
    def check_nonempty(self):
        if len(self.query_type) == 0:
            raise ValueError("\"query_type\" list must be non-empty")
        return self

class FormFieldProfessionalNetworking(BaseModel):
    query_type: list[EFormProfessionalNetworkingQueryType]
    target_specialization: list[EFormProfessionalNetworkingSpecializationType]

    @model_validator(mode='after')
    def check_nonempty(self):
        if len(self.query_type) == 0:
            raise ValueError("\"query_type\" list must be non-empty")
        if len(self.target_specialization) == 0:
            raise ValueError("\"target_specialization\" list must be non-empty")
        return self
    
    
class FormFieldExperienceExchange(BaseModel):
    query_type: list[EFormExperienceExchangeQueryType]
    
    @model_validator(mode='after')
    def check_nonempty(self):
        if len(self.query_type) == 0:
            raise ValueError("\"query_type\" list must be non-empty")
        return self

  
class FormConnects(BaseModel):
    social_circle_expansion: FormFieldSocialSircleExpansion | None = None
    professional_networking: FormFieldProfessionalNetworking | None = None
    experience_exchange: FormFieldExperienceExchange | None = None
    details: str | None = None
    
    @model_validator(mode='after')
    def extended_model_validation(self):
        # Check one of fields nonempty
        validate_fields = (
            'social_circle_expansion',
            'professional_networking',
            'experience_exchange'
        )

        is_all_empty = True
        for field_name in validate_fields:
            is_all_empty = is_all_empty and (self.__getattribute__(field_name) is None)
        
        if is_all_empty:
            raise ValueError("Minimum one of fields [" + ', '.join(validate_fields) + "] must be filled")
        
        return self

# ==============================================================================

# ============================ Mentoring form schema ===========================
class FormMentoring(BaseModel):
    role: EFormMentoringRole
    help_request: list[EFormMentoringHelpRequest]
    custom_query: str | None = None
    specialization: list[EFormMentoringSpecialozations]
    details: str | None = None

    @model_validator(mode='after')
    def extended_model_validation(self):
        # Check nonempty lists
        if len(self.help_request) == 0:
            raise ValueError("\"help_request\" list must be non-empty")
        if len(self.specialization) == 0:
            raise ValueError("\"specialization\" list must be non-empty")

        # Check dependencies between fields
        if EFormMentoringHelpRequest.custom in self.help_request and self.custom_query is None:
            raise ValueError("\"custom_query\" field must be non-empty when \"custom\" help request selected")
        return self
    

# ==============================================================================

# ============================ Refferals form schema ===========================

class FormReferralsFind(BaseModel):
    selected_companies: list[EFormReferralsCompanies]
    resume_s3_link: str
    english_level: EFormEnglishLevel
    english_sertificat_s3_link: str | None = None
    
    @model_validator(mode='after')
    def extended_model_validation(self):
        # Check nonempty lists
        if len(self.help_request) == 0:
            raise ValueError("\"selected_companies\" list must be non-empty")
        return self


class FormReferralsRecommendation(BaseModel):
    is_all_experts_type: bool
    is_need_call: bool
    required_english_level: EFormEnglishLevel
    job_link: str

# ==============================================================================

# ========================= Mock interview form schema =========================

class FormMockInterview(BaseModel):
    interview_type: list[EFormMockInterviewType]
    possible_english_interview: bool
    resume_from_profile: bool
    resume_link: str | None = None
    job_link: str | None = None
    comment: str | None = None
    
    @model_validator(mode='after')
    def validate_depended_fields(self):
        if not self.resume_from_profile and self.resume_link is None:
            raise ValueError("Resume link must be filled when `resume_from_profile` option is enabled")
        return self
    
# ==============================================================================

# ========================= Help Requests form schema ==========================

class FormHelpRequests(BaseModel):
    subtype: EFormHelpRequestSubtype
    query_area: list[EFormHelpRequestQueryArea]
    query_area_details: str | None = None
    query_text: str
    file_link: str | None = None
    
    @model_validator(mode='after')
    def validate_depended_fields(self):
        if len(self.query_area) == 0:
            raise ValueError("\"query_area\" list must be non-empty")
        
        if EFormHelpRequestQueryArea.custom in self.query_area and self.query_area_details is None:
            raise ValueError("\"query_area_details\" must be non-empty when \"custom\" query area selected")

        return self

# ==============================================================================

INTENT_TO_SCHEMA = {
    EFormIntentType.connects: FormConnects,
    EFormIntentType.mentoring: FormMentoring,
    EFormIntentType.referrals_find: FormReferralsFind,
    EFormIntentType.referrals_recommendation: FormReferralsRecommendation,
    EFormIntentType.mock_interview: FormMockInterview,
    EFormIntentType.help_requests: FormHelpRequests,
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
    id: int
