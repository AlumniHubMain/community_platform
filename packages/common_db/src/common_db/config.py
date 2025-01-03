from pydantic import BaseModel, SecretStr

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


# TODO(und3v3l0p3d): поменять после того как перенести миграции в пакет common_db
# class Settings(BaseConfig):
#     db_config: FieldType[PgSettings] = 'db_config.env'
#
# # При импорте файла сразу создастся и провалидируется объект конфига,
# # который можно далее импортировать из разных мест
# settings = Settings()