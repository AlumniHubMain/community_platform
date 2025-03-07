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
    filter_rule: str | list[str]


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
    rules=[
        {
            "name": "location_matching",
            "type": "location",
            "weight": 0.8,  # High weight since location is critical for offline meetings
            "params": {"city_penalty": 0.3, "country_penalty": 0.1},
        },
        {
            "name": "interests_matching",
            "type": "interests",
            "weight": 0.6,  # Medium-high weight for interest alignment
            "params": {
                "base_score": 0.5  # Base score when no interests match
            },
        },
        {
            "name": "expertise_matching",
            "type": "expertise",
            "weight": 0.7,  # High weight for professional matching
            "params": {
                "base_score": 0.6  # Higher base score for expertise
            },
        },
        {
            "name": "grade_matching",
            "type": "grade",
            "weight": 0.5,  # Medium weight for grade/seniority
            "params": {
                "base_score": 0.7  # High base score since grade is less critical
            },
        },
        {
            "name": "intent_specific",
            "type": "intent_specific",
            "weight": 0.9,  # Highest weight since it combines multiple factors
            "params": {
                "non_mentor_penalty": 0.5,  # Penalty for non-senior mentors
                "expertise_base_score": 0.4,  # Base score for expertise in mentoring
                "interest_base_score": 0.3,  # Base score for interests in cooperative learning
            },
        },
    ],
    filters=[],  # Using rules instead of filters
    diversifications=[],  # Can add diversification if needed
    exclude_users=[],
    exclude_companies=[],
    settings_name="heuristic",
    model_type=ModelType.HEURISTIC,
)

model_settings_presets = {
    model_settings_preset_catboost.settings_name: model_settings_preset_catboost,
    model_settings_preset_heuristic.settings_name: model_settings_preset_heuristic,
}
