from common_db.schemas.base import BaseSchema
from fastapi import HTTPException

import base64
import json


class MatchingRequest(BaseSchema):
    user_id: int
    form_id: int
    model_settings_preset: str # heuristic
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
