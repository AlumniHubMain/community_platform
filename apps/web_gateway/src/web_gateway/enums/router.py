from .schemas import EnumValues
from .enum_manager import EnumManger
from fastapi import APIRouter, HTTPException
from common_db.enums.forms import (
    EFormMeetingType,
    EFormLookingForType,
    EFormHelpRequestType,
    EFormQueryType,
)
from common_db.enums.users import (
    EInterests,
    EExpertiseArea,
    ESpecialisation,
    EGrade,
    EIndustry,
    ESkills,
    ECompanyServices,
    ELocation,
    ERequestsToCommunity,
    EWithWhom,
    EVisibilitySettings
)


router = APIRouter(tags=["Enums"], prefix="/enums")
path_to_type = {
    'EInterests': EInterests,
    'EExpertiseArea': EExpertiseArea,
    'ESpecialisation': ESpecialisation,
    'EGrade': EGrade,
    'EIndustry': EIndustry,
    'ESkills': ESkills,
    'ECompanyServices': ECompanyServices,
    'ELocation': ELocation,
    'ERequestsToCommunity': ERequestsToCommunity,
    'EWithWhom': EWithWhom,
    'EVisibilitySettings': EVisibilitySettings,
    'EFormMeetingType': EFormMeetingType,
    'EFormLookingForType': EFormLookingForType,
    'EFormHelpRequestType': EFormHelpRequestType,
    'EFormQueryType': EFormQueryType,
}

@router.get("/{type}", response_model=EnumValues, summary="Returns possible values of enum class")
async def get_list_of_values(
        type: str
) -> EnumValues:
    manager = EnumManger()
    if type not in path_to_type:
        raise HTTPException(status_code=400, detail="Wrong request")
    return manager.get_possible_values(path_to_type[type])