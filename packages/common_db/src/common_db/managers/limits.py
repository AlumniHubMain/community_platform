from common_db.schemas import SUserProfileRead, MeetingsUserLimits
from common_db.managers import UserManager

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException


class LimitsManager:

    @classmethod
    async def update_user_limits(cls, session: AsyncSession, user_id: int, limit_settings: MeetingsUserLimits) -> SUserProfileRead:
        return await UserManager.update_meetings_counters(session, user_id, limit_settings)

    @classmethod
    async def get_user_meetings_limits(cls, session: AsyncSession, user_id: int, limit_settings: MeetingsUserLimits) -> MeetingsUserLimits:
        user_profile = await LimitsManager.update_user_limits(session, user_id, limit_settings)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        limits = MeetingsUserLimits()
        limits.meetings_confirmations_limit = limit_settings.max_user_confirmed_meetings_count
        limits.meetings_pendings_limit = limit_settings.max_user_pended_meetings_count
        limits.available_meeting_pendings = user_profile.available_meetings_pendings_count
        limits.available_meeting_confirmations = user_profile.available_meetings_confirmations_count
        return limits

    @classmethod
    async def validate_user_meetings_limits(cls, session: AsyncSession, user_id: int, limit_settings: MeetingsUserLimits) -> None:
        user_limits = await LimitsManager.get_user_meetings_limits(session, user_id, limit_settings)
        if user_limits.available_meeting_confirmations == 0:
            raise HTTPException(status_code=400, detail="Exceeded the limit of confirmed meetings for user")
        
        if user_limits.available_meeting_pendings == 0:
            raise HTTPException(status_code=400, detail="Exceeded the limit of pended meetings for user")
        
        return user_limits
    
    @classmethod
    async def filter_users_by_limits(
        cls,
        session: AsyncSession,
        user_ids: list[int],
        limit_settings: MeetingsUserLimits
    ) -> list[int]:
        """Filter out users who have reached their meeting limits"""
        filtered_users = []
        for user_id in user_ids:
            try:
                await LimitsManager.validate_user_meetings_limits(session, user_id, limit_settings)
                filtered_users.append(user_id)
            except:
                continue
        return filtered_users