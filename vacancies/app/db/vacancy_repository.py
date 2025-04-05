# Copyright 2024 Alumnihub
"""Vacancy repository module."""

import traceback
from datetime import UTC, datetime, timedelta

from picologging import Logger
from sqlalchemy import select

from app.core.data_extractor.extractor import VacancyStructure
from app.db import PostgresDB
from app.db.vacancy_schema import Vacancy


class VacancyRepository:
    """Репозиторий для работы c вакансиями в базе данных."""

    def __init__(self, db: PostgresDB, logger: Logger) -> None:
        """Инициализация репозитория.

        Args:
            db (PostgresDB): Объект подключения к базе данных

        """
        self._db = db
        self._logger = logger

    def add_or_update(self, url: str, company_name: str, vacancy_data: VacancyStructure) -> Vacancy:
        """Добавление новой вакансии в БД или обновление существующей.

        Args:
            url (str): URL вакансии
            company_name (str): Название компании
            vacancy_data (VacancyStructure): Данные вакансии

        Returns:
            Vacancy: Созданная или обновленная вакансия

        """
        with self._db.get_session() as session:
            try:
                # Проверяем существование вакансии
                stmt = select(Vacancy).where(Vacancy.url == url)
                existing_vacancy = session.execute(stmt).scalar_one_or_none()

                if existing_vacancy:
                    self._logger.info(
                        {
                            "message": "Updating existing vacancy",
                            "url": url,
                        },
                    )
                    # Обновляем существующую вакансию
                    update_data = vacancy_data.model_dump(exclude_unset=True)
                    for key, value in update_data.items():
                        if value is not None:
                            setattr(existing_vacancy, key, value)
                    existing_vacancy.company = company_name
                    existing_vacancy.last_timestamp = datetime.now(UTC)
                    vacancy = existing_vacancy
                else:
                    self._logger.info(
                        {
                            "message": "Creating new vacancy",
                            "url": url,
                        },
                    )
                    # Создаем новую вакансию
                    vacancy = Vacancy(**vacancy_data.model_dump())
                    vacancy.url = url
                    vacancy.company = company_name

                session.add(vacancy)
                session.commit()
                session.refresh(vacancy)
                return vacancy
            except Exception as e:
                self._logger.error(
                    {
                        "message": "Error while adding/updating vacancy",
                        "url": url,
                        "error": traceback.format_exc(),
                    },
                )
                session.rollback()
                raise e

    def get_by_url(self, url: str) -> Vacancy | None:
        """Получение вакансии по URL.

        Returns:
            Optional[Vacancy]: Найденная вакансия или None

        """
        with self._db.get_session() as session:
            try:
                stmt = select(Vacancy).where(Vacancy.url == url)
                result = session.execute(stmt)
                vacancy = result.scalar_one_or_none()
                if vacancy:
                    self._logger.debug("Found vacancy by URL", extra={"url": url})
                else:
                    self._logger.debug("Vacancy not found by URL", extra={"url": url})
                return vacancy
            except Exception as e:
                self._logger.error(
                    {
                        "message": "Error while getting vacancy by URL",
                        "url": url,
                        "error": traceback.format_exc(),
                    },
                )
                session.rollback()
                raise e

    def update_by_url(self, url: str, vacancy: Vacancy, vacancy_data: VacancyStructure) -> Vacancy | None:
        """Обновление вакансии по URL.

        Args:
            url (str): URL вакансии для обновления
            vacancy_data (VacancyStructure): Новые данные вакансии в виде Pydantic модели

        Returns:
            Optional[Vacancy]: Обновленная вакансия или None если вакансия не найдена

        Raises:
            ValueError: Если url или vacancy_data равны None
            SQLAlchemyError: При ошибке работы с базой данных
        """
        if not url or not vacancy_data:
            self._logger.error("Attempted to update vacancy with empty URL or data", extra={"url": url})
            raise ValueError("URL and vacancy data must not be None")

        with self._db.get_session() as session:
            try:
                self._logger.info("Updating vacancy", extra={"url": url})
                update_data = vacancy_data.model_dump(exclude_unset=True)
                for key, value in update_data.items():
                    if value:
                        setattr(vacancy, key, value)
                vacancy.last_timestamp = datetime.now(UTC)
                session.add(vacancy)
                session.commit()
                session.refresh(vacancy)
                return vacancy
            except Exception as e:
                self._logger.error("Error while updating vacancy", extra={"url": url, "error": traceback.format_exc()})
                session.rollback()
                raise e

    def exists_by_url(self, url: str) -> bool:
        """Проверка существования вакансии по URL.

        Args:
            url (str): URL вакансии

        Returns:
            bool: True если существует, False если нет

        """
        with self._db.get_session() as session:
            try:
                one_month_ago = datetime.now(UTC) - timedelta(days=30)
                stmt = select(1).where(Vacancy.url == url).where(Vacancy.last_timestamp > one_month_ago)
                result = session.execute(stmt)
                exists = result.scalar() is not None
                self._logger.debug(
                    {
                        "message": "Checking vacancy existence",
                        "url": url,
                        "exists": exists,
                    },
                )
                return exists
            except Exception as e:
                self._logger.error(
                    {
                        "message": "Error while checking vacancy existence",
                        "url": url,
                        "error": traceback.format_exc(),
                    },
                )
                session.rollback()
                raise e

    def update_time_reachable_by_url(self, url: str) -> Vacancy | None:
        """Обновление time_reachable вакансии по URL.

        Если c момента последней проверки прошло больше месяца,
        устанавливается флаг needs_update.

        Args:
            url (str): URL вакансии

        Returns:
            Optional[Vacancy]: Обновленная вакансия или None

        """
        with self._db.get_session() as session:
            try:
                stmt = select(Vacancy).where(Vacancy.url == url)
                result = session.execute(stmt)
                vacancy = result.scalar_one_or_none()

                if vacancy:
                    self._logger.info(
                        {
                            "message": "Updating time_reachable for vacancy",
                            "url": url,
                        },
                    )
                    vacancy.time_reachable = datetime.now(UTC)
                    session.add(vacancy)
                    session.commit()
                    session.refresh(vacancy)
                    return vacancy
                self._logger.warning(
                    {
                        "message": "Vacancy not found for updating time_reachable",
                        "url": url,
                    },
                )
                return None
            except Exception as e:
                self._logger.error(
                    {
                        "message": "Error while updating time_reachable for vacancy",
                        "url": url,
                        "error": traceback.format_exc(),
                    },
                )
                session.rollback()
                raise e
