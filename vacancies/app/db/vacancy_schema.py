# Copyright 2024 Alumnihub

"""Database schema module."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Vacancy(Base):
    """Model of vacancy in database."""

    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True)

    # Временные метки
    first_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    time_reachable = Column(DateTime, nullable=True)
    last_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    needs_update = Column(Boolean, nullable=False, default=True)

    # Основная информация
    url = Column(String(255), nullable=False, index=True, unique=True)
    company = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)  # Хранится как JSON-строка
    required_experience = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)

    # Уровень и зарплата
    level = Column(String(255), nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(3), nullable=True)  # EUR, USD, RUB и т.д.

    # Дополнительная информация
    responsibilities = Column(Text, nullable=True)
    benefits = Column(Text, nullable=True)  # Плюшки
    remote_type = Column(Enum("office", "hybrid", "remote", name="work_format"), nullable=True)

    # Информация o компании
    department = Column(String(255), nullable=True)  # Отдел или бизнес-юнит

    def __repr__(self) -> str:
        """Return a string representation of the vacancy.

        Returns:
            str: A string representation of the vacancy.

        """
        return f"<Vacancy {self.title} at {self.company_name}>"
