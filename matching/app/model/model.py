"""Model class for loading and applying catboost model with filters and diversification"""

import pandas as pd

from .model_settings import ModelSettings, FilterType, DiversificationType, ModelType
from .predictors import CatBoostPredictor, HeuristicPredictor


class Model:
    """Model class for matching predictions and reranking"""

    def __init__(self, model_settings: ModelSettings):
        """Initialize model with settings"""
        self.model_settings = model_settings
        self.predictor = None

    def load_model(self, model_path: str):
        """Load model predictor based on settings"""
        if self.model_settings.model_type == ModelType.HEURISTIC:
            self.predictor = HeuristicPredictor(self.model_settings)
        elif self.model_settings.model_type == ModelType.CATBOOST:
            self.predictor = CatBoostPredictor()
            self.predictor.load_model(model_path)

    def predict(self, features: pd.DataFrame, user_id: int) -> pd.DataFrame:
        """Make predictions and apply filters and diversification"""
        if self.predictor is None:
            raise ValueError("Model not loaded")

        created_features = self.create_features(features, user_id)

        predictions = self.predictor.predict(created_features)
        results_df = features.copy()
        results_df["score"] = predictions

        for filter_setting in self.model_settings.filters:
            results_df = self._apply_filter(results_df, filter_setting)

        for div_setting in self.model_settings.diversifications:
            results_df = self._apply_diversification(results_df, div_setting)

        results_df = self._apply_exclusions(results_df)

        return results_df.sort_values("score", ascending=False)

    def _apply_filter(self, df: pd.DataFrame, filter_setting, row_callable=None) -> pd.DataFrame:
        """Apply filter based on settings"""
        if filter_setting.filter_type == FilterType.STRICT:
            return df[df[filter_setting.filter_column] == filter_setting.filter_rule]
        elif filter_setting.filter_type == FilterType.SOFT:
            mask = df[filter_setting.filter_column] == filter_setting.filter_rule
            df.loc[~mask, "score"] *= 0.5
            return df
        elif filter_setting.filter_type == FilterType.CUSTOM:
            df['filter_result'] = df.apply(row_callable, axis=1)
            return df[df['filter_result']]
        return df

    def _apply_diversification(self, df: pd.DataFrame, div_setting) -> pd.DataFrame:
        """Apply diversification based on settings"""
        if div_setting.diversification_type == DiversificationType.SCORE_BASED:
            # Sort by score descending
            df = df.sort_values("score", ascending=False)
            result_indices = []
            used_positions = set()

            # Group by the diversification column
            groups = df.groupby(div_setting.diversification_column)

            # For each group, ensure minimum distance between same values
            for _, group in groups:
                group_indices = group.index.tolist()
                for idx in group_indices:
                    # Find next available position that maintains minimum distance
                    position = 0
                    while position in used_positions:
                        position += 1

                    # Check if this position would violate minimum distance
                    valid = True
                    for prev_pos in used_positions:
                        if abs(position - prev_pos) < div_setting.diversification_value:
                            valid = False
                            break

                    if valid:
                        result_indices.append((position, idx))
                        used_positions.add(position)

            # Sort by position and get original indices
            result_indices.sort()
            final_indices = [idx for _, idx in result_indices]
            return df.loc[final_indices]

        elif div_setting.diversification_type == DiversificationType.PROPORTIONAL:
            # Similar logic but weighted by group proportions
            total_groups = len(df[div_setting.diversification_column].unique())
            spacing = max(div_setting.diversification_value // total_groups, 1)

            df = df.sort_values("score", ascending=False)
            result_indices = []
            used_positions = set()

            groups = df.groupby(div_setting.diversification_column)
            group_weights = groups.size() / len(df)

            for group_name, group in groups:
                weight = group_weights[group_name]
                group_indices = group.index.tolist()
                target_positions = int(len(df) * weight)

                for idx in group_indices[:target_positions]:
                    position = 0
                    while position in used_positions:
                        position += spacing

                    result_indices.append((position, idx))
                    used_positions.add(position)

            result_indices.sort()
            final_indices = [idx for _, idx in result_indices]
            return df.loc[final_indices]

        return df

    def _apply_exclusions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply user and company exclusions"""
        if self.model_settings.exclude_users:
            df = df[~df["user_id"].isin(self.model_settings.exclude_users)]
        if self.model_settings.exclude_companies:
            df = df[~df["company"].isin(self.model_settings.exclude_companies)]
        return df
