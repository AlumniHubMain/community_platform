"""
Manager for working with community companies and their services.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.db_abstract import db_manager

from vacancies.app.data_extractor.structure_vacancy import VacancyStructure as DTOVacancy
from vacancies.app.db.vacancy_schema import Vacancy as ORMVacancy


class VacancyManager:
    """Manager for working with community companies and their services"""

        @classmethod
        async def get_by_url(cls, url: str, session: AsyncSession = db_manager.get_session()) -> ORMVacancy | None:
            """Получение вакансии по URL.

            Returns:
                Optional[Vacancy]: Найденная вакансия или None

            """
            try:
                stmt = select(ORMVacancy).where(ORMVacancy.url == url)
                result = await session.execute(stmt)
                vacancy = result.scalar_one_or_none()
                if vacancy:
                    self._logger.debug("Found vacancy by URL", url=url)
                else:
                    self._logger.debug("Vacancy not found by URL", url=url)
                return vacancy
            except Exception as e:
                self._logger.error("Error while getting vacancy by URL", url=url, error=e)
