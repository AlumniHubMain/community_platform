from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.users import ORMUserProfile, ORMSpecialisation, ORMSkill
from ..schemas.users import DTOUserProfileRead, DTOSearchUser


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
        return DTOUserProfileRead.model_validate(user) if user else None

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
