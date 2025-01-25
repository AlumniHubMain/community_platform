from pydantic import BaseModel
from config_library import FieldType, BaseConfig


class CallbotCalendarConfig(BaseModel):
    calendar_id: str
    credentials_file: str
    robot_email: str


class CallbotCalendarSettings(BaseConfig):
    callbot_calendar: FieldType[CallbotCalendarConfig] = "/config/callbot_calendar.json"


callbot_calendar_settings = CallbotCalendarSettings().callbot_calendar
