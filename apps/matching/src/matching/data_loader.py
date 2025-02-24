from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.models import (
    ORMUserProfile, 
    ORMLinkedInProfile,
    ORMForm,
    ORMMeetingResponse,
)
from common_db.schemas import (
    SUserProfileRead,
    LinkedInProfileRead,
    FormRead,
    DTOUserProfile,
)


class DataLoader:
    @classmethod
    async def get_user_profile(cls, session, user_id: int) -> SUserProfileRead:
        """Get user profile by ID with all needed relationships"""
        stmt = (
            select(ORMUserProfile)
            .where(ORMUserProfile.id == user_id)
            .options(
                selectinload(ORMUserProfile.meeting_responses).selectinload(ORMMeetingResponse.meeting),
                selectinload(ORMUserProfile.linkedin_profile),
                selectinload(ORMUserProfile.specialisations),
                selectinload(ORMUserProfile.skills),
                selectinload(ORMUserProfile.user_specialisations),
                selectinload(ORMUserProfile.industries),
                selectinload(ORMUserProfile.interests)
            )
        )
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Use the new from_orm method for ORM instances, or model_validate for mock data
        if hasattr(profile, '__table__'):  # Check if it's an ORM instance
            return SUserProfileRead.from_orm(profile)
        return SUserProfileRead.model_validate(profile)  # For mock data

    @classmethod
    async def get_all_user_profiles(cls, session: AsyncSession) -> list[SUserProfileRead]:
        """Get all user profiles with all needed relationships"""
        stmt = select(ORMUserProfile).options(
            selectinload(ORMUserProfile.meeting_responses).selectinload(ORMMeetingResponse.meeting),
            selectinload(ORMUserProfile.linkedin_profile),
            selectinload(ORMUserProfile.specialisations),
            selectinload(ORMUserProfile.skills),
            selectinload(ORMUserProfile.user_specialisations)
        )
        result = await session.execute(stmt)
        profiles = result.scalars().all()
        
        # Convert all profiles with additional data
        return [await cls.get_user_profile(session, p.id) for p in profiles]

    @classmethod
    async def get_linkedin_profile(cls, session: AsyncSession, user_id: int) -> LinkedInProfileRead:
        """Get LinkedIn profile by user ID"""
        result = await session.execute(
            select(ORMLinkedInProfile).where(ORMLinkedInProfile.users_id_fk == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        return LinkedInProfileRead.model_validate(profile)

    @classmethod
    async def get_all_linkedin_profiles(cls, session: AsyncSession) -> list[LinkedInProfileRead]:
        """Get all LinkedIn profiles"""
        result = await session.execute(select(ORMLinkedInProfile))
        profiles = result.scalars().all()
        return [LinkedInProfileRead.model_validate(p) for p in profiles]

    @classmethod
    async def get_form(cls, session: AsyncSession, form_id: int) -> FormRead:
        """Get form by ID"""
        result = await session.execute(
            select(ORMForm).where(ORMForm.id == form_id)
        )
        form = result.scalar_one_or_none()
        if form is None:
            raise HTTPException(status_code=404, detail="Form not found")
        return FormRead.model_validate(form)

    @classmethod
    async def get_all_forms(cls, session: AsyncSession) -> list[FormRead]:
        """Get all forms"""
        result = await session.execute(select(ORMForm))
        forms = result.scalars().all()
        return [FormRead.model_validate(f) for f in forms]
