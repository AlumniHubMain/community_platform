from google.oauth2 import service_account
import os

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: SecretStr
    ps_credentials_path: str
    ps_project_id: str
    ps_notification_tg_topic: str
    ps_notification_tg_sub_name: str

    model_config = SettingsConfigDict(env_file=os.environ.get('DOTENV', '.env'), env_file_encoding='utf8')

    @property
    def ps_credentials(self) -> service_account.Credentials:
        """Getting credentials from a JSON file"""
        return service_account.Credentials.from_service_account_file(self.ps_credentials_path)


# При импорте файла сразу создастся и провалидируется объект конфига, который можно далее импортировать из разных мест
settings = Settings()
