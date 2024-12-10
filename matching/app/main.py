"""Основной модуль приложения"""

import os
import pandas as pd
from fastapi import (
    FastAPI,
)
from fastapi.middleware.cors import CORSMiddleware
from db_common.config import DatabaseSettings
from db_common.db import DatabaseManager
from app.config import config
from app.data_loader import DataLoader
from app.services import psclient, queue_manager
from app.model import ModelSettings, ModelType, Model


settings = DatabaseSettings(service_name="matching")
db = DatabaseManager(settings)

app = FastAPI(title="Community platform matching service")

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
    n: int = 10,
):
    """Get matches for user and send result to topic"""
    config.logger.info(
        "Recieved matching request user_id: %d, meeting_intent_id: %d",
        user_id,
        meeting_intent_id,
    )
    async with db.session() as session:
        all_users = await DataLoader.get_all_user_profiles(session)
        all_linkedin = await DataLoader.get_all_linkedin_profiles(session)
        intent = await DataLoader.get_meeting_intent(session, meeting_intent_id)
        users_df = pd.DataFrame(all_users)
        linkedin_df = pd.DataFrame(all_linkedin)
        intents_df = pd.DataFrame(intent)
        features_df = users_df.merge(linkedin_df, on="user_id", how="left")
        features_df = features_df.merge(intents_df, on="user_id", how="left")
        model = psclient.get_file(os.getenv("google_cloud_bucket"), os.getenv("model_path"), "model.m")
        model_settings = ModelSettings(
            model_type=ModelType.HEURISTIC,
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
