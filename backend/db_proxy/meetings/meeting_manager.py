from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from common_db import ORMMeeting, ORMMeetingResponse, ORMUserProfile, EMeetingResponseStatus, EMeetingStatus, EMeetingUserRole
from .schemas import MeetingRequestRead, MeetingRequestCreate, MeetingFilter, MeetingList, MeetingRequestUpdate
from limits.limits_manager import LimitsManager


class MeetingManager:
    """
    Class for managing meetings and user participation in meetings.
    """

    @classmethod
    async def get_meeting(cls, session: AsyncSession, meeting_id: int) -> MeetingRequestRead:
        meeting = await session.execute(
            select(ORMMeeting)
            .where(ORMMeeting.id == meeting_id)
            .options(selectinload(ORMMeeting.user_responses).selectinload(ORMMeetingResponse.user))  # eager load
        )
        meeting = meeting.scalar_one_or_none()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        return MeetingRequestRead.model_validate(meeting, from_attributes=True)

    @classmethod
    async def create_meeting(cls, session: AsyncSession, request: MeetingRequestCreate) -> MeetingRequestRead:

        organizer: ORMUserProfile | None = await session.get(ORMUserProfile, request.organizer_id)
        if not organizer:
            raise HTTPException(status_code=404, detail="Organiser not found")

        # Check user limits
        user_limits = await LimitsManager.get_user_meetings_limits(session, request.organizer_id)
        if user_limits.available_meeting_confirmations == 0:
            raise HTTPException(status_code=400, detail="Exceeded the limit of confirmed meetings for user")
        
        if user_limits.available_meeting_pendings == 0:
            raise HTTPException(status_code=400, detail="Exceeded the limit of pended meetings for user")

        user_meeting = ORMMeetingResponse(
            user=organizer,
            role=EMeetingUserRole.organizer,
            response=EMeetingResponseStatus.confirmed,
            meeting=ORMMeeting(status=EMeetingStatus.new, description=request.description, location=request.location,
                               scheduled_time=request.scheduled_time, )
        )
        session.add(user_meeting)
        await LimitsManager.update_user_limits(session, request.organizer_id)
        await session.commit()

        # Return the meeting with the user information and responses
        created_meeting = MeetingRequestRead.model_validate(user_meeting.meeting, from_attributes=True)
        return created_meeting

    @classmethod
    async def update_meeting(cls, session: AsyncSession, meeting_id: int, user_id: int,
                             request: MeetingRequestUpdate) -> MeetingRequestRead:
        stmt = (select(ORMMeeting).where(ORMMeeting.id == meeting_id)
                .options(selectinload(ORMMeeting.user_responses).selectinload(ORMMeetingResponse.user))
                .with_for_update()  # Lock the row for update
                )
        result = await session.execute(stmt)
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        organizer_response = [r for r in meeting.user_responses if
                              r.role == EMeetingUserRole.organizer and r.user_id == user_id]
        if not organizer_response:
            raise HTTPException(status_code=403, detail="Wrong organizer")

        # Apply updates from the request
        for key, value in request.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(meeting, key, value)

        await session.commit()

        return MeetingRequestRead.model_validate(meeting, from_attributes=True)

    @classmethod
    async def add_user_to_meeting(cls, session: AsyncSession, user_id: int, meeting_id: int,
                                  role: EMeetingUserRole) -> MeetingRequestRead:
        # Check if the meeting exists
        result = await session.execute(
            select(ORMMeeting).where(ORMMeeting.id == meeting_id).options(selectinload(ORMMeeting.user_responses)))
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        for response in meeting.user_responses:
            if response.user_id == user_id:
                return MeetingRequestRead.model_validate(meeting, from_attributes=True)
        
        # Check user limits
        user_limits = await LimitsManager.get_user_meetings_limits(session, user_id)
        if user_limits.available_meeting_confirmations == 0:
            raise HTTPException(status_code=400, detail="Exceeded the limit of confirmed meetings for user")
        
        if user_limits.available_meeting_pendings == 0:
            raise HTTPException(status_code=400, detail="Exceeded the limit of pended meetings for user")
        
        # Add the user to the meeting
        meeting.user_responses.append(ORMMeetingResponse(user_id=user_id, meeting=meeting, role=role, response=EMeetingResponseStatus.no_answer))

        # Update the user's limits
        await LimitsManager.update_user_limits(session, user_id)

        await session.commit()
        # ToDo: send a notification to the added user
        return MeetingRequestRead.model_validate(meeting, from_attributes=True)

    @classmethod
    async def update_user_meeting_response(cls, session: AsyncSession, meeting_id: int, user_id: int,
                                           response: EMeetingResponseStatus) -> MeetingRequestRead:

        # Fetch the meeting to ensure it exists
        result = await session.execute(select(ORMMeeting).where(ORMMeeting.id == meeting_id))
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Fetch the user_meeting entry to check if the user is already part of the meeting
        result = await session.execute(
            select(ORMMeetingResponse).where(ORMMeetingResponse.meeting_id == meeting_id, ORMMeetingResponse.user_id == user_id))
        user_meeting = result.scalar_one_or_none()

        if not user_meeting:
            raise HTTPException(status_code=404, detail="User is not part of this meeting")

        # Check user limits
        user_limits = await LimitsManager.get_user_meetings_limits(session, user_id)

        is_check_pendings, is_check_confirmations = False, False
        # Pending - Change status from declined to any
        # Confirmation - Change status from no_answer/declined to any
        old_response = user_meeting.response
        if old_response == EMeetingResponseStatus.declined and response != EMeetingResponseStatus.declined:
            is_check_pendings = True
        if old_response in (EMeetingResponseStatus.declined, EMeetingResponseStatus.no_answer):
            is_check_confirmations = True
        
        if is_check_confirmations and user_limits.available_meeting_confirmations == 0:
            raise HTTPException(status_code=400, detail="Exceeded the limit of confirmed meetings for user")
        
        if is_check_pendings and user_limits.available_meeting_pendings == 0:
            raise HTTPException(status_code=400, detail="Exceeded the limit of pended meetings for user")
        
        # Update the user's response status
        user_meeting.response = response
        
        # Update the user's limits
        await LimitsManager.update_user_limits(session, user_id)

        await session.commit()

        # ToDo: send a notification to the organiser

        # Return the updated meeting response
        return await cls.get_meeting(session, meeting_id)

    @classmethod
    async def get_filtered_meetings(cls, session: AsyncSession, meeting_filter: MeetingFilter) -> MeetingList:
        query = select(ORMMeeting).options(selectinload(ORMMeeting.user_responses))

        # Apply filters to the query
        if meeting_filter.user_id:
            # Filter by user_id: Meetings where the user is either the organizer or an attendee
            query = query.join(ORMMeetingResponse).where(
                (ORMMeetingResponse.user_id == meeting_filter.user_id)
            )

        if meeting_filter.date_from:
            # Filter by date_from: Meetings scheduled after this date
            query = query.where(ORMMeeting.scheduled_time >= meeting_filter.date_from)

        if meeting_filter.date_to:
            # Filter by date_to: Meetings scheduled before this date
            query = query.where(ORMMeeting.scheduled_time <= meeting_filter.date_to)

        result = await session.execute(query)
        meetings = result.scalars().all()

        if not meetings:
            return MeetingList(meetings=[])

        response = MeetingList(
            meetings=[MeetingRequestRead.model_validate(meeting, from_attributes=True) for meeting in meetings])

        return MeetingList.model_validate(response)
