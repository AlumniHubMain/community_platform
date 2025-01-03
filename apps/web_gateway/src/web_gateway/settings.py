from pydantic import BaseModel

from config_library import BaseConfig, FieldType
from common_db.config import PgSettings


class GoogleS3Settings(BaseModel):
    bucket: str


class Settings(BaseConfig):
    environment: FieldType[str] = '/config/environment'
    db: FieldType[PgSettings] = '/config/db.json'
    google_application_credentials: FieldType[str] = '/config/credentials'
    s3: FieldType[GoogleS3Settings] = '/config/s3.json'


settings = Settings()
