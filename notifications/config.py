from google.oauth2 import service_account
import os

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    email_serv_pass: SecretStr
    email_serv_sender: SecretStr
    ps_credentials_path: str
    ps_project_id: str
    ps_notification_topic: str
    ps_notification_sub_name: str
    ps_notification_tg_topic: str
    ps_notification_tg_sub_name: str

    model_config = SettingsConfigDict(env_file=os.environ.get('DOTENV', '.env'), env_file_encoding='utf8')

    @property
    def ps_credentials(self) -> service_account.Credentials:
        """Getting credentials from a JSON file"""
        return service_account.Credentials.from_service_account_file(self.ps_credentials_path)


settings = Settings()
