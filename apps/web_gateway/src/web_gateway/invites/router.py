from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import web_gateway.auth as auth
from web_gateway.invites.schemas import InviteCodeResponse
from web_gateway.invites.service import InvitesManager
from common_db.db_abstract import db_manager


router = APIRouter(tags=["Invites"], prefix="/users/me/invite")


@router.post("")
async def generate_new_code(
    session: Annotated[AsyncSession, Depends(db_manager.get_session)],
    user_id: Annotated[int, Depends(auth.current_user_id)],
) -> InviteCodeResponse:
    """
    Generate new invite code for current user
    """
    code = await InvitesManager.create_new_ref_code(session=session, user_id=user_id)
    return InviteCodeResponse(code=code)


@router.get("")
async def get_invite_code(
    session: Annotated[AsyncSession, Depends(db_manager.get_session)],
    user_id: Annotated[int, Depends(auth.current_user_id)],
) -> InviteCodeResponse:
    """
    Get current user invite code
    """
    code = await InvitesManager.get_invite_code(session=session, user_id=user_id)
    return InviteCodeResponse(code=code)
