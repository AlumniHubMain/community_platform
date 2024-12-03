from datetime import datetime
from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """Base schema for all models"""
    model_config = ConfigDict(from_attributes=True)

class TimestampedSchema(BaseSchema):
    """Base schema for timestamped models"""
    id: int
    created_at: datetime
    updated_at: datetime 