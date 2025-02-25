from loguru import logger

from common_db.schemas.linkedin import LinkedInProfileTask
from src.linkedin.service import LinkedInService
from loader import broker
from src.exceptions import BadRequestError, CredentialsError, PaymentRequiredError


async def handle_profile_task(task: LinkedInProfileTask) -> None:
    """
    Обработчик задач по парсингу профилей LinkedIn.
    Пробрасывает все ошибки наверх для обработки на уровне API.

    HTTP коды определяются в exceptions.py через status_code:
    - 400: BadRequestError, ValidationError -> не повторяем
    - 401: CredentialsError -> повторим, возможно ключ обновят
    - 402: PaymentRequiredError -> повторим, когда пополнят кредиты
    - 403: ForbiddenError -> повторим, возможно права обновят
    - 404: ProfileNotFoundError -> не повторяем
    - 429: RateLimitError -> повторим после таймаута
    - 500: ServerError, DatabaseError -> повторим позже
    """
    try:
        # Парсим профиль через LinkedIn API
        profile = await LinkedInService.validate_profile(
            username=task.username,
            target_company_label=task.target_company_label
        )

        logger.info(f"Successfully parsed profile {task.username}")

        # Публикуем успешный результат в очередь
        await broker.publish(
            "linkedin-results",
            {
                "username": task.username,
                "status": "success",
                "profile_id": profile.id
            }
        )

    except BadRequestError as e:
        logger.error(f"Bad request error for {task.username}: {e}")
        await broker.publish("linkedin-errors", {
            "username": task.username,
            "error": str(e),
            "type": "bad_request",
            "status_code": 400,
            "retry": False,
            "reason": "Неверные параметры запроса"
        })
        raise  # -> HTTP 400, не повторяем

    except CredentialsError as e:
        logger.error(f"Authentication error: {e}")
        await broker.publish("linkedin-errors", {
            "username": task.username,
            "error": str(e),
            "type": "credentials",
            "status_code": 401,
            "retry": True,
            "reason": "Проблемы с API ключом"
        })
        raise  # -> HTTP 401, повторим после обновления ключа

    except PaymentRequiredError as e:
        logger.error(f"No credits left: {e}")
        await broker.publish("linkedin-errors", {
            "username": task.username,
            "error": str(e),
            "type": "payment_required",
            "status_code": 402,
            "retry": True,
            "reason": "Закончились credits в API"
        })
        raise  # -> HTTP 402, повторим после пополнения

    except Exception as e:
        logger.exception(f"Unexpected error for {task.username}: {e}")
        await broker.publish("linkedin-errors", {
            "username": task.username,
            "error": str(e),
            "type": "unexpected_error",
            "status_code": 500,
            "retry": True,
            "reason": "Неожиданная ошибка"
        })
        raise  # -> HTTP 500, повторим позже
