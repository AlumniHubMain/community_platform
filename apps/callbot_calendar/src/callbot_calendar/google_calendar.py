import argparse
import asyncio
import logging

from datetime import UTC, datetime, timedelta

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from common_db.db_abstract import db_manager
from common_db.models.callbot import ORMCallbotMeeting, ORMCallbotEnabledUser
from callbot_api import create_callbot
from schema import Event
from settings import callbot_calendar_settings as settings


def is_robot_invited(event: Event) -> bool:
    return settings.robot_email in event.attendees


async def are_attendees_eligible(event: Event) -> bool:
    """
    Checks if at least one attendee is eligible to start the callbot.
    """
    async with db_manager.session() as session:
        stmt = select(ORMCallbotEnabledUser).where(ORMCallbotEnabledUser.email.in_(event.attendees))
        res = await session.execute(stmt)
        return res.fetchone() is not None


async def is_event_valid(stored_event: Event) -> bool:
    """
    Validates if the event is valid for callbot to join.

    Args:
        event (Event): The event to validate.

    Returns:
        bool: True if the event is valid, False otherwise.
    """
    google_id = stored_event.google_id
    logging.info(f"Validating event: {google_id}")

    # Fetch the event from Google Calendar to check if it's still valid
    service = build_calendar_service()
    if event := service.events().get(calendarId=settings.calendar_id, eventId=google_id).execute():
        if event.get("status") == "cancelled":
            logging.info(f"Event {google_id} has been cancelled")
            return False
        try:
            event = validate_event(event)
        except Exception as e:
            logging.error(e, event)
            return False
        if not is_robot_invited(event):
            logging.info(f"Robot not invited to event {google_id}")
            return False
        if event.end_time < datetime.now(UTC):
            logging.info(f"Event {google_id} has already ended")
            return False
        if not await are_attendees_eligible(event):
            logging.info(f"No eligible attendees for event {google_id}")
            return False
        return True
    return False


def build_calendar_service() -> Credentials:
    credentials = Credentials.from_service_account_file(
        settings.credentials_file, scopes=["https://www.googleapis.com/auth/calendar"]
    )
    return build("calendar", "v3", credentials=credentials)


def check_robot_events(
    calendar_id: str = settings.calendar_id,
    start_time: datetime = datetime.now(),
):
    """
    Checks for events involving the robot email in a Google Calendar.

    Args:
        calendar_id (str): The ID of the Google Calendar.
        last_checked (datetime.datetime): The last datetime to check from.

    Returns:
        list: Events involving the robot email since the last checked time.
    """
    service = build_calendar_service()
    time_min = start_time.isoformat()

    # Fetch events where the robot email is involved
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min,
            singleEvents=True,
            orderBy="startTime",
            fields="items(id,attendees,summary,start,end,hangoutLink)",
        )
        .execute()
    )

    events = events_result.get("items", [])
    return events


def validate_event(event: dict) -> Event:
    """
    Validates the event dictionary.

    Args:
        event (dict): The event dictionary to validate.

    Returns:
        Event: The validated event.
    """
    pydantic_event = Event(
        google_id=event["id"],
        subject=event["summary"],
        start_time=event["start"]["dateTime"],
        end_time=event["end"]["dateTime"],
        attendees=[attendee.get("email") for attendee in event.get("attendees", [])],
        join_url=event["hangoutLink"],
    )
    logging.info(pydantic_event.model_dump_json(indent=4))
    return pydantic_event


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


async def get_event_by_google_id(session: AsyncSession, google_id: str) -> ORMCallbotMeeting | None:
    stmt = select(ORMCallbotMeeting).where(ORMCallbotMeeting.google_id == google_id)
    result = await session.execute(statement=stmt)
    return result.scalar_one_or_none()


async def process_event(event: Event, session: AsyncSession):
    stored_event = await get_event_by_google_id(session, event.google_id)

    if not is_robot_invited(event):
        logging.info(f"Robot not invited to event {event.google_id}")
        if stored_event:
            session.delete(stored_event)
        return

    # upsert
    if not stored_event:
        stored_event = ORMCallbotMeeting()
        session.add(stored_event)

    convert_to_orm(event, stored_event)

    await session.commit()


async def read_calendar(start_time: datetime):
    async with db_manager.session() as session:
        for event in check_robot_events(start_time=start_time):
            try:
                await process_event(validate_event(event), session)
            except Exception as e:
                logging.error(e, event, event)
                raise


async def get_upcoming_events(start_time: datetime, end_time: datetime):
    async with db_manager.session() as session:
        stmt = (
            select(ORMCallbotMeeting)
            .where(ORMCallbotMeeting.google_id.isnot(None))
            .where(start_time <= ORMCallbotMeeting.start_time)
            .where(ORMCallbotMeeting.start_time <= end_time)
        )
        res = await session.execute(statement=stmt)
        for e in res.scalars():
            event = Event.model_validate(e)
            if await is_event_valid(event):
                logging.info(f"Upcoming meeting: {event}")
                logging.info(f"Creating callbot for event {event.google_id}")
                callbot_id = create_callbot(event)
                logging.info(f"Callbot created: {callbot_id}")
                e.callbot_id = callbot_id
                await session.commit()


async def main():
    parser = argparse.ArgumentParser(description="Launcher for Calendar Tasks")
    parser.add_argument(
        "task",
        type=str,
        choices=["read_calendar", "upcoming_events"],
        help="Specify the task to run: read_calendar, upcoming_events",
    )
    args = parser.parse_args()

    if args.task == "read_calendar":
        logging.info(f"Reading Google calendar: {settings.calendar_id}")
        future = read_calendar(start_time=datetime.now(UTC) - timedelta(days=2))
    elif args.task == "upcoming_events":
        logging.info("Getting upcoming events")
        future = get_upcoming_events(
            start_time=datetime.now(UTC) - timedelta(hours=2), end_time=datetime.now(UTC) + timedelta(minutes=10)
        )
    else:
        return

    await future


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d:%H:%M:%S",
        level=logging.INFO,
    )
    asyncio.run(main())
