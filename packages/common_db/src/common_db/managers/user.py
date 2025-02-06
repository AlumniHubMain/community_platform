from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.users import ORMUserProfile, ORMSpecialisation, ORMInterest, ORMSkill, ORMRequestsCommunity
from ..schemas.users import (
    DTOUserProfile,
    DTOUserProfileUpdate,
    DTOUserProfileRead,
    DTOSearchUser,
    DTOSpecialisation,
    DTOInterest,
    DTOSkill,
    DTORequestsCommunity
)


class UserManager:
    """
    Manager for interacting with the user table
    """

    @classmethod
    async def get_user_by_id(
            cls,
            session: AsyncSession,
            user_id: int
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
                selectinload(ORMUserProfile.specialisations),
                selectinload(ORMUserProfile.interests),
                selectinload(ORMUserProfile.industries),
                selectinload(ORMUserProfile.skills),
                selectinload(ORMUserProfile.requests_to_community),
                selectinload(ORMUserProfile.meeting_responses)
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
            session: AsyncSession,
            user_data: DTOUserProfile
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
            session: AsyncSession,
            user_data: DTOUserProfileUpdate
    ) -> JSONResponse:
        """
        Update existing user in the database.

        Args:
            session: database session
            user_data: user data for update

        Returns:
            JSONResponse: response with status and updated user id
        """
        user = await cls.get_user_by_id(session, user_data.id)

        await session.execute(update(ORMUserProfile)
                              .where(ORMUserProfile.id == user_data.id)
                              .values(**user_data.model_dump(exclude_unset=True, exclude_none=True)))

        await session.flush()
        await session.commit()
        return JSONResponse(
            content={
                "status": "success",
                "message": "Updated successfully",
                "user_id": user.id
            },
            status_code=status.HTTP_200_OK
        )

    @classmethod
    async def get_user_by_tg_id(
            cls,
            session: AsyncSession,
            user_tg_id: int
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
                selectinload(ORMUserProfile.specialisations),
                selectinload(ORMUserProfile.interests),
                selectinload(ORMUserProfile.industries),
                selectinload(ORMUserProfile.skills),
                selectinload(ORMUserProfile.requests_to_community),
                selectinload(ORMUserProfile.meeting_responses)
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
            session: AsyncSession
    ) -> list[DTOSpecialisation]:
        """
        Get all specialisations from the database.

        Args:
            session: database session

        Returns:
            list[DTOSpecialisation]: list of all specialisations
        """
        query = select(ORMSpecialisation)
        result = await session.execute(query)
        specialisations = result.scalars().all()
        return [DTOSpecialisation.model_validate(spec) for spec in specialisations]

    @classmethod
    async def get_all_specialisations_label(
            cls,
            session: AsyncSession
    ) -> list[str]:
        """
        Get all labels of specialisations from the database.

        Args:
            session: database session

        Returns:
            list[DTOSpecialisation]: list of all labels of specialisations
        """
        query = select(ORMSpecialisation).filter(ORMSpecialisation.is_custom == False)
        result = await session.execute(query)
        specialisations = result.scalars().all()
        return [DTOSpecialisation.model_validate(spec).label for spec in specialisations]

    @classmethod
    async def get_all_interests(
            cls,
            session: AsyncSession
    ) -> list[DTOInterest]:
        """
        Get all interests from the database.

        Args:
            session: database session

        Returns:
            list[DTOInterest]: list of all interests
        """
        query = select(ORMInterest)
        result = await session.execute(query)
        interests = result.scalars().all()
        return [DTOInterest.model_validate(interest) for interest in interests]

    @classmethod
    async def get_all_interests_label(
            cls,
            session: AsyncSession
    ) -> list[str]:
        """
        Get all labels of interests from the database.

        Args:
            session: database session

        Returns:
            list[DTOInterest]: list of all labels of interests
        """
        query = select(ORMInterest).filter(ORMInterest.is_custom == False)
        result = await session.execute(query)
        interests = result.scalars().all()
        return [DTOInterest.model_validate(interest).label for interest in interests]

    @classmethod
    async def get_all_skills(
            cls,
            session: AsyncSession
    ) -> list[DTOSkill]:
        """
        Get all skills from the database.

        Args:
            session: database session

        Returns:
            list[DTOSkill]: list of all skills
        """
        query = select(ORMSkill)
        result = await session.execute(query)
        skills = result.scalars().all()
        return [DTOSkill.model_validate(skill) for skill in skills]

    @classmethod
    async def get_all_skills_label(
            cls,
            session: AsyncSession
    ) -> list[str]:
        """
        Get all labels of skills from the database.

        Args:
            session: database session

        Returns:
            list[str]: list of all labels of skills
        """
        query = select(ORMSkill).filter(ORMSkill.is_custom == False)
        result = await session.execute(query)
        skills = result.scalars().all()
        return [DTOSkill.model_validate(skill).label for skill in skills]

    @classmethod
    async def get_all_requests_to_community(
            cls,
            session: AsyncSession
    ) -> list[DTORequestsCommunity]:
        """
        Get all requests to community from the database.

        Args:
            session: database session

        Returns:
            list[DTORequestsCommunity]: list of all requests to community
        """
        query = select(ORMRequestsCommunity)
        result = await session.execute(query)
        requests = result.scalars().all()
        return [DTORequestsCommunity.model_validate(request) for request in requests]

    @classmethod
    async def get_all_requests_to_community_label(
            cls,
            session: AsyncSession
    ) -> list[str]:
        """
        Get all labels of requests to community from the database.

        Args:
            session: database session

        Returns:
            list[str]: list of all labels of requests to community
        """
        query = select(ORMRequestsCommunity).filter(ORMSkill.is_custom == False)
        result = await session.execute(query)
        requests = result.scalars().all()
        return [DTORequestsCommunity.model_validate(request).label for request in requests]

    @classmethod
    async def search_users(
            cls,
            session: AsyncSession,
            search_params: DTOSearchUser
    ) -> list[DTOUserProfileRead]:
        """
            Search for users by the specified parameters.

            Args:
                search_params: search parameters (DTOSearchUser)
                session: database session

            Returns:
                list[DTOUserProfileRead]: the list of found users
            """
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
