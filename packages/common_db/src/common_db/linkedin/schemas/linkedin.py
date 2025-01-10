from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, HttpUrl

from packages.common_db.src.common_db.linkedin.schemas.piggy_bitches import Education, Experience


class LinkedInProfileBase(BaseModel):
    """Base schema for LinkedIn profile data"""
    # Basic Info
    profile_id: str | None = None
    username: str | None = None
    full_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    headline: str | None = None
    summary: str | None = None

    # Location
    country: str | None = None
    city: str | None = None

    # Professional Info
    occupation: str | None = None
    industry: str | None = None

    # Education and Experience
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)

    # Skills and Endorsements
    skills: list[str] = Field(default_factory=list)
    endorsements: dict[str, int] = Field(default_factory=dict)

    # Contact Info
    email: str | None = None
    phone: str | None = None
    twitter: str | None = None

    # Profile URLs
    profile_url: HttpUrl
    profile_picture: HttpUrl | None = None

    # Connections
    connections_count: int | None = None

    # Additional Info
    languages: list[str] = Field(default_factory=list)
    certifications: list[dict[str, Any]] = Field(default_factory=list)
    volunteer_work: list[dict[str, Any]] = Field(default_factory=list)
    publications: list[dict[str, Any]] = Field(default_factory=list)

    # Raw data
    raw_data: dict[str, Any]


class LinkedInProfileResponse(LinkedInProfileBase):
    """Response schema for API LinkedIn profile data"""
    # TODO: вынести в локальный пакет
    # API Limits
    credits_left: int
    rate_limit_left: int

    class Config:
        from_attributes = True


class LinkedInProfileRead(LinkedInProfileBase):
    """Schema for reading LinkedIn profile from database"""
    users_id_fk: int
    id: int
    created_at: datetime
    updated_at: datetime
    # TODO: добавить схему Юзверя

    class Config:
        from_attributes = True


class LinkedInProfileTask(BaseModel):
    """Task schema for profile parsing"""
    # TODO: вынести в локальный пакет - для pubsub
    username: str
    target_company: str
