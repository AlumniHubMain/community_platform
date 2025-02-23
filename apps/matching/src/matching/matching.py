import logging
from typing import Callable, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from common_db.models import ORMMatchingResult
from common_db.enums.forms import EFormIntentType
from common_db.schemas import FormRead, SUserProfileRead, MeetingsUserLimits
from common_db.managers.limits import LimitsManager
from matching.data_loader import DataLoader
from matching.model import Model
from matching.model.model_settings import model_settings_presets, ModelType
from matching.transport import PSClient


async def process_matching_request(  # pylint: disable=too-many-arguments
    db_session_callable: Callable[[], AsyncSession],
    psclient: PSClient,
    logger: logging.Logger,
    user_id: int,
    form_id: int,
    model_settings_preset: str,
    n: int = 5,
) -> Tuple[int, List[int]]:
    """Common matching logic used by both endpoints"""
    async with db_session_callable() as session:
        try:
            if model_settings_preset not in model_settings_presets:
                raise ValueError("Invalid model settings preset")

            model_settings = model_settings_presets[model_settings_preset]

            # Get user profiles with their LinkedIn data
            all_users = await DataLoader.get_all_user_profiles(session)
            form = await DataLoader.get_form(session, form_id)
            linkedin_profiles = await DataLoader.get_all_linkedin_profiles(session)

            # Validate form content structure
            if not form.content:
                raise ValueError("Form content is empty")

            # Validate form content based on intent
            if form.intent == EFormIntentType.mentoring_mentor:
                if not form.content.get('required_grade'):
                    raise ValueError("Required grade not specified for mentor form")
            elif form.intent == EFormIntentType.mentoring_mentee:
                if not form.content.get('mentor_specialization'):
                    raise ValueError("Mentor specialization not specified for mentee form")

            # Create model instance
            model = None
            if model_settings.model_type == ModelType.CATBOOST:
                model = psclient.get_file(model_settings.model_path)

            matcher = Model(model_settings)
            matcher.load_model(model)

            # Make predictions
            predictions = matcher.predict(all_users, form, linkedin_profiles, user_id, n)

            # TODO: get from settings
            limit_settings = MeetingsUserLimits(
                max_user_confirmed_meetings_count=5,
                max_user_pended_meetings_count=10,
            )

            # Filter predictions based on user limits
            filtered_predictions = await LimitsManager.filter_users_by_limits(
                session,
                predictions,
                limit_settings
            )

            # Save results with filtered predictions
            matching_result = ORMMatchingResult(
                model_settings_preset=model_settings_preset,
                match_users_count=n,
                user_id=user_id,
                form_id=form_id,
                matching_result=filtered_predictions,
            )
            session.add(matching_result)
            await session.commit()
            await session.refresh(matching_result)

            if logger:
                logger.info(
                    "Matching results saved for user_id: %d, form_id: %d, filtered from %d to %d matches",
                    user_id,
                    form_id,
                    len(predictions),
                    len(filtered_predictions)
                )

            return matching_result.id, filtered_predictions

        except Exception as e:
            # Save error result
            error_result = ORMMatchingResult(
                model_settings_preset=model_settings_preset,
                match_users_count=n,
                user_id=user_id,
                form_id=form_id,
                error_code="MATCHING_ERROR",
                error_details={"error": str(e)},
                matching_result=[],
            )
            session.add(error_result)
            await session.commit()
            raise
