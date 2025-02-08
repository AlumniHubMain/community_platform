from pydantic import BaseModel
from config_library import FieldType, BaseConfig


class MatchingConfig(BaseModel):
    project_id: str
    bucket_name: str


class EmitterSettings(BaseModel):
    meetings_notification_target: str
    meetings_google_pubsub_notification_topic: str


class LimitsSettings(BaseModel):
    max_user_confirmed_meetings_count: int
    max_user_pended_meetings_count: int


class Settings(BaseConfig):
    # ToDo(und3v3l0p3d): Move db_config into root config
    google_application_credentials: str = "../../credentials/credentials.json"
    google_cloud_bucket: str = "community_platform_media1"
    environment: str = "../../config/environment/environment"
    emitter_settings: FieldType[EmitterSettings] = "../../config/emitter_settings/emitter_settings.json"
    limits: FieldType[LimitsSettings] = "../../config/limits/limits.json"
    matching: FieldType[MatchingConfig] = "../../config/matching/matching.json"


settings = Settings()
