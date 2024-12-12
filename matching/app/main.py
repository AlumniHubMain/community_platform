"""Основной модуль приложения"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import config

print(os.environ)
from db_common.config import DatabaseSettings
from db_common.db import DatabaseManager
from app.data_loader import DataLoader
from app.services import psclient, queue_manager
from app.model import ModelType, Model, model_settings_presets
from app.transport import CloudStorageAdapter, GoogleQueueManager, PSClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    global queue_manager
    global ps_client
    global config
    queue_manager = GoogleQueueManager()
    await queue_manager.initialize(config.project_id)
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


@app.get("/get_matches/{user_id}/{meeting_intent_id}/{model_settings_preset}/{n}")
async def get_matches(
    user_id: int,
    meeting_intent_id: int,
    model_settings_preset: str = "heuristic",
    n: int = 10,
):
    """Get matches for user and send result to topic"""
    config.logger.info(
        "Recieved matching request user_id: %d, meeting_intent_id: %d, model_settings_preset: %s, n: %d",
        user_id,
        meeting_intent_id,
        model_settings_preset,
        n,
    )
    async with db.session() as session:
        all_users = await DataLoader.get_all_user_profiles(session)
        all_linkedin = await DataLoader.get_all_linkedin_profiles(session)
        intent = await DataLoader.get_meeting_intent(session, meeting_intent_id)
        model_settings = model_settings_presets[model_settings_preset]
        model = None
        if model_settings.model_type == ModelType.CATBOOST:
            model = psclient.get_file(model_settings.model_path)
        matcher = Model(model_settings)
        matcher.load_model(model)
        predictions = matcher.predict(all_users, all_linkedin, intent, user_id, n)
        await queue_manager.put_to_queue(config.result_topic_id, {"matches": predictions})
        config.logger.info(
            "Matches sent to topic for user_id: %d, meeting_intent_id: %d, model_settings_preset: %s, n: %d",
            user_id,
            meeting_intent_id,
            model_settings_preset,
            n,
        )
        await session.close()
