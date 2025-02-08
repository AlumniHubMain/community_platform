from common_db.schemas.forms import INTENT_TO_SCHEMA, FormCreate, FormRead, EFormIntentType
from common_db.enums.forms import EFormIntentType
from common_db.models import ORMForm, ORMUserProfile
from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from pydantic import ValidationError


class FormsManager:
    """
    Класс для управления анкетами пользователей.
    """

    @classmethod
    async def validate_form_schema(cls, schema, content):
        try:
            _ = schema.model_validate(content, from_attributes=True)
        except ValidationError as e:
            error_desc = {}
            for error in e.errors():
                for key, value in error.items():
                    if key == 'type':
                        error_desc['error_type'] = value
                    elif key == 'loc':
                        error_desc['field'] = value
                    elif key == 'msg':
                        error_desc['message'] = value
                break
            raise HTTPException(status_code=400, detail=error_desc)
    
    @classmethod
    async def check_user_exists(cls, session: AsyncSession, user_id: int):
        user: ORMUserProfile | None = await session.get(
            ORMUserProfile, user_id
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
    @classmethod
    async def get_user_form(
        cls, session: AsyncSession, user_id: int, intent_type: EFormIntentType
    ) -> FormRead:

        await cls.check_user_exists(session, user_id)
        
        # Select one last form by User and Intent type.
        result = await session.execute(
            select(ORMForm)
            .where(ORMForm.user_id == user_id)
            .where(ORMForm.intent == intent_type)
            .order_by(desc("created_at"))
            .limit(1)
        )
        form_orm = result.scalar_one_or_none()
        if form_orm is None:
            raise HTTPException(status_code=404, detail="Form not found")
        return FormRead.model_validate(form_orm)

    @classmethod
    async def create_form(
        cls, session: AsyncSession, form: FormCreate
    ) -> FormRead:
        
        """mock_interview
        {
            "interview_type": ["technical", "behavioral", "role"] <- list,
            "possible_english_interview": bool,
            "resume_from_profile": bool,
            "resume_link": Text,
            "job_link": Text,
            "comment": Text
        }
        """
        """help_requests
        {
            "subtype": ["question", "assistance"],
            "query_area": [...] <- list,
            "query_area_details": "Text",
            (opt)"query_text": Text,
            (opt)"file_link": Text
        }
        """
        
        await cls.check_user_exists(session, form.user_id)
        
        if not (form.intent in INTENT_TO_SCHEMA):
            raise HTTPException(status_code=400, detail="Unknown intent type")
        schema = INTENT_TO_SCHEMA[form.intent]
        
        await cls.validate_form_schema(schema, form.content)
        
        form_orm = ORMForm(
            **form.model_dump(exclude_unset=True, exclude_none=True)
        )
        session.add(form_orm)
        await session.commit()
        return FormRead.model_validate(form_orm)
