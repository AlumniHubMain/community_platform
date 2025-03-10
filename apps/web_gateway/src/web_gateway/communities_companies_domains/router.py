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
from web_gateway import auth
from web_gateway.communities_companies_domains.manager import CommunityCompanyManager

router = APIRouter(prefix="/community-companies", tags=["community-companies"])


@router.get(
    "/communities_companies_with_services",
    name="get_communities_companies",
    response_model=List[DTOCommunityCompanyRead]
)
async def get_community_companies(
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(db_manager.get_session)]
):
    """
    Get a list of all community companies (Yandex, VK, etc.) with their services
    
    Returns a list of companies with their basic information and related services.
    Each company contains a unique domain (e.g., yandex, vk).
    
    Figma: 4365
    """
    return await CommunityCompanyManager.get_all_community_companies_and_services(
        session=session
    )


@router.get(
    "/community_company_with_services/{company_id}",
    name="get_community_company",
    response_model=DTOCommunityCompanyRead
)
async def get_community_company(
    company_id: int,
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(db_manager.get_session)]
):
    """
    Get a specific community company with all its services by ID
    
    - **company_id**: Unique company identifier
    
    Returns detailed information about a company and all its services.
    If the company is not found, returns a 404 error.
    
    Figma: 4366
    """
    company = await CommunityCompanyManager.get_community_company_with_services(
        company_id=company_id,
        session=session
    )
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Company not found"
        )
    return company
