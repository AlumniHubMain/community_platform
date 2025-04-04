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

from common_db.schemas.users import DTOUserProfileRead
from web_gateway import auth
from web_gateway.referrals.manager import ReferralManager

router = APIRouter(prefix="/referrals", tags=["Referrals"])



@router.get(
    "/docs",
    name="FRONTEND INTEGRATION GUIDE: get_integration_docs"
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
                         " in recommended_companies: list[str], vacancy_pages: list[str] fileds."
            },
            "figma_4335": {
                "description": "Search users who are recommenders for a specific company",
                "endpoint": "get /referrals/company/{company_label}/users",
                "notes": "Returns a list of users who have the specified company in their recommender_companies list."
            },
            "figma_4336": {
                "description": "Search users who have a specific vacancy page",
                "endpoint": "get /referrals/vacancy/{vacancy_page}/users",
                "notes": "Returns a list of users who have the specified vacancy page in their vacancy_pages list."
            },
            "figma_4436": {
                "description": "Remove a company from user's recommender companies",
                "endpoint": "patch /referrals/user/{user_id}/company/{company_label}/remove",
                "notes": "Removes the specified company from the user's recommender_companies list."
            }
        }
    }


@router.get(
    "/company/{company_label}/users",
    name="get_company_recommenders",
    response_model=list[DTOUserProfileRead]
)
async def get_company_recommenders(
    company_label: str,
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(db_manager.get_session)]
):
    """
    Get users who are recommenders for a specific company
    This endpoint retrieves users who have the specified company in their recommender_companies list.
    Args:
        company_label: Company label to filter by (e.g., "Yandex", "VK")
    Returns:
        List of users who are recommenders for the specified company
    Figma: 4335
    """
    return await ReferralManager.get_users_by_company(
        company_label=company_label,
        session=session
    )


@router.patch(
    "/user/{user_id}/company/{company_label}/remove",
    name="remove_company_from_user",
    status_code=status.HTTP_200_OK
)
async def remove_company_from_user(
        company_label: str,
        user_id: Annotated[int, Depends(auth.current_user_id)],
        session: Annotated[AsyncSession, Depends(db_manager.get_session)]
):
    """
    Remove a company from user's recommender_companies list
    This endpoint removes the specified company from the user's recommender_companies list.
    If the company is not in the list, no changes are made.
    Args:
        user_id: User ID
        company_label: Company label to remove (e.g., "Yandex", "VK")
    Returns:
        200 OK with success message
    Figma: 4436
    """
    success = await ReferralManager.remove_company_from_user_recommenders(
        user_id=user_id,
        company_label=company_label,
        session=session
    )
    # Return 200 OK with success message
    return {"status": "success", "message": f"Company '{company_label}' removed from user's recommender companies"}


@router.get(
    "/vacancy/{vacancy_page}/users",
    name="get_vacancy_page_users",
    response_model=list[DTOUserProfileRead]
)
async def get_vacancy_page_users(
    vacancy_page: str,
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(db_manager.get_session)]
):
    """
    Get users who have a specific vacancy page
    This endpoint retrieves users who have the specified vacancy page in their vacancy_pages list.
    Args:
        vacancy_page: Vacancy page to filter by (e.g., "jobs.yandex.ru/backend")
    Returns:
        List of users who have the specified vacancy page
    Figma: 4336
    """
    return await ReferralManager.get_users_by_vacancy_page(
        vacancy_page=vacancy_page,
        session=session
    )
