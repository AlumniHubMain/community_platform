from pydantic import BaseModel, SecretStr
from pydantic_core import ValidationError

from config_library import BaseConfig, FieldType


class PgSettings(BaseModel):
    db_host: SecretStr
    db_port: int
    db_name: SecretStr
    db_user: SecretStr
    db_pass: SecretStr
    db_schema: str  # DB_SCHEMA=your_schema (default=public)

    @property
    def database_url_asyncpg(self) -> SecretStr:
        return SecretStr(
            f"postgresql+asyncpg://"
            f"{self.db_user.get_secret_value()}:"
            f"{self.db_pass.get_secret_value()}@"
            f"{self.db_host.get_secret_value()}:"
            f"{self.db_port}/"
            f"{self.db_name.get_secret_value()}"
        )

class DbSettings(BaseConfig):
    db: FieldType[PgSettings] = './config/db_config.env'

class DbSettingsLocal(BaseConfig):
    db: FieldType[PgSettings] = '../../config/db.json'

try:
    db_settings = DbSettings()
except ValidationError as e:
    print(f"Error loading DbSettings from /config/db.json: {e}")
    db_settings = DbSettingsLocal()

schema: str = db_settings.db.db_schema
