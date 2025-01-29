import asyncio
from loguru import logger
from typing import List

from src.linkedin.service import LinkedInService
from src.linkedin.helpers import validate_linkedin_username, InvalidLinkedInUsernameError
from config import settings


async def parse_linkedin_profiles(usernames: List[str], target_company_label: str):
    """
    Парсинг списка LinkedIn профилей
    
    Args:
        usernames: Список username'ов для парсинга
        target_company_label: Название компании для проверки
        
    Returns:
        None
    """
    try:
        logger.info(f"Starting parsing {len(usernames)} profiles using {settings.linkedin_provider} provider")
        
        # Создаем корутины для каждого профиля
        tasks = []
        for raw_username in usernames:
            try:
                username = validate_linkedin_username(raw_username)
                tasks.append(LinkedInService.validate_profile(
                    username=username,
                    target_company_label=target_company_label,
                    use_mock=True
                ))
            except InvalidLinkedInUsernameError as e:
                logger.error(f"Неверный LinkedIn username/URL '{raw_username}': {e}")
                continue
        
        # Обрабатываем профили асинхронно
        for task in asyncio.as_completed(tasks):
            try:
                profile = await task
                logger.info(
                    f"Successfully parsed {profile.linkedin_url} "
                    f"(credits left: {profile.credits_left}, "
                    f"rate limit: {profile.rate_limit_left})"
                )
            except Exception as e:
                logger.error(f"Error processing profile: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Service initialization error: {e}")
        raise


if __name__ == "__main__":
    # Список профилей для парсинга
    test_profiles = [
        "anar-dadashov-6ba236169",  # Чистый username
        "https://www.linkedin.com/in/maxmax1/",  # URL с завершающим слешем
        "https://www.linkedin.com/in/dmknstv",  # URL без завершающего слеша
        "https://www.linkedin.com/mwlite/in/igor-oleynick",  # Мобильный URL
        "https://ae.linkedin.com/in/andreiryan",  # Региональный домен
        "https://www.linkedin.com/in/maxim-zagrebin?utm_source=share",  # URL с параметрами
        # "linked.in/dimatverd",  # Короткий домен
        "drveles",  # Чистый username
        "alex-kozinov",  # Чистый username
        "https://www.linkedin.com/feed/",  # Неверный - нет username
        "http://linkedin.com",  # Неверный - нет username
        "Sionyx.ru",  # Неверный - неправильный домен
    ]
    
    # Целевая компания для проверки
    target_company_label = "Yandex"
    
    # Запускаем парсинг
    asyncio.run(parse_linkedin_profiles(test_profiles, target_company_label))
    