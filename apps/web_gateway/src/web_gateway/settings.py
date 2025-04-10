from pydantic import BaseModel

from config_library import BaseConfig, FieldType


class Secrets(BaseConfig, BaseModel):
    access_secret: FieldType[str]
    bot_token: FieldType[str]


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
    environment: str = "dev"
    google_application_credentials: str = "../../credentials/credentials.json"
    google_cloud_bucket: str = "community_platform_media1"
    emitter_settings: FieldType[EmitterSettings] = "./public_config/emitter_settings.json"
    limits: FieldType[LimitsSettings] = "./public_config/limits.json"
    matching_requests: FieldType[MatchingRequestsSettings] = "./public_config/matching_requests.json"
    secrets: FieldType[Secrets] = "./public_config/secret_files.json"

    # PubSub Topics & Subscriptions - TODO: get! from where?
    pubsub_linkedin_tasks_topic: str = "linkedin-tasks"
    pubsub_linkedin_tasks_sub: str = "linkedin-tasks-sub"
    pubsub_limits_alert_topic: str = "linkedin-limits"
    pubsub_limits_alert_sub: str = "linkedin-limits-sub"
    google_cloud_project: str = 'communityp-440714'


settings = Settings()
