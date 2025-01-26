from pydantic import BaseModel
from pydantic_core import ValidationError
from config_library import FieldType, BaseConfig


class MatchingConfig(BaseModel):
    project_id: str
    bucket_name: str


class MatchingSettings(BaseConfig):
    matching: FieldType[MatchingConfig] = "/config/matching.json"


class MatchingSettingsLocal(BaseConfig):
    matching: FieldType[MatchingConfig] = "../../config/matching.json"


try:
    matching_settings = MatchingSettings()
except ValidationError as e:
    print(f"Error loading MatchingSettings from /config/matching.json: {e}")
    matching_settings = MatchingSettingsLocal()
