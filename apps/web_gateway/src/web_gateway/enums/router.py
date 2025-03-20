from .schemas import EnumValues
from .enum_manager import EnumManger
from fastapi import APIRouter, HTTPException
from common_db.enums.users import (
    EInterestsArea,
    EExpertiseArea,
    ESpecialisation,
    EGrade,
    EIndustry,
    ESkillsArea,
    ECompanyServices,
    ELocation,
    ERequestsArea,
    EWithWhom,
    EVisibilitySettings
)
from common_db.enums.forms import (
    EFormIntentType,
    EFormEnglishLevel,
    EFormConnectsMeetingFormat,
    EFormMentoringHelpRequest,
    EFormRefferalsCompanyType,
    EFormMockInterviewType,
    EFormLangluage,
    EFormProjectProjectState,
    EFormProjectUserRole,
)



router = APIRouter(tags=["Enums"], prefix="/enums")
types = [
    EInterestsArea,
    EExpertiseArea,
    ESpecialisation,
    EGrade,
    EIndustry,
    ESkillsArea,
    ECompanyServices,
    ELocation,
    ERequestsArea,
    EWithWhom,
    EVisibilitySettings,
    EFormIntentType,
    EFormEnglishLevel,
    EFormConnectsMeetingFormat,
    EFormMentoringHelpRequest,
    EFormRefferalsCompanyType,
    EFormMockInterviewType,
    EFormLangluage,
    EFormProjectProjectState,
    EFormProjectUserRole,
]
path_to_type = {
    str(c.__class__.__name__): c for c in types
}

@router.get("/{type}", response_model=EnumValues, summary="Returns possible values of enum class")
async def get_list_of_values(
        type: str
) -> EnumValues:
    manager = EnumManger()
    if type not in path_to_type:
        raise HTTPException(status_code=400, detail="Wrong request")
    return manager.get_possible_values(path_to_type[type])