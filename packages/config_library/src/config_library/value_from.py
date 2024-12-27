
from typing import TypeVar, Type

from pydantic_settings import PydanticBaseSettingsSource, EnvSettingsSource, \
    DotEnvSettingsSource, JsonConfigSettingsSource, YamlConfigSettingsSource


T = TypeVar('T')

def get_value(path: str, type_: Type[T]) -> T:
    source: PydanticBaseSettingsSource | None = None
    if path == 'env':
        source = EnvSettingsSource(
            settings_cls=type_,
            case_sensitive=False,
        )
    elif path.endswith('.env'):
        source = DotEnvSettingsSource(
            settings_cls=type_,
            env_file=path,
            env_file_encoding='utf-8',
        )
    elif path.endswith('.json'):
        source = JsonConfigSettingsSource(
            settings_cls=type_,
            json_file=path,
            json_file_encoding='utf-8',
        )
    elif path.endswith('.yaml'):
        source = YamlConfigSettingsSource(
            settings_cls=type_,
            yaml_file=path,
            yaml_file_encoding='utf-8',
        )

    if source is None:
        raise ValueError(f'Unsupported value source: {path}')

    return type_(**source())
