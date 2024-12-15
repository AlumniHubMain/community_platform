from limits.config import LimitsConfig, EDefaultUserLimits
from users.schemas import SUserProfileRead
from users.user_profile_manager import UserProfileManager
from meetings.schemas import MeetingsUserLimits

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException


config_path = '/configs/limits_config.json'
config = LimitsConfig(config_path=config_path)


class LimitsManager:

    @classmethod
    async def update_user_limits(cls, session: AsyncSession, user_id: int) -> SUserProfileRead:
        return await UserProfileManager.update_meetings_counters(session, user_id, config)

    @classmethod
    async def get_user_meetings_limits(cls, session: AsyncSession, user_id: int) -> MeetingsUserLimits:
        user_profile = await LimitsManager.update_user_limits(session, user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        limits = MeetingsUserLimits()
        limits.meetings_confirmations_limit = config.get("max_user_confirmed_meetings_count", 
                                                         default=EDefaultUserLimits.MAX_CONFIRMED_MEETINGS_COUNT)
        limits.meetings_pendings_limit = config.get("max_user_pended_meetings_count", 
                                                    default=EDefaultUserLimits.MAX_PENDED_MEETINGS_COUNT)
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

        """cases
        1. Create meeting
        2. Add user to meeting
        3. Update user meeting response
        3.1 Declined -> Confirmed
        3.2 Declined -> Pended
        3.3 Pended -> Confirmed
        4. Passed meeting
        """
    