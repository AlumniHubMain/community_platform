from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema for all models"""

    model_config = ConfigDict(
        from_attributes=True,
        ser_json_timedelta='iso8601',
        validate_assignment=True
    )

    def model_dump(self, *args, **kwargs) -> dict:
        """Override model_dump to handle enum serialization"""
        data = super().model_dump(*args, **kwargs)
        return {k: convert_enum_value(v) for k, v in data.items()}


class TimestampedSchema(BaseSchema):
    """Base schema for timestamped models"""

    id: int
    created_at: datetime
    updated_at: datetime


def convert_enum_value(value):
    """Convert enum values for serialization"""
    try:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            return [convert_enum_value(item) for item in value]
        if isinstance(value, dict):
            return {k: convert_enum_value(v) for k, v in value.items()}
        return value.value
    except AttributeError:
        return value
