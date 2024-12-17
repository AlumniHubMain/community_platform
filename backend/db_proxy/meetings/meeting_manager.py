import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from alumnihub.community_platform.event_emitter import EmitterFactory, IEventEmitter
from common_db import ORMMeeting, ORMMeetingResponse, ORMUserProfile
from common_db.config import settings
from notification_event_builder import NotificationEventBuilder
from schemas import (MeetingFilter, MeetingList, MeetingRequestCreate, MeetingRequestRead, MeetingRequestUpdate)


class MeetingManager:
    """
    Class for managing meetings and user participation in meetings.
    """

    __notification_event_emitter: IEventEmitter = None

    @classmethod
    def notification_sender(cls) -> IEventEmitter:
        if not cls.__notification_event_emitter:
            cls.__notification_event_emitter = EmitterFactory.create_event_emitter(
                target=settings.notification_target,
                topic=settings.google_pubsub_notification_topic,
            )
        return cls.__notification_event_emitter

    @classmethod
    async def get_meeting(
        cls, session: AsyncSession, meeting_id: int
    ) -> MeetingRequestRead:
        meeting = await session.execute(
            select(ORMMeeting)
            .where(ORMMeeting.id == meeting_id)
            .options(
                selectinload(ORMMeeting.user_responses).selectinload(
                    ORMMeetingResponse.user
                )
            )  # eager load
        )
        meeting = meeting.scalar_one_or_none()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        return MeetingRequestRead.model_validate(meeting, from_attributes=True)

    @classmethod
    async def create_meeting(
        cls, session: AsyncSession, request: MeetingRequestCreate
    ) -> MeetingRequestRead:
        organizer: ORMUserProfile | None = await session.get(
            ORMUserProfile, request.organizer_id
        )
        if not organizer:
            raise HTTPException(status_code=400, detail="Organiser not found")

        user_meeting = ORMMeetingResponse(
            user=organizer,
            role="organizer",
            response="confirmed",
            meeting=ORMMeeting(
                status="new",
                description=request.description,
                location=request.location,
                scheduled_time=request.scheduled_time,
            ),
        )
        session.add(user_meeting)
        await session.commit()

        # Return the meeting with the user information and responses
        created_meeting = MeetingRequestRead.model_validate(
            user_meeting.meeting, from_attributes=True
        )
        return created_meeting

    @classmethod
    async def update_meeting(
        cls,
        session: AsyncSession,
        meeting_id: int,
        user_id: int,
        request: MeetingRequestUpdate,
    ) -> MeetingRequestRead:
        stmt = (
            select(ORMMeeting)
            .where(ORMMeeting.id == meeting_id)
            .options(
                selectinload(ORMMeeting.user_responses).selectinload(
                    ORMMeetingResponse.user
                )
            )
            .with_for_update()  # Lock the row for update
        )
        result = await session.execute(stmt)
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        organizer_response = [
            r
            for r in meeting.user_responses
            if r.role == "organizer" and r.user_id == user_id
        ]
        if not organizer_response:
            raise HTTPException(status_code=403, detail="Wrong organizer")

        # Apply updates from the request
        for key, value in request.model_dump(
            exclude_unset=True, exclude_none=True
        ).items():
            setattr(meeting, key, value)

        await session.commit()

        return MeetingRequestRead.model_validate(meeting, from_attributes=True)

    @classmethod
    async def add_user_to_meeting(
        cls, session: AsyncSession, user_id: int, meeting_id: int, role: str
    ) -> MeetingRequestRead:
        # Check if the meeting exists
        result = await session.execute(
            select(ORMMeeting)
            .where(ORMMeeting.id == meeting_id)
            .options(selectinload(ORMMeeting.user_responses))
        )
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        if next(
            (resp for resp in meeting.user_responses if resp.user_id == user_id), None
        ):
            # this user is already invited, although maybe without a response
            return MeetingRequestRead.model_validate(meeting, from_attributes=True)

        # Add the user to the meeting
        meeting.user_responses.append(
            ORMMeetingResponse(user_id=user_id, meeting=meeting, role=role)
        )

        await session.commit()

        # Check for an organizer and emit an event
        # ToDo: can use the authenticated user instead
        if organizer := next(
            (user for user in meeting.user_responses if user.role == "organizer"), None
        ):
            organizer_id: int = organizer.user_id
            cls.notification_sender().emit(
                NotificationEventBuilder.build_meeting_invitation_event(
                    invited_id=user_id, meeting_id=meeting_id, inviter_id=organizer_id
                )
            )
        else:
            logging.warning(f"Meeting {meeting_id} has no organizer")

        return MeetingRequestRead.model_validate(meeting, from_attributes=True)

    @classmethod
    async def update_user_meeting_response(
        cls, session: AsyncSession, meeting_id: int, user_id: int, response: str
    ) -> MeetingRequestRead:
        # Validate the response status
        if response not in ["confirmed", "tentative", "declined"]:
            raise HTTPException(status_code=400, detail="Invalid response status")

        # Fetch the meeting to ensure it exists
        result = await session.execute(
            select(ORMMeeting)
            .where(ORMMeeting.id == meeting_id)
            .options(selectinload(ORMMeeting.user_responses))
        )
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Fetch the user_meeting entry to check if the user is already part of the meeting
        result = await session.execute(
            select(ORMMeetingResponse).where(
                ORMMeetingResponse.meeting_id == meeting_id,
                ORMMeetingResponse.user_id == user_id,
            )
        )
        user_meeting = result.scalar_one_or_none()

        if not user_meeting:
            raise HTTPException(
                status_code=404, detail="User is not part of this meeting"
            )

        # If the response is unchanged, return early
        if user_meeting.response == response:
            return MeetingRequestRead.model_validate(meeting, from_attributes=True)

        # Update the user's response status
        user_meeting.response = response
        await session.commit()

        cls.notification_sender().emit(
            NotificationEventBuilder.build_meeting_response_event(
                user_id=user_id, meeting_id=meeting_id
            )
        )

        # Return the updated meeting response
        return MeetingRequestRead.model_validate(meeting, from_attributes=True)

    @classmethod
    async def get_filtered_meetings(
        cls, session: AsyncSession, meeting_filter: MeetingFilter
    ) -> MeetingList:
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
            meetings=[
                MeetingRequestRead.model_validate(meeting, from_attributes=True)
                for meeting in meetings
            ]
        )

        return MeetingList.model_validate(response)
