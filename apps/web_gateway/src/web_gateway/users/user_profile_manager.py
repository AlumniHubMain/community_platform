from datetime import datetime
from common_db import ORMUserProfile
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from .schemas import SUserProfileRead, SUserProfileUpdate, UserProfile, ORMMeeting, ORMMeetingResponse, EMeetingResponseStatus
from web_gateway.settings import settings


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
    async def update_user_profile(
        cls, session: AsyncSession, profile_passed: SUserProfileUpdate) -> SUserProfileRead:
        result = await session.execute(select(ORMUserProfile).where(ORMUserProfile.id == profile_passed.id))
        profile_to_write = result.scalar_one_or_none()
        if profile_to_write is None:
            raise HTTPException(status_code=400, detail="Wrong request")

        for key, value in profile_passed.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(profile_to_write, key, value)

        await session.commit()
        return SUserProfileRead.model_validate(profile_to_write)


    @classmethod
    async def create_user_profile(
        cls, session: AsyncSession, profile: UserProfile
    ) -> SUserProfileRead:
        profile_orm = ORMUserProfile(
            **profile.model_dump(exclude_unset=True, exclude_none=True)
        )
        session.add(profile_orm)
        await session.commit()
        return SUserProfileRead.model_validate(profile_orm)
    
    @classmethod
    async def get_user_id_by_telegram_id(cls, session: AsyncSession, tg_id: int) -> int:
        result = await session.execute(
            select(ORMUserProfile.user_id).where(ORMUserProfile.telegram_id == tg_id)
        )
        user_id = result.scalar_one_or_none()
        if user_id is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        return user_id
    
    @classmethod
    async def update_meetings_counters(
        cls, session: AsyncSession, 
        user_id: int
    ) -> SUserProfileRead:
        
        # Select user meeting responses
        reponses_query = select(ORMMeetingResponse).options(selectinload(ORMMeetingResponse.meeting)) \
                         .where(ORMMeetingResponse.user_id == user_id) \
                         .join(ORMMeeting).where(ORMMeeting.scheduled_time >= datetime.now())

        result = await session.execute(reponses_query)
        responses = result.scalars().all()

        # Select user filtered meetings with all responses
        meeting_ids = tuple({response.meeting.id for response in responses})
        meetings_query = select(ORMMeeting).options(selectinload(ORMMeeting.user_responses)) \
                         .filter(ORMMeeting.id.in_(meeting_ids))

        result = await session.execute(meetings_query)
        user_meetings = result.scalars().all()
        
        # Find meetings which all users confirm
        confirmed_count = 0
        for user_meeting in user_meetings:
            # Skip meetings with only 1 user
            if len(user_meeting.user_responses) == 1:
                continue
            is_all_confirm = True
            for response in user_meeting.user_responses:
                is_all_confirm = is_all_confirm and response.response == EMeetingResponseStatus.confirmed
            confirmed_count += int(is_all_confirm)

        # Meetings with user response in (no_answer, confirmed)
        pended_count: int = len([1 for response in responses 
                                   if (response.response != EMeetingResponseStatus.declined and response.user_id == user_id)])
        
        confirmation_limit = settings.limits.max_user_confirmed_meetings_count
        pending_limit = settings.limits.max_user_pended_meetings_count

        # Try to find user profile
        result = await session.execute(select(ORMUserProfile).where(ORMUserProfile.id == user_id))
        profile_to_write = result.scalar_one_or_none()
        if profile_to_write is None:
            raise HTTPException(status_code=404, detail="User profile not found")

        # Update counters
        profile_to_write.available_meetings_pendings_count = max(0, pending_limit - pended_count)
        profile_to_write.available_meetings_confirmations_count = max(0, confirmation_limit - confirmed_count)
        
        await session.commit()
        return SUserProfileRead.model_validate(profile_to_write)
