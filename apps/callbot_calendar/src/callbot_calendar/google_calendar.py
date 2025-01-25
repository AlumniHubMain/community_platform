import argparse
import asyncio
import logging

from google.oauth2.service_account import Credentials

from googleapiclient.discovery import build

from datetime import UTC, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from common_db.db_abstract import db_manager

from common_db.models.callbot import ORMCallbotScheduledMeeting
from schema import Event
from settings import callbot_calendar_settings as settings


# ROBOT_EMAIL = "call-bot-calendar-test@communityp-440714.iam.gserviceaccount.com"
# # CALENDAR_ID = "6eaed8ffd23f46e6405237f1cc69453b9118d513be23fd2acf2ccdc592301f5e@group.calendar.google.com"
# CALENDAR_ID = "primary"
# CREDENTIALS_FILE = "./communityp-440714-48e01c4b5888.json"


def check_robot_events(calendar_id: str, robot_email: str, credentials_file: str, last_checked: datetime):
    """
    Checks for events involving the robot email in a Google Calendar.

    Args:
        calendar_id (str): The ID of the Google Calendar.
        robot_email (str): The robot's email address to check for in attendees.
        credentials_file (str): Path to the service account credentials JSON file.
        last_checked (datetime.datetime): The last datetime to check from.

    Returns:
        list: Events involving the robot email since the last checked time.
    """
    credentials = Credentials.from_service_account_file(
        credentials_file, scopes=["https://www.googleapis.com/auth/calendar"]
    )
    service = build("calendar", "v3", credentials=credentials)

    time_min = last_checked.isoformat()

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
    for e in events:
        if any(attendee.get("email") == robot_email for attendee in e.get("attendees", [])):
            yield e


async def read_calendar():
    LAST_CHECKED = datetime.now(UTC) - timedelta(days=1)

    async with db_manager.session() as session:
        for event in check_robot_events(
            settings.calendar_id, settings.robot_email, settings.credentials_file, LAST_CHECKED
        ):
            try:
                # validate using pydantic
                pydantic_event = Event(
                    google_id=event["id"],
                    subject=event["summary"],
                    start_time=event["start"]["dateTime"],
                    end_time=event["end"]["dateTime"],
                    attendees=[attendee.get("email") for attendee in event.get("attendees", [])],
                    join_url=event["hangoutLink"],
                )
                logging.info(pydantic_event.model_dump_json(indent=4))

                # upsert
                stmt = select(ORMCallbotScheduledMeeting).where(
                    ORMCallbotScheduledMeeting.google_id == pydantic_event.google_id
                )
                result = await session.execute(statement=stmt)
                stored_event: ORMCallbotScheduledMeeting = result.scalar_one_or_none()
                if not stored_event:
                    stored_event = ORMCallbotScheduledMeeting(google_id=pydantic_event.google_id)
                    session.add(stored_event)

                # store to the database as an upcoming meeting
                stored_event.start_time = pydantic_event.start_time
                stored_event.end_time = pydantic_event.end_time
                print("\n".join(pydantic_event.attendees))
                stored_event.attendees = "\n".join(pydantic_event.attendees)
                stored_event.join_url = pydantic_event.join_url
                stored_event.subject = pydantic_event.subject
                await session.commit()

            except Exception as e:
                logging.error(e, event, stored_event)
                raise


async def get_upcoming_meetings(start_time: datetime, end_time: datetime):
    async with db_manager.session() as session:
        stmt = (
            select(ORMCallbotScheduledMeeting)
            .where(ORMCallbotScheduledMeeting.google_id.isnot(None))
            .where(start_time <= ORMCallbotScheduledMeeting.start_time)
            .where(ORMCallbotScheduledMeeting.start_time <= end_time)
        )
        res = await session.execute(statement=stmt)
        for e in res.scalars():
            event = Event.model_validate(e)
            # TODO: invite the bot
            print(event)


async def main():
    parser = argparse.ArgumentParser(description="Launcher for Calendar Tasks")
    parser.add_argument(
        "task",
        type=str,
        choices=["read_calendar", "upcoming_meetings"],
        help="Specify the task to run: read_calendar, upcoming_meetings"
    )
    args = parser.parse_args()

    if args.task == "read_calendar":
        future = read_calendar()
    elif args.task == "upcoming_meetings":
        future = get_upcoming_meetings(datetime.now() - timedelta(days=2), datetime.now())
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
