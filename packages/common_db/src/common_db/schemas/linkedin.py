from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, model_validator

# TODO: добавить логгер, который договорились использовать
# from loguru import logger

from common_db.schemas.linkedin_helpers import EducationAPIResponse, WorkExperienceAPIResponse


class LinkedInProfileBase(BaseModel):
    """Базовый класс для LinkedIn профиля с общими полями"""
    # Basic Info
    public_identifier: str | None = None
    linkedin_identifier: str | None = None
    member_identifier: str | None = None
    linkedin_url: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    headline: str | None = None
    location: str | None = None
    summary: str | None = None

    photo_url: str | None = None
    background_url: str | None = None
    is_open_to_work: bool | None = None
    is_premium: bool | None = None
    pronoun: str | None = None
    is_verification_badge_shown: bool | None = None
    creation_date: datetime | None = None
    follower_count: int | None = None
    parsed_date: datetime = Field(default_factory=datetime.now)  # Дата и время парсинга профиля

    # Professional Info
    work_experience: list[WorkExperienceAPIResponse] | None = None  # из positions.positionHistory
    education: list[EducationAPIResponse] | None = None  # из schools.educationHistory
    skills: list[str] | None = None
    languages: list[str] | None = None
    recommendations: dict[str, Any] | None = None  # весь объект recommendations как есть
    certifications: dict[str, Any] | None = None  # весь объект certifications как есть

    # TODO: Возможно вынести в головную таблицу User для оптимизации запросов
    # Инфа о текущем месте работы, вынесено из experience history (последняя запись с откр. датой завершения работы)
    is_currently_employed: bool | None = Field(
        default=None,
        description="Флаг, указывающий работает ли человек в данный момент "
                    "(определяется по наличию хотя бы одной записи без end_date)"
    )
    current_jobs_count: int | None = Field(
        default=None,
        description="Количество текущих мест работы (определяется по количеству записей без end_date)"
    )
    # Информация о последней активной работе (первая в списке work_experience с end_date=None)
    current_company_label: str | None = Field(
        default=None,
        description="Название компании последней активной работы (если есть)"
    )
    current_company_linkedin_id: str | None = Field(
        default=None,
        description="LinkedIn ID компании последней активной работы (если есть)"
    )
    current_position_title: str | None = Field(
        default=None,
        description="Должность на последней активной работе (если есть)"
    )
    current_company_linkedin_url: str | None = Field(
        default=None,
        description="LinkedIn URL компании последней активной работы (если есть)"
    )

    # TODO: Возможно вынести в головную таблицу User
    # Target Company Info - посл. место работы в легитимных компаниях (с точки зрения продуктовой верификации)
    is_target_company_found: bool | None = Field(
        default=None,
        description="Флаг, указывающий найдена ли целевая компания в опыте работы"
    )
    target_company_positions_count: int | None = Field(
        default=None,
        description="Количество позиций в легитимных компаниях"
    )
    # Информация о последней работе в целевой компании
    target_company_label: str | None = Field(
        default=None,
        description="Название целевой компании из опыта работы"
    )
    target_company_linkedin_id: str | None = Field(
        default=None,
        description="LinkedIn ID целевой компании"
    )
    target_position_title: str | None = Field(
        default=None,
        description="Последняя должность в целевой компании"
    )
    target_company_linkedin_url: str | None = Field(
        default=None,
        description="LinkedIn URL целевой компании"
    )
    is_employee_in_target_company: bool | None = Field(
        default=None,
        description="Флаг, указывающий работает ли человек в целевой компании в данный момент"
    )



class LinkedInProfileAPI(LinkedInProfileBase):
    """Схема для парсинга и валидации данных из LinkedIn API"""
    model_config = {
        'from_attributes': True,  # Включаем поддержку ORM
        'populate_by_name': True  # Включаем поддержку алиасов
    }
    
    # TODO: вынести в локальный пакет - для pubsub
    # Алиасы для маппинга полей из API
    public_identifier: str | None = Field(default=None, alias="publicIdentifier")
    linkedin_identifier: str | None = Field(default=None, alias="linkedInIdentifier")
    member_identifier: str | None = Field(default=None, alias="memberIdentifier")
    linkedin_url: str | None = Field(default=None, alias="linkedInUrl")
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    photo_url: str | None = Field(default=None, alias="photoUrl")
    background_url: str | None = Field(default=None, alias="backgroundUrl")
    is_open_to_work: bool | None = Field(default=None, alias="openToWork")
    is_premium: bool | None = Field(default=None, alias="premium")
    is_verification_badge_shown: bool | None = Field(default=None, alias="showVerificationBadge")
    follower_count: int | None = Field(default=None, alias="followerCount")
    creation_date: datetime | None = Field(default=None, alias="creationDate")
    credits_left: int | None = Field(exclude=True)
    rate_limit_left: int | None = Field(exclude=True)

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
    def extract_nested_fields(cls, values):
        """
        Извлекает данные из вложенной структуры ответа Scrapin API и преобразует их в плоскую структуру.

        Пример входных данных:
        {
            'success': True,
            'person': {
                'firstName': 'John',
                'lastName': 'Doe',
                'positions': {
                    'positionHistory': [...]
                }
            }
        }

        Преобразуется в:
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'work_experience': [WorkExperience(...)]
        }

        Args:
            values: Исходный словарь с данными от API

        Returns:
            Dict: Преобразованный словарь с извлеченными полями
        """
        person = values.get('person', {})

        # Копируем поля как есть из API
        for field in [
            'publicIdentifier', 'linkedInIdentifier', 'memberIdentifier',
            'linkedInUrl', 'firstName', 'lastName', 'headline',
            'location', 'summary', 'photoUrl', 'backgroundUrl',
            'openToWork', 'premium', 'pronoun', 'showVerificationBadge',
            'followerCount', 'skills', 'languages'
        ]:
            values[field] = person.get(field)

        # Преобразуем даты
        values['creationDate'] = cls._convert_api_date(person.get('creationDate'))
        values['recommendations'] = person.get('recommendations', {})
        values['certifications'] = person.get('certifications', {})

        # Преобразуем positions в work_experience
        try:
            positions = person.get('positions', {}).get('positionHistory', [])
            values['work_experience'] = [
                WorkExperienceAPIResponse(
                    company_label=pos.get('companyName'),
                    title=pos.get('title'),
                    description=pos.get('description'),
                    start_date=cls._convert_api_date(pos.get('startEndDate', {}).get('start')),
                    end_date=cls._convert_api_date(pos.get('startEndDate', {}).get('end')),
                    company_location=pos.get('companyLocation'),
                    contract_type=pos.get('contractType'),
                    company_logo=pos.get('companyLogo'),
                    linkedin_url=pos.get('linkedInUrl'),
                    linkedin_id=pos.get('linkedInId')
                ) for pos in positions if pos  # Пропускаем None записи
            ]

            # Находим все текущие работы (без end_date)
            current_jobs = []
            for pos in positions:
                if not pos:
                    continue
                try:
                    if not pos.get('startEndDate', {}).get('end'):
                        current_jobs.append(pos)
                except AttributeError:
                    continue

            # Определяем последнюю активную работу (первая в списке без end_date)
            # API возвращает записи в порядке от новых к старым
            current_job = current_jobs[0] if current_jobs else None

            # Заполняем денормализованные поля текущей работы
            values.update({
                'is_currently_employed': bool(current_jobs),  # True если есть хотя бы одна текущая работа
                'current_jobs_count': len(current_jobs),  # Количество текущих работ
                # Информация о последней активной работе
                'current_company_label': current_job.get('companyName') if current_job else None,
                'current_company_linkedin_id': current_job.get('linkedInId') if current_job else None,
                'current_position_title': current_job.get('title') if current_job else None,
                'current_company_linkedin_url': current_job.get('linkedInUrl') if current_job else None,
            })
        except Exception as e:
            # TODO: вернуть логгер
            # logger.error(f"Error processing work experience: {e}")
            # Устанавливаем безопасные значения по умолчанию
            values.update({
                'work_experience': [],
                'is_currently_employed': False,
                'current_jobs_count': 0,
                'current_company_label': None,
                'current_company_linkedin_id': None,
                'current_position_title': None,
                'current_company_linkedin_url': None,
            })

        # Информация о целевой компании будет заполняться позже в сервисе,
        # здесь инициализируем значения по умолчанию
        values.update({
            'is_target_company_found': False,
            'target_company_positions_count': 0,
            'target_company_label': None,
            'target_company_linkedin_id': None,
            'target_position_title': None,
            'target_company_linkedin_url': None,
            'is_employee_in_target_company': False,
        })

        # Преобразуем schools в education
        try:
            values['education'] = [
                EducationAPIResponse(
                    school=edu.get('schoolName'),
                    degree=edu.get('degreeName'),
                    field=edu.get('fieldOfStudy'),
                    start_date=cls._convert_api_date(edu.get('startEndDate', {}).get('start')),
                    end_date=cls._convert_api_date(edu.get('startEndDate', {}).get('end')),
                    linkedin_url=edu.get('linkedInUrl'),
                    school_logo=edu.get('schoolLogo')
                ) for edu in person.get('schools', {}).get('educationHistory', [])
            ]
        except Exception as e:
            # TODO: вернуть логгер
            # logger.error(f"Error processing education: {e}")
            values['education'] = []

        values['raw_data'] = values
        return values


class LinkedInProfileRead(LinkedInProfileBase):
    """Схема для чтения профиля из БД другими сервисами"""
    users_id_fk: int
    id: int
    created_at: datetime
    updated_at: datetime


class LinkedInProfileTask(BaseModel):
    """Схема для задачи парсинга профиля"""
    # TODO: вынести в локальный пакет - для pubsub
    username: str
    target_company_label: str


# TODO: Вынести raw_data, companies в отдельные схемы
