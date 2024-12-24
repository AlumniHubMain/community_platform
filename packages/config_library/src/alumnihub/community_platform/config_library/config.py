import json

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PlatformSettings(BaseSettings):
    def read_file(self, field_name: str) -> str:
        with open(self.model_dump()[field_name]) as file_to_read:
            return file_to_read.read()

    # No way to define return type for json object in python
    def read_json_file(self, field_name: str):
        return json.loads(self.read_file(field_name))

    # Cannot annotate result_type because it's py type
    def read_dotenv_config(self, field_name: str, result_type) -> BaseSettings:
        return result_type(_env_file=self.model_dump()[field_name], _env_file_encoding='utf-8')


class PlatformPGSettings(BaseSettings):
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

    model_config = SettingsConfigDict(
        # .env is default filename. It can be replaced by passing _env_file param into constructor.
        # See PlatformSettings.read_dotenv_config() method
        env_file='.env', env_file_encoding='utf-8'
    )

