"""Основной модуль приложения"""

import os
from typing import Annotated
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import (
    Depends,
    FastAPI,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.common_db.db_abstract import get_async_session
from app.transport.persistent_storage import CloudStorageAdapter, PSClient
from app.transport.queueing import GoogleQueueManager
from .data_loader import DataLoader
from .services import psclient, queue_manager
from .model import ModelSettings, ModelType, Model


@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=unused-argument,redefined-outer-name
    """Lifecycle func"""
    global psclient, queue_manager  # pylint: disable=global-statement
    psadapter = CloudStorageAdapter()
    await psadapter.initialize()
    psclient = PSClient()
    await psclient.initialize(psadapter)

    queue_manager = GoogleQueueManager()
    await queue_manager.initialize(config)
    print("Service started")
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


@app.get("/get_matches/{user_id}/{meeting_intent_id}")
async def get_matches(
    user_id: int,
    meeting_intent_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    n: int = 10,
):
    """Get matches for user and send result to topic"""
    config.logger.info(
        "Recieved matching request user_id: %d, meeting_intent_id: %d",
        user_id,
        meeting_intent_id,
    )
    all_users = await DataLoader.get_all_user_profiles(session)
    all_linkedin = await DataLoader.get_all_linkedin_profiles(session)
    all_intents = await DataLoader.get_all_meeting_intents(session)
    users_df = pd.DataFrame(all_users)
    linkedin_df = pd.DataFrame(all_linkedin)
    intents_df = pd.DataFrame(all_intents)
    features_df = users_df.merge(linkedin_df, on="user_id", how="left")
    features_df = features_df.merge(intents_df, on="user_id", how="left")
    model = psclient.get_file(os.getenv("google_cloud_bucket"), os.getenv("model_path"), "model.m")
    model_settings = ModelSettings(
        model_type=ModelType.CATBOOST,
        model_path=model,
        filters=[],
        diversifications=[],
        exclude_users=[],
        exclude_companies=[],
    )
    matcher = Model(model_settings)
    matcher.load_model(model)
    predictions = matcher.predict(features_df, user_id)
    await queue_manager.put_to_queue(os.getenv("result_topic_id"), {"matches": predictions.user_id.tolist()[:n]})
    await session.close()
