from typing import Annotated

from common_db.db_abstract import db_manager
from common_db.enums.notifications import ENotificationType
from common_db.managers.notifications import NotificationManager
from common_db.schemas.notifications import DTOUserNotificationRead

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from web_gateway import auth

router = APIRouter(tags=["Notifications"], prefix="/notifications")


@router.get("", response_model=list[DTOUserNotificationRead])
async def get_user_notifications(
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(db_manager.get_session)],
    is_read: bool | None = Query(None, description="Filter by read status"),
    notification_type: ENotificationType | None = Query(None, description="Filter by notification type"),
) -> list[DTOUserNotificationRead]:
    """
    Get user notifications with filtering options
    """
    return await NotificationManager.get_user_notifications(
        user_id=user_id,
        is_read=is_read,
        notification_type=notification_type,
        session=session
    )


@router.get("/types", response_model=list[str])
async def get_notification_types() -> list[str]:
    """
    Get all available notification types
    """
    return [e.name for e in ENotificationType]


@router.patch("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(db_manager.get_session)],
) -> JSONResponse:
    """
    Mark notification as read
    """
    return await NotificationManager.mark_notification_as_read(
        user_id=user_id,
        notification_id=notification_id,
        session=session
    )


@router.patch("/read-all")
async def mark_all_notifications_as_read(
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(db_manager.get_session)],
) -> JSONResponse:
    """
    Mark all user notifications as read
    """
    return await NotificationManager.mark_all_notifications_as_read(
        user_id=user_id,
        session=session
    )


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    user_id: Annotated[int, Depends(auth.current_user_id)],
    session: Annotated[AsyncSession, Depends(db_manager.get_session)],
) -> JSONResponse:
    """
    Delete notification
    """
    return await NotificationManager.delete_notification(
        user_id=user_id,
        notification_id=notification_id,
        session=session
    )
