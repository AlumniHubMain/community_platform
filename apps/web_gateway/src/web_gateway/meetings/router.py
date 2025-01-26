from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.db_abstract import db_manager
from .meeting_manager import MeetingManager
from .schemas import (
    MeetingRequestRead,
    MeetingRequestCreate,
    MeetingRequestUpdate,
    MeetingList,
    MeetingsUserLimits,
    EMeetingResponseStatus,
    MeetingsFilter
)
from web_gateway.limits.limits_manager import LimitsManager


router = APIRouter(tags=["Meetings"], prefix="/meetings")
session_dependency = Depends(db_manager.get_session)


@router.get(
    "/{meeting_id}", response_model=MeetingRequestRead, summary="Get meeting by ID"
)
async def get_meeting(
    meeting_id: int, session: AsyncSession = session_dependency
) -> MeetingRequestRead:
    """
    Fetch a meeting by its ID along with its participants.
    """
    return await MeetingManager.get_meeting(session, meeting_id)


@router.get(
    "", response_model=MeetingList, summary="Get all user meetings"
)
async def get_meeting_with_filtering(
    filter: MeetingsFilter, session: AsyncSession = session_dependency
) -> MeetingRequestRead:
    """
    Fetch all user meetings with filtering.
    """
    return await MeetingManager.get_meetings_with_filtering(session, filter)


@router.post(
    "/create", response_model=MeetingRequestRead, summary="Create a new meeting"
)
async def create_meeting(
    create_request: MeetingRequestCreate, session: AsyncSession = session_dependency
) -> MeetingRequestRead:
    """
    Create a new meeting. The organiser is specified in the request payload.
    """
    return await MeetingManager.create_meeting(session, create_request)


@router.patch(
    "/{meeting_id}/user/{user_id}", response_model=MeetingRequestRead, summary="Update meeting details by user"
)
async def update_meeting(
    meeting_id: int,
    user_id: int,
    update_request: MeetingRequestUpdate,
    session: AsyncSession = session_dependency,
) -> MeetingRequestRead:
    """
    Update an existing meeting's details.
    """
    # ToDo: restrict to organizers
    # If you will change state of meeting - please add limitations check and updating here
    return await MeetingManager.update_meeting(session, meeting_id, user_id, update_request)

@router.patch(
    "/{meeting_id}/user/{user_id}/response",
    response_model=MeetingRequestRead,
    summary="Update user's meeting response",
)
async def update_user_meeting_response(
    meeting_id: int,
    user_id: int,
    status: EMeetingResponseStatus,
    session: AsyncSession = session_dependency,
) -> MeetingRequestRead:
    """
    Update a user's response status for a specific meeting.
    """
    # ToDo: restrict to the user affected and admins
    return await MeetingManager.update_user_meeting_response(
        session, meeting_id, user_id, status
    )

@router.get("/limits/user", response_model=MeetingsUserLimits, summary="Get user limits for meetings")
async def get_meetings_user_limits(user_id: int, session: AsyncSession = session_dependency) -> MeetingsUserLimits:
    return await LimitsManager.get_user_meetings_limits(session, user_id)
