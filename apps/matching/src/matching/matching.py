import logging
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from common_db.models import ORMMatchingResult, ORMForm
from common_db.enums.forms import EFormIntentType
from common_db.schemas import FormRead, MeetingsUserLimits
from common_db.managers.limits import LimitsManager
from matching.data_loader import DataLoader
from matching.model import Model
from matching.model.model_settings import model_settings_presets, ModelType
from matching.transport import PSClient
from matching.parser.form_parser_service import FormParserService

# Initialize the parser service
form_parser_service = FormParserService()


async def process_matching_request(  # pylint: disable=too-many-arguments
    db_session_callable: Callable[[], AsyncSession],
    psclient: PSClient,
    logger: logging.Logger,
    user_id: int,
    form_id: int,
    model_settings_preset: str,
    n: int = 5,
    use_limits: bool = True,
) -> tuple[int, list[int]]:
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
                if not form.content.get("required_grade"):
                    raise ValueError("Required grade not specified for mentor form")
            elif form.intent == EFormIntentType.mentoring_mentee:
                if not form.content.get("mentor_specialization"):
                    raise ValueError("Mentor specialization not specified for mentee form")
            elif form.intent == EFormIntentType.connects:
                # Check for either social_circle_expansion or professional_networking
                if not (form.content.get("social_circle_expansion") or form.content.get("professional_networking")):
                    raise ValueError("Either social_circle_expansion or professional_networking must be specified")
            elif form.intent == EFormIntentType.mock_interview:
                if not form.content.get("interview_type") or not form.content.get("language"):
                    raise ValueError("Interview type and language must be specified for mock interview form")
            elif form.intent in [EFormIntentType.projects_find_contributor, EFormIntentType.projects_find_cofounder]:
                if not form.content.get("specialization") or not form.content.get("skills"):
                    raise ValueError("Specialization and skills must be specified for project forms")
                    
            # Create model instance
            model = None
            if model_settings.model_type == ModelType.CATBOOST:
                model = psclient.get_file(model_settings.model_path)

            matcher = Model(model_settings)
            matcher.load_model(model)

            # Make predictions
            predictions = matcher.predict(all_users, form, linkedin_profiles, user_id, n)

            # Get user meeting limits
            limit_settings = MeetingsUserLimits(
                max_user_confirmed_meetings_count=5,
                max_user_pended_meetings_count=10,
            )

            # Filter predictions based on user limits
            if use_limits:
                filtered_predictions = await LimitsManager.filter_users_by_limits(session, predictions, limit_settings)
            else:
                filtered_predictions = predictions

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
                    len(filtered_predictions),
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


async def process_text_to_form_content(
    db_session_callable: Callable[[], AsyncSession],
    logger: logging.Logger,
    user_id: int,
    intent_type: EFormIntentType,
    text_description: str,
) -> tuple[int, dict]:
    """
    Process a text description into structured form content and save it.

    Args:
        db_session_callable: Callable that returns a database session
        logger: Logger instance
        user_id: User ID
        intent_type: Form intent type
        text_description: Text description to parse

    Returns:
        Tuple of (form_id, form_content)
    """
    async with db_session_callable() as session:
        try:
            # Initialize the parser service if needed
            if not form_parser_service.initialized:
                await form_parser_service.initialize()

            # Parse the text description into structured form content
            form_content = await form_parser_service.parse_text_to_form_content(text_description, intent_type)

            # Create a new form with the parsed content
            form = ORMForm(
                user_id=user_id,
                intent=intent_type,
                content=form_content,
            )
            session.add(form)
            await session.commit()
            await session.refresh(form)

            if logger:
                logger.info(
                    "Created form from text description for user_id: %d, intent: %s",
                    user_id,
                    intent_type.value,
                )

            return form.id, form_content

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error processing text to form: %s", str(e))
            # Create a form with minimal content in case of error
            form = ORMForm(
                user_id=user_id,
                intent=intent_type,
                content={"error": "Failed to parse text", "text": text_description},
            )
            session.add(form)
            await session.commit()
            await session.refresh(form)

            return form.id, form.content


async def parse_text_for_matching(
    db_session_callable: Callable[[], AsyncSession],
    psclient: PSClient,
    logger: logging.Logger,
    user_id: int,
    text_description: str,
    intent_type: EFormIntentType | None = None,
    model_settings_preset: str = "heuristic",
    n: int = 5,
) -> tuple[int, list[int]]:
    """
    Parse text description and directly use it for matching without creating a form.

    Args:
        db_session_callable: Callable that returns a database session
        psclient: Persistent storage client
        logger: Logger instance
        user_id: User ID
        text_description: Text description to parse
        intent_type: The form intent type (optional, will be detected from text)
        model_settings_preset: Model settings preset name
        n: Number of matches to return

    Returns:
        Tuple of (match_id, matching_results)
    """
    async with db_session_callable() as session:
        try:
            if not form_parser_service.initialized:
                await form_parser_service.initialize()

            detected_intent, form_content = await form_parser_service.parse_text_to_form_content(
                text_description, intent_type
            )

            intent_type = detected_intent

            temp_form = FormRead(
                id=-1,
                user_id=user_id,
                intent=intent_type,
                content=form_content,
                created_at="2023-01-01T00:00:00",
                updated_at="2023-01-01T00:00:00",
                description=f"Temporary form from text: {text_description[:50]}...",
            )

            all_users = await DataLoader.get_all_user_profiles(session)
            linkedin_profiles = await DataLoader.get_all_linkedin_profiles(session)

            if model_settings_preset not in model_settings_presets:
                raise ValueError("Invalid model settings preset")
            model_settings = model_settings_presets[model_settings_preset]

            model = None
            if model_settings.model_type == ModelType.CATBOOST:
                model = psclient.get_file(model_settings.model_path)

            matcher = Model(model_settings)
            matcher.load_model(model)

            predictions = matcher.predict(all_users, temp_form, linkedin_profiles, user_id, n)

            # Get user meeting limits
            limit_settings = MeetingsUserLimits(
                max_user_confirmed_meetings_count=5,
                max_user_pended_meetings_count=10,
            )

            # Filter predictions based on user limits
            filtered_predictions = await LimitsManager.filter_users_by_limits(session, predictions, limit_settings)

            # Save matching result without creating a form
            matching_result = ORMMatchingResult(
                model_settings_preset=model_settings_preset,
                match_users_count=n,
                user_id=user_id,
                form_id=None,  # No form ID since we're not creating a form
                matching_result=filtered_predictions,
                additional_data={
                    "parsed_content": form_content,
                    "text_description": text_description,
                    "intent_type": intent_type.value,
                },
            )
            session.add(matching_result)
            await session.commit()
            await session.refresh(matching_result)

            if logger:
                logger.info(
                    "Matching results from text description saved for user_id: %d, intent: %s, filtered from %d to %d matches",  # pylint: disable=line-too-long
                    user_id,
                    intent_type.value,
                    len(predictions),
                    len(filtered_predictions),
                )

            return matching_result.id, filtered_predictions

        except Exception as e:
            logger.error("Error processing text to matching: %s", str(e))
            # Save error result
            error_result = ORMMatchingResult(
                model_settings_preset=model_settings_preset,
                match_users_count=n,
                user_id=user_id,
                form_id=None,
                error_code="TEXT_MATCHING_ERROR",
                error_details={"error": str(e), "text_description": text_description, 
                               "intent_type": intent_type.value if intent_type else None},
                matching_result=[],
            )
            session.add(error_result)
            await session.commit()
            await session.refresh(error_result)

            raise
