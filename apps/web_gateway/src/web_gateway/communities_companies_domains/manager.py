"""
Manager for working with community companies and their services.
"""
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.models.communities_companies_domains import ORMCommunityCompany, ORMCommunityCompanyService
from common_db.schemas.communities_companies_domains import (
    DTOCommunityCompanyRead
)
from common_db.db_abstract import db_manager


class CommunityCompanyManager:
    """Manager for working with community companies and their services"""
    
    @classmethod
    async def get_all_community_companies_and_services(
            cls,
            session: AsyncSession = db_manager.get_session(),
    ) -> list[DTOCommunityCompanyRead]:
        """
        Get a list of all community companies with all their services
        
        Args:
            session: Database session
            
        Returns:
            list[DTOCommunityCompanyRead]: List of companies
        """
        query = (
            select(ORMCommunityCompany)
            .options(selectinload(ORMCommunityCompany.services))
        )
            
        result = await session.execute(query)
        companies = result.scalars().all()
        
        return [DTOCommunityCompanyRead.model_validate(company) for company in companies]
    
    @classmethod
    async def get_community_company_with_services(
            cls,
            company_id: int,
            session: AsyncSession = db_manager.get_session(),
    ) -> DTOCommunityCompanyRead | None:
        """
        Get a specific community company with all its services by ID
        
        Args:
            company_id: Company ID
            session: Database session
            
        Returns:
            DTOCommunityCompanyRead | None: Company with services or None if not found
        """
        query = (
            select(ORMCommunityCompany)
            .options(selectinload(ORMCommunityCompany.services))
            .filter(ORMCommunityCompany.id == company_id)
        )
            
        result = await session.execute(query)
        company = result.scalar_one_or_none()
        
        if company is None:
            return None
            
        return DTOCommunityCompanyRead.model_validate(company)
