from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger
import asyncio
import os

from src.api.v1.api import api_router
from config import settings
from src.linkedin.service import LinkedInService
from src.pubsub.handlers import handle_profile_task
from loader import broker


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Создаем LinkedIn сервис с готовым broker
        # linkedin_service = LinkedInService(broker=broker)

        # Запускаем подписку на задания
        await broker.subscribe("my-topic-sub", handle_profile_task)

        logger.info("Application startup complete")
        yield

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))  # Default to 8000 if not set
    logger.info(f"Starting FastAPI application on port {port}")
    uvicorn.run(app, host='0.0.0.0', port=port)


    # Example:
    # broker = BrokerFactory.create_broker(BrokerType.GOOGLE_PUBSUB,
    #                                      project_id="my-project",
    #                                      credentials=settings.ps_credentials)
    # await broker.subscribe("my-topic-sub", message_handler)
    # await broker.publish("my-topic", message)

    # asyncio.create_task(broker.subscribe(settings.ps_notification_tg_sub_name, message_handler))
