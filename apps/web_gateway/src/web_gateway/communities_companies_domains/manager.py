"""
Manager for working with community companies and their services.
"""
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.models.communities_companies_domains import ORMCommunityCompany
from common_db.schemas.communities_companies_domains import DTOCommunityCompanyRead
from common_db.db_abstract import db_manager


class CommunityCompanyManager:
    """Manager for working with community companies and their services"""
    
    @classmethod
    async def get_curr_community_company_with_services(
            cls,
            company_label: str,
            session: AsyncSession = db_manager.get_session(),
    ) -> DTOCommunityCompanyRead | None:
        """
        Get a specific community company with all its services by company_id
        Not personal <- according to Tech Spec in clickup.
        Args:
            company_label: Company label (if we fuck normalization so this)
            session: Database session
        Returns:
            DTOCommunityCompanyRead | None: Company with services or None if not found
        """
        query = (
            select(ORMCommunityCompany)
            .options(selectinload(ORMCommunityCompany.services))
            .filter(ORMCommunityCompany.community_company_domain_label == company_label)
        )
            
        result = await session.execute(query)
        company = result.scalar_one_or_none()
        
        if company is None:
            return None
            
        return DTOCommunityCompanyRead.model_validate(company)
