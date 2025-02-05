from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from schema import Event
from common_db.models.callbot import ORMCallbotMeeting, ORMCallbotEnabledUser


class CallbotCalendarManager:
    @staticmethod
    def convert_to_orm(event: Event, orm_event: ORMCallbotMeeting) -> None:
        """
        Converts an Event to an ORMCallbotMeeting.

        Args:
            event (Event): The event to convert.
            orm_event (ORMCallbotMeeting): The ORM event to convert to.
        """
        orm_event.google_id = event.google_id
        orm_event.start_time = event.start_time
        orm_event.end_time = event.end_time
        orm_event.attendees = "\n".join(event.attendees)
        orm_event.join_url = event.join_url
        orm_event.subject = event.subject

    @classmethod
    async def get_event_by_google_id(cls, session: AsyncSession, google_id: str) -> ORMCallbotMeeting | None:
        stmt = select(ORMCallbotMeeting).where(ORMCallbotMeeting.google_id == google_id)
        result = await session.execute(statement=stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def delete_event(cls, session: AsyncSession, google_id: str) -> None:
        stmt = select(ORMCallbotMeeting).where(ORMCallbotMeeting.google_id == google_id)
        result = await session.execute(statement=stmt)
        event = result.scalar_one_or_none()
        if event:
            session.delete(event)
            await session.commit()

    @classmethod
    async def save_event(cls, session: AsyncSession, event: Event) -> None:
        stored_event = await CallbotCalendarManager.get_event_by_google_id(session, event.google_id)

        if not stored_event:
            stored_event = ORMCallbotMeeting()
            session.add(stored_event)

        CallbotCalendarManager.convert_to_orm(event, stored_event)

        await session.commit()

    @classmethod
    async def get_upcoming_events_not_joined(
        cls, session: AsyncSession, start_time_from: datetime, end_time_to: datetime
    ):
        """
        Fetches upcoming events that have not been joined by the callbot.

        Args:
            session: The database session.
            start_time_from: The start time of the range to fetch events from.
            start_time_to: The end time of the range to fetch events from.
        """
        stmt = (
            select(ORMCallbotMeeting)
            .where(ORMCallbotMeeting.google_id.isnot(None))
            .where(ORMCallbotMeeting.start_time <= start_time_from)
            .where(ORMCallbotMeeting.end_time >= end_time_to)
            .where(ORMCallbotMeeting.callbot_id.is_(None))
        )
        res = await session.execute(statement=stmt)
        for e in res.scalars():
            yield e

    @classmethod
    async def record_callbot_id(cls, session: AsyncSession, google_id: str, callbot_id: str) -> None:
        stmt = select(ORMCallbotMeeting).where(ORMCallbotMeeting.google_id == google_id)
        result = await session.execute(statement=stmt)
        if event := result.scalar_one_or_none():
            event.callbot_id = callbot_id
            await session.commit()
        else:
            raise ValueError(f"Event with google_id {google_id} not found")

    @classmethod
    async def any_of_attendees_enabled(cls, session: AsyncSession, attendees: list[str]) -> bool:
        """
        Checks if any of the attendees are enabled for the callbot.

        Args:
            attendees: The list of attendees to check.

        Returns:
            bool: True if any of the attendees are enabled for the callbot, False otherwise.
        """
        stmt = select(ORMCallbotEnabledUser).where(ORMCallbotEnabledUser.email.in_(attendees))
        res = await session.execute(stmt)
        return res.fetchone() is not None
