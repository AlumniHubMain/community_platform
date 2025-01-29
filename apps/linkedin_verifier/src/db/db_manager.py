from datetime import datetime
from typing import Dict, Any
from loguru import logger
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from common_db.db_abstract import db_manager
from common_db.models.users import ORMUserProfile
from common_db.models.linkedin import ORMLinkedInProfile, ORMLinkedInRawData
from common_db.models.linkedin_helpers import ORMLinkedInApiLimits

from common_db.schemas.linkedin import (
    LinkedInProfileAPI,
    # LinkedInProfileRead,
    # LinkedInProfileTask
)
from ..schemas.pubsub import LinkedInLimitsAlert


class LinkedInDBManager:
    """Менеджер для работы с БД"""

    @staticmethod
    async def save_profile(session: AsyncSession, profile_data: LinkedInProfileAPI) -> ORMLinkedInProfile:
        # TODO: возвращать в DTO, и затем model.dump
        """Сохраняет профиль LinkedIn в БД.
        
        Args:
            session: Сессия SQLAlchemy
            profile_data: Данные профиля из API
            
        Returns:
            Сохраненный профиль
        """
        # Определяем текущее место работы
        current_job = next(
            (job for job in profile_data.work_experience if job.end_date is None),
            None
        ) if profile_data.work_experience else None

        # Добавляем информацию о текущей работе в profile_data
        profile_data.is_currently_employed = current_job is not None
        profile_data.current_company_label = current_job.company_label if current_job else None
        profile_data.current_company_linkedin_id = current_job.linkedin_id if current_job else None
        profile_data.current_position_title = current_job.title if current_job else None
        profile_data.current_company_linkedin_url = current_job.company_linkedin_url if current_job else None

        # Получаем данные профиля без education и work_experience
        profile_dict = profile_data.model_dump(
            exclude={
                'education',
                'work_experience',
                'credits_left',
                'rate_limit_left',
                'rate_limit',
            }
        )

        # Ищем существующий профиль
        existing_profile = await session.scalar(
            select(ORMLinkedInProfile)
            .where(ORMLinkedInProfile.public_identifier == profile_data.public_identifier)
        )

        try:
            if not existing_profile:
                # Создаем новый профиль через insert()
                result = await session.execute(
                    insert(ORMLinkedInProfile)
                    .values(**profile_dict)
                    .returning(ORMLinkedInProfile)
                )
                db_profile = result.scalar_one()
            else:
                # Обновляем существующий профиль
                result = await session.execute(
                    update(ORMLinkedInProfile)
                    .where(ORMLinkedInProfile.public_identifier == profile_data.public_identifier)
                    .values(**profile_dict)
                    .returning(ORMLinkedInProfile)
                )
                db_profile = result.scalar_one()

            await session.flush()

            # Добавляем образование и опыт работы через bulk insert
            if profile_data.education:
                education_data = [
                    {**edu.model_dump(), 'profile_id': db_profile.id}
                    for edu in profile_data.education
                ]
                await session.execute(
                    insert(ORMLinkedInProfile.education.property.mapper.class_)
                    .values(education_data)
                    .on_conflict_do_nothing()
                )

            if profile_data.work_experience:
                work_data = [
                    {**work.model_dump(), 'profile_id': db_profile.id}
                    for work in profile_data.work_experience
                ]
                await session.execute(
                    insert(ORMLinkedInProfile.work_experience.property.mapper.class_)
                    .values(work_data)
                    .on_conflict_do_nothing()
                )

            await session.flush()
            
            # Логируем результат операции
            logger.info(f"{'Обновлен' if existing_profile else 'Создан'} профиль для {profile_data.public_identifier}")
            
            return db_profile

        except Exception as e:
            logger.error(f"Ошибка при сохранении профиля {profile_data.public_identifier}: {e}")
            raise

    @classmethod
    async def update_verification_status(
            cls,
            session: AsyncSession,
            username: str,
            is_verified: bool
    ) -> None:
        """Обновляет статус верификации в основном профиле"""
        if not session:
            raise ValueError("Session cannot be None")
        if not username:
            raise ValueError("Username cannot be None or empty")
        if is_verified is None:
            raise ValueError("is_verified cannot be None")

        stmt = select(ORMUserProfile).where(ORMUserProfile.username == username)
        result = await session.execute(stmt)
        main_profile = result.scalar_one_or_none()

        if not main_profile:
            main_profile = ORMUserProfile(username=username)
            session.add(main_profile)

        # TODO: return for platform users, not community?
        # main_profile.is_verified = is_verified
        # await session.commit()

    @classmethod
    async def update_api_limits(cls, limits: LinkedInLimitsAlert) -> None:
        """Обновляет лимиты API в отдельной транзакции
        
        Args:
            limits: Данные о лимитах API
                provider_type: тип провайдера (SCRAPIN/TOMQUIRK)
                provider_id: для SCRAPIN - последние 4 символа API ключа,
                           для TOMQUIRK - часть email до @
                credits_left: оставшиеся кредиты
                rate_limit_left: оставшийся rate limit
                updated_at: время обновления
        """
        async for session in db_manager.get_session():
            stmt = select(ORMLinkedInApiLimits).where(
                and_(
                    ORMLinkedInApiLimits.provider_type == limits.provider_type,
                    ORMLinkedInApiLimits.provider_id == limits.provider_id
                )
            )
            result = await session.execute(stmt)
            limit = result.scalar_one_or_none()

            if not limit:
                # Создаем новую запись
                limit = ORMLinkedInApiLimits(
                    provider_type=limits.provider_type,
                    provider_id=limits.provider_id,
                    credits_left=limits.credits_left,
                    rate_limit_left=limits.rate_limit_left,
                    updated_at=limits.updated_at
                )
                session.add(limit)
            else:
                # Обновляем существующую запись через update()
                await session.execute(
                    update(ORMLinkedInApiLimits)
                    .where(
                        and_(
                            ORMLinkedInApiLimits.provider_type == limits.provider_type,
                            ORMLinkedInApiLimits.provider_id == limits.provider_id
                        )
                    )
                    .values(
                        credits_left=limits.credits_left,
                        rate_limit_left=limits.rate_limit_left,
                        updated_at=limits.updated_at
                    )
                )
            
            # Сохраняем изменения
            await session.commit()

    @staticmethod
    async def save_raw_data(linkedin_url: str, raw_data: Dict[str, Any]) -> None:
        """Сохраняет сырые данные профиля в отдельной транзакции
        
        Args:
            linkedin_url: URL профиля LinkedIn
            raw_data: Сырые данные от API
        """
        async for session in db_manager.get_session():
            try:
                # Создаем новую запись
                raw_data_record = ORMLinkedInRawData(
                    target_linkedin_url=linkedin_url,
                    raw_data=raw_data,
                    parsed_date=datetime.utcnow()
                )
                session.add(raw_data_record)
                await session.commit()
                logger.info(f"Saved raw data for profile: {linkedin_url}")
                
            except Exception as e:
                logger.error(f"Failed to save raw data for {linkedin_url}: {e}")
                await session.rollback()
                raise
