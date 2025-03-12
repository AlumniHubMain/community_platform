"""
Router for working with referrals.

============================================================================
FRONTEND INTEGRATION GUIDE, see endpoint: /referrals/docs
This endpoint provides comprehensive information about all available endpoints
and how to use them with Figma screens: 4433, 4434
============================================================================
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.db_abstract import db_manager
from common_db.schemas.communities_companies_domains import (
    DTOCommunityCompanyRead
)
from common_db.schemas.users import DTOUserProfileRead
from common_db.managers.user import UserManager
from web_gateway import auth
from web_gateway.referrals.manager import ReferralManager

router = APIRouter(prefix="/referrals", tags=["referrals"])
















@router.get(
    "/docs",
    name="get_integration_docs",
    include_in_schema=False  # Не показывать в Swagger
)
async def get_integration_docs():
    """
    Integration documentation for frontend developers.
    """
    return {
        "title": "Referrals Integration Guide",
        "subtitle": "With love from backend ❤️",
        "integration_guide": {
            "figma_4433": {
                "description": "Load user's companies list (Всех, Яндекс, ВК)",
                "endpoint": "get /user/{user_id}",
                "field_to_use": "communities_companies_domains",
                "notes": ""
                         "Returns the user profile which contains [communities_companies_domains] field."
                         "For Figma screen 4433, frontend should use the [communities_companies_domains] field."
                         "According Tech Spec: without another fields in form."
            },
            "figma_4334": {
                "description": "Save companies and vacancy_pages to refer (without else fields - Tech Spec).",
                "endpoint": "patch /user/{user_id}",
                "notes": "Should put selected by user"
                         " in recommender_companies: list[str], vacancy_pages: list[str] fileds."
            }
        }
    }
