from google.oauth2.service_account import Credentials

from googleapiclient.discovery import build

from datetime import UTC, datetime, timedelta

ROBOT_EMAIL = "call-bot-calendar-test@communityp-440714.iam.gserviceaccount.com"
# CALENDAR_ID = "6eaed8ffd23f46e6405237f1cc69453b9118d513be23fd2acf2ccdc592301f5e@group.calendar.google.com"
CALENDAR_ID="primary"
CREDENTIALS_FILE = "./communityp-440714-48e01c4b5888.json"


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


# Example usage
if __name__ == "__main__":
    LAST_CHECKED = datetime.now(UTC) - timedelta(days=1)

    for event in check_robot_events(CALENDAR_ID, ROBOT_EMAIL, CREDENTIALS_FILE, LAST_CHECKED):
        pass
