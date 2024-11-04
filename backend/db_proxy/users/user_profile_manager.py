from common_db import ORMUserProfile

from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .schemas import SUserProfileRead, UserProfile


class UserProfileManager:
    """
    Класс для управления профилями пользователей.
    """

    @classmethod
    async def get_user_profile(
        cls, session: AsyncSession, user_id: int
    ) -> SUserProfileRead:
        result = await session.execute(
            select(ORMUserProfile).where(ORMUserProfile.id == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        return SUserProfileRead.model_validate(profile)

    @classmethod
    async def create_user_profile(
        cls, session: AsyncSession, profile: UserProfile
    ) -> SUserProfileRead:
        profile_orm = ORMUserProfile(**profile.model_dump(exclude_unset=True, exclude_none=True))
        session.add(profile_orm)
        await session.commit()
        return SUserProfileRead.model_validate(profile_orm)
