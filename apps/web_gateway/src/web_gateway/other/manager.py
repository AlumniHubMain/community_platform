"""
Manager for working with community companies and their services.
"""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.db_abstract import db_manager

from vacancies.app.db.vacancy_schema import Vacancy as ORMVacancy

# Настройка логгера для модуля
logger = logging.getLogger(__name__)


class VacancyManager:
    """Manager for working with community companies and their services"""

    @classmethod
    async def get_by_url(cls, url: str, session: AsyncSession = db_manager.get_session()) -> ORMVacancy | None:
        """Получение вакансии по URL.

        Args:
            url: URL вакансии
            session: Сессия базы данных

        Returns:
            Optional[Vacancy]: Найденная вакансия или None
        """
        try:
            logger.info("Getting vacancy by URL", extra={"url": url})
            stmt = select(ORMVacancy).where(ORMVacancy.url == url)
            result = await session.execute(stmt)
            vacancy = result.scalar_one_or_none()
            
            if vacancy:
                logger.info("Found vacancy by URL", extra={"url": url})
            else:
                logger.warning("Vacancy not found by URL", extra={"url": url})
                
            return vacancy
            
        except Exception as e:
            logger.error("Error while getting vacancy by URL", extra={"url": url, "error": str(e)})
            raise
