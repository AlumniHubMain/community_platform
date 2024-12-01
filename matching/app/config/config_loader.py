"""Модуль для управления конфигурацией сервиса."""

import os
import logging
from typing import Literal
import json

from google.cloud import logging as google_cloud_logging
from google.cloud import secretmanager
from google.protobuf import text_format, json_format
from app.config.config_proto.config_pb2 import Config as ConfigProto  # pylint: disable=no-name-in-module, import-error


class ConfigLoader:
    """Класс для загрузки конфигурации и инициализации логгера."""

    def __init__(
        self,
        instance_stage: Literal["prod", "staging", "dev"] = "prod",
        logging_stream: Literal["google", "default"] = "google",
    ):
        self.instance_stage = instance_stage
        self.logging_stream = logging_stream
        self._load_config()
        self._init_logger()
        self._load_secrets_google()
        self._load_to_env()

    def _load_config(self):
        config_path = os.path.join(os.path.os.path.dirname(__file__), "config_proto/config.textproto")
        with open(config_path, "r", encoding="utf-8") as f:
            config_text = f.read()

        self.proto_config = ConfigProto()
        text_format.Parse(config_text, self.proto_config)
        json_config = json_format.MessageToJson(self.proto_config)
        self.config_dict = json.loads(json_config)[self.instance_stage]

    def _init_logger(self):
        if self.logging_stream == "google":
            client = google_cloud_logging.Client()
            client.setup_logging(log_level=self.active_config.log_level)
        else:
            logging.basicConfig(level=self.active_config.log_level)
        self.logger = logging.getLogger()

    @property
    def active_config(self):
        """Возвращает активную конфигурацию в зависимости от текущей среды."""
        match self.instance_stage:
            case "prod":
                return self.proto_config.prod
            case "staging":
                return self.proto_config.staging
            case "dev":
                return self.proto_config.dev
            case _:
                return {}

    def _load_secrets_google(
        self,
    ):
        """
        Retrieve Cloud SQL credentials stored in Secret Manager
        or default to environment variables.
        """
        secret = os.environ.get("matching_service_config")
        if secret:
            self.variables = json.loads(secret)
        else:
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv("PROJECT_ID", "communityp")
            secret_id = os.getenv("SECRET_ID", "matching_service_config")
            version_id = os.getenv("VERSION_SECRET", "latest")
            name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
            response = client.access_secret_version(request={"name": name})
            self.variables = json.loads(response.payload.data.decode("UTF-8"))

    def _load_to_env(
        self,
    ):
        for key, value in (self.variables | self.config_dict).items():
            os.environ[key] = value


config = ConfigLoader()
