from .schemas import Form, SFormRead, EIntentType
from common_db.models import ORMForm
from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc


class FormsManager:
    """
    Класс для управления анкетами пользователей.
    """

    @classmethod
    async def get_user_form(
        cls, session: AsyncSession, user_id: int, intent_type: EIntentType
    ) -> SFormRead:
        # Select one last form by User and Intent type.
        result = await session.execute(
            select(ORMForm)
            .where(ORMForm.user_id == user_id)
            .where(ORMForm.intent_type == intent_type)
            .order_by(desc("created_at"))
            .limit(1)
        )
        form_orm = result.scalar_one_or_none()
        if form_orm is None:
            raise HTTPException(status_code=404, detail="Form not found")
        return SFormRead.model_validate(form_orm)

    @classmethod
    async def create_form(
        cls, session: AsyncSession, form: Form
    ) -> SFormRead:
        form_orm = ORMForm(
            **form.model_dump(exclude_unset=True, exclude_none=True)
        )
        session.add(form_orm)
        await session.commit()
        return SFormRead.model_validate(form_orm)
