"""
Router for working with community companies and their services.
"""
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.db_abstract import db_manager
from common_db.schemas.communities_companies_domains import (
    DTOCommunityCompanyRead,
    DTOCompanyServiceRead
)
from web_gateway import auth
from web_gateway.communities_companies_domains.manager import CommunityCompanyManager

router = APIRouter(prefix="/community-companies", tags=["community-companies"])


@router.get(
    "/communities_companies",
    name="get_communities_companies",
    response_model=List[DTOCommunityCompanyRead]
)
async def get_community_companies(
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(db_manager.get_session)]
):
    """
    Get a list of community companies (Yandex, VK, etc.)
    
    - **active_only**: If True, returns only active companies
    
    Returns a list of companies with their basic information and related services.
    Each company contains a unique domain (e.g., yandex.ru, vk.com).
    """
    return await CommunityCompanyManager.get_community_companies(
        session=session
    )


@router.get(
    "/{company_id}/services",
    name="get_company_services",
    response_model=List[DTOCompanyServiceRead]
)
async def get_company_services(
    company_id: int,
    session: Annotated[AsyncSession, Depends(db_manager.get_session)]
):
    """
    Get a list of services for a specific company
    
    - **company_id**: Unique company identifier
    - **active_only**: If True, returns only active services
    
    Returns a list of services belonging to the specified company.
    For example, for Yandex these could be: Yandex.Food, Yandex.Afisha, etc.
    If the company is not found, returns a 404 error.
    """
    company = await CommunityCompanyManager.get_community_company(
        company_id=company_id,
        session=session
    )
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Company not found"
        )
    return await CommunityCompanyManager.get_company_services(
        company_id=company_id,
        session=session
    )
