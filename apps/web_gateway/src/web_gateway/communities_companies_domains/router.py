"""
Router for working with community companies and their services.

============================================================================
FRONTEND INTEGRATION GUIDE, see endpoint: /community-companies/docs
This endpoint provides comprehensive information about all available endpoints
and how to use them with Figma screens: 4365, 4366
============================================================================
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.db_abstract import db_manager
from common_db.schemas.communities_companies_domains import (
    DTOCommunityCompanyRead
)
from web_gateway import auth
from web_gateway.communities_companies_domains.manager import CommunityCompanyManager

router = APIRouter(prefix="/community_companies", tags=["community-companies"])


@router.get(
    "/{company_label}",
    name="get_community_company",
    response_model=DTOCommunityCompanyRead
)
async def get_curr_community_company(
    company_label: str,
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(db_manager.get_session)]
):
    """
    Get a specific community company with all its services by company_label (not personal)

    Returns detailed information about a company and all its services.
    If the company is not found, returns a 404 error.
    According to Tech Spec, this endpoint doesn't include personal services.
    
    Figma: 4366
    """
    company = await CommunityCompanyManager.get_curr_community_company_with_services(
        company_label=company_label,
        session=session
    )
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Company not found"
        )
    return company


@router.get(
    "/docs",
    name="get_integration_docs"
)
async def get_integration_docs():
    """
    Integration documentation for frontend developers.
    """
    return {
        "title": "Community Companies Integration Guide",
        "subtitle": "With love from backend ❤️",
        "integration_guide": {
            "figma_4365": {
                "description": "Load user's companies list (without personal services - Tech Spec).",
                "endpoint": "get /user/{user_id}",
                "field_to_use": "communities_companies_domains",
                "notes": "Returns the user profile which contains [communities_companies_domains] field."
                         "For Figma screen 4365, frontend should use the [communities_companies_domains] field."
                         "According Tech Spec: this endpoint doesn't include services."
            },
            "figma_4366": {
                "description": "Company details with services (without pre-load personal services - Tech Spec).",
                "endpoint": "/community_company_with_services/{company_label}",
                "notes": "Returns detailed information about a specific company with all its services, not personal."
                         "Arg: company_label should bring from [communities_companies_domains] list from figma_4365."
            },
            "figma_4367": {
                "description": "Save personal services.",
                "endpoint": "patch /user/{user_id}",
                "notes": "Should put selected by user services (list[str]) in [communities_companies_services] filed."
            }
        }
    }
