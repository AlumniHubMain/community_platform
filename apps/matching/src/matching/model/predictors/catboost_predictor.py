"""CatBoost predictor"""
from catboost import CatBoostClassifier
import pandas as pd
import numpy as np

from .base import BasePredictor


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
