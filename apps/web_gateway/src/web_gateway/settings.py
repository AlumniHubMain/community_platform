from pydantic import BaseModel

from config_library import BaseConfig, FieldType


class SecretFiles(BaseModel):
    access_secret_file: str
    bot_token_file: str


class EmitterSettings(BaseModel):
    meetings_notification_target: str
    meetings_google_pubsub_notification_topic: str
    matching_requests_google_pubsub_topic: str
    matching_requests_google_pubsub_project_id: int


class MatchingRequestsSettings(BaseModel):
    requested_users_count: int
    model_settings_preset: str
    matching_delay_sec: int


class LimitsSettings(BaseModel):
    max_user_confirmed_meetings_count: int
    max_user_pended_meetings_count: int


class Settings(BaseConfig):
    # ToDo(und3v3l0p3d): Move db_config into root config
    environment: str = 'dev'
    google_application_credentials: str  = './config/credentials.json'
    google_cloud_bucket: str = 'community_platform_media1'
    access_secret_file: FieldType[str] = './config/access_secret_file'
    bot_token_file: FieldType[str] = './config/token'
    emitter_settings: FieldType[EmitterSettings] = './public_config/emitter_settings.json'
    limits: FieldType[LimitsSettings] = './public_config/limits.json'
    matching_requests: FieldType[MatchingRequestsSettings] = "./public_config/matching_requests.json"


settings = Settings()
