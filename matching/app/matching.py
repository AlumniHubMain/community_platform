import logging
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from app.data_loader import DataLoader
from app.model import Model
from app.model.model_settings import model_settings_presets, ModelType
from db_common.models import ORMMatchingResult
from app.transport import PSClient


async def process_matching_request(
    db_session_callable: Callable[[], AsyncSession],
    psclient: PSClient,
    user_id: int,
    meeting_intent_id: int,
    model_settings_preset: str,
    n: int,
    form_id: int | None = None,
    logger: logging.Logger = None,
) -> tuple[int, list[int]]:
    """Common matching logic used by both endpoints"""
    async with db_session_callable() as session:
        try:
            if model_settings_preset not in model_settings_presets:
                raise ValueError("Invalid model settings preset")

            model_settings = model_settings_presets[model_settings_preset]

            all_users = await DataLoader.get_all_user_profiles(session)
            all_linkedin = await DataLoader.get_all_linkedin_profiles(session)
            intent = await DataLoader.get_meeting_intent(session, meeting_intent_id)

            model = None
            if model_settings.model_type == ModelType.CATBOOST:
                model = psclient.get_file(model_settings.model_path)

            matcher = Model(model_settings)
            matcher.load_model(model)
            predictions = matcher.predict(all_users, all_linkedin, intent, user_id, n)

            matching_result = ORMMatchingResult(
                model_settings_preset=model_settings_preset,
                match_users_count=n,
                user_id=user_id,
                form_id=form_id,
                intent_id=meeting_intent_id,
                matching_result=predictions,
            )
            session.add(matching_result)
            await session.commit()

            logger.info(
                "Matching results saved for user_id: %d, meeting_intent_id: %d",
                user_id,
                meeting_intent_id,
            )
        except Exception as e:
            error_result = ORMMatchingResult(
                model_settings_preset=model_settings_preset,
                match_users_count=n,
                user_id=user_id,
                form_id=form_id,
                intent_id=meeting_intent_id,
                error_code="MATCHING_ERROR",
                error_details={"error": str(e)},
                matching_result=[],
            )
            session.add(error_result)
            await session.commit()
            raise

    return matching_result.id, predictions
