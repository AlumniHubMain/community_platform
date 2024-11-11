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


@asynccontextmanager
async def lifespan(app: FastAPI): # pylint: disable=unused-argument,redefined-outer-name
    """Lifecycle func"""
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

@app.get('/get_matches/{user_id}/{match_query_id}')
async def get_matches(
    user_id: int, match_query_id: int, session: Annotated[AsyncSession, Depends(get_async_session)]
):
    """Get matches for user and send result to topic"""
    config.logger.info(
        "Recieved matching request user_id: %d, match_query_id: %d", user_id, match_query_id,
    )
    await session.close()
