from pydantic import BaseModel

from config_library import BaseConfig, FieldType
from common_db.config import PgSettings


class AppSettings(BaseModel):
    environment: str


class GoogleApplicationCreds(BaseModel):
    ...


class GoogleS3Settings(BaseModel):
    ...


class Settings(BaseConfig):
    app: FieldType[AppSettings] = 'env'
    db_config: FieldType[PgSettings] = 'db_config.env'
    google_application_credentials: FieldType[GoogleApplicationCreds] = 'google_application.env'

