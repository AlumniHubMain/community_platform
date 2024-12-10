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

    model_type: ModelType
    model_path: str | None = None
    filters: list[FilterSettings] = []
    diversifications: list[DiversificationSettings] = []
    exclude_users: list[int] = []
    exclude_companies: list[str] = []
