from .schemas import EnumValues
from .enum_manager import EnumManger
from fastapi import APIRouter, HTTPException
from common_db.enums.forms import (
    EIntentType,
    EMeetingFormat,
)
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


router = APIRouter(tags=["Enums"], prefix="/enums")
path_to_type = {
    'EIntentType': EIntentType,
    'EMeetingFormat': EMeetingFormat,
    'EInterestsArea': EInterestsArea,
    'EExpertiseArea': EExpertiseArea,
    'ESpecialisation': ESpecialisation,
    'EGrade': EGrade,
    'EIndustry': EIndustry,
    'ESkillsArea': ESkillsArea,
    'ECompanyServices': ECompanyServices,
    'ELocation': ELocation,
    'ERequestsArea': ERequestsArea,
    'EWithWhom': EWithWhom,
    'EVisibilitySettings': EVisibilitySettings,
}

@router.get("/{type}", response_model=EnumValues, summary="Returns possible values of enum class")
async def get_list_of_values(
        type: str
) -> EnumValues:
    manager = EnumManger()
    if type not in path_to_type:
        raise HTTPException(status_code=400, detail="Wrong request")
    return manager.get_possible_values(path_to_type[type])