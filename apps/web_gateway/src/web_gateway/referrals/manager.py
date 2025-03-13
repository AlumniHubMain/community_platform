"""
Manager for working with community companies and their services.
"""
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.models.users import ORMUserProfile
from common_db.schemas.users import DTOUserProfileRead
from common_db.db_abstract import db_manager


class ReferralManager:
    """Manager for working with referrals."""
    
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
            # .options(
            #     selectinload(ORMUserProfile.interests),
            #     selectinload(ORMUserProfile.industries),
            #     selectinload(ORMUserProfile.skills),
            #     selectinload(ORMUserProfile.requests_to_community),
            #     selectinload(ORMUserProfile.meeting_responses),
            #     selectinload(ORMUserProfile.user_specialisations)
            #     .joinedload(ORMUserProfile.user_specialisations.specialisation)
            # )
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
            .filter(func.array_contains(ORMUserProfile.vacancy_pages, vacancy_page))
        )
            
        result = await session.execute(query)
        users = result.scalars().all()
        
        return [DTOUserProfileRead.model_validate(user) for user in users]
