from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from common_db import get_async_session
from .schemas import SMeetingRequestRead, MeetingRequestCreate
from .meeting_manager import MeetingManager

router = APIRouter(tags=["Meetings"], prefix="/meetings")


@router.get("/{meeting_id}", response_model=SMeetingRequestRead, summary="Get meeting by ID")
async def get_meeting(
    meeting_id: int, session: AsyncSession = Depends(get_async_session)
) -> SMeetingRequestRead:
    """
    Fetch a meeting by its ID along with its participants.
    """
    return await MeetingManager.get_meeting(session, meeting_id)


@router.post("/create", response_model=SMeetingRequestRead, summary="Create a new meeting")
async def create_meeting(
    request: MeetingRequestCreate,
    session: AsyncSession = Depends(get_async_session)
) -> SMeetingRequestRead:
    """
    Create a new meeting. The organiser is specified in the request payload.
    """
    return await MeetingManager.create_meeting(session, request)


@router.patch("/{meeting_id}", response_model=SMeetingRequestRead, summary="Update meeting details")
async def update_meeting(
    meeting_id: int,
    request: MeetingRequestCreate,
    session: AsyncSession = Depends(get_async_session)
) -> SMeetingRequestRead:
    """
    Update an existing meeting's details.
    """
    return await MeetingManager.update_meeting(session, meeting_id, request)


@router.get("", response_model=List[SMeetingRequestRead], summary="Get all meetings")
async def get_all_meetings(
    session: AsyncSession = Depends(get_async_session)
) -> List[SMeetingRequestRead]:
    """
    Get a list of all meetings.
    """
    return await MeetingManager.get_all_meetings(session)


@router.post("/{meeting_id}/add_user", status_code=204, summary="Add user to a meeting")
async def add_user_to_meeting(
    meeting_id: int,
    user_id: int,
    role: str = "attendee",
    session: AsyncSession = Depends(get_async_session)
) -> None:
    """
    Add a user to a meeting with a specified role.
    """
    await MeetingManager.add_user_to_meeting(session, user_id, meeting_id, role)


@router.patch("/{meeting_id}/user/{user_id}/response", response_model=SMeetingRequestRead, summary="Update user's meeting response")
async def update_user_meeting_response(
    meeting_id: int,
    user_id: int,
    agreement: str,  # Agreement status, can be 'confirmed', 'tentative', or 'declined'
    session: AsyncSession = Depends(get_async_session)
) -> SMeetingRequestRead:
    """
    Update a user's agreement status for a specific meeting.
    """
    return await MeetingManager.update_user_meeting_response(session, meeting_id, user_id, agreement)
