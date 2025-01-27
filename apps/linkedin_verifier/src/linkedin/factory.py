from config import settings
from src.linkedin.base import LinkedInRepository
from src.linkedin.providers.scrapin import LinkedInScrapinRepository
# from src.linkedin.providers.tomquirk import LinkedInTomquirkRepository
from src.db.models.limits import LinkedInProvider


class LinkedInRepositoryFactory:
    """Фабрика для создания репозиториев LinkedIn"""

    @staticmethod
    def create() -> type[LinkedInRepository]:
        """
        Создает репозиторий на основе настроек
        
        Returns:
            type[LinkedInRepository]: Класс конкретной реализации репозитория
        """
        providers = {
            LinkedInProvider.SCRAPIN: LinkedInScrapinRepository,
            # LinkedInProvider.TOMQUIRK: LinkedInTomquirkRepository
        }

        repository_class = providers.get(settings.current_provider)
        if not repository_class:
            raise ValueError(f"Unknown provider: {settings.current_provider}")

        return repository_class
