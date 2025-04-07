"""
Manager for working with community companies and their services.
"""
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from common_db.models.users import ORMUserProfile
from common_db.schemas.users import DTOUserProfileRead
from common_db.db_abstract import db_manager

logger = logging.getLogger(__name__)


class ReferralManager:
    """Manager for working with referrals."""

    @classmethod
    async def remove_company_from_user_recommenders(
            cls,
            user_id: int,
            company_label: str,
            session: AsyncSession = db_manager.get_session(),
    ) -> dict:
        """
        Remove a company from user's recommender_companies list.
        
        This method removes the specified company from the user's recommender_companies list.
        If the company is not in the list, no changes are made.
        
        Args:
            user_id: User ID
            company_label: Company label to remove (e.g., "Yandex", "VK")
            session: Database session
            
        Returns:
            dict: A dictionary containing:
                - success: bool - True if the operation was successful
                - message: str - A descriptive message about the operation result
        """
        try:
            # Get user data with companies list
            query = (
                select(ORMUserProfile)
                .filter(ORMUserProfile.id == user_id)
            )

            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if user is None:  # User not found
                return {
                    "success": False,
                    "message": f"User with ID {user_id} not found"
                }

            # Get current companies list or empty list if None
            current_companies = user.recommender_companies or []

            if company_label not in current_companies:
                return {
                    "success": False,
                    "message": f"Company '{company_label}' was not in the user's recommender companies list"
                }

            # Create a new list without the company
            updated_companies = [c for c in current_companies if c != company_label]
            # Update user data
            user.recommender_companies = updated_companies
            await session.commit()
            
            return {
                "success": True,
                "message": f"Company '{company_label}' was successfully removed from user's recommender companies"
            }
            
        except Exception as e:
            logger.error(f"Error removing company {company_label} from user {user_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Error removing company: {str(e)}"
            }
    
    @classmethod
    async def get_users_by_company(
            cls,
            company_label: str,
            session: AsyncSession = db_manager.get_session(),
    ) -> list[DTOUserProfileRead]:
        """
        Get users who are recommenders for a specific company
        This method retrieves users who have the specified company in their recommender_companies list.
        Args:
            company_label: Company label to filter by (e.g., "Yandex", "VK")
            session: Database session
        Returns:
            list[DTOUserProfileRead]: List of users who are recommenders for the specified company
        """
        query = (
            select(ORMUserProfile)
            .options(
                selectinload(ORMUserProfile.interests),
                selectinload(ORMUserProfile.industries),
                selectinload(ORMUserProfile.skills),
                selectinload(ORMUserProfile.requests_to_community),
                selectinload(ORMUserProfile.meeting_responses),
                selectinload(ORMUserProfile.user_specialisations)
                .joinedload(ORMUserProfile.user_specialisations.specialisation)
            )
            .filter(func.array_contains(ORMUserProfile.recommender_companies, company_label))
        )
            
        result = await session.execute(query)
        users = result.scalars().all()
        
        return [DTOUserProfileRead.model_validate(user) for user in users]
    
    @classmethod
    async def get_users_by_vacancy_page(
            cls,
            vacancy_page: str,
            session: AsyncSession = db_manager.get_session(),
    ) -> list[DTOUserProfileRead]:
        """
        Get users who have a specific vacancy page
        This method retrieves users who have the specified vacancy page in their vacancy_pages list.
        Args:
            vacancy_page: Vacancy page to filter by (e.g., "jobs.yandex.ru/backend")
            session: Database session
        Returns:
            list[DTOUserProfileRead]: List of users who have the specified vacancy page
        """
        query = (
            select(ORMUserProfile)
            .options(
                selectinload(ORMUserProfile.interests),
                selectinload(ORMUserProfile.industries),
                selectinload(ORMUserProfile.skills),
                selectinload(ORMUserProfile.requests_to_community),
                selectinload(ORMUserProfile.meeting_responses),
                selectinload(ORMUserProfile.user_specialisations)
                .joinedload(ORMUserProfile.user_specialisations.specialisation)
            )
            .filter(func.array_contains(ORMUserProfile.vacancy_pages, vacancy_page))
        )
            
        result = await session.execute(query)
        users = result.scalars().all()
        
        return [DTOUserProfileRead.model_validate(user) for user in users]
