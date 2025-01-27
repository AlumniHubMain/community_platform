from datetime import datetime
from pydantic import BaseModel, Field
from linkedin_verifier.app.db.models.limits import LinkedInProviderType


class LinkedInProfileTask(BaseModel):
    """Schema for LinkedIn profile parsing task"""
    profile_url: str
    task_id: str
    created_at: datetime = datetime.utcnow()


class LinkedInLimitsAlert(BaseModel):
    """Alert schema for API limits update"""
    provider_type: LinkedInProviderType
    provider_id: str
    credits_left: int
    rate_limit_left: int
    updated_at: datetime = Field(default_factory=datetime.utcnow)
