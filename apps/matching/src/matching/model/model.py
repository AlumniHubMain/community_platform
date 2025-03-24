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
import logging


class Model:
    """
    Main matching model class that handles feature preparation and predictor initialization
    """
    def __init__(self, model_settings: ModelSettings):
        """
        Initialize the model with specific settings

        Args:
            model_settings: Model settings object
        """
        self.model_settings = model_settings
        self.predictor = None
        self.logger = logging.getLogger(__name__)
        self.current_form = None
        self.current_user = None

    def load_model(self, model=None):
        """
        Load the underlying model

        Args:
            model: The model object or path to model file
        """
        if self.model_settings.model_type == ModelType.HEURISTIC:
            self.predictor = HeuristicPredictor(self.model_settings.rules)
        elif self.model_settings.model_type == ModelType.CATBOOST:
            self.predictor = CatBoostPredictor()
            self.predictor.load_model(model)
        else:
            raise ValueError(f"Unknown model type: {self.model_settings.model_type}")

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

    def _prepare_features(
        self, users: list[SUserProfileRead], form: FormRead, linkedin_profiles: list[LinkedInProfileRead], user_id: int
    ) -> pd.DataFrame:
        """
        Prepare feature data frame from user profiles, form, and LinkedIn profiles

        Args:
            users: List of user profiles
            form: Form with matching criteria
            linkedin_profiles: List of LinkedIn profiles
            user_id: ID of the user making the request

        Returns:
            DataFrame with features for prediction
        """
        # Create mapping of user_id to LinkedIn profile
        linkedin_map = {p.users_id_fk: p.model_dump() if hasattr(p, 'model_dump') else p.dict() 
                        for p in linkedin_profiles if p.users_id_fk is not None}

        # Filter out the user who made the request
        filtered_users = [u for u in users if u.id != user_id]

        # Create main user profile (the one who submitted the form)
        main_user = next((u for u in users if u.id == user_id), None)

        if not main_user:
            self.logger.warning("Main user profile not found, using first user as fallback")
            # Fallback to using the first user as main user if not found
            main_user = users[0] if users else None

        # Initialize features list to be converted to DataFrame
        features_list = []

        # Add main user first (for reference in prediction)
        if main_user:
            main_user_dict = main_user.model_dump() if hasattr(main_user, 'model_dump') else main_user.dict()
            
            main_profile = {
                "id": main_user.id,
                "user_id": main_user.id,  # For backward compatibility
                "grade": main_user_dict.get("grade"),
                "expertise_area": main_user_dict.get("expertise_area"),
                "interests": main_user_dict.get("interests"),
                "specialisations": main_user_dict.get("specialisations"),
                "specialisation": main_user_dict.get("specialisations"),  # Alias for compatibility
                "skills": main_user_dict.get("skills"),
                "location": main_user_dict.get("location"),
                "current_position_title": main_user_dict.get("current_position_title"),
                "is_currently_employed": main_user_dict.get("is_currently_employed", False),
                "industries": main_user_dict.get("industries"),
                "industry": main_user_dict.get("industries"),  # Alias for compatibility
                "linkedin_profile": linkedin_map.get(main_user.id),
                "main_intent": form.intent.value if hasattr(form.intent, 'value') else form.intent,
                "main_content": form.content,
                "main_grade": main_user_dict.get("grade"),
                "main_expertise_area": main_user_dict.get("expertise_area"),
                "main_interests": main_user_dict.get("interests"),
                "main_location": main_user_dict.get("location"),
                "main_industry": main_user_dict.get("industries"),
            }
            features_list.append(main_profile)

        # Add other users
        for user in filtered_users:
            user_dict = user.model_dump() if hasattr(user, 'model_dump') else user.dict()
            
            profile = {
                "id": user.id,
                "user_id": user.id,  # For backward compatibility
                "grade": user_dict.get("grade"),
                "expertise_area": user_dict.get("expertise_area"),
                "interests": user_dict.get("interests"),
                "specialisations": user_dict.get("specialisations"),
                "specialisation": user_dict.get("specialisations"),  # Alias for compatibility
                "skills": user_dict.get("skills"),
                "location": user_dict.get("location"),
                "current_position_title": user_dict.get("current_position_title"),
                "is_currently_employed": user_dict.get("is_currently_employed", False),
                "industries": user_dict.get("industries"),
                "industry": user_dict.get("industries"),  # Alias for compatibility
                "linkedin_profile": linkedin_map.get(user.id),
                "main_intent": form.intent.value if hasattr(form.intent, 'value') else form.intent,
                "main_content": form.content,
                "main_grade": main_user_dict.get("grade") if main_user else None,
                "main_expertise_area": main_user_dict.get("expertise_area") if main_user else None,
                "main_interests": main_user_dict.get("interests") if main_user else None,
                "main_location": main_user_dict.get("location") if main_user else None,
                "main_industry": main_user_dict.get("industries") if main_user else None,
            }
            features_list.append(profile)

        # Create DataFrame
        features_df = pd.DataFrame(features_list)
        
        # Add compatibility measures
        features_df = self._add_compatibility_measures(features_df)
        
        return features_df
        
    def _add_compatibility_measures(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add compatibility measures to help with matching by aggregating data from
        both user profile and LinkedIn profile before calculating scores.

        Args:
            features_df: Input feature DataFrame

        Returns:
            Enhanced DataFrame with additional compatibility measures
        """
        # Create columns for aggregated data
        features_df["aggregated_skills"] = None
        features_df["aggregated_languages"] = None
        features_df["aggregated_interests"] = None
        
        # First pass: aggregate data from multiple sources for each user
        for idx, row in features_df.iterrows():
            # Aggregate skills from both profile and LinkedIn
            skills = set()
            
            # Add skills from user profile
            if row.get("skills") and isinstance(row["skills"], list):
                if row["skills"] and hasattr(row["skills"][0], "label"):
                    skills.update(skill.label.lower() for skill in row["skills"] if hasattr(skill, "label"))
                else:
                    skills.update(str(skill).lower() for skill in row["skills"])
            
            # Add skills from LinkedIn profile
            if row.get("linkedin_profile") and row["linkedin_profile"].get("skills"):
                skills.update(str(skill).lower() for skill in row["linkedin_profile"]["skills"] if skill)
            
            features_df.at[idx, "aggregated_skills"] = list(skills) if skills else []
            
            # Aggregate languages from both profile and LinkedIn
            languages = set()
            
            # Add languages from user profile if available
            if row.get("languages") and isinstance(row["languages"], list):
                if row["languages"] and hasattr(row["languages"][0], "label"):
                    languages.update(lang.label.lower() for lang in row["languages"] if hasattr(lang, "label"))
                else:
                    languages.update(str(lang).lower() for lang in row["languages"])
            
            # Add languages from LinkedIn profile
            if row.get("linkedin_profile") and row["linkedin_profile"].get("languages"):
                languages.update(str(lang).lower() for lang in row["linkedin_profile"]["languages"] if lang)
            
            features_df.at[idx, "aggregated_languages"] = list(languages) if languages else []
            
            # Aggregate interests from user profile
            interests = set()
            
            if row.get("interests") and isinstance(row["interests"], list):
                if row["interests"] and hasattr(row["interests"][0], "label"):
                    interests.update(interest.label.lower() for interest in row["interests"] if hasattr(interest, "label"))
                else:
                    interests.update(str(interest).lower() for interest in row["interests"])
            
            # Add interests from LinkedIn profile summary if available (as keywords)
            if row.get("linkedin_profile") and row["linkedin_profile"].get("summary"):
                summary = row["linkedin_profile"]["summary"]
                # Add simple word extraction from summary (could be enhanced with NLP)
                if summary:
                    words = str(summary).lower().split()
                    interest_keywords = [word for word in words if len(word) > 4]  # Simple filtering
                    interests.update(interest_keywords)
            
            features_df.at[idx, "aggregated_interests"] = list(interests) if interests else []
        
        # Second pass: calculate match scores using the aggregated data
        if len(features_df) > 0:
            # Get main user's aggregated data
            main_skills = set(features_df.at[0, "aggregated_skills"])
            main_languages = set(features_df.at[0, "aggregated_languages"])
            main_interests = set(features_df.at[0, "aggregated_interests"])
            
            # Calculate skills match score using Jaccard similarity
            def calculate_skill_match(row):
                if not row.get("aggregated_skills"):
                    return 0
                user_skills = set(row["aggregated_skills"])
                if not main_skills or not user_skills:
                    return 0
                # Jaccard similarity: intersection / union
                return len(main_skills & user_skills) / len(main_skills | user_skills)
            
            features_df["skill_match_score"] = features_df.apply(calculate_skill_match, axis=1)
            
            # Calculate language match score
            def calculate_language_match(row):
                if not row.get("aggregated_languages"):
                    return 0
                user_languages = set(row["aggregated_languages"])
                if not main_languages or not user_languages:
                    return 0
                # Jaccard similarity: intersection / union
                return len(main_languages & user_languages) / len(main_languages | user_languages)
            
            features_df["language_match_score"] = features_df.apply(calculate_language_match, axis=1)
            
            # Calculate interest match score
            def calculate_interest_match(row):
                if not row.get("aggregated_interests"):
                    return 0
                user_interests = set(row["aggregated_interests"])
                if not main_interests or not user_interests:
                    return 0
                # Jaccard similarity: intersection / union
                return len(main_interests & user_interests) / len(main_interests | user_interests)
            
            features_df["interest_match_score"] = features_df.apply(calculate_interest_match, axis=1)
        
        return features_df

    def _apply_diversification(self, df: pd.DataFrame, div_setting=None) -> pd.DataFrame:
        """Apply diversification strategy to results"""
        # For backward compatibility with both old and new diversification schemes
        if div_setting:
            # Old-style diversification (for backward compatibility)
            if div_setting.diversification_type == DiversificationType.PROPORTIONAL:
                if div_setting.diversification_column in df.columns:
                    # Sort by score within each value of the diversification column
                    df = df.sort_values([div_setting.diversification_column, "score"], ascending=[True, False])
                    # Take top N from each value of the diversification column
                    df = df.groupby(div_setting.diversification_column).head(div_setting.diversification_value)
                    # Resort by score
                    df = df.sort_values("score", ascending=False)
        else:
            # New-style diversification
            if hasattr(self.model_settings, 'diversification_type') and self.model_settings.diversification_type == DiversificationType.PROPORTIONAL:
                if hasattr(self.model_settings, 'diversification_column') and self.model_settings.diversification_column in df.columns:
                    # Sort by score within each value of the diversification column
                    df = df.sort_values([self.model_settings.diversification_column, "score"], ascending=[True, False])
                    # Take top N from each value of the diversification column
                    count = getattr(self.model_settings, 'diversification_value', 2)
                    df = df.groupby(self.model_settings.diversification_column).head(count)
                    # Resort by score
                    df = df.sort_values("score", ascending=False)
                    
        return df

    def _apply_exclusions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply user and company exclusions"""
        if hasattr(self.model_settings, 'exclude_users') and self.model_settings.exclude_users:
            df = df[~df["id"].isin(self.model_settings.exclude_users)]
        if hasattr(self.model_settings, 'exclude_companies') and self.model_settings.exclude_companies and "company" in df.columns:
            df = df[~df["company"].isin(self.model_settings.exclude_companies)]
        return df

    def predict(
        self, all_users: list[SUserProfileRead], form: FormRead, linkedin_profiles: list[LinkedInProfileRead], user_id: int, n: int = 5
    ) -> list[int]:
        """
        Make predictions for a given form and user profiles

        Args:
            all_users: List of user profiles
            form: Form with matching criteria
            linkedin_profiles: List of LinkedIn profiles
            user_id: ID of the user making the request
            n: Number of top matches to return

        Returns:
            List of user IDs of top matches
        """
        # Store for backward compatibility
        self.current_form = form
        self.current_user = next((user for user in all_users if user.id == user_id), None)
        
        if not self.predictor:
            raise ValueError("Model not loaded")

        if not all_users:
            return []

        # Prepare features
        features_df = self._prepare_features(all_users, form, linkedin_profiles, user_id)

        if len(features_df) <= 1:
            # Only contains the main user or is empty
            return []

        # Get predictions
        predictions = self.predictor.predict(features_df)
        
        # Skip the first row which is the main user
        other_users_df = features_df.iloc[1:].copy()
        other_users_df["score"] = predictions[1:]
        
        # Backward compatibility with old code
        if hasattr(self.model_settings, 'filters'):
            # Apply filters from model settings
            for filter_setting in self.model_settings.filters:
                other_users_df = self._apply_filter(other_users_df, filter_setting)
                
        # Backward compatibility with old code
        if hasattr(self.model_settings, 'diversifications'):
            # Apply diversifications from model settings
            for div_setting in self.model_settings.diversifications:
                other_users_df = self._apply_diversification(other_users_df, div_setting)
        elif hasattr(self.model_settings, 'diversification_type') and self.model_settings.diversification_type != DiversificationType.NONE:
            # New style diversification
            other_users_df = self._apply_diversification(other_users_df)
            
        # Apply exclusions
        other_users_df = self._apply_exclusions(other_users_df)
        
        # Sort by score descending and take top N
        other_users_df = other_users_df.sort_values("score", ascending=False)
        top_user_ids = other_users_df.head(n)["id"].tolist()

        return top_user_ids
