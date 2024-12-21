import json
import datetime as dt
from enum import Enum
from typing import Any, Union
import os


# Default user limits values
class EDefaultUserLimits(Enum):
    MAX_PENDED_MEETINGS_COUNT = 6
    MAX_CONFIRMED_MEETINGS_COUNT = 3


class LimitsConfig:
    def __init__(self, config_path: os.PathLike, min_update_delay_sec: int=60):
        self.config_path = config_path
        self.min_update_delay_sec = min_update_delay_sec
        
        self.last_update = None
        self.config = None
        # First config load
        _ = self.update()

    def get(self, key: str, default=None) -> Union[Any | None]:
        self._update_state_if_needed()
        if self.config:
            return self.config.get(key, default)
        return default
    
    def _update_state_if_needed(self) -> bool:
        if (dt.datetime.now() - self.last_update).seconds > self.min_update_delay_sec:
            return self.update()
        return True

    def update(self) -> bool:
        # Copy actual state
        new_config = self.config
        update_timestamp = self.last_update
        
        # Try to update config state
        try:
            with open(self.config_path, 'r') as file:
                new_config = json.load(file)
                update_timestamp = dt.datetime.now()
        except Exception:
            return False

        # Save state with consistency guarantee
        self.config = new_config
        self.last_update = update_timestamp
        return True
