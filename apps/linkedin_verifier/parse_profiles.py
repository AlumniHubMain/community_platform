import asyncio
from loguru import logger
import csv
from pathlib import Path

from src.linkedin.service import LinkedInService
from src.linkedin.helpers import validate_linkedin_username, InvalidLinkedInUsernameError
from config import settings


def read_linkedin_profiles_from_csv(csv_path: str | Path) -> list[str]:
    """
    Читает LinkedIn профили из CSV файла.
    
    Args:
        csv_path: Путь к CSV файлу
        
    Returns:
        list[str]: Список LinkedIn URL/username'ов
        
    Raises:
        FileNotFoundError: Если файл не найден
        ValueError: Если в файле нет колонки 'LinkedIn'
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV файл не найден: {csv_path}")

    profiles = []
    skipped = 0

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Проверяем наличие нужной колонки
            if 'LinkedIn' not in reader.fieldnames:
                raise ValueError(f"В файле {csv_path.name} отсутствует колонка 'LinkedIn'")

            for row in reader:
                linkedin_url = row['LinkedIn'].strip()
                if linkedin_url:  # Пропускаем пустые значения
                    profiles.append(linkedin_url)
                else:
                    skipped += 1

        logger.info(f"Загружено {len(profiles)} профилей из {csv_path.name} "
                    f"(пропущено пустых: {skipped})")
        return profiles

    except UnicodeDecodeError:
        logger.error(f"Ошибка кодировки файла {csv_path.name}. Попробуйте сохранить в UTF-8")
        raise
    except Exception as e:
        logger.error(f"Ошибка чтения CSV файла {csv_path.name}: {e}")
        raise


async def parse_linkedin_profiles(usernames: list[str], target_company_label: str):
    """
    Парсинг списка LinkedIn профилей
    
    Args:
        usernames: Список username'ов для парсинга
        target_company_label: Название компании для проверки
        
    Returns:
        None
    """
    try:
        # Ограничиваем список первыми 50 профилями
        usernames = usernames[701:702]  # первые 700 уже ебанули из Олиного списка
        logger.info(f"Starting parsing {len(usernames)} profiles using {settings.linkedin_provider} provider")

        # Создаем семафор для ограничения одновременных подключений к БД
        # Оставляем запас для других операций
        semaphore = asyncio.Semaphore(3)

        async def process_profile(raw_username: str):
            async with semaphore:  # Ограничиваем количество одновременных операций
                try:
                    username = await validate_linkedin_username(raw_username)
                    return await LinkedInService.validate_profile(
                        username=username,
                        target_company_label=target_company_label,
                        # use_mock=True
                    )
                except InvalidLinkedInUsernameError as e:
                    logger.error(f"Неверный LinkedIn username/URL '{raw_username}': {e}")
                    return None
                except Exception as e:
                    logger.error(f"Error processing profile '{raw_username}': {e}")
                    return None

        # Создаем задачи для каждого профиля
        tasks = [process_profile(raw_username) for raw_username in usernames]

        # Обрабатываем профили асинхронно
        for profile in await asyncio.gather(*tasks):
            if profile:
                logger.info(
                    f"Successfully parsed {profile.linkedin_url} "
                    f"(credits left: {profile.credits_left}, "
                    f"rate limit: {profile.rate_limit_left})"
                )

    except Exception as e:
        logger.error(f"Service initialization error: {e}")
        raise


if __name__ == "__main__":
    # Читаем профили из CSV
    csv_path = Path(__file__).parent / "community_profiles_from_Olya.csv"  # "Den1_pre.csv"
    test_profiles = read_linkedin_profiles_from_csv(csv_path)

    # Целевая компания для проверки
    target_company_label = "Yandex"

    # Запускаем парсинг
    asyncio.run(parse_linkedin_profiles(test_profiles, target_company_label))
