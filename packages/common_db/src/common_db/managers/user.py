from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.users import ORMUserProfile, ORMSpecialisation, ORMInterest, ORMSkill, ORMRequestsCommunity
from ..schemas.users import (
    DTOUserProfileUpdate,
    DTOUserProfileRead,
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
    async def check_user(
            cls,
            session: AsyncSession,
            user_id: int
    ) -> DTOUserProfileRead:
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
        await cls.check_user(session, user_data.id)

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
        Get all non-custom specialisations from the database.

        Args:
            session: database session

        Returns:
            list[DTOSpecialisation]: list of all non-custom specialisations
        """
        query = select(ORMSpecialisation).filter(ORMSpecialisation.is_custom == False)
        result = await session.execute(query)
        specialisations = result.scalars().all()
        return [DTOSpecialisation.model_validate(spec) for spec in specialisations]

    @classmethod
    async def get_all_specialisations_label(
            cls,
            session: AsyncSession
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
        return [DTOSpecialisation.model_validate(spec).label for spec in specialisations]

    @classmethod
    async def get_all_interests(
            cls,
            session: AsyncSession
    ) -> list[DTOInterest]:
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
        return [DTOInterest.model_validate(interest) for interest in interests]

    @classmethod
    async def get_all_interests_label(
            cls,
            session: AsyncSession
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
        return [DTOInterest.model_validate(interest).label for interest in interests]

    @classmethod
    async def get_all_skills(
            cls,
            session: AsyncSession
    ) -> list[DTOSkill]:
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
        return [DTOSkill.model_validate(skill) for skill in skills]

    @classmethod
    async def get_all_skills_label(
            cls,
            session: AsyncSession
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
        return [DTOSkill.model_validate(skill).label for skill in skills]

    @classmethod
    async def get_all_requests_to_community(
            cls,
            session: AsyncSession
    ) -> list[DTORequestsCommunity]:
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
        return [DTORequestsCommunity.model_validate(request) for request in requests]

    @classmethod
    async def get_all_requests_to_community_label(
            cls,
            session: AsyncSession
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
        return [DTORequestsCommunity.model_validate(request).label for request in requests]
