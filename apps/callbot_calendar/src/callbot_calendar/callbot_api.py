import requests

from schema import Event
from settings import callbot_calendar_settings as settings


def create_callbot(event: Event) -> str:
    payload = {"meeting_url": event.join_url, "emails": event.attendees, "wait_time": 10, "prompt_key": "default"}

    if not settings.callbot_api_token:
        settings.callbot_api_token = get_callbot_token()

    response = requests.post(
        f"{settings.callbot_api_url}/api/v1/callbots",
        json=payload,
        headers={"Authorization": f"Bearer {settings.callbot_api_token}"},
    )

    response.raise_for_status()
    return response.json()["callbot_id"]


def get_callbot_token() -> str:
    payload = {"username": "callbot_test", "password": settings.callbot_password}

    response = requests.post(
        f"{settings.callbot_api_url}/token",
        data=payload,
    )
    print(response.json())
    response.raise_for_status()
    return response.json()["access_token"]
