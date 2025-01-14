from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import catboost


class BasePredictor(ABC):
    """Abstract base class for prediction models"""

    @abstractmethod
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Make predictions on features"""


class CatBoostPredictor(BasePredictor):
    """CatBoost model predictor"""

    def __init__(self):
        self.model = None

    def load_model(self, model_path: str):
        """Load saved CatBoost model"""
        self.model = catboost.CatBoostClassifier()
        self.model.load_model(model_path)

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Make predictions using CatBoost model"""
        if self.model is None:
            raise ValueError("Model not loaded")
        return self.model.predict_proba(features)[:, 1]


class HeuristicPredictor(BasePredictor):
    """Heuristic-based predictor"""

    def __init__(self, rules: list[dict]):
        """Initialize with list of rules

        Each rule is a dict with:
        - column: str - column name to check
        - operation: str - 'equals', 'contains', 'greater_than', etc
        - value: any - value to compare against
        - weight: float - weight of this rule (0-1)
        """
        self.rules = rules

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Apply heuristic rules to make predictions"""
        scores = np.zeros(len(features))

        for rule in self.rules:
            col = rule["column"]
            op = rule["operation"]
            val = rule["value"]
            weight = rule["weight"]

            if op == "equals":
                mask = features[col] == val
            elif op == "contains":
                mask = features[col].str.contains(val, na=False)
            elif op == "greater_than":
                mask = features[col] > val
            elif op == "less_than":
                mask = features[col] < val
            else:
                continue

            scores[mask] += weight

        if len(self.rules) == 0:
            return scores
        return scores / len(self.rules)
