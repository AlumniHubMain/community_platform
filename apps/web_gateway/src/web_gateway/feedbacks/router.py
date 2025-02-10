from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.db_abstract import db_manager
from common_db.schemas.feedbacks import MeetingFeedback, MeetingFeedbackRead
from typing import Annotated
from .feedbacks_manager import FeedbacksManager


router = APIRouter(tags=["Feedbacks"], prefix="/feedback")


@router.post("/meeting/{meeting_id}", response_model=MeetingFeedbackRead, summary="Create a new feedback about meeting with second user")
async def create_meeting_feedback(
        meeting_id: int,
        feedback: MeetingFeedback,
        session: Annotated[AsyncSession, Depends(db_manager.get_session)]
) -> MeetingFeedbackRead:
    """
    Create a new feedback about meeting.
    """
    async with session.begin():
        created_feedback = await FeedbacksManager.create_meeting_feedback(session, meeting_id, feedback)
        return created_feedback


@router.get("/meeting/{meeting_id}/{user_id}", response_model=MeetingFeedbackRead, summary="Get meeting feedback by meeting id")
async def get_meeting_feedback(
        meeting_id: int,
        user_id: int,
        session: Annotated[AsyncSession, Depends(db_manager.get_session)]
) -> MeetingFeedbackRead:
    """
    Get the last created form for user and selected intent type.    
    """
    return await FeedbacksManager.get_meeting_feedback(session, meeting_id, user_id)
