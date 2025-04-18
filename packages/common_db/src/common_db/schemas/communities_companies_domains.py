"""
Schemas for working with community companies and their services.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DTOCommunityCompanyServiceBase(BaseModel):
    """Base schema for company service with common fields"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    
    service_label: str | None = None
    description: str | None = None
    logo_url: str | None = None
    is_active: bool = True
    is_custom: bool = False

class DTOCommunityCompanyServiceRead(DTOCommunityCompanyServiceBase):
    """Schema for reading a company service"""
    id: int
    company_id_fk: int
    created_at: datetime
    updated_at: datetime


class DTOCommunityCompanyBase(BaseModel):
    """Base schema for community company with common fields"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

    community_company_domain_label: str | None = None
    description: str | None = None
    logo_url: str | None = None
    is_active: bool = True
    is_custom: bool = False

class DTOCommunityCompanyRead(DTOCommunityCompanyBase):
    """Schema for reading a community company"""
    id: int
    created_at: datetime
    updated_at: datetime
    services: list[DTOCommunityCompanyServiceRead] = []
