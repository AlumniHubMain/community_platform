"""
Validators for LinkedIn data.
"""

class LinkedInValidationError(Exception):
    """Базовое исключение для ошибок валидации LinkedIn."""


class InvalidLinkedInUsernameError(LinkedInValidationError):
    """Ошибка валидации username LinkedIn."""


async def validate_linkedin_username(raw_input: str | None) -> str:
    """
    Т.к. данные в базе профилей Сообществ грязные, то нужно их почистить перед использованием.
    Извлекает username из LinkedIn URL или возвращает сам username.

    Примеры валидных входных данных:
        - drveles -> drveles (чистый username)
        - alex-kozinov -> alex-kozinov (чистый username)
        - https://www.linkedin.com/in/maxmax1/ -> maxmax1
        - https://www.linkedin.com/in/dmknstv -> dmknstv
        - https://www.linkedin.com/in/maxim-zagrebin?utm_source=share -> maxim-zagrebin
        - https://www.linkedin.com/in/julie-rustamyan-259a14b4/,https://twitter.com/julie -> julie-rustamyan-259a14b4
        - https://facebook.com/julie,https://www.linkedin.com/in/julie-rustamyan-259a14b4/ -> julie-rustamyan-259a14b4

    Пограничные случаи:
        - https://www.linkedin.com/in/ -> InvalidLinkedInUsernameError
        - None -> InvalidLinkedInUsernameError
        - '' -> InvalidLinkedInUsernameError
        - 'test.com' -> InvalidLinkedInUsernameError (содержит точку)
        - 'test,com' -> InvalidLinkedInUsernameError (содержит запятую)
        - 'test;com' -> InvalidLinkedInUsernameError (содержит точку с запятой)
        - 'test?com' -> InvalidLinkedInUsernameError (содержит вопрос)
    """
    if not raw_input:
        raise InvalidLinkedInUsernameError("Username не может быть пустым")

    # Очищаем вход
    cleaned = raw_input.strip().lower()
    if not cleaned:
        raise InvalidLinkedInUsernameError("Username не может быть пустым")

    # Проверяем на чистый username - не должен содержать спецсимволов
    special_chars = ['.', ',', ';', '?']
    if not any(char in cleaned for char in special_chars):
        return cleaned

    # Ищем LinkedIn URL
    if 'linkedin' not in cleaned:
        raise InvalidLinkedInUsernameError(f"Не найден URL LinkedIn: {raw_input}")

    # Если есть несколько URL, берем первый с LinkedIn
    if ',' in cleaned:
        urls = [url.strip() for url in cleaned.split(',')]
        linkedin_urls = [url for url in urls if 'linkedin' in url]
        if not linkedin_urls:
            raise InvalidLinkedInUsernameError(f"Не найден URL LinkedIn: {raw_input}")
        cleaned = linkedin_urls[0]

    # Извлекаем username из URL
    if '/in/' not in cleaned:
        raise InvalidLinkedInUsernameError(f"Неверный формат URL: {raw_input}")

    username = cleaned.split('/in/')[1].split('?')[0].split('/')[0]
    if not username:
        raise InvalidLinkedInUsernameError("Username не может быть пустым")

    return username
