from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from common_db import ORMMeeting, ORMUserMeeting
from .schemas import SMeetingRequestRead, MeetingRequestCreate, MeetingUserStatus


class MeetingManager:
    """
    Class for managing meetings and user participation in meetings.
    """

    @classmethod
    async def get_meeting(
            cls, session: AsyncSession, meeting_id: int
    ) -> SMeetingRequestRead:
        result = await session.execute(
            select(ORMMeeting)
            .where(ORMMeeting.id == meeting_id)
            .options(selectinload(ORMMeeting.users))  # Eager load users
        )
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Populate users with their statuses
        users_status = [
            MeetingUserStatus(
                user_id=user.id,
                name=f"{user.name} {user.surname}",
                role=user_meeting.role,
                agreement=user_meeting.agreement,
            )
            for user, user_meeting in zip(meeting.users, meeting.user_meetings)
        ]

        return SMeetingRequestRead(
            id=meeting.id,
            description=meeting.description,
            location=meeting.location,
            scheduled_time=meeting.scheduled_time,
            status=meeting.status,
            users=users_status,
        )


    @classmethod
    async def create_meeting(
            cls, session: AsyncSession, request: MeetingRequestCreate
    ) -> SMeetingRequestRead:
        meeting_orm = ORMMeeting(
            **request.model_dump(exclude_unset=True, exclude_none=True)
        )
        session.add(meeting_orm)
        meeting_user_orm = ORMUserMeeting(
            uid=request.organiser_id, meeting_id=meeting_orm.id, role="organiser", agreement="accepted"
        )
        session.add(meeting_user_orm)
        await session.commit()
        return SMeetingRequestRead.model_validate(meeting_orm)

    @classmethod
    async def update_meeting(
            cls, session: AsyncSession, meeting_id: int, request: MeetingRequestCreate
    ) -> SMeetingRequestRead:
        stmt = (
            select(ORMMeeting)
            .where(ORMMeeting.id == meeting_id)
            .with_for_update()  # Lock the row for update
        )
        result = await session.execute(stmt)
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Apply updates from the request
        for key, value in request.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(meeting, key, value)

        await session.commit()
        return SMeetingRequestRead.model_validate(meeting)

    @classmethod
    async def get_all_meetings(
            cls, session: AsyncSession
    ) -> list[SMeetingRequestRead]:
        result = await session.execute(select(ORMMeeting).options(selectinload(ORMMeeting.users)))
        meetings = result.scalars().all()
        return [SMeetingRequestRead.model_validate(meeting) for meeting in meetings]

    @classmethod
    async def add_user_to_meeting(
            cls, session: AsyncSession, user_id: int, meeting_id: int, role: str
    ) -> None:
        # Check if the meeting exists
        result = await session.execute(select(ORMMeeting).where(ORMMeeting.id == meeting_id))
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Check if the user is already in the meeting
        existing_user_meeting = await session.execute(
            select(ORMUserMeeting).where(
                ORMUserMeeting.uid == user_id, ORMUserMeeting.meeting_id == meeting_id
            )
        )
        if existing_user_meeting.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User already added to the meeting")

        # Add the user to the meeting
        user_meeting_orm = ORMUserMeeting(uid=user_id, meeting_id=meeting_id, role=role)
        session.add(user_meeting_orm)

        # ToDo: send a notification to the added user

        await session.commit()


    @classmethod
    async def update_user_meeting_response(
        cls, session: AsyncSession, meeting_id: int, user_id: int, agreement: str
    ) -> SMeetingRequestRead:
        # Validate the agreement status
        if agreement not in ['confirmed', 'tentative', 'declined']:
            raise HTTPException(status_code=400, detail="Invalid agreement status")

        # Fetch the meeting to ensure it exists
        result = await session.execute(
            select(ORMMeeting).where(ORMMeeting.id == meeting_id)
        )
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        # Fetch the user_meeting entry to check if the user is already part of the meeting
        result = await session.execute(
            select(ORMUserMeeting).where(
                ORMUserMeeting.meeting_id == meeting_id, ORMUserMeeting.uid == user_id
            )
        )
        user_meeting = result.scalar_one_or_none()

        if not user_meeting:
            raise HTTPException(status_code=404, detail="User is not part of this meeting")

        # Update the user's agreement status
        user_meeting.agreement = agreement
        await session.commit()

        # ToDo: send a notification to the organiser

        # Return the updated meeting response
        return await cls.get_meeting(session, meeting_id)
