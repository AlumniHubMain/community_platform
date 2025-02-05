import argparse
import asyncio
import logging

from datetime import UTC, datetime, timedelta

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.db_abstract import db_manager
from callbot_api import create_callbot
from schema import Event
from settings import callbot_calendar_settings as settings
from callbot_calendar_manager import CallbotCalendarManager


def is_robot_invited(event: Event) -> bool:
    return settings.robot_email in event.attendees


async def is_event_valid(session: AsyncSession, stored_event: Event) -> bool:
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
        if not await CallbotCalendarManager.any_of_attendees_enabled(session, event.attendees):
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
    print(event)
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


async def process_event(event: Event, session: AsyncSession):
    if is_robot_invited(event):
        await CallbotCalendarManager.save_event(session, event)
    else:
        logging.info(f"Robot not invited to event {event.google_id}")
        await CallbotCalendarManager.delete_event(session, event.google_id)
        return


async def read_calendar(start_time: datetime):
    async with db_manager.session() as session:
        for event in check_robot_events(start_time=start_time):
            try:
                await process_event(validate_event(event), session)
            except Exception as e:
                logging.error(e, event, event)


async def start_callbot_for_upcoming_events(start_time_from: datetime, end_time_to: datetime):
    logging.info(f"Checking for upcoming events from {start_time_from} to {end_time_to}")
    async with db_manager.session() as session:
        async for e in CallbotCalendarManager.get_upcoming_events_not_joined(session, start_time_from, end_time_to):
            event = Event.model_validate(e)
            if await is_event_valid(session, event):
                logging.info(f"Upcoming meeting: {event}")
                logging.info(f"Creating callbot for event {event.google_id}")
                callbot_id = create_callbot(event)
                logging.info(f"Callbot created: {callbot_id}")
                await CallbotCalendarManager.record_callbot_id(session, e.google_id, callbot_id)


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
        future = read_calendar(start_time=datetime.now(UTC) - timedelta(hours=2))
    elif args.task == "upcoming_events":
        logging.info("Processing upcoming events")
        future = start_callbot_for_upcoming_events(
            start_time_from=datetime.now(UTC)
            + timedelta(minutes=settings.join_time_earliest),  # join 5 minutes before the event
            end_time_to=datetime.now(UTC),  # join all events that are currently ongoing
        )
    else:
        logging.error("Invalid task")
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
