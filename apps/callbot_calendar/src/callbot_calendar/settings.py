from pydantic import BaseModel
from config_library import FieldType, BaseConfig


class CallbotCalendarConfig(BaseModel):
    calendar_id: str
    callbot_api_token: str
    callbot_api_url: str
    credentials_file: str
    robot_email: str
    callbot_password: str
    join_time_earliest: int = 5  # The earliest time to join a call in minutes before the start time.
    join_time_latest: int = 20  # The latest time to join a call in minutes after the start time.


class CallbotCalendarSettings(BaseConfig):
    callbot_calendar: FieldType[CallbotCalendarConfig] = "./config/callbot/callbot_calendar.json"


callbot_calendar_settings = CallbotCalendarSettings().callbot_calendar
