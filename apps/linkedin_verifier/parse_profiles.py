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
    
    Поддерживает два формата:
    1. CSV с заголовком 'LinkedIn'
    2. Простой список URL-адресов LinkedIn (один столбец без заголовка)
    
    Args:
        csv_path: Путь к CSV файлу
        
    Returns:
        list[str]: Список LinkedIn URL/username'ов
        
    Raises:
        FileNotFoundError: Если файл не найден
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV файл не найден: {csv_path}")

    profiles = []
    skipped = 0

    try:
        # Сначала пробуем обработать как стандартный CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            try:
                reader = csv.DictReader(f)
                
                # Проверяем наличие нужной колонки
                if 'LinkedIn' in reader.fieldnames:
                    for row in reader:
                        linkedin_url = row['LinkedIn'].strip()
                        if linkedin_url:  # Пропускаем пустые значения
                            profiles.append(linkedin_url)
                        else:
                            skipped += 1
                    
                    logger.info(f"Загружено {len(profiles)} профилей из {csv_path.name} "
                                f"(пропущено пустых: {skipped})")
                    return profiles
                else:
                    # Если нет колонки 'LinkedIn', пробуем как простой список
                    raise ValueError(f"В файле {csv_path.name} отсутствует колонка 'LinkedIn'")
            
            except (ValueError, AttributeError):
                # Если не удалось обработать как CSV с заголовком 'LinkedIn',
                # пробуем как простой список
                f.seek(0)  # Возвращаемся в начало файла
                profiles = []
                skipped = 0
                
                for line in f:
                    linkedin_url = line.strip()
                    if linkedin_url:  # Пропускаем пустые строки
                        profiles.append(linkedin_url)
                    else:
                        skipped += 1
                
                logger.info(f"Загружено {len(profiles)} профилей из {csv_path.name} как простой список "
                            f"(пропущено пустых: {skipped})")
                return profiles

    except UnicodeDecodeError:
        logger.error(f"Ошибка кодировки файла {csv_path.name}. Попробуйте сохранить в UTF-8")
        raise
    except Exception as e:
        logger.error(f"Ошибка чтения файла {csv_path.name}: {e}")
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
        usernames = usernames[5:135]  # первые  701:702 700 уже ебанули из Олиного списка
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
    csv_path = Path(__file__).parent / "ml_in.csv"  # "Den1_pre.csv"
    test_profiles = read_linkedin_profiles_from_csv(csv_path)

    # Целевая компания для проверки
    target_company_label = "Yandex"

    # Запускаем парсинг
    asyncio.run(parse_linkedin_profiles(test_profiles, target_company_label))
