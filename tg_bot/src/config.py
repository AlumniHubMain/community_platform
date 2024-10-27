import os
from pathlib import Path
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: SecretStr

    model_config = SettingsConfigDict(env_file=os.environ.get('DOTENV', '.env'), env_file_encoding='utf8')


# При импорте файла сразу создастся и провалидируется объект конфига, который можно далее импортировать из разных мест
settings = Settings()
