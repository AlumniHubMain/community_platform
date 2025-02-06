from typing import Annotated

from common_db.db_abstract import db_manager
from common_db.schemas import DTOSpecialisation, DTOInterest, DTOSkill, DTORequestsCommunity\

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from .user_profile_manager import UserProfileManager



router = APIRouter(tags=["User properties"], prefix="/properties")


@router.get("/specialisations", response_model=list[DTOSpecialisation])
async def search_users(session: Annotated[AsyncSession, Depends(db_manager.get_session)]) -> list[DTOSpecialisation]:
    """
    Endpoint for getting all non-custom specialisations from the database.
    """
    return await UserProfileManager.get_all_specialisations(session)

@router.get("/interests", response_model=list[DTOInterest])
async def search_users(session: Annotated[AsyncSession, Depends(db_manager.get_session)]) -> list[DTOInterest]:
    """
    Endpoint for getting all non-custom interests from the database.
    """
    return await UserProfileManager.get_all_interests(session)

@router.get("/skills", response_model=list[DTOSkill])
async def search_users(session: Annotated[AsyncSession, Depends(db_manager.get_session)]) -> list[DTOSkill]:
    """
    Endpoint for getting all non-custom skills from the database.
    """
    return await UserProfileManager.get_all_skills(session)

@router.get("/requests_community", response_model=list[DTORequestsCommunity])
async def search_users(session: Annotated[AsyncSession, Depends(db_manager.get_session)]) -> list[DTORequestsCommunity]:
    """
    Endpoint for getting all non-custom requests to community from the database.
    """
    return await UserProfileManager.get_all_requests_to_community(session)
