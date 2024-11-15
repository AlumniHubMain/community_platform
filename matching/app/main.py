"""Основной модуль приложения"""
import os
from typing import Annotated
from contextlib import asynccontextmanager

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


@asynccontextmanager
async def lifespan(app: FastAPI): # pylint: disable=unused-argument,redefined-outer-name
    """Lifecycle func"""
    global psclient, queue_manager # pylint: disable=global-statement
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

@app.get('/get_matches/{user_id}/{meeting_intent_id}')
async def get_matches(
    user_id: int, meeting_intent_id: int, session: Annotated[AsyncSession, Depends(get_async_session)]
):
    """Get matches for user and send result to topic"""
    config.logger.info(
        "Recieved matching request user_id: %d, meeting_intent_id: %d", user_id, meeting_intent_id,
    )
    user_info = await DataLoader.get_user_profile(session, user_id)
    linkedin_info = await DataLoader.get_linkedin_profile(session, user_id)
    intent_info = await DataLoader.get_meeting_intent(session, meeting_intent_id)
    model = psclient.get_file(os.getenv('google_cloud_bucket'), os.getenv('model_path'), 'model.m')

    await queue_manager.put_to_queue(os.getenv('result_topic_id'), {'matches': []})
    await session.close()
