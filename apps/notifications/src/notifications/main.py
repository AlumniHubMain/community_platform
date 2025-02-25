import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from loguru import logger

from notifications.config import settings
from notifications.loader import broker
from notifications.logic.incoming_message import message_handler
from notifications.utils.logging import setup_logger, setup_logging_middleware, setup_exception_handlers

# Setup logger
setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Subscribe to the topic on startup
    asyncio.create_task(broker.subscribe(settings.ps_notification_sub_name, message_handler))
    logger.info("Service started, message subscription activated")
    yield
    # Add cleanup code on shutdown
    logger.info("Service is shutting down")


app = FastAPI(title='Notification service', lifespan=lifespan)

# Setup logging middleware and exception handlers
setup_logging_middleware(app)
setup_exception_handlers(app)


@app.get("/health")
async def health_check():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "notifications",
            "version": "0.1.0"
        }
    )
