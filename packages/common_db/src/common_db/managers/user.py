from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.users import DTOSearchUser, SUserProfileRead


class UserManager:
    """
    Manager for interacting with the user table
    """

    @classmethod
    async def search_users(
            cls,
            session: AsyncSession,
            user: DTOSearchUser
    ) -> list[SUserProfileRead]:
        query = text("""
                SELECT * FROM search_users(
                    :name,
                    :surname,
                    :location,
                    :expertise_area,
                    :specialisation,
                    :skills,
                    :limit
                )
            """)

        result = await session.execute(
            query,
            {
                "name": user.name,
                "surname": user.surname,
                "location": user.location,
                "expertise_area": user.expertise_area,
                "specialisation": user.specialisation,
                "skills": user.skills,
                "limit": user.limit
            }
        )

        users = result.unique().scalars().all()
        return [SUserProfileRead.model_validate(user) for user in users]
