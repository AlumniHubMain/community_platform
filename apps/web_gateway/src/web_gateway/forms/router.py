from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.db_abstract import db_manager
from common_db.schemas.forms import FormCreate, FormRead
from common_db.schemas.matching import MatchingResultRead
from common_db.enums.forms import EFormIntentType
from typing import Annotated
import web_gateway.auth as auth
from .forms_manager import FormsManager


router = APIRouter(tags=["Forms"], prefix="/forms")


@router.post("", response_model=FormRead, summary="Create a new form")
async def create_form(
        user_id: Annotated[int, Depends(auth.current_user_id)],
        form: FormCreate,
        session: Annotated[AsyncSession, Depends(db_manager.get_session)]
) -> FormRead:
    """
    Create a new form.
    """
    form.user_id = user_id
    async with session.begin():
        created_form = await FormsManager.create_form(session, form)
        return created_form


@router.get("", response_model=FormRead, summary="Get actual form for user and intent type")
async def get_user_form(
        user_id: Annotated[int, Depends(auth.current_user_id)],
        intent_type: EFormIntentType,
        session: Annotated[AsyncSession, Depends(db_manager.get_session)]
) -> FormRead:
    """
    Get the last created form for user and selected intent type.    
    """
    return await FormsManager.get_user_form(session, user_id, intent_type)


@router.post("/match/{user_id}/{form_id}", response_model=MatchingResultRead, summary="Send form to matching")
async def match_form(
        user_id: Annotated[int, Depends(auth.current_user_id)],
        form_id: int,
        intent: EFormIntentType,
        session: Annotated[AsyncSession, Depends(db_manager.get_session)]
) -> FormRead:
    """
    Send form to matching service.
    """
    async with session.begin():
        matching_result = await FormsManager.send_match(session, user_id, form_id, intent)
        return matching_result