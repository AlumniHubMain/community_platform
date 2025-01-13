# Copyright 2024 Alumnihub
"""Vacancy repository module."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.vacancy_schema import Vacancy


class VacancyRepository:
    """Репозиторий для работы c вакансиями в базе данных."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория.

        Args:
            session (AsyncSession): Сессия SQLAlchemy

        """
        self._session = session

    async def add(self, vacancy_data: dict) -> Vacancy:
        """Добавление новой вакансии в БД.

        Args:
            vacancy_data (dict): Данные вакансии

        Returns:
            Vacancy: Созданная вакансия

        """
        try:
            vacancy = Vacancy(**vacancy_data)
            self._session.add(vacancy)
            await self._session.commit()
        except Exception as e:
            await self._session.rollback()
            raise e from e
        else:
            await self._session.refresh(vacancy)
            return vacancy

    async def get_by_id(self, vacancy_id: int) -> Vacancy | None:
        """Получение вакансии по ID.

        Args:
            vacancy_id (int): ID вакансии

        Returns:
            Optional[Vacancy]: Найденная вакансия или None

        """
        try:
            result = await self._session.execute(
                select(Vacancy).where(Vacancy.id == vacancy_id),
            )
            return result.scalar_one_or_none()
        except Exception as e:
            await self._session.rollback()
            raise e from e

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
        filters: dict | None = None,
    ) -> list[Vacancy]:
        """Получение списка вакансий c применением фильтров.

        Args:
            offset (int): Смещение
            limit (int): Лимит записей
            filters (Optional[dict]): Словарь c фильтрами

        Returns:
            List[Vacancy]: Список вакансий

        """
        try:
            query = select(Vacancy)

            if filters:
                if filters.get("level"):
                    query = query.where(Vacancy.level == filters["level"])
                if filters.get("location"):
                    query = query.where(Vacancy.location.ilike(f"%{filters['location']}%"))
                if filters.get("remote_type"):
                    query = query.where(Vacancy.remote_type == filters["remote_type"])
                if filters.get("salary_min"):
                    query = query.where(
                        or_(
                            Vacancy.salary_min >= filters["salary_min"],
                            Vacancy.salary_max >= filters["salary_min"],
                        ),
                    )
                if filters.get("company_name"):
                    query = query.where(Vacancy.company_name.ilike(f"%{filters['company_name']}%"))

            query = query.offset(offset).limit(limit)
            result = await self._session.execute(query)
            return result.scalars().all()
        except Exception as e:
            await self._session.rollback()
            raise e from e

    async def update(self, vacancy_id: int, vacancy_data: dict) -> Vacancy | None:
        """Обновление вакансии.

        Args:
            vacancy_id (int): ID вакансии
            vacancy_data (dict): Данные для обновления

        Returns:
            Optional[Vacancy]: Обновленная вакансия или None

        """
        vacancy = await self.get_by_id(vacancy_id)
        if vacancy:
            for key, value in vacancy_data.items():
                setattr(vacancy, key, value)
            vacancy.last_timestamp = datetime.now(UTC)
            await self._session.commit()
            await self._session.refresh(vacancy)
        return vacancy

    async def delete(self, vacancy_id: int) -> bool:
        """Удаление вакансии.

        Args:
            vacancy_id (int): ID вакансии

        Returns:
            bool: True если удалено, False если не найдено

        """
        vacancy = await self.get_by_id(vacancy_id)
        if vacancy:
            await self._session.delete(vacancy)
            await self._session.commit()
            return True
        return False

    async def search(
        self,
        search_term: str,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Vacancy]:
        """Поиск вакансий по ключевым словам.

        Args:
            search_term (str): Поисковый запрос
            offset (int): Смещение
            limit (int): Лимит записей

        Returns:
            List[Vacancy]: Список найденных вакансий

        """
        query = (
            select(Vacancy)
            .where(
                or_(
                    Vacancy.title.ilike(f"%{search_term}%"),
                    Vacancy.description.ilike(f"%{search_term}%"),
                    Vacancy.skills.ilike(f"%{search_term}%"),
                    Vacancy.company_name.ilike(f"%{search_term}%"),
                ),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self._session.execute(query)
        return result.scalars().all()

    async def exists(self, vacancy_id: int) -> bool:
        """Проверка существования вакансии.

        Args:
            vacancy_id (int): ID вакансии

        Returns:
            bool: True если существует, False если нет

        """
        query = select(1).where(Vacancy.id == vacancy_id).exists()
        result = await self._session.execute(select(query))
        return result.scalar()

    async def get_by_url(self, url: str) -> Vacancy | None:
        """Получение вакансии по URL.

        Args:
            url (str): URL вакансии

        Returns:
            Optional[Vacancy]: Найденная вакансия или None

        """
        query = select(Vacancy).where(Vacancy.url == url)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def update_by_url(self, url: str, vacancy_data: dict) -> Vacancy | None:
        """Обновление вакансии по URL.

        Args:
            url (str): URL вакансии
            vacancy_data (dict): Данные для обновления

        Returns:
            Optional[Vacancy]: Обновленная вакансия или None

        """
        vacancy = await self.get_by_url(url)
        if vacancy:
            for key, value in vacancy_data.items():
                setattr(vacancy, key, value)
            vacancy.last_timestamp = datetime.now(UTC)
            await self._session.commit()
            await self._session.refresh(vacancy)
        return vacancy

    async def exists_by_url(self, url: str) -> bool:
        """Проверка существования вакансии по URL.

        Args:
            url (str): URL вакансии

        Returns:
            bool: True если существует, False если нет

        """
        query = select(1).where(Vacancy.url == url).exists()
        result = await self._session.execute(select(query))
        return result.scalar()

    async def update_time_reachable_by_url(self, url: str, vacancy_data: dict) -> Vacancy | None:
        """Обновление time_reachable вакансии по URL.

        Если c момента последней проверки прошло больше месяца,
        устанавливается флаг needs_update.

        Args:
            url (str): URL вакансии
            vacancy_data (dict): Данные для обновления

        Returns:
            Optional[Vacancy]: Обновленная вакансия или None

        """
        vacancy = await self.get_by_url(url)
        if vacancy:
            # Обновляем time_reachable из входных данных
            for key, value in vacancy_data.items():
                setattr(vacancy, key, value)

            # Проверяем, прошел ли месяц c момента последней проверки
            one_month_ago = datetime.now(UTC) - timedelta(days=30)
            if vacancy.time_reachable <= one_month_ago:
                vacancy.needs_update = True

            # Обновляем last_seen на текущее время
            vacancy.last_seen = datetime.now(UTC)

            await self._session.commit()
            await self._session.refresh(vacancy)
            return vacancy
        return None
