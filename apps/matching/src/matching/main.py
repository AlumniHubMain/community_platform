"""Основной модуль приложения"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from common_db.db_abstract import db_manager
from common_db.schemas.matching import MatchingRequest
from matching.transport import CloudStorageAdapter, PSClient
from matching.matching import process_matching_request, parse_text_for_matching
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


@app.post("/pubsub/push")
async def pubsub_push(request: Request):
    """Handle Pub/Sub push messages"""
    try:
        envelope = await request.json()
        message = envelope.get("message")

        if not message:
            raise HTTPException(status_code=400, detail="No message received")

        matching_request = MatchingRequest.from_pubsub_message(message)

        # Check if this is a text-based matching request
        if hasattr(matching_request, "text_description") and matching_request.text_description:
            logger.info(
                "Received text-based matching request: user_id: %d, text_description: %s..., model_settings_preset: %s, n: %d",  # pylint: disable=line-too-long
                matching_request.user_id,
                matching_request.text_description[:50],  # pylint: disable=unsubscriptable-object
                matching_request.model_settings_preset,
                matching_request.n,
            )

            match_id, _ = await parse_text_for_matching(
                db_session_callable=db_manager.session,
                psclient=psclient,
                logger=logger,
                user_id=matching_request.user_id,
                text_description=matching_request.text_description,
                intent_type=matching_request.intent_type,  # This might be None, and that's OK
                model_settings_preset=matching_request.model_settings_preset,
                n=matching_request.n,
            )
        else:
            # Standard form-based matching request
            logger.info(
                "Received form-based matching request: user_id: %d, form_id: %d, model_settings_preset: %s, n: %d",
                matching_request.user_id,
                matching_request.form_id,
                matching_request.model_settings_preset,
                matching_request.n,
            )

            match_id, _ = await process_matching_request(
                db_session_callable=db_manager.session,
                psclient=psclient,
                logger=logger,
                user_id=matching_request.user_id,
                form_id=matching_request.form_id,
                model_settings_preset=matching_request.model_settings_preset,
                n=matching_request.n,
            )

        return {"status": "ok", "match_id": match_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing Pub/Sub message: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
