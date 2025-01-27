import os

from common_db.schemas import SUserProfileRead, MeetingsUserLimits
from web_gateway.users.user_profile_manager import UserProfileManager

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from web_gateway.settings import settings


class LimitsManager:

    @classmethod
    async def update_user_limits(cls, session: AsyncSession, user_id: int) -> SUserProfileRead:
        return await UserProfileManager.update_meetings_counters(session, user_id)

    @classmethod
    async def get_user_meetings_limits(cls, session: AsyncSession, user_id: int) -> MeetingsUserLimits:
        user_profile = await LimitsManager.update_user_limits(session, user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        limits = MeetingsUserLimits()
        limits.meetings_confirmations_limit = settings.limits.max_user_confirmed_meetings_count
        limits.meetings_pendings_limit = settings.limits.max_user_pended_meetings_count
        limits.available_meeting_pendings = user_profile.available_meetings_pendings_count
        limits.available_meeting_confirmations = user_profile.available_meetings_confirmations_count
        return limits

    @classmethod
    async def validate_user_meetings_limits(cls, session: AsyncSession, user_id: int) -> None:
        user_limits = await LimitsManager.get_user_meetings_limits(session, user_id)
        if user_limits.available_meeting_confirmations == 0:
            raise HTTPException(status_code=400, detail="Exceeded the limit of confirmed meetings for user")
        
        if user_limits.available_meeting_pendings == 0:
            raise HTTPException(status_code=400, detail="Exceeded the limit of pended meetings for user")
