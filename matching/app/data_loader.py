
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.common_db import ORMUserProfile, ORMLinkedInProfile, ORMMeetingIntents
from app.common_db.schemas import SUserProfileRead, SLinkedInProfileRead, SMeetingIntentRead


class DataLoader:

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
    async def get_linkedin_profile(
        cls, session: AsyncSession, user_id: int
    ) -> SLinkedInProfileRead:
        result = await session.execute(
            select(ORMLinkedInProfile).where(ORMLinkedInProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        return SLinkedInProfileRead.model_validate(profile)
    
    @classmethod
    async def get_meeting_intent(
        cls, session: AsyncSession, intent_id: int
    ) -> SMeetingIntentRead:
        result = await session.execute(
            select(ORMMeetingIntents).where(ORMMeetingIntents.id == intent_id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        return SMeetingIntentRead.model_validate(profile)
    
