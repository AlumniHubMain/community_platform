from common_db.schemas.feedbacks import MeetingFeedback, MeetingFeedbackRead
from common_db.enums.meetings import EMeetingStatus
from common_db.models import ORMMeetingFeedback, ORMMeeting, ORMUserProfile
from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


class FormsManager:
    """
    Класс для управления анкетами пользователей.
    """

    @classmethod
    async def check_user_exists(cls, session: AsyncSession, user_id: int):
        user: ORMUserProfile | None = await session.get(
            ORMUserProfile, user_id
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
    @classmethod
    async def validate_meeting_state(cls, session: AsyncSession, meeting_id: int):
        meeting: ORMMeeting | None = await session.get(
            ORMMeeting, meeting_id
        )
        if not (meeting.status == EMeetingStatus.archived):
            raise HTTPException(status_code=400, detail="Meeting is active or declined")
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
    
    
    @classmethod
    async def get_meeting_feedback(
        cls, session: AsyncSession, meeting_id: int, user_id: int
    ) -> MeetingFeedbackRead:

        await cls.check_user_exists(session, user_id)
        await cls.validate_meeting_state(session, meeting_id)
        
        result = await session.execute(
            select(ORMMeetingFeedback)
            .where(ORMMeetingFeedback.meeting_id == meeting_id)
            .where(ORMMeetingFeedback.user_id == user_id)
            .limit(1)
        )
        feedback_orm = result.scalar_one_or_none()
        if feedback_orm is None:
            raise HTTPException(status_code=404, detail="Feedback not found")
        return MeetingFeedbackRead.model_validate(feedback_orm)

    @classmethod
    async def create_meeting_feedback(
        cls, session: AsyncSession, meeting_id: int, feedback: MeetingFeedback
    ) -> MeetingFeedbackRead:
        
        await cls.check_user_exists(session, feedback.user_id)
        await cls.validate_meeting_state(session, meeting_id)

        feedback_orm = ORMMeetingFeedback(
            meeting_id=meeting_id,
            **feedback.model_dump(exclude_unset=True, exclude_none=True)
        )
        session.add(feedback_orm)
        await session.commit()
        return MeetingFeedbackRead.model_validate(feedback_orm)
