from datetime import datetime

from common_db.enums import EMeetingResponseStatus
from common_db.managers.user import UserManager
from common_db.models import ORMUserProfile, ORMMeeting, ORMMeetingResponse, ORMSpecialisation, ORMSkill
from common_db.schemas import DTOSearchUser, DTOUserProfileRead

from fastapi import HTTPException
from sqlalchemy import and_

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from .schemas import SUserProfileRead
from web_gateway.settings import settings


class UserProfileManager(UserManager):
    """
    A class for managing user profiles.
    """
    
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

    @classmethod
    async def search_users(
            cls,
            user_id: int,
            session: AsyncSession,
            search_params: DTOSearchUser
    ) -> list[DTOUserProfileRead]:
        """
            Search for users by the specified parameters.

            Args:
                user_id: user ID of the verified user
                search_params: search parameters (DTOSearchUser)
                session: database session

            Returns:
                list[DTOUserProfileRead]: the list of found users
            """

        await cls.check_user(session=session, user_id=verified_user_id)

        query = (
            select(ORMUserProfile)
            .options(
                selectinload(ORMUserProfile.specialisations),
                selectinload(ORMUserProfile.skills)
            )
        )

        # Creating a list of conditions
        conditions = []

        if search_params.name:
            conditions.append(ORMUserProfile.name.ilike(f"%{search_params.name}%"))

        if search_params.surname:
            conditions.append(ORMUserProfile.surname.ilike(f"%{search_params.surname}%"))

        if search_params.country:
            conditions.append(ORMUserProfile.country.ilike(f"%{search_params.country}%"))

        if search_params.city:
            conditions.append(ORMUserProfile.city.ilike(f"%{search_params.city}%"))

        # To search by expertise_area or specialisation, need to join with the specialisation table.
        if search_params.expertise_area or search_params.specialisation:
            query = query.join(
                ORMUserProfile.specialisations
            )

            # To search by expertise_area
            if search_params.expertise_area:
                conditions.append(ORMSpecialisation.expertise_area.ilike(f"%{search_params.expertise_area}%"))

            # To search by specialization
            if search_params.specialisation:
                conditions.append(ORMSpecialisation.label.ilike(f"%{search_params.specialisation}%"))

        # To search by skills
        if search_params.skill:
            query = query.join(
                ORMUserProfile.skills
            )
            conditions.append(ORMSkill.label.ilike(f"%{search_params.skill}%"))

        # Adding all the conditions to the request using and_
        if conditions:
            query = query.where(and_(*conditions))

        # Adding a limit
        query = query.limit(search_params.limit)

        # Executing the request
        result = await session.execute(query)
        users = result.scalars().unique().all()
        return [DTOUserProfileRead.model_validate(user) for user in users]
