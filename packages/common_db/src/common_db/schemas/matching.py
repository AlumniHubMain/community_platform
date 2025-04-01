from common_db.schemas.base import BaseSchema, TimestampedSchema
from common_db.enums.forms import EFormIntentType

import base64
import json
from pydantic import field_validator


SUPPORTED_INTENTS: set[EFormIntentType] = {
    EFormIntentType.connects,
    EFormIntentType.mentoring_mentee,
    EFormIntentType.mentoring_mentor,
    EFormIntentType.mock_interview,
    EFormIntentType.projects_find_cofounder,
    EFormIntentType.projects_find_contributor,
    EFormIntentType.projects_pet_project,
}


class MatchingRequest(BaseSchema):
    """Matching request schema"""
    user_id: int
    form_id: int | None = None
    model_settings_preset: str = "heuristic"
    n: int = 5
    
    # Fields for text-based matching
    text_description: str | None = None
    intent_type: EFormIntentType | None = None
    
    @field_validator('form_id')
    def validate_form_or_text(cls, v, info):
        """Validate that either form_id or text_description is provided"""
        data = info.data
        if 'text_description' in data and data['text_description']:
            # For text-based matching, text_description is required
            return v
        elif v is None:
            # For form-based matching, form_id is required
            raise ValueError("form_id is required for form-based matching")
        return v
    
    @classmethod
    def from_pubsub_message(cls, message):
        """Create MatchingRequest from PubSub message"""
        if not message.get("data"):
            return cls(user_id=0, form_id=0)
        
        data = base64.b64decode(message["data"]).decode("utf-8")
        json_data = json.loads(data)
        
        return cls(**json_data)


class MatchingResultRead(TimestampedSchema):
    model_settings_preset: str
    match_users_count: int
    user_id: int
    form_id: int | None
    error_code: str | None
    error_details: str | None
    matching_result: list[int]
