from common_db.schemas.base import BaseSchema, TimestampedSchema
from common_db.enums.forms import EFormIntentType
from fastapi import HTTPException

import base64
import json


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
    user_id: int
    form_id: int
    model_settings_preset: str
    n: int

    @classmethod
    def from_pubsub_message(cls, message: dict) -> "MatchingRequest":
        if not message.get("data"):
            raise HTTPException(status_code=400, detail="No data in message")

        try:
            decoded_data = base64.b64decode(message["data"]).decode("utf-8")
            data = json.loads(decoded_data)
            return cls(**data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid message format: {str(e)}") from e


class MatchingResultRead(TimestampedSchema):
    model_settings_preset: str
    match_users_count: int
    user_id: int
    form_id: int | None
    error_code: str | None
    error_details: str | None
    matching_result: list[int]
