from pydantic import BaseModel, model_validator

from common_db.schemas.base import BaseSchema, TimestampedSchema
from common_db.enums.forms import (
    EFormIntentType,
    EFormConnectsMeetingFormat,
    EFormMentoringHelpRequest,
    EFormRefferalsCompanyType,
    EFormEnglishLevel,
    EFormMockInterviewType,
    EFormLangluage,
    EFormProjectProjectState,
    EFormProjectUserRole,
)
from common_db.enums.users import (
    ESpecialisation,
    EExpertiseArea,
)
from common_db.enums.users import EGrade


def validate_non_empty_list(obj, fields):
    for field_name in fields:
        if len(obj.__getattribute__(field_name)) == 0:
            raise ValueError(f"\"{field_name}\" list must be non-empty")


# ============================ Connects form schema ============================
class FormFieldSocialSircleExpansion(BaseModel):
    meeting_formats: list[EFormConnectsMeetingFormat]
    topics: list[int | None] # List of specializations id or custom topic(None)
    custom_topics: list[str] | None = None
    details: str | None = None
    
    @model_validator(mode='after')
    def check_nonempty(self):
        validate_non_empty_list(self, ["topics"])
        none_cnt = sum([1 for topic in self.topics if topic is None])
        if none_cnt > 0:
            if self.custom_topics is None:
                raise ValueError("\"custom_topics\" list must be setted, when None topic added")
            if len(self.custom_topics) == 0:
                raise ValueError("\"custom_topics\" list must be non-empty, when None topic added")
            if len(self.custom_topics) != none_cnt:
                raise ValueError("\"custom_topics\" list must gave size equal to None count in \"topics\" field, when None topic added")
        return self


class FormFieldProfessionalNetworking(BaseModel):
    required_expertises: list[EExpertiseArea]
    user_query: str | None = None

    @model_validator(mode='after')
    def check_nonempty(self):
        validate_non_empty_list(self, ["required_expertises"])
        return self

  
class FormConnects(BaseModel):
    social_circle_expansion: FormFieldSocialSircleExpansion | None = None
    professional_networking: FormFieldProfessionalNetworking | None = None
    is_local_community: bool
    
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
        if EFormMentoringHelpRequest.relocation_and_adaptation in self.request and self.country is None:
            raise ValueError("\"country\" field must be non-empty when " + 
                             f"\"{EFormMentoringHelpRequest.relocation_and_adaptation.value}\"" + 
                             " help request selected")
        

class FormMentoringMentor(BaseModel):
    is_local_community: bool
    required_grade: list[EGrade]
    specialization: list[ESpecialisation]
    help_request: FormMentoringHelpRequest
    about: str

    @model_validator(mode='after')
    def extended_model_validation(self):
        validate_non_empty_list(self, ["required_grade", "specialization"])
        return self


class FormMentoringMentee(BaseModel):
    mentor_specialization: list[int] # List of specializations id
    help_request: FormMentoringHelpRequest
    about: str

    @model_validator(mode='after')
    def extended_model_validation(self):
        validate_non_empty_list(self, ["grade", "mentor_specialization"])
        return self

# ==============================================================================

# ============================ Refferals form schema ===========================

class FormReferralsRecommendation(BaseModel):
    is_local_community: bool
    is_all_experts_type: bool
    is_need_call: bool
    required_english_level: EFormEnglishLevel
    job_link: str
    company_type: EFormRefferalsCompanyType


# ==============================================================================

# ========================= Mock interview form schema =========================

class FromMockInterviewInterviewLangluage(BaseModel):
    langs: list[EFormLangluage]
    custom_langs: list[str] | None = None
    
    @model_validator(mode='after')
    def check_nonempty(self):
        validate_non_empty_list(self, ["langs"])

        if EFormLangluage.custom in self.langs:
            if self.custom_langs is None:
                raise ValueError("\"custom_langs\" list must be setted, when " + 
                                 f"\"{EFormLangluage.custom.value}\"" + 
                                 " langluage added")
            if len(self.custom_langs) == 0:
                raise ValueError("\"custom_langs\" list must be non-empty, when " + 
                                 f"\"{EFormLangluage.custom.value}\"" + 
                                 " langluage added")
        return self


class FormMockInterview(BaseModel):
    interview_type: list[EFormMockInterviewType]
    custom_interview_type: str | None = None
    job_link: str | None = None
    language: FromMockInterviewInterviewLanguage
    resume: str
    details: str
    public_interview: bool
    
    @model_validator(mode='after')
    def extended_valiation(self):
        validate_non_empty_list(self, ["interview_type"])
        if EFormMockInterviewType.custom in self.interview_type and self.custom_interview_type is None:
            raise ValueError("\"custom_interview_type\" must be setted, when " + 
                                 f"\"{EFormMockInterviewType.custom.value}\"" + 
                                 " interview type added")
        return self

# ==============================================================================

# ============================ Projects form schema ============================

class FormProjectsBase(BaseModel):
    project_description: str
    specializations: list[int] # List of specializations id
    skills: list[int] # List of skill id
    
    @model_validator(mode='after')
    def validate_depended_fields(self):
        validate_non_empty_list(self, ["specializations", "skills"])        
        return self


class FormProjectsFindHead(FormProjectsBase):
    project_state: EFormProjectProjectState


class FormProjectPetProject(FormProjectsBase):
    role: EFormProjectUserRole

# ==============================================================================


class FormBase(BaseSchema):
    """Base schema for forms"""
    intent: EFormIntentType
    content: dict
    
    @model_validator(mode='after')
    def validate_schemas(self):
        
        REGISTERED_INTENT_SCHEMAS = {
            EFormIntentType.connects: FormConnects,
            EFormIntentType.mentoring_mentor: FormMentoringMentor,
            EFormIntentType.mentoring_mentee: FormMentoringMentee,
            EFormIntentType.referrals_recommendation: FormReferralsRecommendation,
            EFormIntentType.mock_interview: FormMockInterview,
            EFormIntentType.projects_find_cofounder: FormProjectsFindHead,
            EFormIntentType.projects_find_contributor: FormProjectsFindHead,
            EFormIntentType.projects_pet_project: FormProjectPetProject,
        }
        
        if not (self.intent in REGISTERED_INTENT_SCHEMAS):
            raise ValueError("Unregistred intent type")
        
        schema = REGISTERED_INTENT_SCHEMAS[self.intent]
        _ = schema.model_validate(self.content, from_attributes=True)
        return self


class UserForm(FormBase):
    """Form assigned to user"""
    user_id: int

class FormCreate(UserForm):
    """Schema for creating a form"""
    pass


class FormRead(UserForm, TimestampedSchema):
    """Schema for reading a form"""
    id: int
    intent: EFormIntentType
    content: dict
    description: str | None = None
    
    # Add helper properties for the predictor
    @property
    def meeting_format(self) -> str | None:
        """Extract meeting format from content based on intent type"""
        if self.intent == EFormIntentType.connects.value:
            if 'social_circle_expansion' in self.content:
                formats = self.content['social_circle_expansion'].get('meeting_formats', [])
                return formats[0] if formats else None
        return self.content.get('meeting_format', 'any')

    @property
    def specialization(self) -> list[str]:
        """Get specialization from content"""
        return self.content.get('specialization', [])

    @property
    def required_grade(self) -> list[str]:
        """Get required grade from content"""
        return self.content.get('required_grade', [])
