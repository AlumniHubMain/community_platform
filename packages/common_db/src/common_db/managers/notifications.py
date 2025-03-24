from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .user import UserManager
from ..db_abstract import db_manager
from ..enums.notifications import ENotificationType
from ..models.notifications import ORMUserNotifications
from ..schemas.notifications import DTOGeneralNotification, DTOUserNotificationRead


class NotificationManager:
    """
    Manager for interacting with the user notifications table
    """

    @classmethod
    async def create_notification(
            cls,
            notification_data: DTOGeneralNotification,
            session: AsyncSession = db_manager.get_session()
    ) -> JSONResponse:
        """
        Create a new notification in the database.

        Args:
            session: database session
            notification_data: notification data for creation

        Returns:
            JSONResponse: response with status and created notification id
        """
        notification = ORMUserNotifications(**notification_data.model_dump(exclude_unset=True, exclude_none=True))
        session.add(notification)
        await session.flush()
        await session.commit()
        return JSONResponse(
            content={
                "status": "success",
                "message": "Notification created successfully",
                "notification_id": notification.id
            },
            status_code=status.HTTP_201_CREATED
        )

    @classmethod
    async def get_user_notifications(
            cls,
            user_id: int,
            is_read: bool = None,
            notification_type: ENotificationType = None,
            session: AsyncSession = db_manager.get_session()
    ) -> list[DTOUserNotificationRead]:
        """
        Get user notifications.

        Args:
            session: database session
            user_id: user identifier
            is_read: optional filter by read status
            notification_type: optional filter by notification type

        Returns:
            list[DTOUserNotificationRead]: list of user notifications
        """
        await UserManager.check_user(session=session, user_id=user_id)

        query = select(ORMUserNotifications).where(ORMUserNotifications.user_id == user_id)

        if is_read is not None:
            query = query.where(ORMUserNotifications.is_read == is_read)

        if notification_type is not None:
            query = query.where(ORMUserNotifications.notification_type == notification_type)

        # Sort from newest to oldest
        query = query.order_by(ORMUserNotifications.created_at.desc())

        result = await session.execute(query)
        notifications = result.scalars().all()

        return [DTOUserNotificationRead.model_validate(notification) for notification in notifications]

    @classmethod
    async def mark_notification_as_read(
            cls,
            user_id: int,
            notification_id: int,
            session: AsyncSession = db_manager.get_session()
    ) -> JSONResponse:
        """
        Mark notification as read.

        Args:
            user_id: user identifier
            session: database session
            notification_id: notification identifier

        Returns:
            JSONResponse: response with status
        Raise:
            HTTPException 404 if not found
        """
        await UserManager.check_user(session=session, user_id=user_id)

        result = await session.execute(
            select(ORMUserNotifications).where(ORMUserNotifications.id == notification_id)
        )
        notification = result.scalar_one_or_none()

        if not notification:
            raise HTTPException(status_code=404, detail="Not found")

        await session.execute(
            update(ORMUserNotifications)
            .where(ORMUserNotifications.id == notification_id)
            .values(is_read=True)
        )

        await session.commit()

        return JSONResponse(
            content={
                "status": "success",
                "message": "Notification marked as read"
            },
            status_code=status.HTTP_200_OK
        )

    @classmethod
    async def mark_all_notifications_as_read(
            cls,
            user_id: int,
            session: AsyncSession = db_manager.get_session()
    ) -> JSONResponse:
        """
        Mark all user notifications as read.

        Args:
            session: database session
            user_id: user identifier

        Returns:
            JSONResponse: response with status
        """
        await UserManager.check_user(session=session, user_id=user_id)

        await session.execute(
            update(ORMUserNotifications)
            .where(ORMUserNotifications.user_id == user_id, ORMUserNotifications.is_read == False)
            .values(is_read=True)
        )

        await session.commit()

        return JSONResponse(
            content={
                "status": "success",
                "message": "All notifications marked as read"
            },
            status_code=status.HTTP_200_OK
        )

    @classmethod
    async def delete_notification(
            cls,
            user_id: int,
            notification_id: int,
            session: AsyncSession = db_manager.get_session()
    ) -> JSONResponse:
        """
        Delete notification.

        Args:
            user_id: user identifier
            session: database session
            notification_id: notification identifier to delete

        Returns:
            JSONResponse: response with status
        Raise:
            HTTPException 404 if not found
        """
        await UserManager.check_user(session=session, user_id=user_id)

        result = await session.execute(
            select(ORMUserNotifications).where(ORMUserNotifications.id == notification_id)
        )

        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Not found")

        await session.execute(
            delete(ORMUserNotifications).where(ORMUserNotifications.id == notification_id)
        )

        await session.commit()

        return JSONResponse(
            content={
                "status": "success",
                "message": "Notification deleted successfully"
            },
            status_code=status.HTTP_200_OK
        )
