"""Основной модуль приложения для верификации LinkedIn профилей"""

import base64
import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from src.pubsub.handlers import handle_profile_task
from src.linkedin.helpers import validate_linkedin_username
from common_db.schemas.linkedin import LinkedInProfileTask
from loader import broker
from config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# CORS settings
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
CORS_ORIGINS = [
    BASE_URL,
    "http://localhost:5173",  # для локальной разработки
    "http://localhost:8080",  # для Swagger UI
]


@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=unused-argument
    yield


app = FastAPI(title="LinkedIn Profile Validator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint для Cloud Run"""
    return {"status": "ok"}


@app.post("/pubsub/push")
async def pubsub_push(request: Request) -> dict[str, str]:
    """
    Обработчик push-сообщений от Pub/Sub для верификации LinkedIn профилей.

    Flow:
    1. Декодирует base64 данные из сообщения
    2. Валидирует через LinkedInProfileTask (username, target_company)
    3. Передает задачу в handler для проверки профиля через Scrapin.io API
    4. Результаты публикуются в очереди:
       - linkedin-results: успешные проверки
       - linkedin-errors: ошибки обработки

    Returns:
        HTTP 200 - сообщение обработано успешно (ack):
            - профиль успешно проверен
            - результат опубликован в linkedin-results

        HTTP 4xx - клиентская ошибка (nack без повтора):
            - 400: невалидное сообщение, неверные параметры
            - 404: профиль не найден
            Pub/Sub прекратит доставку - ошибки неисправимые

        HTTP 5xx - серверная ошибка (nack с повтором):
            - 401: проблемы с API ключом
            - 402: нет credits в API
            - 403: нет прав доступа
            - 429: rate limit API (>500 req/min)
            - 500: ошибка сервера
            Pub/Sub повторит доставку - ошибки временные

    Args:
        request: Сообщение от Pub/Sub:
            message.data: base64-encoded JSON с параметрами задачи
            message.message_id: ID сообщения
            subscription: имя подписки

    Raises:
        HTTPException:
            - 4xx для клиентских ошибок (без повтора)
            - 5xx для серверных ошибок (с повтором)
    """
    try:
        logger.info("--> Staring process task", request)
        envelope = await request.json()
        message = envelope.get("message")
        logger.info("Processing profile for user: %s", message)
        if not message.get("data"):
            raise HTTPException(status_code=400, detail="No data in message")
        try:
            decoded_data = base64.b64decode(message["data"]).decode("utf-8")
            data = json.loads(decoded_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid message format: {str(e)}") from e


        task = LinkedInProfileTask.model_validate(data)
        # task = LinkedInProfileTask.model_validate(message)

        logger.info("Processing profile for user: %s", task.username)
        await handle_profile_task(task)

        return {"status": "ok"}  # 200 = ack

    except (ValueError, json.JSONDecodeError) as e:
        logger.error("Error processing message: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))  # nack без повтора

    except Exception as e:
        logger.error("Error processing message: %s", str(e))
        raise HTTPException(status_code=500, detail="Processing failed")  # nack с повтором


@app.post("/tasks/create", response_model=dict[str, str])
async def create_task(task: LinkedInProfileTask) -> dict[str, str]:
    """
    Создает задание на проверку LinkedIn профиля через Pub/Sub.

    Args:
        task: Параметры задания:
            username: LinkedIn username для проверки (можно и в "грязном" виде, есть предвалидатор -
            TODO: решить, где его использовать: на этапе создания задания или на этапе парсинга.
             Пока что в обоих местах.
            target_company_label: название компании для проверки

    Returns:
        HTTP 200: Задание успешно создано и опубликовано
        HTTP 400: Неверные параметры запроса
        HTTP 500: Ошибка при публикации в Pub/Sub

    Example:
        {
            "username": "pavellukyanov",
            "target_company_label": "Yandex"
        }
    """
    try:
        logger.info("Start processing create pubsub-task for user: %s", task.username)
        # data = await request.json()
        task = LinkedInProfileTask.model_validate(task)
        task.username = await validate_linkedin_username(task.username)

        # Публикуем в Pub/Sub через наш брокер
        await broker.publish(
            settings.pubsub_linkedin_tasks_topic,  # Топик для заданий
            task
        )

        logger.info("End processing (success) create pubsub-task for user: %s", task.username)
        return {
            "status": "ok",
            "message": f"Pubsub-task created for profile: {task.username}, "
                       f"topic: {settings.pubsub_linkedin_tasks_topic}"
        }

    except Exception as e:
        logger.error(f"Error creating pubsub-task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create pubsub-task: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


# Старая версия с pull подпиской:
"""
from loguru import logger
import asyncio

from config import settings
from src.pubsub.handlers import handle_profile_task
from loader import broker


async def main():
    try:
        logger.info("Starting LinkedIn profile validator...")

        # Создаем задачу для подписки на PubSub
        subscription_task = asyncio.create_task(
            broker.subscribe(
                settings.pubsub_linkedin_tasks_sub,
                handle_profile_task
            )
        )

        logger.info("Started listening for LinkedIn profile tasks")

        # Держим приложение активным
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        raise
    finally:
        logger.info("Shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
"""
