from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.models import ORMUserProfile, ORMMeetingIntent, ORMLinkedInProfile
from common_db.schemas import SUserProfileRead, SMeetingIntentRead, LinkedInProfileRead


class DataLoader:
    @classmethod
    async def get_user_profile(cls, session, user_id: int) -> SUserProfileRead:
        stmt = (
            select(ORMUserProfile)
            .where(ORMUserProfile.id == user_id)
            .options(selectinload(ORMUserProfile.meeting_responses).selectinload(ORMMeetingResponse.meeting))
        )
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        return SUserProfileRead.model_validate(profile)

    @classmethod
    async def get_all_user_profiles(cls, session: AsyncSession) -> list[SUserProfileRead]:
        stmt = select(ORMUserProfile).options(
            selectinload(ORMUserProfile.meeting_responses).selectinload(ORMMeetingResponse.meeting)
        )
        result = await session.execute(stmt)
        profiles = result.scalars().all()
        return [SUserProfileRead.model_validate(p) for p in profiles]

    @classmethod
    async def get_linkedin_profile(cls, session: AsyncSession, user_id: int) -> LinkedInProfileRead:
        """Get LinkedIn profile by user ID"""
        result = await session.execute(
            select(ORMLinkedInProfile).where(ORMLinkedInProfile.users_id_fk == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        return LinkedInProfileRead.model_validate(profile)

    @classmethod
    async def get_all_linkedin_profiles(cls, session: AsyncSession) -> list[LinkedInProfileRead]:
        """Get all LinkedIn profiles"""
        result = await session.execute(select(ORMLinkedInProfile))
        profiles = result.scalars().all()
        return [LinkedInProfileRead.model_validate(p) for p in profiles]

    @classmethod
    async def get_meeting_intent(cls, session: AsyncSession, intent_id: int) -> SMeetingIntentRead:
        result = await session.execute(select(ORMMeetingIntent).where(ORMMeetingIntent.id == intent_id))
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Intent not found")
        return SMeetingIntentRead.model_validate(profile)

    @classmethod
    async def get_all_meeting_intents(cls, session: AsyncSession) -> list[SMeetingIntentRead]:
        result = await session.execute(select(ORMMeetingIntent))
        intents = result.scalars().all()
        return [SMeetingIntentRead.model_validate(i) for i in intents]
