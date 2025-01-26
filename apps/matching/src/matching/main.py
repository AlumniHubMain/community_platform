"""Основной модуль приложения"""

import os
import base64
import json
import logging
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from common_db.db_abstract import db_manager

from matching.transport import CloudStorageAdapter, PSClient
from matching.matching import process_matching_request
from matching.services import psclient


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=unused-argument, redefined-outer-name
    global psclient  # pylint: disable=global-statement
    psclient = PSClient()
    storage_client = CloudStorageAdapter()
    await storage_client.initialize()
    await psclient.initialize(storage_client)
    yield


app = FastAPI(title="Community platform matching service", lifespan=lifespan)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

origins = [
    BASE_URL,
    "http://localhost:5173",
    "https://platform-web-flax.vercel.app",
    "https://platform-web-flax.vercel.app:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MatchingRequest(BaseModel):
    user_id: int
    meeting_intent_id: int
    model_settings_preset: str
    n: int
    form_id: int | None = None

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


@app.post("/pubsub/push")
async def pubsub_push(request: Request):
    """Handle Pub/Sub push messages"""
    try:
        envelope = await request.json()
        message = envelope.get("message")

        if not message:
            raise HTTPException(status_code=400, detail="No message received")

        matching_request = MatchingRequest.from_pubsub_message(message)

        logger.info(
            "Received matching request: user_id: %d, meeting_intent_id: %d, model_settings_preset: %s, n: %d",
            matching_request.user_id,
            matching_request.meeting_intent_id,
            matching_request.model_settings_preset,
            matching_request.n,
        )

        match_id, _ = await process_matching_request(
            db_session_callable=db_manager.session,
            psclient=psclient,
            logger=logger,
            user_id=matching_request.user_id,
            meeting_intent_id=matching_request.meeting_intent_id,
            model_settings_preset=matching_request.model_settings_preset,
            n=matching_request.n,
            form_id=matching_request.form_id,
        )

        return {"status": "ok", "match_id": match_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing Pub/Sub message: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
