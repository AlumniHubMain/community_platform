from typing import Annotated

from common_db import get_async_session
from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import SUserProfileRead, UserProfile
from .user_profile_manager import UserProfileManager


router = APIRouter(tags=["Client profiles"], prefix="/user")


@router.get("/{user_id}", response_model=SUserProfileRead,
            summary="Get user's profile")
async def get_profile(
    user_id: int, session: Annotated[AsyncSession, Depends(get_async_session)]
) -> SUserProfileRead:
    return await UserProfileManager.get_user_profile(session, user_id)


# @router.patch("/me", response_model=SUserProfileRead)
# async def update_profile(
#                          profile_data: Annotated[SUserProfileUpdate, Depends(SUserProfileUpdate)],
#                          session: Annotated[AsyncSession, Depends(get_async_session)],
#                          user=Depends(verified_current_user)):
#     return await UserProfileManager.update_user_profile(session, user.id, profile_data)
#
#
# @router.get("", response_model=List[SUserProfileRead])
# async def get_all_users(session: Annotated[AsyncSession, Depends(get_async_session)],
#                         user=Depends(verified_current_user)):
#     pass  # return await UserManager.get_all_users(db)


@router.post("/create", response_model=SUserProfileRead,
             summary="Creates user's profile")
async def create_user(
    profile: UserProfile,
    session: Annotated[AsyncSession, Depends(get_async_session)]
) -> SUserProfileRead:
    async with session.begin():
        created_profile = await UserProfileManager.create_user_profile(session, profile)
        return created_profile
