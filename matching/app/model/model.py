"""Model class for loading and applying catboost model with filters and diversification"""

import pandas as pd

from db_common.schemas import convert_enum_value

from .model_settings import ModelSettings, FilterType, DiversificationType, ModelType
from .predictors import CatBoostPredictor, HeuristicPredictor
from db_common.schemas import UserProfile, LinkedInProfile, MeetingIntent


class Model:
    """Model class for matching predictions and reranking"""

    def __init__(self, model_settings: ModelSettings):
        """Initialize model with settings"""
        self.model_settings = model_settings
        self.predictor = None

    def load_model(self, model_path: str | None = None):
        """Load model predictor based on settings"""
        if self.model_settings.model_type == ModelType.HEURISTIC:
            self.predictor = HeuristicPredictor(self.model_settings.rules)
        elif self.model_settings.model_type == ModelType.CATBOOST:
            self.predictor = CatBoostPredictor()
            self.predictor.load_model(model_path)

    def create_features(self, features_df: pd.DataFrame, user_id: int) -> pd.DataFrame:
        """Create features for the model"""
        return features_df

    def predict(
        self,
        all_users: list[UserProfile],
        all_linkedin: list[LinkedInProfile],
        intent: MeetingIntent,
        user_id: int,
        n: int,
    ) -> list[int]:
        """Make predictions and apply filters and diversification"""
        if self.predictor is None:
            raise ValueError("Model not loaded")
        users_data = [user.model_dump() for user in all_users]
        linkedin_data = [profile.model_dump() for profile in all_linkedin]
        intent_data = intent.model_dump()
        for i, user in enumerate(users_data):
            for field, value in user.items():
                users_data[i][field] = convert_enum_value(value)
        for i, profile in enumerate(linkedin_data):
            for field, value in profile.items():
                linkedin_data[i][field] = convert_enum_value(value)
        for field, value in intent_data.items():
            intent_data[field] = convert_enum_value(value)
        users_df = pd.DataFrame(users_data).rename(columns={"id": "user_id"})
        linkedin_df = pd.DataFrame(linkedin_data)
        intents_df = pd.DataFrame([intent_data])
        main_user_df = users_df[users_df["user_id"] == user_id].copy()
        main_user_df = main_user_df.merge(linkedin_df, on="user_id", how="left", suffixes=("_user", "_linkedin"))
        main_user_df = intents_df.merge(main_user_df, on="user_id", how="left", suffixes=("_intent", ""))
        main_user_df = main_user_df.add_prefix("main_")
        main_user_df = main_user_df.iloc[0:1]
        other_users_df = users_df[users_df["user_id"] != user_id].copy()
        other_users_df = other_users_df.merge(linkedin_df, on="user_id", how="left", suffixes=("_user", "_linkedin"))
        main_user_repeated = pd.concat([main_user_df] * len(other_users_df), ignore_index=True)
        features_df = pd.concat([main_user_repeated, other_users_df.reset_index(drop=True)], axis=1)
        created_features = self.create_features(features_df, user_id)
        predictions = self.predictor.predict(created_features)
        results_df = features_df.copy()
        results_df["score"] = predictions
        for filter_setting in self.model_settings.filters:
            results_df = self._apply_filter(results_df, filter_setting)
        for div_setting in self.model_settings.diversifications:
            results_df = self._apply_diversification(results_df, div_setting)
        results_df = self._apply_exclusions(results_df)
        results_df = results_df.sort_values("score", ascending=False)
        return results_df.user_id.tolist()[:n]

    @staticmethod
    def check_match(x, filter_setting):
        values = x if isinstance(x, list) else [x]
        if isinstance(filter_setting.filter_rule, list):
            return any(val in filter_setting.filter_rule for val in values)
        return filter_setting.filter_rule in values

    def _apply_filter(self, df: pd.DataFrame, filter_setting, row_callable=None) -> pd.DataFrame:
        """Apply filter based on settings"""
        if filter_setting.filter_type == FilterType.STRICT:
            return df[df[filter_setting.filter_column].apply(lambda x: self.check_match(x, filter_setting))]

        elif filter_setting.filter_type == FilterType.SOFT:
            mask = df[filter_setting.filter_column].apply(lambda x: self.check_match(x, filter_setting))
            df.loc[~mask, "score"] *= 0.5
            return df

        elif filter_setting.filter_type == FilterType.CUSTOM:
            if row_callable is None:
                raise ValueError("Row callable is required for custom filter")
            df["filter_result"] = df.apply(row_callable, axis=1)
            return df[df["filter_result"]]
        return df

    def _apply_diversification(self, df: pd.DataFrame, div_setting) -> pd.DataFrame:
        """Apply diversification based on settings"""

        def get_values(x):
            if isinstance(x, list):
                return x
            return [x]

        if div_setting.diversification_type == DiversificationType.SCORE_BASED:
            df = df.sort_values("score", ascending=False)
            result_indices = []
            used_positions = set()
            df_exploded = df.copy()
            df_exploded[div_setting.diversification_column] = df_exploded[div_setting.diversification_column].apply(
                get_values
            )
            df_exploded = df_exploded.explode(div_setting.diversification_column)
            groups = df_exploded.groupby(div_setting.diversification_column)
            for _, group in groups:
                group_indices = group.index.unique().tolist()
                for idx in group_indices:
                    position = 0
                    while position in used_positions:
                        position += 1
                    valid = True
                    for prev_pos in used_positions:
                        if abs(position - prev_pos) < div_setting.diversification_value:
                            valid = False
                            break

                    if valid:
                        result_indices.append((position, idx))
                        used_positions.add(position)
            result_indices.sort()
            final_indices = [idx for _, idx in result_indices]
            return df.loc[final_indices]

        elif div_setting.diversification_type == DiversificationType.PROPORTIONAL:
            df_exploded = df.copy()
            df_exploded[div_setting.diversification_column] = df_exploded[div_setting.diversification_column].apply(
                get_values
            )
            df_exploded = df_exploded.explode(div_setting.diversification_column)

            total_groups = len(df_exploded[div_setting.diversification_column].unique())
            spacing = max(div_setting.diversification_value // total_groups, 1)

            df = df.sort_values("score", ascending=False)
            result_indices = []
            used_positions = set()

            groups = df_exploded.groupby(div_setting.diversification_column)
            group_weights = groups.size() / len(df_exploded)

            for group_name, group in groups:
                weight = group_weights[group_name]
                group_indices = group.index.unique().tolist()
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
