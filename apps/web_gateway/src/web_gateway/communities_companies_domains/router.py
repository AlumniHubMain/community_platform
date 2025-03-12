"""
Router for working with community companies and their services.
"""
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.db_abstract import db_manager
from common_db.schemas.communities_companies_domains import (
    DTOCommunityCompanyRead
)
from common_db.schemas.users import DTOUserProfileRead
from common_db.managers.user import UserManager
from web_gateway import auth
from web_gateway.communities_companies_domains.manager import CommunityCompanyManager

router = APIRouter(prefix="/community-companies", tags=["community-companies"])


@router.get(
    "communities_companies_with_services/me",
    name="get_communities_companies",
    response_model=DTOUserProfileRead
)
async def get_personal_community_companies(
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(db_manager.get_session)]
):
    """
    Get user`s profile with his communities (communities_companies_domains)
    
    Returns the user profile which contains communities_companies_domains field.
    According to requirements, this endpoint doesn't include services (also separated by companies).
    For Figma screen 4365, frontend should use the communities_companies_domains field.
    
    Figma: 4365
    """
    await UserManager.check_user(session=session, user_id=user_id)

    return await UserManager.get_user_by_id(
        user_id=user_id,
        session=session
    )


@router.get(
    "/community_company_with_services/{company_id}",
    name="get_community_company",
    response_model=DTOCommunityCompanyRead
)
async def get_curr_community_company(
    company_id: int,
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(db_manager.get_session)]
):
    """
    Get a specific community company with all its services by company_id (not personal)

    Returns detailed information about a company and all its services.
    If the company is not found, returns a 404 error.
    According to requirements, this endpoint doesn't include personal services.
    
    Figma: 4366
    """
    company = await CommunityCompanyManager.get_curr_community_company_with_services(
        company_id=company_id,
        session=session
    )
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Company not found"
        )
    return company
