from common_db.schemas.feedbacks import MeetingFeedbackCreate, MeetingFeedbackRead
from common_db.enums.meetings import EMeetingStatus
from common_db.models import ORMMeetingFeedback, ORMMeeting, ORMMeetingResponse
from common_db.managers import UserManager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_

from fastapi import HTTPException


class FeedbacksManager:
    """
    Класс для управления анкетами пользователей.
    """

    @classmethod
    async def get_meeting_with_check(cls, session: AsyncSession, meeting_id: int) -> ORMMeeting:
        # TODO: @ilyabiro Move meeting manager into common_db and remove it
        
        meeting = await session.execute(
            select(ORMMeeting)
            .options(
                selectinload(ORMMeeting.user_responses).selectinload(
                    ORMMeetingResponse.user
                )
            )  # eager load
            .where(ORMMeeting.id == meeting_id)
        )
        meeting = meeting.scalar_one_or_none()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        if not (meeting.status == EMeetingStatus.archived):
            raise HTTPException(status_code=400, detail="Meeting is active or declined")
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        return meeting
    
    
    @classmethod
    async def get_meeting_feedback(
        cls, session: AsyncSession, meeting_id: int, user_id: int
    ) -> MeetingFeedbackRead:

        await UserManager.check_user(session, user_id)
        meeting = await cls.get_meeting_with_check(session, meeting_id)
        
        # If user not it meeting - return 401
        is_user_found = meeting.organizer_id == user_id
        for response in meeting.user_responses:
            if is_user_found:
                break
            is_user_found = (user_id == response.user_id)
        
        if not is_user_found:
            raise HTTPException(status_code=401, detail="User not permitted for this operation")
        
        result = await session.execute(
            select(ORMMeetingFeedback)
            .where(ORMMeetingFeedback.meeting_id == meeting_id)
            .where(ORMMeetingFeedback.from_user_id == user_id)
            .limit(1)
        )
        feedback_orm = result.scalar_one_or_none()
        if feedback_orm is None:
            raise HTTPException(status_code=404, detail="Feedback not found")
        return MeetingFeedbackRead.model_validate(feedback_orm)

    @classmethod
    async def create_meeting_feedback(
        cls, 
        session: AsyncSession, 
        user_id: int, 
        meeting_id: int, 
        feedback: MeetingFeedbackCreate
    ) -> MeetingFeedbackRead:
        
        await UserManager.check_user(session, user_id)
        await UserManager.check_user(session, feedback.assignee_id)
        await cls.get_meeting_with_check(session, meeting_id)

        feedback_orm = ORMMeetingFeedback(
            from_user_id=user_id,
            meeting_id=meeting_id,
            **feedback.model_dump(exclude_unset=True, exclude_none=True)
        )
        session.add(feedback_orm)
        await session.commit()
        return MeetingFeedbackRead.model_validate(feedback_orm)
