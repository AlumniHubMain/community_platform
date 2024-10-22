from common_db import ORMUserProfile

from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .schemas import SUserProfileRead


class UserProfileManager:
    """
    Класс для управления профилями пользователей.
    """

    @classmethod
    async def get_user_profile(
            cls,
            session: AsyncSession,
            user_id: int
    ) -> SUserProfileRead:
        result = await session.execute(select(ORMUserProfile).where(ORMUserProfile.id == user_id))
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        return SUserProfileRead.from_orm(profile)
