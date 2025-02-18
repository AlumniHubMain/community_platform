from typing import Annotated

from common_db.db_abstract import db_manager
from common_db.managers.user import UserManager
from common_db.schemas import (
    DTOSpecialisationRead,
    DTOInterestRead,
    DTOSkillRead,
    DTORequestsCommunityRead,
    DTOAllProperties)

from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(tags=["User properties"], prefix="/properties")


@router.get("/specialisations", response_model=list[DTOSpecialisationRead])
async def get_all_specialisations(
        session: Annotated[AsyncSession,
        Depends(db_manager.get_session)]
) -> list[DTOSpecialisationRead]:
    """
    Endpoint for getting all non-custom specialisations from the database.
    """
    return await UserManager.get_all_specialisations(session)

@router.get("/interests", response_model=list[DTOInterestRead])
async def get_all_interests(
        session: Annotated[AsyncSession,
        Depends(db_manager.get_session)]
) -> list[DTOInterestRead]:
    """
    Endpoint for getting all non-custom interests from the database.
    """
    return await UserManager.get_all_interests(session)

@router.get("/skills", response_model=list[DTOSkillRead])
async def get_all_skills(
        session: Annotated[AsyncSession,
        Depends(db_manager.get_session)]
) -> list[DTOSkillRead]:
    """
    Endpoint for getting all non-custom skills from the database.
    """
    return await UserManager.get_all_skills(session)

@router.get("/requests_community", response_model=list[DTORequestsCommunityRead])
async def get_all_requests_community(
        session: Annotated[AsyncSession,
        Depends(db_manager.get_session)]
) -> list[DTORequestsCommunityRead]:
    """
    Endpoint for getting all non-custom requests to community from the database.
    """
    return await UserManager.get_all_requests_to_community(session)


@router.get("/all", response_model=DTOAllProperties)
async def get_all_properties(
    session: Annotated[AsyncSession, Depends(db_manager.get_session)]
) -> DTOAllProperties:
    """
    Endpoint for getting all non-custom properties from the database.
    """
    all_properties: DTOAllProperties = DTOAllProperties(
        specialisations=await UserManager.get_all_specialisations(session),
        interests=await UserManager.get_all_interests(session),
        skills=await UserManager.get_all_skills(session),
        requests_to_community=await UserManager.get_all_requests_to_community(session)
    )
    return all_properties
