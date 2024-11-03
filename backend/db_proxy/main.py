from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging

import os

from users.router import router as users_router
from media_storage.router import router as mds_router

import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Service started")
    yield


app = FastAPI(title='Community platform', lifespan=lifespan)

# ToDo(evseev.dmsr) уточнить, что тут нужно
origins = [
    "http://localhost:5173",
    "https://platform-web-flax.vercel.app",
    "https://platform-web-flax.vercel.app:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(mds_router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Default to 8000 if not set
    logger.info(f"Starting FastAPI application on port {port}")
    uvicorn.run(app, host='0.0.0.0', port=port)
