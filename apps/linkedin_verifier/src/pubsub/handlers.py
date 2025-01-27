from loguru import logger
from google.cloud.pubsub_v1.subscriber.message import Message
from pydantic import ValidationError as PydanticError

from common_db.schemas.linkedin import LinkedInProfileTask

from src.linkedin.service import LinkedInService
from loader import broker
from src.exceptions import (
    ValidationError, ScrapinAPIError, DatabaseError,
    BadRequestError, CredentialsError, PaymentRequiredError,
    ForbiddenError, ProfileNotFoundError, RateLimitError,
    ServerError
)


async def handle_profile_task(message: Message) -> None:
    """
    Обработчик задач по парсингу профилей LinkedIn.
    Вызывается брокером при получении сообщения.
    """
    try:
        try:
            # Валидируем входящие данные через Pydantic
            task = LinkedInProfileTask.model_validate_json(message.data)
        except PydanticError as e:
            raise ValidationError(f"Invalid message format: {e}")

        # Парсим профиль через classmethod сервиса
        profile = await LinkedInService.validate_profile(
            username=task.username,
            target_company_label=task.target_company
        )

        logger.info(f"Successfully parsed profile {task.username}")

        # # Публикуем успешный результат
        # await broker.publish(
        #     "linkedin-results",
        #     {
        #         "username": task.username,
        #         "status": "success",
        #         "profile_id": profile.id
        #     }
        # )
        message.ack()

    except BadRequestError as e:
        # 400 - Неверные параметры запроса
        logger.error(f"Bad request error for {task.username}: {e}")
        await broker.publish(
            "linkedin-errors",
            {
                "username": task.username,
                "error": str(e),
                "type": "bad_request",
                "status_code": 400
            }
        )
        message.ack()  # Не повторяем - параметры не изменятся

    except CredentialsError as e:
        # 401 - Проблемы с API ключом
        logger.error(f"Authentication error: {e}")
        await broker.publish(
            "linkedin-errors",
            {
                "username": task.username,
                "error": str(e),
                "type": "credentials",
                "status_code": 401
            }
        )
        message.nack()  # Повторим, возможно ключ обновят

    except PaymentRequiredError as e:
        # 402 - Нет кредитов
        logger.error(f"No credits left: {e}")
        await broker.publish(
            "linkedin-errors",
            {
                "username": task.username,
                "error": str(e),
                "type": "payment_required",
                "status_code": 402
            }
        )
        message.nack()  # Повторим, когда пополнят кредиты

    except ForbiddenError as e:
        # 403 - Нет прав
        logger.error(f"Access forbidden: {e}")
        await broker.publish(
            "linkedin-errors",
            {
                "username": task.username,
                "error": str(e),
                "type": "forbidden",
                "status_code": 403
            }
        )
        message.nack()  # Повторим, возможно права обновят

    except ProfileNotFoundError as e:
        # 404 - Профиль не найден
        logger.warning(f"Profile not found: {task.username}")
        await broker.publish(
            "linkedin-results",
            {
                "username": task.username,
                "status": "not_found",
                "error": str(e),
                "status_code": 404
            }
        )
        message.ack()  # Не повторяем - профиль не появится

    except RateLimitError as e:
        # 429 - Превышен лимит запросов
        logger.warning(f"Rate limit exceeded for {task.username}: {e}")
        await broker.publish(
            "linkedin-errors",
            {
                "username": task.username,
                "error": str(e),
                "type": "rate_limit",
                "status_code": 429
            }
        )
        message.nack()  # Повторим позже, когда лимиты восстановятся

    except ServerError as e:
        # 500 - Ошибка сервера
        logger.error(f"Scrapin server error: {e}")
        await broker.publish(
            "linkedin-errors",
            {
                "username": task.username,
                "error": str(e),
                "type": "server_error",
                "status_code": 500
            }
        )
        message.nack()  # Повторим, возможно временная проблема

    except DatabaseError as e:
        # Ошибки нашей БД
        logger.error(f"Database error: {e}")
        await broker.publish(
            "linkedin-errors",
            {
                "username": task.username,
                "error": str(e),
                "type": "database_error"
            }
        )
        message.nack()  # Повторим, когда БД заработает

    except ValidationError as e:
        # Ошибки валидации данных
        logger.error(f"Validation error: {e}")
        await broker.publish(
            "linkedin-errors",
            {
                "username": getattr(task, 'username', None),
                "error": str(e),
                "type": "validation_error"
            }
        )
        message.ack()  # Не повторяем - данные не валидны

    except Exception as e:
        # Неожиданные ошибки
        logger.exception(f"Unexpected error: {e}")
        await broker.publish(
            "linkedin-errors",
            {
                "username": getattr(task, 'username', None),
                "error": str(e),
                "type": "unexpected_error"
            }
        )
        message.nack()  # Повторим на всякий случай
