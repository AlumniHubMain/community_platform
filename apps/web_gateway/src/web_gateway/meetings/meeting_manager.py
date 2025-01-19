import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


from event_emitter import EmitterFactory, IProtoEmitter
from common_db import ORMMeeting, ORMMeetingResponse, ORMUserProfile, EMeetingResponseStatus, EMeetingStatus, EMeetingUserRole
from web_gateway.settings import settings
from web_gateway.limits.limits_manager import LimitsManager, MeetingsUserLimits
from .notification_event_builder import NotificationEventBuilder
from .schemas import (
    MeetingFilter,
    MeetingList,
    MeetingRequestCreate,
    MeetingRequestRead,
    MeetingRequestUpdate,
)


class MeetingManager:
    """
    Class for managing meetings and user participation in meetings.
    """

    __notification_event_emitter: IProtoEmitter = None

    @classmethod
    def notification_sender(cls) -> IProtoEmitter:
        if not cls.__notification_event_emitter:
            cls.__notification_event_emitter = EmitterFactory.create_event_emitter(
                target=settings.emitter_settings.meetings_notification_target,
                topic=settings.emitter_settings.meetings_google_pubsub_notification_topic,
            )
        return cls.__notification_event_emitter

    @classmethod
    async def check_confirmations_limit(cls, user_id: int, user_limits: MeetingsUserLimits):
        if user_limits.available_meeting_confirmations == 0:
            raise HTTPException(status_code=400, detail=f"Exceeded the limit of confirmed meetings for user {user_id}")
        
    @classmethod
    async def check_pendings_limit(cls, user_id: int, user_limits: MeetingsUserLimits):
        if user_limits.available_meeting_confirmations == 0:
            raise HTTPException(status_code=400, detail=f"Exceeded the limit of pended meetings for user {user_id}")
    
    @classmethod
    async def create_meeting(
        cls, session: AsyncSession, request: MeetingRequestCreate
    ) -> MeetingRequestRead:
        organizer: ORMUserProfile | None = await session.get(
            ORMUserProfile, request.organizer_id
        )
        if not organizer:
            raise HTTPException(status_code=404, detail="Organiser not found")
        meeting_users = [organizer]

        # Check organizer limits
        organizer_limits = await LimitsManager.get_user_meetings_limits(session, request.organizer_id)
        cls.check_pendings_limit(request.organizer_id, organizer_limits)
        cls.check_confirmations_limit(request.organizer_id, organizer_limits)
        
        # Check attendees exist
        for user_id in request.attendees_id:
            user_profile: ORMUserProfile | None = await session.get(
                ORMUserProfile, user_id
            )
            if not user_profile:
                raise HTTPException(status_code=404, detail=f"Attendee with id {user_id} not found")
            meeting_users.append(user_profile)
    
        # Check attendees pending limits
        for user_id in request.attendees_id:
            attendee_limits = await LimitsManager.get_user_meetings_limits(session, user_id)
            cls.check_pendings_limit(user_id, attendee_limits)

        # Create meeting
        meeting = ORMMeeting(
            organizer_id=request.organizer_id,
            match_id=request.match_id,
            scheduled_time=request.scheduled_time,
            location=request.location,
            description=request.description, 
            status=EMeetingStatus.new,
        )
        session.add(meeting)
        
        # Create response and update limits for users
        for idx, user_orm in enumerate(meeting_users): 
            role = EMeetingUserRole.organizer if idx == 0 else EMeetingUserRole.attendee
            response_status = EMeetingResponseStatus.confirmed if idx == 0 else EMeetingResponseStatus.no_answer
            meeting_response = ORMMeetingResponse(
                user=user_orm,
                role=role,
                response=response_status,
                meeting=meeting
            )
            session.add(meeting_response)
            await LimitsManager.update_user_limits(session, user_orm.id)

        await session.commit()

        # Return the meeting with the user information and responses
        return MeetingRequestRead.model_validate(meeting, from_attributes=True)


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
    async def update_user_meeting_response(
        cls, session: AsyncSession, meeting_id: int, user_id: int, new_status: EMeetingResponseStatus
    ) -> MeetingRequestRead:
        # Change status
        # Send notification to organizer
        
        # Fetch the meeting to ensure it exists
        result = await session.execute(
            select(ORMMeeting)
            .where(ORMMeeting.id == meeting_id)
            .options(selectinload(ORMMeeting.user_responses))
        )
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Get user response ORM
        user_response: ORMMeetingResponse = None
        for response in meeting.user_responses:
            if response.user_id == user_id:
                user_response = response
        
        # Early stop when actual status equal to new status
        if user_response.response == new_status:
            return MeetingRequestRead.model_validate(meeting, from_attributes=True)
        
        # Check limits
        user_limits = await LimitsManager.get_user_meetings_limits(session, user_id)
        if user_response.response == EMeetingResponseStatus.declined:
            # If status will change form declined to other
            cls.check_pendings_limit(user_id, user_limits)
        if new_status == EMeetingResponseStatus.confirmed:
            # If status will change to confirmed from other
            cls.check_confirmations_limit(user_id, user_limits)

        # Update the user's response status
        user_response.response = response
        
        # TODO: @ilyabiro - Add update meeting status
        
        # Update the user's limits
        await LimitsManager.update_user_limits(session, user_id)

        await session.commit()
        
        # Send notification about status change
        cls.notification_sender().emit(
            NotificationEventBuilder.build_meeting_response_event(
                user_id=user_id, meeting_id=meeting_id
            )
        )

        # Return the updated meeting response
        return MeetingRequestRead.model_validate(meeting, from_attributes=True)

        
    # @classmethod
    # async def update_meeting(
    #     cls,
    #     session: AsyncSession,
    #     meeting_id: int,
    #     user_id: int,
    #     request: MeetingRequestUpdate,
    # ) -> MeetingRequestRead:
    #     stmt = (
    #         select(ORMMeeting)
    #         .where(ORMMeeting.id == meeting_id)
    #         .options(
    #             selectinload(ORMMeeting.user_responses).selectinload(
    #                 ORMMeetingResponse.user
    #             )
    #         )
    #         .with_for_update()  # Lock the row for update
    #     )
    #     result = await session.execute(stmt)
    #     meeting = result.scalar_one_or_none()
    #     if not meeting:
    #         raise HTTPException(status_code=404, detail="Meeting not found")
    #     organizer_response = [
    #         r 
    #         for r in meeting.user_responses 
    #         if r.role == EMeetingUserRole.organizer and r.user_id == user_id
    #     ]
    #     if not organizer_response:
    #         raise HTTPException(status_code=403, detail="Wrong organizer")

    #     # Apply updates from the request
    #     for key, value in request.model_dump(
    #         exclude_unset=True, exclude_none=True
    #     ).items():
    #         setattr(meeting, key, value)

    #     await session.commit()

    #     return MeetingRequestRead.model_validate(meeting, from_attributes=True)

    # @classmethod
    # async def update_user_meeting_response(
    #     cls, session: AsyncSession, meeting_id: int, user_id: int, response: EMeetingResponseStatus
    # ) -> MeetingRequestRead:

    #     cls.notification_sender().emit(
    #         NotificationEventBuilder.build_meeting_response_event(
    #             user_id=user_id, meeting_id=meeting_id
    #         )
    #     )

    #     # Return the updated meeting response
    #     return MeetingRequestRead.model_validate(meeting, from_attributes=True)

    # @classmethod
    # async def get_filtered_meetings(
    #     cls, session: AsyncSession, meeting_filter: MeetingFilter
    # ) -> MeetingList:
    #     query = select(ORMMeeting).options(selectinload(ORMMeeting.user_responses))

    #     # Apply filters to the query
    #     if meeting_filter.user_id:
    #         # Filter by user_id: Meetings where the user is either the organizer or an attendee
    #         query = query.join(ORMMeetingResponse).where(
    #             (ORMMeetingResponse.user_id == meeting_filter.user_id)
    #         )

    #     if meeting_filter.date_from:
    #         # Filter by date_from: Meetings scheduled after this date
    #         query = query.where(ORMMeeting.scheduled_time >= meeting_filter.date_from)

    #     if meeting_filter.date_to:
    #         # Filter by date_to: Meetings scheduled before this date
    #         query = query.where(ORMMeeting.scheduled_time <= meeting_filter.date_to)

    #     result = await session.execute(query)
    #     meetings = result.scalars().all()

    #     if not meetings:
    #         return MeetingList(meetings=[])

    #     response = MeetingList(
    #         meetings=[
    #             MeetingRequestRead.model_validate(meeting, from_attributes=True)
    #             for meeting in meetings
    #         ]
    #     )

    #     return MeetingList.model_validate(response)
