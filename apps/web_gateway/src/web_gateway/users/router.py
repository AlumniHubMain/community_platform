from typing import Annotated

from common_db.db_abstract import get_async_session
from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import SUserProfileRead, SUserProfileUpdate, UserProfile
from .user_profile_manager import UserProfileManager
from web_gateway import auth


router = APIRouter(tags=["Client profiles"], prefix="/user")


@router.get("/me", response_model=SUserProfileRead)
async def get_current_user_profile(
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    ) -> SUserProfileRead:
    return await UserProfileManager.get_user_profile(session, user_id)

@router.patch("/me", response_model=SUserProfileRead)
async def update_current_user_profile(
    profile: SUserProfileUpdate,
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> SUserProfileRead:
    return await UserProfileManager.update_user_profile(session, profile)


@router.get("/{user_id}", response_model=SUserProfileRead, summary="Get user's profile", dependencies=[Depends(auth.owner_or_admin)])
async def get_profile(
    user_id: int, session: Annotated[AsyncSession, Depends(get_async_session)]
) -> SUserProfileRead:
    return await UserProfileManager.get_user_profile(session, user_id)


# ToDo: evseev.dmsr check user id before patch
# https://app.clickup.com/t/86c11fz94
@router.patch("/{user_id}", response_model=SUserProfileRead, summary="Modify user's profile", dependencies=[Depends(auth.owner_or_admin)])
async def update_profile(
    profile: SUserProfileUpdate, session: Annotated[AsyncSession, Depends(get_async_session)]
) -> SUserProfileRead:
    return await UserProfileManager.update_user_profile(session, profile)


@router.post(
    "", response_model=SUserProfileRead, summary="Creates user's profile"
)
async def create_user(
    profile: UserProfile, session: Annotated[AsyncSession, Depends(get_async_session)]
) -> SUserProfileRead:
    async with session.begin():
        created_profile = await UserProfileManager.create_user_profile(session, profile)
        return created_profile
