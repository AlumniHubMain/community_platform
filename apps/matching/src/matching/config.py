from pydantic import BaseModel
from config_library import FieldType, BaseConfig


class MatchingConfig(BaseModel):
    project_id: str
    bucket_name: str

class MatchingSettings(BaseConfig):
    matching: FieldType[MatchingConfig] = '/config/matching.json'

matching_settings = MatchingSettings()
