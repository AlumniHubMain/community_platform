"""Base predictor"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np


class BasePredictor(ABC):
    """Abstract base class for prediction models"""

    @abstractmethod
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Make predictions on features"""
