"""Основной модуль приложения для верификации LinkedIn профилей"""

import base64
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.pubsub.handlers import handle_profile_task
from src.linkedin.helpers import validate_linkedin_username
from common_db.schemas.linkedin import LinkedInProfileTask
from loader import broker
from config import settings

# Настройка логгера для Cloud Run
logger = logging.getLogger("linkedin_verifier")
logger.setLevel(logging.INFO)

# Добавляем обработчик для вывода в stdout
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

# Создаем форматтер для логов
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Добавляем обработчик к логгеру
logger.addHandler(handler)

# CORS settings
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
CORS_ORIGINS = [
    BASE_URL,
    "http://localhost:5173",  # для локальной разработки
    "http://localhost:8080",  # для Swagger UI
]


@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=unused-argument
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")


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
    logger.info("Health check requested")
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
        logger.info("Received pubsub push request")
        envelope = await request.json()
        message = envelope.get("message")
        logger.info(f"Processing message: {message}")
        
        if not message.get("data"):
            logger.error("No data in message")
            raise HTTPException(status_code=400, detail="No data in message")
        
        try:
            decoded_data = base64.b64decode(message["data"]).decode("utf-8")
            data = json.loads(decoded_data)
            logger.info(f"Decoded data: {data}")
        except Exception as e:
            logger.error(f"Invalid message format: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid message format: {str(e)}") from e

        task = LinkedInProfileTask.model_validate(data)
        logger.info(f"Processing profile for user: {task.username}")
        
        await handle_profile_task(task)
        logger.info(f"Successfully processed task for user: {task.username}")

        return {"status": "ok"}  # 200 = ack

    except (ValueError, json.JSONDecodeError) as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))  # nack без повтора

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail="Processing failed")  # nack с повтором


# Определим модель ответа для большей ясности
class TasksCreateResponse(BaseModel):
    status: str
    successful: List[str]
    failed: Dict[str, str]
    message: str

@app.post("/tasks/create", response_model=TasksCreateResponse)
async def create_tasks(tasks: List[LinkedInProfileTask] = Body(...)) -> TasksCreateResponse:
    """
    Создает задания на проверку LinkedIn профилей через Pub/Sub.

    Args:
        tasks: Список параметров заданий:
            username: LinkedIn username для проверки
            target_company_label: название компании для проверки

    Returns:
        HTTP 200: Информация о созданных заданиях
            status: Статус операции
            successful: Список успешно созданных заданий (usernames)
            failed: Словарь неудачных заданий с причинами ошибок
            message: Общее сообщение о результате

    Example:
        [
            {
                "username": "pavellukyanov",
                "target_company_label": "Yandex"
            },
            {
                "username": "johndoe",
                "target_company_label": "Google"
            }
        ]
    """
    successful = []
    failed = {}
    
    logger.info(f"Start: processing batch of {len(tasks)} pubsub-tasks")
    
    for task in tasks:
        try:
            # Валидация и нормализация username
            try:
                username = await validate_linkedin_username(task.username)
                task.username = username
            except Exception as e:
                failed[task.username] = f"Invalid username: {str(e)}"
                continue
                
            # Публикуем в Pub/Sub через наш брокер
            await broker.publish(
                settings.pubsub_linkedin_tasks_topic,  # Топик для заданий
                task
            )
            
            successful.append(task.username)
            logger.info(f"Published task for user: {task.username} to topic: {settings.pubsub_linkedin_tasks_topic}")
            
        except Exception as e:
            error_msg = f"Failed to create task: {str(e)}"
            failed[task.username] = error_msg
            logger.error(f"Error creating pubsub-task for {task.username}: {e}")
    
    # Формируем итоговое сообщение
    total = len(tasks)
    success_count = len(successful)
    fail_count = len(failed)
    
    message = f"Processed {total} tasks: {success_count} successful, {fail_count} failed"
    logger.info(f"End: {message}")
    
    # Определяем общий статус операции
    status = "ok" if success_count > 0 else "error"
    
    # Если все задания завершились с ошибкой, возвращаем 500
    if status == "error":
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "successful": successful,
                "failed": failed,
                "message": message
            }
        )
    
    # Возвращаем результат
    return TasksCreateResponse(
        status=status,
        successful=successful,
        failed=failed,
        message=message
    )


if __name__ == "__main__":
    import uvicorn

    # Настройка логирования uvicorn
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        log_config=log_config
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
