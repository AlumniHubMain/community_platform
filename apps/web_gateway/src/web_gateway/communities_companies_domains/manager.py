"""
Manager for working with community companies and their services.
"""
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.models.communities_companies_domains import ORMCommunityCompany, ORMCompanyService
from common_db.schemas.communities_companies_domains import (
    DTOCommunityCompanyRead,
    DTOCompanyServiceRead
)
from common_db.db_abstract import db_manager


class CommunityCompanyManager:
    """Manager for working with community companies and their services"""
    
    @classmethod
    async def get_community_companies(
            cls,
            session: AsyncSession = db_manager.get_session(),
            active_only: bool = False
    ) -> list[DTOCommunityCompanyRead]:
        """
        Get a list of all community companies
        
        Args:
            session: Database session
            active_only: Only active companies
            
        Returns:
            list[DTOCommunityCompanyRead]: List of companies
        """
        query = (
            select(ORMCommunityCompany)
            .options(selectinload(ORMCommunityCompany.services))
        )
        
        if active_only:
            query = query.filter(ORMCommunityCompany.is_active == True)
            
        result = await session.execute(query)
        companies = result.scalars().all()
        
        return [DTOCommunityCompanyRead.model_validate(company) for company in companies]
    
    @classmethod
    async def get_community_company(
            cls,
            company_id: int,
            session: AsyncSession = db_manager.get_session()
    ) -> DTOCommunityCompanyRead | None:
        """
        Get a community company by ID
        
        Args:
            company_id: Company ID
            session: Database session
            
        Returns:
            DTOCommunityCompanyRead | None: Company or None if not found
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
    
    @classmethod
    async def get_company_services(
            cls,
            company_id: int,
            session: AsyncSession = db_manager.get_session(),
            active_only: bool = False
    ) -> list[DTOCompanyServiceRead]:
        """
        Get a list of company services
        
        Args:
            company_id: Company ID
            session: Database session
            active_only: Only active services
            
        Returns:
            list[DTOCompanyServiceRead]: List of services
        """
        query = select(ORMCompanyService).filter(ORMCompanyService.company_id == company_id)
        
        if active_only:
            query = query.filter(ORMCompanyService.is_active == True)
            
        result = await session.execute(query)
        services = result.scalars().all()
        
        return [DTOCompanyServiceRead.model_validate(service) for service in services]
    
    @classmethod
    async def get_company_service(
            cls,
            company_id: int,
            service_id: int,
            session: AsyncSession
    ) -> DTOCompanyServiceRead | None:
        """
        Get a company service by ID
        
        Args:
            company_id: Company ID
            service_id: Service ID
            session: Database session
            
        Returns:
            DTOCompanyServiceRead | None: Service or None if not found
        """
        query = (
            select(ORMCompanyService)
            .filter(
                ORMCompanyService.company_id == company_id,
                ORMCompanyService.id == service_id
            )
        )
        result = await session.execute(query)
        service = result.scalar_one_or_none()
        
        if service is None:
            return None
            
        return DTOCompanyServiceRead.model_validate(service)
