from pydantic import BaseModel, model_validator

from common_db.schemas.base import BaseSchema, TimestampedSchema
from common_db.enums.forms import (
    EFormIntentType,
    EFormConnectsMeetingFormat,
    EFormConnectsSocialExpansionTopic,
    EFormProfessionalNetworkingTopic,
    EFormMentoringGrade,
    EFormMentoringHelpRequest, 
    EFormSpecialization,
    EFormRefferalsCompanyType,
    EFormCompanies,
    EFormEnglishLevel,
    EFormMockInterviewType,
    EFormMockInterviewLangluages,
    EFormSkills,
    EFormProjectProjectState,
    EFormProjectUserRole,
)


def validate_non_empty_list(obj, fields):
    for field_name in fields:
        if len(obj.__getattribute__(field_name)) == 0:
            raise ValueError(f"\"{field_name}\" list must be non-empty")


# ============================ Connects form schema ============================
class FormFieldSocialSircleExpansion(BaseModel):
    meeting_formats: list[EFormConnectsMeetingFormat]
    topics: list[EFormConnectsSocialExpansionTopic] | None # TODO: Is it optional? Figma - optional
    custom_topics: list[str] | None
    details: str | None
    
    @model_validator(mode='after')
    def check_nonempty(self):
        if len(self.meeting_formats) == 0:
            raise ValueError("\"meeting_formats\" list must be non-empty")
        if self.themes:
            if len(self.themes) == 0:
                raise ValueError("\"themes\" list must be non-empty")
            if EFormConnectsSocialExpansionTopic.custom in self.themes:
                if self.custom_themes is None:
                    raise ValueError("\"custom_topics\" list must be setted, when " + 
                                     f"\"{EFormConnectsSocialExpansionTopic.custom.value}\"" + 
                                     " topic added")
                if len(self.custom_themes) == 0:
                    raise ValueError("\"custom_topics\" list must be non-empty, when " + 
                                     f"\"{EFormConnectsSocialExpansionTopic.custom.value}\"" + 
                                     " topic added")
        return self


class FormFieldProfessionalNetworking(BaseModel):
    topics: list[EFormProfessionalNetworkingTopic]
    user_query: str | None

    @model_validator(mode='after')
    def check_nonempty(self):
        validate_non_empty_list(self, ["topics"])
        return self

  
class FormConnects(BaseModel):
    social_circle_expansion: FormFieldSocialSircleExpansion | None = None
    professional_networking: FormFieldProfessionalNetworking | None = None
    companies: EFormCompanies
    
    @model_validator(mode='after')
    def extended_model_validation(self):
        # Check one of fields nonempty
        validate_fields = (
            'social_circle_expansion',
            'professional_networking'
        )

        is_all_empty = True
        for field_name in validate_fields:
            is_all_empty = is_all_empty and (self.__getattribute__(field_name) is None)
        
        if is_all_empty:
            raise ValueError("Minimum one of fields [" + ', '.join(validate_fields) + "] must be filled")
        
        return self

# ==============================================================================

# ============================ Mentoring form schema ===========================

class FormMentoringHelpRequest(BaseModel):
    request: list[EFormMentoringHelpRequest]
    custom_request: str | None = None
    country: str | None = None # String or Enum?

    @model_validator(mode='after')
    def extended_model_validation(self):
        validate_non_empty_list(self, ["request"])
        # Check dependencies between fields
        if EFormMentoringHelpRequest.custom in self.request and self.custom_request is None:
            raise ValueError("\"custom_request\" field must be non-empty when " + 
                             f"\"{EFormMentoringHelpRequest.custom.value}\"" + 
                             " help request selected")
        if EFormMentoringHelpRequest.adaptation_after_relocate in self.request and self.country is None:
            raise ValueError("\"country\" field must be non-empty when " + 
                             f"\"{EFormMentoringHelpRequest.adaptation_after_relocate.value}\"" + 
                             " help request selected")
        

class FormMentoringMentor(BaseModel):
    companies: list[EFormCompanies]
    required_grade: list[EFormMentoringGrade]
    specialization: list[EFormSpecialization]
    help_request: FormMentoringHelpRequest
    about: str

    @model_validator(mode='after')
    def extended_model_validation(self):
        validate_non_empty_list(self, ["companies", "required_grade", "specialization"])
        return self


class FormMentoringMentee(BaseModel):
    grade: list[EFormMentoringGrade]
    mentor_specialization: list[EFormSpecialization]
    help_request: FormMentoringHelpRequest
    details: str

    @model_validator(mode='after')
    def extended_model_validation(self):
        validate_non_empty_list(self, ["grade", "mentor_specialization"])
        return self

# ==============================================================================

# ============================ Refferals form schema ===========================

class FormReferralsRecommendation(BaseModel):
    required_companies: list[EFormCompanies]
    is_all_experts_type: bool
    is_need_call: bool
    required_english_level: EFormEnglishLevel
    job_link: str
    company_type: EFormRefferalsCompanyType
    
    @model_validator(mode='after')
    def check_nonempty(self):
        validate_non_empty_list(self, ["required_companies"])
        return self


# ==============================================================================

# ========================= Mock interview form schema =========================

class FromMockInterviewInterviewLangluage(BaseModel):
    langs: list[EFormMockInterviewLangluages]
    custom_langs: list[str] | None = None
    
    @model_validator(mode='after')
    def check_nonempty(self):
        validate_non_empty_list(self, ["langs"])

        if EFormMockInterviewLangluages.custom in self.langs:
            if self.custom_langs is None:
                raise ValueError("\"custom_langs\" list must be setted, when " + 
                                 f"\"{EFormMockInterviewLangluages.custom.value}\"" + 
                                 " langluage added")
            if len(self.custom_langs) == 0:
                raise ValueError("\"custom_langs\" list must be non-empty, when " + 
                                 f"\"{EFormMockInterviewLangluages.custom.value}\"" + 
                                 " langluage added")
        return self


class FormMockInterview(BaseModel):
    interview_type: list[EFormMockInterviewType]
    job_link: str | None = None
    langluage: FromMockInterviewInterviewLangluage
    resume: str
    details: str
    public_interview: bool
    
    @model_validator(mode='after')
    def extended_valiation(self):
        validate_non_empty_list(self, ["interview_type"])
        return self

# ==============================================================================

# ============================ Projects form schema ============================

class FormProjectsBase(BaseModel):
    project_description: str
    specialization: list[EFormSpecialization]
    skills: list[EFormSkills]
    @model_validator(mode='after')
    def validate_depended_fields(self):
        validate_non_empty_list(self, ["specialization", "skills"])        
        return self


class FormProjectsFindHead(FormProjectsBase):
    project_state: EFormProjectProjectState


class FormProjectPetProject(FormProjectsBase):
    role: EFormProjectUserRole

# ==============================================================================

INTENT_TO_SCHEMA = {
    EFormIntentType.connects: FormConnects,
    EFormIntentType.mentoring_mentor: FormMentoringMentor,
    EFormIntentType.mentoring_mentee: FormMentoringMentee,
    EFormIntentType.referrals_recommendation: FormReferralsRecommendation,
    EFormIntentType.mock_interview: FormMockInterview,
    EFormIntentType.projects_find_cofounder: FormProjectsFindHead,
    EFormIntentType.projects_find_contributor: FormProjectsFindHead,
    EFormIntentType.projects_pet_project: FormProjectPetProject,
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
