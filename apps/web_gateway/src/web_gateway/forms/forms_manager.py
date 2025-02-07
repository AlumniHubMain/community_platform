from common_db.schemas.forms import FormBase, FormRead, EFormQueryType
from common_db.models import ORMForm, ORMUserProfile
from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc


class FormsManager:
    """
    Класс для управления анкетами пользователей.
    """

    @classmethod
    async def check_user_exists(cls, session: AsyncSession, user_id: int):
        user: ORMUserProfile | None = await session.get(
            ORMUserProfile, user_id
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
    @classmethod
    async def get_user_form(
        cls, session: AsyncSession, user_id: int, query_type: EFormQueryType
    ) -> FormRead:

        await cls.check_user_exists(session, user_id)
        
        # Select one last form by User and Intent type.
        result = await session.execute(
            select(ORMForm)
            .where(ORMForm.user_id == user_id)
            .where(ORMForm.query_type == query_type)
            .order_by(desc("created_at"))
            .limit(1)
        )
        form_orm = result.scalar_one_or_none()
        if form_orm is None:
            raise HTTPException(status_code=404, detail="Form not found")
        return FormRead.model_validate(form_orm)

    @classmethod
    async def create_form(
        cls, session: AsyncSession, form: FormBase
    ) -> FormRead:
        
        await cls.check_user_exists(session, form.user_id)
        
        form_orm = ORMForm(
            **form.model_dump(exclude_unset=True, exclude_none=True)
        )
        session.add(form_orm)
        await session.commit()
        return FormRead.model_validate(form_orm)
