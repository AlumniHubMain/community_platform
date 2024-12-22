"""Основной модуль приложения"""

import os
import base64
import json
from pydantic import BaseModel
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import config

from db_common.config import DatabaseSettings
from db_common.db import DatabaseManager
from app.transport import CloudStorageAdapter, PSClient
from app.matching import process_matching_request


@asynccontextmanager
async def lifespan(app: FastAPI):
    global ps_client
    global config
    ps_client = PSClient()
    storage_client = CloudStorageAdapter()
    await storage_client.initialize()
    await ps_client.initialize(storage_client)
    yield


settings = DatabaseSettings(service_name="matching")

db = DatabaseManager(settings)

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
        data = json.loads(message["data"])
        return cls(**data)


@app.post("/pubsub/push")
async def pubsub_push(request: Request):
    """Handle Pub/Sub push messages"""
    try:
        envelope = await request.json()
        message = envelope.get("message", {})

        matching_request = MatchingRequest.from_pubsub_message(message)

        if not message:
            raise HTTPException(status_code=400, detail="No message received")

        user_id = matching_request.user_id
        meeting_intent_id = matching_request.meeting_intent_id
        model_settings_preset = matching_request.model_settings_preset
        n = matching_request.n
        form_id = matching_request.form_id

        config.logger.info(
            "Received matching request via Pub/Sub: user_id: %d, meeting_intent_id: %d, model_settings_preset: %s, n: %d",
            user_id,
            meeting_intent_id,
            model_settings_preset,
            n,
        )

        match_id, _ = await process_matching_request(
            db_session_callable=db.session,
            psclient=ps_client,
            logger=config.logger,
            user_id=user_id,
            meeting_intent_id=meeting_intent_id,
            model_settings_preset=model_settings_preset,
            n=n,
            form_id=form_id,
        )

        return {"status": "ok", "match_id": match_id}

    except Exception as e:
        config.logger.error("Error processing Pub/Sub message: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
