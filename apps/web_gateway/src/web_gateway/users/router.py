from typing import Annotated

from common_db.db_abstract import db_manager
from common_db.managers.user import UserManager
from common_db.schemas import DTOUserProfile, DTOUserProfileRead, DTOUserProfileUpdate, DTOSearchUser

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from web_gateway import auth
from .properties_router import router as properties_router

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


@router.get(
    "/{user_id}",
    response_model=DTOUserProfileRead,
    summary="Get user's profile"
)
async def get_profile(
        user_id: int,
        session: Annotated[AsyncSession, Depends(db_manager.get_session)]
) -> DTOUserProfileRead:
    return await UserManager.get_user_by_id(session=session, user_id=user_id)


# ToDo: evseev.dmsr check user id before patch
# https://app.clickup.com/t/86c11fz94
@router.patch("/{user_id}", summary="Modify user's profile")
async def update_profile(
        profile: DTOUserProfileUpdate,
        session: Annotated[AsyncSession, Depends(db_manager.get_session)]
) -> JSONResponse:
    return await UserManager.update_user(session=session, user_data=profile)


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
