"""Model class for loading and applying catboost model with filters and diversification"""

import pandas as pd
from common_db.schemas import (
    SUserProfileRead,
    FormRead,
    LinkedInProfileRead,
)
from common_db.schemas.base import convert_enum_value
from common_db.enums.forms import EFormIntentType

from .model_settings import ModelSettings, FilterType, DiversificationType, ModelType
from .predictors import CatBoostPredictor, HeuristicPredictor


class Model:
    """Model class for matching predictions and reranking"""

    def __init__(self, model_settings: ModelSettings):
        """Initialize model with settings"""
        self.model_settings = model_settings
        self.predictor = None
        self.current_intent = None
        self.current_user = None
        self.current_form = None

    def load_model(self, model_path: str | None = None):
        """Load model predictor based on settings"""
        if self.model_settings.model_type == ModelType.HEURISTIC:
            self.predictor = HeuristicPredictor(self.model_settings.rules)
        elif self.model_settings.model_type == ModelType.CATBOOST:
            self.predictor = CatBoostPredictor()
            self.predictor.load_model(model_path)

    def create_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Create additional features for the model using LinkedIn data"""
        # Add form content features
        if "content" in features_df.columns:
            features_df["meeting_format"] = features_df["content"].apply(
                lambda x: x.get("social_circle_expansion", {}).get("meeting_formats", [None])[0]
                if isinstance(x, dict) and "social_circle_expansion" in x
                else None
            )

            # Extract specialization based on form type
            features_df["specialization"] = features_df.apply(
                lambda row: (
                    row["content"].get("specialization", [])
                    if row["intent"] == EFormIntentType.mentoring_mentor.value
                    else row["content"].get("mentor_specialization", [])
                    if row["intent"] == EFormIntentType.mentoring_mentee.value
                    else []
                )
                if isinstance(row["content"], dict)
                else [],
                axis=1,
            )

            # Extract grade based on form type
            features_df["grade"] = features_df.apply(
                lambda row: (
                    row["content"].get("required_grade", [])
                    if row["intent"] == EFormIntentType.mentoring_mentor.value
                    else row["content"].get("grade", [])
                    if row["intent"] == EFormIntentType.mentoring_mentee.value
                    else []
                )
                if isinstance(row["content"], dict)
                else [],
                axis=1,
            )

        # Add skill matching feature
        if "skills" in features_df.columns and "main_skills" in features_df.columns:
            features_df["skill_match_score"] = features_df.apply(
                lambda row: len(set(row["skills"] or []) & set(row["main_skills"] or []))
                if isinstance(row["skills"], list) and isinstance(row["main_skills"], list)
                else 0,
                axis=1,
            )

        # Add language matching feature
        if "languages" in features_df.columns and "main_languages" in features_df.columns:
            features_df["language_match_score"] = features_df.apply(
                lambda row: len(set(row["languages"] or []) & set(row["main_languages"] or []))
                if isinstance(row["languages"], list) and isinstance(row["main_languages"], list)
                else 0,
                axis=1,
            )

        # Add location matching feature
        if "location" in features_df.columns and "main_location" in features_df.columns:
            features_df["same_location"] = (features_df["location"] == features_df["main_location"]).astype(int)

        return features_df

    @staticmethod
    def check_match(x, filter_setting) -> bool:
        """Check if value matches filter rule"""
        values = x if isinstance(x, list) else [x]
        filter_rules = (
            filter_setting.filter_rule if isinstance(filter_setting.filter_rule, list) else [filter_setting.filter_rule]
        )
        result = bool(set(values) & set(filter_rules))
        return result

    def _apply_filter(self, df: pd.DataFrame, filter_setting) -> pd.DataFrame:
        """Apply filter based on settings"""
        if filter_setting.filter_type == FilterType.STRICT:
            mask = df[filter_setting.filter_column].apply(lambda x: self.check_match(x, filter_setting))
            filtered_df = df[mask]
            return filtered_df
        if filter_setting.filter_type == FilterType.SOFT:
            mask = df[filter_setting.filter_column].apply(lambda x: self.check_match(x, filter_setting))
            df.loc[~mask, "score"] *= 0.5
            return df
        return df

    def predict(
        self,
        all_users: list[SUserProfileRead],
        form: FormRead,
        linkedin_profiles: list[LinkedInProfileRead],
        user_id: int,
        n: int,
    ) -> list[int]:
        """Make predictions and apply filters and diversification"""
        # Store current form and user for custom filters
        self.current_form = form
        self.current_user = next((user for user in all_users if user.id == user_id), None)

        if self.predictor is None:
            raise ValueError("Model not loaded")

        # Convert users and form data
        users_data = [user.model_dump() for user in all_users]
        form_data = form.model_dump()

        # Convert enum values
        for i, user in enumerate(users_data):
            for field, value in user.items():
                users_data[i][field] = convert_enum_value(value)
        for field, value in form_data.items():
            form_data[field] = convert_enum_value(value)

        # Create DataFrames
        users_df = pd.DataFrame(users_data).rename(columns={"id": "user_id"})
        linkedin_df = pd.DataFrame([p.model_dump() for p in linkedin_profiles])

        # Prepare LinkedIn features
        if not linkedin_df.empty:
            linkedin_features = linkedin_df[
                [
                    "users_id_fk",
                    "current_company_label",
                    "current_position_title",
                    "is_currently_employed",
                    "skills",
                    "languages",
                    "headline",
                    "location",  # This will be used for location matching
                ]
            ].rename(
                columns={
                    "users_id_fk": "user_id",
                    "location": "location",  # Keep original name for clarity
                }
            )

            # Merge LinkedIn data with users
            users_df = users_df.merge(
                linkedin_features,
                on="user_id",
                how="left",
                suffixes=("", "_linkedin"),  # Prevent _x, _y suffixes
            )

        intents_df = pd.DataFrame([form_data])

        # Create main user DataFrame with form data
        main_user_df = users_df[users_df["user_id"] == user_id].copy()
        main_user_df = intents_df.merge(
            main_user_df,
            on="user_id",
            how="left",
            suffixes=("_form", ""),  # Use meaningful suffixes
        )
        main_user_df = main_user_df.add_prefix("main_")

        # Create other users DataFrame
        other_users_df = users_df[users_df["user_id"] != user_id].copy()

        # Create features DataFrame
        main_user_repeated = pd.concat([main_user_df] * len(other_users_df), ignore_index=True)
        features_df = pd.concat([main_user_repeated, other_users_df.reset_index(drop=True)], axis=1)

        # Ensure location columns are properly named
        if "location" in features_df.columns:
            features_df = features_df.rename(columns={"location": "location_other"})
        if "main_location" not in features_df.columns and "main_location" in main_user_df.columns:
            features_df["main_location"] = main_user_df["main_location"].iloc[0]

        # Create additional features using LinkedIn data
        features_df = self.create_features(features_df)

        # Get predictions and apply filters/diversification
        predictions = self.predictor.predict(features_df)
        results_df = other_users_df.copy()
        results_df["score"] = predictions

        for filter_setting in self.model_settings.filters:
            results_df = self._apply_filter(results_df, filter_setting)

        for div_setting in self.model_settings.diversifications:
            results_df = self._apply_diversification(results_df, div_setting)

        results_df = self._apply_exclusions(results_df)
        results_df = results_df.sort_values("score", ascending=False)
        predictions = results_df.head(n)["user_id"].tolist()

        return predictions

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

        if div_setting.diversification_type == DiversificationType.PROPORTIONAL:
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
