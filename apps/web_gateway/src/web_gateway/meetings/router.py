from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.db_abstract import db_manager
from .meeting_manager import MeetingManager
from common_db.enums.meetings import EMeetingResponseStatus
from common_db.schemas.meetings import (
    MeetingRequestRead,
    MeetingRequestCreate,
    MeetingRequestUpdate,
    MeetingList,
    MeetingFilter,
    MeetingsUserLimits,
    MeetingRequestUpdateUserResponse,
)
from common_db.managers import LimitsManager
from web_gateway import auth
from web_gateway.settings import settings


router = APIRouter(tags=["Meetings"], prefix="/meetings")
session_dependency = Depends(db_manager.get_session)


@router.get(
    "/{meeting_id}", response_model=MeetingRequestRead, summary="Get meeting by ID"
)
async def get_meeting(
    meeting_id: int, 
    user_id: Annotated[int, Depends(auth.current_user_id)], 
    session: AsyncSession = session_dependency
) -> MeetingRequestRead:
    """
    Fetch a meeting by its ID along with its participants.
    """
    return await MeetingManager.get_meeting(session, user_id, meeting_id)


@router.get(
    "", response_model=MeetingList, summary="Get all user meetings by filter"
)
async def get_meeting_with_filtering(
    filter: MeetingFilter, 
    user_id: Annotated[int, Depends(auth.current_user_id)], 
    session: AsyncSession = session_dependency
) -> MeetingRequestRead:
    """
    Fetch all user meetings with filtering.
    """
    return await MeetingManager.get_meetings_with_filtering(session, user_id, filter)


@router.post(
    "/create", response_model=MeetingRequestRead, summary="Create a new meeting"
)
async def create_meeting(
    create_request: MeetingRequestCreate, 
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: AsyncSession = session_dependency
) -> MeetingRequestRead:
    """
    Create a new meeting. The organiser is specified in the request payload.
    """
    return await MeetingManager.create_meeting(session, user_id, create_request)


@router.patch(
    "/{meeting_id}", response_model=MeetingRequestRead, summary="Update meeting details by user"
)
async def update_meeting(
    meeting_id: int,
    update_request: MeetingRequestUpdate,
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: AsyncSession = session_dependency,
) -> MeetingRequestRead:
    """
    Update an existing meeting's details.
    """
    # ToDo: restrict to organizers
    # If you will change state of meeting - please add limitations check and updating here
    return await MeetingManager.update_meeting(session, meeting_id, user_id, update_request)

@router.patch(
    "/{meeting_id}/response",
    response_model=MeetingRequestRead,
    summary="Update user's meeting response",
)
async def update_user_meeting_response(
    meeting_id: int,
    request: MeetingRequestUpdateUserResponse,
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: AsyncSession = session_dependency,
) -> MeetingRequestRead:
    """
    Update a user's response status for a specific meeting.
    """
    # ToDo: restrict to the user affected and admins
    return await MeetingManager.update_user_meeting_response(
        session, meeting_id, user_id, request
    )

@router.get("/limits/user", response_model=MeetingsUserLimits, summary="Get user limits for meetings")
async def get_meetings_user_limits(
    user_id: Annotated[int, Depends(auth.current_user_id)], 
    session: AsyncSession = session_dependency
) -> MeetingsUserLimits:
    return await LimitsManager.get_user_meetings_limits(session, user_id, settings.limits)
