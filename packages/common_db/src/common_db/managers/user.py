from datetime import datetime
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from ..db_abstract import db_manager
from ..enums import EMeetingResponseStatus
from ..models import (
    ORMUserProfile,
    ORMSpecialisation,
    ORMUserSpecialisation,
    ORMInterest,
    ORMSkill,
    ORMRequestsCommunity,
    ORMMeeting,
    ORMMeetingResponse,
    ORMReferralCode
)
from ..models.linkedin import ORMLinkedInProfile
from ..schemas import (
    DTOUserProfile,
    DTOUserProfileUpdate,
    DTOUserProfileRead,
    DTOSpecialisationRead,
    DTOInterestRead,
    DTOSkillRead,
    DTORequestsCommunityRead,
    DTOSearchUser,
    SUserProfileRead,
    MeetingsUserLimits,
)


class UserManager:
    """
    Manager for interacting with the user table
    """

    @classmethod
    async def check_user(
            cls,
            user_id: int,
            session: AsyncSession = db_manager.get_session()
    ) -> JSONResponse:
        """
        Check user by id.

        Args:
            session: database session
            user_id: user identifier

        Returns:
            JSONResponse: response with status and created user id
        Raise:
            HTTPException 404 if not found
        """
        result = await session.execute(select(ORMUserProfile).where(ORMUserProfile.id == user_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Not found")
        return JSONResponse(
            content={
                "status": "success"
            },
            status_code=status.HTTP_200_OK
        )

    @classmethod
    async def get_user_by_id(
            cls,
            user_id: int,
            session: AsyncSession = db_manager.get_session()
    ) -> DTOUserProfileRead:
        """
        Get user by id.

        Args:
            session: database session
            user_id: user identifier

        Returns:
            DTOUserProfileRead: user data
        Raise:
            HTTPException 404 if not found
        """
        query = (
            select(ORMUserProfile)
            .options(
                selectinload(ORMUserProfile.interests),
                selectinload(ORMUserProfile.industries),
                selectinload(ORMUserProfile.skills),
                selectinload(ORMUserProfile.requests_to_community),
                selectinload(ORMUserProfile.meeting_responses),
                selectinload(ORMUserProfile.user_specialisations)
                .joinedload(ORMUserSpecialisation.specialisation),
                joinedload(ORMUserProfile.referrer),
                selectinload(ORMUserProfile.referred),
                # for linkedin
                selectinload(ORMUserProfile.linkedin_profile)
                .selectinload(ORMLinkedInProfile.education),
                selectinload(ORMUserProfile.linkedin_profile)
                .selectinload(ORMLinkedInProfile.work_experience)
            )
            .where(ORMUserProfile.id == user_id)
        )

        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Not found")
        return DTOUserProfileRead.model_validate(user)

    @classmethod
    async def create_user(
            cls,
            user_data: DTOUserProfile,
            session: AsyncSession = db_manager.get_session()
    ) -> JSONResponse:
        """
        Create a new user in the database.

        Args:
            session: database session
            user_data: user data for creation

        Returns:
            JSONResponse: response with status and created user id
        """
        user = ORMUserProfile(**user_data.model_dump(exclude_unset=True, exclude_none=True))
        session.add(user)
        await session.flush()
        await session.commit()
        return JSONResponse(
            content={
                "status": "success",
                "message": "Create successfully",
                "user_id": user.id
            },
            status_code=status.HTTP_201_CREATED
        )

    @classmethod
    async def update_user(
            cls,
            user_data: DTOUserProfileUpdate,
            session: AsyncSession = db_manager.get_session()
    ) -> JSONResponse:
        """
        Update existing user in the database.

        Args:
            session: database session
            user_data: user data for update

        Returns:
            JSONResponse: response with status and updated user id
        """
        await cls.check_user(session=session, user_id=user_data.id)

        await session.execute(update(ORMUserProfile)
                              .where(ORMUserProfile.id == user_data.id)
                              .values(**user_data.model_dump(exclude_unset=True, exclude_none=True)))

        await session.flush()
        await session.commit()
        return JSONResponse(
            content={
                "status": "success",
                "message": "Updated successfully",
                "user_id": user_data.id
            },
            status_code=status.HTTP_200_OK
        )

    @classmethod
    async def get_user_by_tg_id(
            cls,
            user_tg_id: int,
            session: AsyncSession = db_manager.get_session()
    ) -> DTOUserProfileRead:
        """
        Get user by id.

        Args:
            session: database session
            user_tg_id: user identifier

        Returns:
            DTOUserProfileRead: user data
        Raise:
            HTTPException 404 if not found
        """
        query = (
            select(ORMUserProfile)
            .options(
                selectinload(ORMUserProfile.interests),
                selectinload(ORMUserProfile.industries),
                selectinload(ORMUserProfile.skills),
                selectinload(ORMUserProfile.requests_to_community),
                selectinload(ORMUserProfile.meeting_responses),
                selectinload(ORMUserProfile.user_specialisations)
                .joinedload(ORMUserSpecialisation.specialisation),
                joinedload(ORMUserProfile.referrer),
                selectinload(ORMUserProfile.referred),
                # for linkedin
                selectinload(ORMUserProfile.linkedin_profile)
                .joinedload(ORMLinkedInProfile.education),
                selectinload(ORMUserProfile.linkedin_profile)
                .joinedload(ORMLinkedInProfile.work_experience)
            )
            .where(ORMUserProfile.telegram_id == user_tg_id)
        )

        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Not found")
        return DTOUserProfileRead.model_validate(user)

    @classmethod
    async def get_all_specialisations(
            cls,
            session: AsyncSession = db_manager.get_session()
    ) -> list[DTOSpecialisationRead]:
        """
        Get all non-custom specialisations from the database.

        Args:
            session: database session

        Returns:
            list[DTOSpecialisation]: list of all non-custom specialisations
        """
        query = select(ORMSpecialisation).filter(ORMSpecialisation.is_custom == False)
        result = await session.execute(query)
        specialisations = result.scalars().all()
        return [DTOSpecialisationRead.model_validate(spec) for spec in specialisations]

    @classmethod
    async def get_all_specialisations_label(
            cls,
            session: AsyncSession = db_manager.get_session()
    ) -> list[str]:
        """
        Get all labels of non-custom specialisations from the database.

        Args:
            session: database session

        Returns:
            list[DTOSpecialisation]: list of all labels of non-custom specialisations
        """
        query = select(ORMSpecialisation).filter(ORMSpecialisation.is_custom == False)
        result = await session.execute(query)
        specialisations = result.scalars().all()
        return [DTOSpecialisationRead.model_validate(spec).label for spec in specialisations]

    @classmethod
    async def get_all_interests(
            cls,
            session: AsyncSession = db_manager.get_session()
    ) -> list[DTOInterestRead]:
        """
        Get all non-custom interests from the database.

        Args:
            session: database session

        Returns:
            list[DTOInterest]: list of all non-custom interests
        """
        query = select(ORMInterest).filter(ORMInterest.is_custom == False)
        result = await session.execute(query)
        interests = result.scalars().all()
        return [DTOInterestRead.model_validate(interest) for interest in interests]

    @classmethod
    async def get_all_interests_label(
            cls,
            session: AsyncSession = db_manager.get_session()
    ) -> list[str]:
        """
        Get all labels of non-custom interests from the database.

        Args:
            session: database session

        Returns:
            list[DTOInterest]: list of all labels of non-custom interests
        """
        query = select(ORMInterest).filter(ORMInterest.is_custom == False)
        result = await session.execute(query)
        interests = result.scalars().all()
        return [DTOInterestRead.model_validate(interest).label for interest in interests]

    @classmethod
    async def get_all_skills(
            cls,
            session: AsyncSession = db_manager.get_session()
    ) -> list[DTOSkillRead]:
        """
        Get all non-custom skills from the database.

        Args:
            session: database session

        Returns:
            list[DTOSkill]: list of all non-custom skills
        """
        query = select(ORMSkill).filter(ORMSkill.is_custom == False)
        result = await session.execute(query)
        skills = result.scalars().all()
        return [DTOSkillRead.model_validate(skill) for skill in skills]

    @classmethod
    async def get_all_skills_label(
            cls,
            session: AsyncSession = db_manager.get_session()
    ) -> list[str]:
        """
        Get all labels of non-custom skills from the database.

        Args:
            session: database session

        Returns:
            list[str]: list of all labels of non-custom skills
        """
        query = select(ORMSkill).filter(ORMSkill.is_custom == False)
        result = await session.execute(query)
        skills = result.scalars().all()
        return [DTOSkillRead.model_validate(skill).label for skill in skills]

    @classmethod
    async def get_all_requests_to_community(
            cls,
            session: AsyncSession = db_manager.get_session()
    ) -> list[DTORequestsCommunityRead]:
        """
        Get all non-custom requests to community from the database.

        Args:
            session: database session

        Returns:
            list[DTORequestsCommunity]: list of all non-custom requests to community
        """
        query = select(ORMRequestsCommunity).filter(ORMRequestsCommunity.is_custom == False)
        result = await session.execute(query)
        requests = result.scalars().all()
        return [DTORequestsCommunityRead.model_validate(request) for request in requests]

    @classmethod
    async def get_all_requests_to_community_label(
            cls,
            session: AsyncSession = db_manager.get_session()
    ) -> list[str]:
        """
        Get all labels of non-custom requests to community from the database.

        Args:
            session: database session

        Returns:
            list[str]: list of all labels of non-custom requests to community
        """
        query = select(ORMRequestsCommunity).filter(ORMRequestsCommunity.is_custom == False)
        result = await session.execute(query)
        requests = result.scalars().all()
        return [DTORequestsCommunityRead.model_validate(request).label for request in requests]

    @classmethod
    async def search_users(
            cls,
            user_id: int,
            search_params: DTOSearchUser,
            session: AsyncSession = db_manager.get_session()
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

        await cls.check_user(session=session, user_id=user_id)

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

    @classmethod
    async def update_meetings_counters(
            cls, session: AsyncSession,
            user_id: int,
            limit_settings: MeetingsUserLimits
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
                                 if (response.response != EMeetingResponseStatus.declined
                                     and response.user_id == user_id)])
        confirmation_limit = limit_settings.max_user_confirmed_meetings_count
        pending_limit = limit_settings.max_user_pended_meetings_count

        # Try to find user profile
        result = await session.execute(select(ORMUserProfile).where(ORMUserProfile.id == user_id))
        profile_to_write = result.scalar_one_or_none()
        if profile_to_write is None:
            raise HTTPException(status_code=404, detail="User profile not found")

        # Update counters
        profile_to_write.available_meetings_pendings_count = max(0, pending_limit - pended_count)
        profile_to_write.available_meetings_confirmations_count = max(0, confirmation_limit - confirmed_count)

        await session.commit()
        return DTOUserProfileRead.model_validate(profile_to_write).to_old_schema()

    @classmethod
    async def get_user_id_by_referral_code(
            cls,
            user_id: int,
            code: str,
            session: AsyncSession = db_manager.get_session()
    ) -> int:
        """
        Get user id by referral code.

        Args:
            user_id: user ID of the verified user
            code: referral code
            session: database session

        Returns:
            int: user identifier

        Raises:
            HTTPException 404: if code not found or inactive
        """
        await cls.check_user(session=session, user_id=user_id)

        query = select(ORMReferralCode).where(
            and_(
                ORMReferralCode.code == code.strip(),
                ORMReferralCode.is_active == True
            )
        )
        
        result = await session.execute(query)
        referral_code = result.scalar_one_or_none()
        
        if not referral_code:
            raise HTTPException(status_code=404, detail="Not found")

        return referral_code.user_id
