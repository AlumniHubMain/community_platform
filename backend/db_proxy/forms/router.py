from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common_db import get_async_session
from .schemas import Form, SFormRead, EIntentType
from typing import Annotated
from forms_manager import FormsManager


router = APIRouter(tags=["Forms"], prefix="/forms")


@router.post("", response_model=SFormRead, summary="Create a new form")
async def create_form(
        form: Form,
        session: Annotated[AsyncSession, Depends(get_async_session)]
) -> SFormRead:
    """
    Create a new form.
    """
    async with session.begin():
        created_form = await FormsManager.create_form(session, form)
        return created_form


@router.get("", response_model=SFormRead, summary="Get actual form for user and intent type")
async def get_user_form(
        user_id: int,
        intent_type: str,
        session: Annotated[AsyncSession, Depends(get_async_session)]
) -> SFormRead:
    """
    Get the last created form for user and selected intent type.    
    """
    return await FormsManager.get_user_form(session, user_id, EIntentType(intent_type))
