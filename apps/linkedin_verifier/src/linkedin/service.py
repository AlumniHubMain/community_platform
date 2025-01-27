from loguru import logger
from pydantic import ValidationError

from packages.common_db.src.common_db.db_abstract import db_manager

from datetime import datetime

# from linkedin_verifier.app.schemas.linkedin import ProfileResponse, ScrapinProfileResponse
from common_db.schemas.linkedin import (
    LinkedInProfileAPI,
    LinkedInProfileRead,
    LinkedInProfileTask
)

from src.linkedin.factory import LinkedInRepositoryFactory
from src.linkedin.providers.scrapin import LinkedInScrapinRepository
from apps.linkedin_verifier.src.db.db_manager import LinkedInDBManager
from loader import broker  # Используем готовый broker
from src.exceptions import APIError, DatabaseError, RateLimitError

from src.db.models.limits import LinkedInApiLimits
from config import settings
from src.schemas.pubsub import LinkedInLimitsAlert


class LinkedInService:
    """Сервис для работы с LinkedIn API"""

    @classmethod
    async def validate_profile(cls, username: str, target_company_label: str, use_mock: bool = False) ->\
            LinkedInProfileAPI:
        """
        Проверяет профиль LinkedIn на наличие опыта работы в целевой компании.
        
        Args:
            username: Username профиля LinkedIn
            target_company_label: Название целевой компании
            use_mock: Использовать ли мок-данные
            
        Returns:
            LinkedInProfileAPI: Данные профиля с результатами проверки
        """
        try:
            repository_class = LinkedInRepositoryFactory.create()
            
            # 1. Получаем и валидируем данные из API
            raw_data = await repository_class.get_profile(username, use_mock=use_mock)
            scrapin_profile = LinkedInProfileAPI.model_validate(raw_data)
            
            # 2. Проверяем опыт работы (вне транзакции)
            is_verified = cls.validate_work_experience(scrapin_profile, target_company_label)
            
            db_profile = None  # Инициализируем до транзакции
            
            # 3. Начало единой транзакции для сохранения профиля и статуса
            try:
                async for session in db_manager.get_async_session():
                    # Все операции внутри этого блока - одна транзакция
                    db_profile = await LinkedInDBManager.save_profile(
                        session=session,
                        profile_data=scrapin_profile
                    )

                    # TODO: вернуть после согласования. Как мерджить исторические данные-профили? Не на что ссылаться.
                    # await LinkedInDBManager.update_verification_status(
                    #     session=session,
                    #     username=scrapin_profile.username,
                    #     is_verified=is_verified
                    # )
                    
                    # Явно коммитим изменения
                    await session.commit()
                
                # Транзакция завершена успешно
                
                # 4. Отдельная транзакция для лимитов API, именно для LinkedInScrapinRepository,
                # т.к. только там кредиты есть
                # TODO: а уменьшатся ли кредиты, если выше не успех? можт if profile and ...
                if scrapin_profile and isinstance(repository_class, LinkedInScrapinRepository):
                    try:
                        await LinkedInDBManager.update_api_limits(
                            LinkedInLimitsAlert(
                                provider_type=settings.current_provider,
                                provider_id=LinkedInApiLimits.get_provider_id(
                                    provider_type=settings.current_provider,
                                    api_key=settings.scrapin_api_key.get_secret_value()
                                ),
                                credits_left=scrapin_profile.credits_left,
                                rate_limit_left=scrapin_profile.rate_limit
                            )
                        )
                    except Exception as e:
                        logger.warning(f"Failed to update API limits: {e}")
                    
                # Преобразуем ORM модель обратно в API модель
                return LinkedInProfileAPI.model_validate(db_profile)  # Теперь точно не будет None
                    
            except Exception as e:
                raise DatabaseError(f"Error saving profile: {e}")
            
        except Exception as e:
            logger.error(f"Error parsing profile {username}: {e}")
            raise

    @staticmethod
    def validate_work_experience(profile_data: LinkedInProfileAPI, target_company_label: str) -> bool:
        """
        Проверяет опыт работы в целевой компании и заполняет соответствующие поля профиля.
        
        Args:
            profile_data: Данные профиля LinkedIn
            target_company_label: Название целевой компании
            
        Returns:
            bool: True если найден опыт работы в целевой компании
        """
        try:
            # 1. Проверка входных данных
            if not profile_data or not target_company_label:
                logger.warning("Empty profile_data or target_company_label")
                return False
                
            if not profile_data.work_experience:
                logger.debug(f"No work experience for profile {getattr(profile_data, 'username', 'N/A')}")
                return False
                
            # 2. Безопасный поиск позиций в целевой компании
            target_positions = []
            for exp in profile_data.work_experience:
                if not exp or not exp.company_label:  # Пропускаем записи без названия компании
                    continue
                    
                try:
                    if target_company_label.lower() in exp.company_label.lower():
                        target_positions.append(exp)
                except AttributeError as e:
                    logger.warning(f"Error comparing company labels: {e}")
                    continue
            
            # 3. Обработка найденных позиций
            if target_positions:
                try:
                    # Сортируем по дате начала (от новых к старым)
                    # Используем безопасную дату для None значений
                    target_positions.sort(
                        key=lambda x:
                        x.start_date if x.start_date is not None else datetime(1900, 1, 1),
                        reverse=True
                    )
                    
                    # Берем самую свежую позицию
                    latest_position = target_positions[0]  # Теперь безопасно, так как проверили if target_positions
                    
                    # Заполняем поля профиля
                    profile_data.is_target_company_found = True
                    profile_data.target_company_positions_count = len(target_positions)
                    
                    # Безопасно заполняем данные о последней позиции
                    if latest_position:
                        profile_data.target_company_label = latest_position.company_label
                        profile_data.target_company_linkedin_id = latest_position.linkedin_id
                        profile_data.target_position_title = latest_position.title
                        profile_data.target_company_linkedin_url = latest_position.company_linkedin_url
                    
                    # Проверяем текущую работу в целевой компании
                    profile_data.is_employee_in_target_company = any(
                        not pos.end_date 
                        for pos in target_positions 
                        if hasattr(pos, 'end_date')  # Проверяем наличие атрибута
                    )
                    
                    return True
                    
                except Exception as e:
                    logger.error(f"Error processing target positions: {e}")
                    LinkedInService._set_default_target_values(profile_data)
                    return False
            
            # Если не нашли ни одной позиции
            LinkedInService._set_default_target_values(profile_data)
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error in validate_work_experience: {e}")
            LinkedInService._set_default_target_values(profile_data)
            return False

    @staticmethod
    def _set_default_target_values(profile_data: LinkedInProfileAPI) -> None:
        """Устанавливает значения по умолчанию для полей целевой компании."""
        profile_data.is_target_company_found = False
        profile_data.target_company_positions_count = 0
        profile_data.target_company_label = None
        profile_data.target_company_linkedin_id = None
        profile_data.target_position_title = None
        profile_data.target_company_linkedin_url = None
        profile_data.is_employee_in_target_company = False
