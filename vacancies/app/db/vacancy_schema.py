# Copyright 2024 Alumnihub

"""Database schema module."""

from datetime import UTC, datetime

from sqlalchemy import ARRAY, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Vacancy(Base):
    """Model of vacancy in database."""

    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True)

    # Временные метки
    first_timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    time_reachable = Column(DateTime(timezone=True), nullable=True, default=lambda: datetime.now(UTC))
    last_timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    # Основная информация
    url = Column(String(255), nullable=False, index=True, unique=True)
    full_text = Column(Text, nullable=True)
    company = Column(String(255), nullable=True)

    # Информация о вакансии
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    skills = Column(ARRAY(Text), nullable=True)  # Хранится как JSON-строка
    required_experience = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    level = Column(String(255), nullable=True)
    salary = Column(String(255), nullable=True)

    # Информация о вакансии
    responsibilities = Column(ARRAY(Text), nullable=True)
    benefits = Column(ARRAY(Text), nullable=True)  # Плюшки
    additional_advantages = Column(ARRAY(Text), nullable=True)
    remote_type = Column(String(255), nullable=True)

    # Информация o компании
    department = Column(String(255), nullable=True)  # Отдел или бизнес-юнит

    def __repr__(self) -> str:
        """Return a string representation of the vacancy.

        Returns:
            str: A string representation of the vacancy.

        """
        return f"<Vacancy {self.title} at {self.company}>"
