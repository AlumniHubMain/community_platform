import logging
from typing import TypeVar, Type

from pydantic_settings import PydanticBaseSettingsSource, EnvSettingsSource, \
    DotEnvSettingsSource, JsonConfigSettingsSource, YamlConfigSettingsSource


logger = logging.getLogger(__name__)


T = TypeVar('T')


def if_raw_type(type_: Type[T]) -> bool:
    return issubclass(type_, str) or issubclass(type_, int) or issubclass(type_, float) or issubclass(type_, bool)


def get_raw_value(path: str, type_: Type[T]) -> T:
    with open(path, 'r') as file:
        return type_(file.read())


def get_value(path: str, type_: Type[T]) -> T:
    source: PydanticBaseSettingsSource | None = None
    if path == 'env':
        logger.debug('Getting value from environment')
        source = EnvSettingsSource(
            settings_cls=type_,
            case_sensitive=False,
        )
    elif path.endswith('.env'):
        logger.debug('Getting value from dotenv file: %s', path)
        source = DotEnvSettingsSource(
            settings_cls=type_,
            env_file=path,
            env_file_encoding='utf-8',
            case_sensitive=False,
        )
    elif path.endswith('.json'):
        logger.debug('Getting value from json file: %s', path)
        source = JsonConfigSettingsSource(
            settings_cls=type_,
            json_file=path,
            json_file_encoding='utf-8',
        )
    elif path.endswith('.yaml'):
        logger.debug('Getting value from yaml file: %s', path)
        source = YamlConfigSettingsSource(
            settings_cls=type_,
            yaml_file=path,
            yaml_file_encoding='utf-8',
        )
    elif if_raw_type(type_):
        logger.debug('Assume source is raw %s', path)
        return get_raw_value(path, type_)


    if source is None:
        raise ValueError(f'Unsupported value source: {path}')

    return type_(**source())
