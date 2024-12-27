from collections import defaultdict
from typing import Any, Type

from config_library import value_from


class Storage:
    _register: dict[str, dict[str, Any]]
    _stored: dict[str, dict[str, Any]]

    def __init__(self):
        self._register = defaultdict(dict)
        self._stored = defaultdict(dict)

    def register(self, key: str, type_: Type[Any]):
        print(f'Registering {key} with {type_}')
        self._register[key][str(type_)] = type_

    def get(self, key: str, type_: Type[Any]) -> Any:
        if key not in self._register:
            raise ValueError(f'Unknown key: {key}')

        if key not in self._stored:
            self._stored[key][str(type_)] = value_from.get_value(key, type_)

        return self._stored[key][str(type_)]


STORAGE = Storage()
