from typing import Annotated

from common_db.db_abstract import db_manager
from common_db.managers.user import UserManager
from common_db.schemas import DTOUserProfile, DTOUserProfileRead, DTOUserProfileUpdate, DTOSearchUser
from common_db.schemas.linkedin import LinkedInProfileTask
from common_db.functions import validate_linkedin_username

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from web_gateway import auth
from .properties_router import router as properties_router

from loader import broker
from web_gateway.settings import settings

router = APIRouter(tags=["Client profiles"], prefix="/user")
router.include_router(properties_router)


@router.get("/me", response_model=DTOUserProfileRead)
async def get_current_user_profile(
        user_id: Annotated[int, Depends(auth.current_user_id)],
        session: Annotated[AsyncSession, Depends(db_manager.get_session)],
) -> DTOUserProfileRead:
    return await UserManager.get_user_by_id(session=session, user_id=user_id)


@router.patch("/me")
async def update_current_user_profile(
        profile: DTOUserProfileUpdate,
        session: Annotated[AsyncSession, Depends(db_manager.get_session)],
) -> JSONResponse:
    return await UserManager.update_user(session=session, user_data=profile)


# @router.get(
#    "/{user_id}",
#    response_model=DTOUserProfileRead,
#    summary="Get user's profile"
#)
# async def get_profile(
#        user_id: int,
#        session: Annotated[AsyncSession, Depends(db_manager.get_session)]
#) -> DTOUserProfileRead:
#    return await UserManager.get_user_by_id(session=session, user_id=user_id)


# ToDo: evseev.dmsr check user id before patch
# https://app.clickup.com/t/86c11fz94
# @router.patch("/{user_id}", summary="Modify user's profile")
# async def update_profile(
#        profile: DTOUserProfileUpdate,
#        session: Annotated[AsyncSession, Depends(db_manager.get_session)]
#) -> JSONResponse:
#    return await UserManager.update_user(session=session, user_data=profile)


@router.post("", response_model=DTOUserProfile, summary="Creates user's profile")
async def create_user(
        profile: DTOUserProfile,
        session: Annotated[AsyncSession, Depends(db_manager.get_session)]
) -> JSONResponse:
    async with session.begin():
        return await UserManager.create_user(session=session, user_data=profile)


@router.get("/search", response_model=list[DTOUserProfileRead])
async def search_users(
        user_id: Annotated[int, Depends(auth.current_user_id)],
        search_params: DTOSearchUser,
        session: Annotated[AsyncSession, Depends(db_manager.get_session)]
) -> list[DTOUserProfileRead]:
    """
    Endpoint for searching for a user using the specified optional parameters
    """
    return await UserManager.search_users(user_id=user_id, session=session, search_params=search_params)


@router.post(
    "/verify-linkedin",
    summary="Verify LinkedIn account of a user",
    description="Initiates LinkedIn profile verification process for the current user"
)
async def create_task_verify_linkedin(
    linkedin_username: str,
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(db_manager.get_session)],
) -> JSONResponse:
    """
    Verify LinkedIn account of the current user.
    This endpoint initiates the LinkedIn verification process for the user's profile.
    The verification runs asynchronously and the user profile will be updated once complete.
    Args:
        linkedin_username: LinkedIn username to verify
        user_id: ID of current authenticated user (from token)
        session: Database session
    Returns:
        JSONResponse with status and message
    
    Figma: 3963
    """

    # Sanitize username input
    clean_username = await validate_linkedin_username(linkedin_username)

    # Create verification task
    verification_task = LinkedInProfileTask(
        username=clean_username,
        target_company_label="Yandex",  # TODO: patch logic
        user_id = user_id  # TODO: patch logic: update verification flag, add companies from parse_answer (!!! after make new parser)
    )

    # public task in Pub/Sub via our broker
    await broker.publish(
        settings.pubsub_linkedin_tasks_topic,  # Топик для заданий
        verification_task
    )

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "LinkedIn verification task has been successfully created",
            "details": {
                "username": clean_username,
                "note": "The verification process will run asynchronously."
            }
        }
    )
