import asyncio
from loguru import logger
from typing import List

from src.linkedin.service import LinkedInService
from config import settings
from common_db.schemas.linkedin import LinkedInProfileAPI


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
        
        # Парсим каждый профиль
        for username in usernames:
            try:
                logger.info(f"Parsing profile: {username}")
                profile = await LinkedInService.validate_profile(
                    username=username,
                    target_company_label=target_company_label,
                    use_mock=True
                )
                
                logger.info(
                    f"Successfully parsed {profile.linkedin_url} "
                    # f"(credits left: {profile.credits_left}, "
                    # f"rate limit: {profile.rate_limit_left})"
                )
                
            except Exception as e:
                logger.error(f"Error parsing profile {username}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Service initialization error: {e}")
        raise


if __name__ == "__main__":
    # Список профилей для парсинга
    test_profiles = [
        "anar-dadashov-6ba236169",
    ]
    
    # Целевая компания для проверки
    target_company_label = "Microsoft"
    
    # Запускаем парсинг
    asyncio.run(parse_linkedin_profiles(test_profiles, target_company_label))
    