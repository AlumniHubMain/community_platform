"""Model settings"""

from enum import Enum
from pydantic import BaseModel


class FilterType(Enum):
    """Filter type"""

    STRICT = "strict"
    SOFT = "soft"
    CUSTOM = "custom"


class DiversificationType(Enum):
    """Diversification type"""

    SCORE_BASED = "score_based"
    PROPORTIONAL = "proportional"


class FilterSettings(BaseModel):
    """Filter settings"""

    filter_type: FilterType
    filter_name: str
    filter_column: str
    filter_rule: str


class DiversificationSettings(BaseModel):
    """Diversification settings"""

    diversification_type: DiversificationType
    diversification_name: str
    diversification_column: str
    diversification_value: int


class ModelType(Enum):
    """Type of model to use for predictions"""

    CATBOOST = "catboost"
    HEURISTIC = "heuristic"


class ModelSettings(BaseModel):
    """Model settings"""

    settings_name: str | None = None
    filters: list[FilterSettings] = []
    diversifications: list[DiversificationSettings] = []
    exclude_users: list[int] = []
    exclude_companies: list[str] = []


class CatBoostModelSettings(ModelSettings):
    """CatBoost model settings"""

    model_type: ModelType = ModelType.CATBOOST
    model_path: str


class HeuristicModelSettings(ModelSettings):
    """Heuristic model settings"""

    model_type: ModelType = ModelType.HEURISTIC
    rules: list[dict]


model_settings_preset_catboost = CatBoostModelSettings(
    model_path="gs://matching-model-bucket/model.m",
    filters=[],
    diversifications=[],
    exclude_users=[],
    exclude_companies=[],
    settings_name="catboost",
)

model_settings_preset_heuristic = HeuristicModelSettings(
    rules=[],
    filters=[],
    diversifications=[],
    exclude_users=[],
    exclude_companies=[],
    settings_name="heuristic",
)

model_settings_presets = {
    model_settings_preset_catboost.settings_name: model_settings_preset_catboost,
    model_settings_preset_heuristic.settings_name: model_settings_preset_heuristic,
}
