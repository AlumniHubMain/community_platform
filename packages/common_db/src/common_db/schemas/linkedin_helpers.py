from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class EducationBase(BaseModel):
    """Базовая схема для записи об образовании"""
    school: str = Field(description="Название учебного заведения")
    degree: str | None = Field(default=None, description="Степень")
    field_of_study: str | None = Field(default=None, description="Специальность")
    start_date: datetime | None = Field(default=None, description="Дата начала")
    end_date: datetime | None = Field(default=None, description="Дата окончания")
    description: str | None = Field(default=None, description="Описание")
    linkedin_url: str | None = Field(default=None, description="LinkedIn URL")
    school_logo: str | None = Field(default=None, description="URL логотипа учебного заведения")


class EducationAPIResponse(EducationBase):
    """Схема записи об образовании для входных данных API"""
    # TODO: вынести в локальный пакет
    # Алиасы для маппинга полей из API
    school: str = Field(alias="schoolName", description="Название учебного заведения")
    degree: str | None = Field(default=None, alias="degreeName", description="Степень")
    field_of_study: str | None = Field(default=None, alias="fieldOfStudy", description="Специальность")
    school_logo: str | None = Field(default=None, alias="schoolLogo", description="URL логотипа учебного заведения")

    @staticmethod
    def _convert_api_date(date_dict: dict | None) -> datetime | None:
        """Конвертирует формат даты из API (месяц, год) в datetime"""
        if not date_dict:
            return None

        return datetime(
            year=date_dict['year'],
            month=date_dict['month'],
            day=1  # Первый день месяца, т.к. в API только месяц и год
        )

    @model_validator(mode='before')
    @classmethod
    def convert_dates(cls, values: dict) -> dict:
        """Конвертирует даты из формата API в datetime"""
        if start_end_date := values.get('startEndDate'):
            values['start_date'] = cls._convert_api_date(start_end_date.get('start'))
            values['end_date'] = cls._convert_api_date(start_end_date.get('end'))
        return values

    class Config:
        from_attributes = True
        populate_by_name = True


class EducationRead(EducationBase):
    """Схема ответа для записи об образовании"""
    profile_id: int
    id: int

    class Config:
        from_attributes = True


class WorkExperienceBase(BaseModel):
    """Базовая схема для записи об опыте работы"""
    company_label: str | None = Field(default=None, description="Название компании")
    title: str = Field(description="Должность")
    company_linkedin_url: str | None = Field(default=None, description="LinkedIn URL компании")
    location: str | None = Field(default=None, description="Локация")
    start_date: datetime | None = Field(default=None, description="Дата начала")
    end_date: datetime | None = Field(default=None, description="Дата окончания")
    description: str | None = Field(default=None, description="Описание")
    duration: str | None = Field(default=None, description="Продолжительность")
    employment_type: str | None = Field(default=None, description="Тип занятости")
    company_logo: str | None = Field(default=None, description="URL логотипа компании")
    linkedin_url: str | None = Field(default=None, description="LinkedIn URL")
    linkedin_id: str | None = Field(default=None, description="LinkedIn ID")


class WorkExperienceAPIResponse(WorkExperienceBase):
    """Схема записи об опыте работы для входных данных API"""
    # TODO: вынести в локальный пакет
    # Алиасы для маппинга полей из API
    company_label: str | None = Field(
        default=None,
        alias="companyName",
        description="Название компании из API"
    )
    company_linkedin_url: str | None = Field(
        default=None,
        alias="companyUrl",
        description="LinkedIn URL компании"
    )
    employment_type: str | None = Field(
        default=None,
        alias="contractType",
        description="Тип занятости"
    )

    @staticmethod
    def _convert_api_date(date_dict: dict | None) -> datetime | None:
        """Конвертирует формат даты из API (месяц, год) в datetime"""
        if not date_dict:
            return None

        return datetime(
            year=date_dict['year'],
            month=date_dict['month'],
            day=1  # Первый день месяца, т.к. в API только месяц и год
        )

    @model_validator(mode='before')
    @classmethod
    def convert_dates(cls, values: dict) -> dict:
        """Конвертирует даты из формата API в datetime"""
        if start_end_date := values.get('startEndDate'):
            values['start_date'] = cls._convert_api_date(start_end_date.get('start'))
            values['end_date'] = cls._convert_api_date(start_end_date.get('end'))
        return values

    class Config:
        from_attributes = True
        populate_by_name = True


class WorkExperienceRead(WorkExperienceBase):
    """Схема ответа для записи об опыте работы"""
    profile_id: int
    id: int

    class Config:
        from_attributes = True
