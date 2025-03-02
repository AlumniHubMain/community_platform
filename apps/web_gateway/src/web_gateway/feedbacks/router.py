from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.db_abstract import db_manager
from common_db.schemas.feedbacks import MeetingFeedbackCreate, MeetingFeedbackRead
from .feedbacks_manager import FeedbacksManager

from typing import Annotated
from web_gateway import auth


router = APIRouter(tags=["Feedbacks"], prefix="/feedback")


@router.post("/meeting/{meeting_id}", response_model=MeetingFeedbackRead, summary="Create a new feedback about meeting with second user")
async def create_meeting_feedback(
        meeting_id: int,
        user_id: Annotated[int, Depends(auth.current_user_id)],
        feedback: MeetingFeedbackCreate,
        session: Annotated[AsyncSession, Depends(db_manager.get_session)]
) -> MeetingFeedbackRead:
    """
    Create a new feedback about meeting.
    """
    async with session.begin():
        return await FeedbacksManager.create_meeting_feedback(session, user_id, meeting_id, feedback)


@router.get("/meeting/{meeting_id}", response_model=MeetingFeedbackRead, summary="Get users's meeting feedback by meeting id")
async def get_meeting_feedback(
        meeting_id: int,
        user_id: Annotated[int, Depends(auth.current_user_id)],
        session: Annotated[AsyncSession, Depends(db_manager.get_session)]
) -> MeetingFeedbackRead:
    """
    Get user's feedback about meeting  
    """
    return await FeedbacksManager.get_meeting_feedback(session, meeting_id, user_id)
