from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from common_db import ORMMeeting, ORMUserMeeting, ORMUserProfile
from .schemas import MeetingRequestRead, MeetingRequestCreate, MeetingFilter


class MeetingManager:
    """
    Class for managing meetings and user participation in meetings.
    """

    @classmethod
    async def get_meeting(cls, session: AsyncSession, meeting_id: int) -> MeetingRequestRead:
        meeting = await session.execute(
            select(ORMMeeting)
            .where(ORMMeeting.id == meeting_id)
            .options(selectinload(ORMMeeting.user_responses).selectinload(ORMUserMeeting.user))  # eager load
        )
        meeting = meeting.scalar_one_or_none()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        return MeetingRequestRead.model_validate(meeting, from_attributes=True)

    @classmethod
    async def create_meeting(cls, session: AsyncSession, request: MeetingRequestCreate) -> MeetingRequestRead:

        organizer: ORMUserProfile | None = await session.get(ORMUserProfile, request.organizer_id)
        if not organizer:
            raise HTTPException(status_code=400, detail="Organiser not found")

        user_meeting = ORMUserMeeting(
            user=organizer,
            role="organizer",
            response="confirmed",
            meeting=ORMMeeting(status="new", description=request.description, location=request.location,
                               scheduled_time=request.scheduled_time, )
        )
        session.add(user_meeting)
        await session.commit()

        # Return the meeting with the user information and responses
        created_meeting = MeetingRequestRead.model_validate(user_meeting.meeting, from_attributes=True)
        return created_meeting

    @classmethod
    async def update_meeting(cls, session: AsyncSession, meeting_id: int,
                             request: MeetingRequestCreate) -> MeetingRequestRead:
        stmt = (select(ORMMeeting).where(ORMMeeting.id == meeting_id)
                .options(selectinload(ORMMeeting.user_responses).selectinload(ORMUserMeeting.user))
                .with_for_update()  # Lock the row for update
                )
        result = await session.execute(stmt)
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        organizer_response = [r for r in meeting.user_responses if
                              r.role == "organizer" and r.user_id == request.organizer_id]
        if not organizer_response:
            raise HTTPException(status_code=403, detail="Wrong organizer")

        # Apply updates from the request
        for key, value in request.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(meeting, key, value)

        await session.commit()

        return MeetingRequestRead.model_validate(meeting, from_attributes=True)

    @classmethod
    async def get_all_meetings(cls, session: AsyncSession) -> list[MeetingRequestRead]:
        result = await session.execute(select(ORMMeeting).options(selectinload(ORMMeeting.users)))
        meetings = result.scalars().all()
        return [MeetingRequestRead.model_validate(meeting) for meeting in meetings]

    @classmethod
    async def add_user_to_meeting(cls, session: AsyncSession, user_id: int, meeting_id: int, role: str) -> None:
        # Check if the meeting exists
        result = await session.execute(select(ORMMeeting).where(ORMMeeting.id == meeting_id))
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Check if the user is already in the meeting
        existing_user_meeting = await session.execute(
            select(ORMUserMeeting).where(ORMUserMeeting.user_id == user_id, ORMUserMeeting.meeting_id == meeting_id))
        if existing_user_meeting.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User already added to the meeting")

        # Add the user to the meeting
        user_meeting_orm = ORMUserMeeting(user_id=user_id, meeting_id=meeting_id, role=role)
        session.add(user_meeting_orm)

        # ToDo: send a notification to the added user

        await session.commit()

    @classmethod
    async def update_user_meeting_response(cls, session: AsyncSession, meeting_id: int, user_id: int,
                                           response: str) -> MeetingRequestRead:
        # Validate the response status
        if response not in ['confirmed', 'tentative', 'declined']:
            raise HTTPException(status_code=400, detail="Invalid response status")

        # Fetch the meeting to ensure it exists
        result = await session.execute(select(ORMMeeting).where(ORMMeeting.id == meeting_id))
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Fetch the user_meeting entry to check if the user is already part of the meeting
        result = await session.execute(
            select(ORMUserMeeting).where(ORMUserMeeting.meeting_id == meeting_id, ORMUserMeeting.user_id == user_id))
        user_meeting = result.scalar_one_or_none()

        if not user_meeting:
            raise HTTPException(status_code=404, detail="User is not part of this meeting")

        # Update the user's response status
        user_meeting.response = response
        await session.commit()

        # ToDo: send a notification to the organiser

        # Return the updated meeting response
        return await cls.get_meeting(session, meeting_id)

    @classmethod
    async def get_filtered_meetings(cls, session: AsyncSession, filter: MeetingFilter) -> list[MeetingRequestRead]:
        query = select(ORMMeeting).options(selectinload(ORMMeeting.user_responses).selectinload(ORMUserMeeting.user))

        # Apply filters to the query
        if filter.user_id:
            # Filter by user_id: Meetings where the user is either the organizer or an attendee
            query = query.join(ORMUserMeeting).where(
                (ORMUserMeeting.user_id == filter.user_id)
            )

        if filter.date_from:
            # Filter by date_from: Meetings starting after this date
            query = query.where(ORMMeeting.scheduled_time >= filter.date_from)

        if filter.date_to:
            # Filter by date_to: Meetings ending before this date
            query = query.where(ORMMeeting.scheduled_time <= filter.date_to)

        # Execute the query
        result = await session.execute(query)
        meetings = result.scalars().all()

        # If no meetings are found, raise a 404 error
        if not meetings:
            raise HTTPException(status_code=404, detail="No meetings found")

        return [MeetingRequestRead.model_validate(m, from_attributes=True) for m in meetings]
