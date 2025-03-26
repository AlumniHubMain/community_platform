"""Heuristic-based predictor implementation"""
import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime

from .base import BasePredictor
from .scoring_config import ScoringConfig
from .scoring_rules import RuleFactory
from .data_normalizer import DataNormalizer
from .intent_rules import IntentRuleFactory
from common_db.enums.forms import (
    EFormMentoringGrade,
    EFormConnectsMeetingFormat,
)

logger = logging.getLogger(__name__)

class HeuristicPredictor(BasePredictor):
    """Heuristic-based predictor implementation"""
    
    def __init__(
        self,
        rules: Optional[List[str]] = None,
        config: Optional[ScoringConfig] = None,
        normalizer: Optional[DataNormalizer] = None,
    ):
        """Initialize the predictor"""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config = config or ScoringConfig()
        self.normalizer = normalizer or DataNormalizer()
        self.rule_factory = RuleFactory(self.config, self.normalizer)
        self.intent_rule_factory = IntentRuleFactory(self.config, self.normalizer, self.rule_factory)
        
        # Initialize rules
        self.rules = rules or [
            "location",
            "grade",
            "skill",
            "language",
            "expertise",
            "network",
            "project_experience",
            "education",
            "availability",
            "communication",
            "professional_background",
        ]
        
        # Grade mapping for mentoring
        self.grade_mapping = {
            EFormMentoringGrade.junior: ["junior", "intern", "student"],
            EFormMentoringGrade.middle: ["middle", "mid-level"],
            EFormMentoringGrade.senior: ["senior", "lead", "principal"],
            EFormMentoringGrade.lead: ["lead", "supervisor"],
            EFormMentoringGrade.head: ["staff", "distinguished", "head"],
            EFormMentoringGrade.executive: ["executive", "ceo", "founder"],
        }

        
    def _aggregate_user_data(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate user data from different sources into a consistent format
        
        Args:
            features: Input features DataFrame
            
        Returns:
            DataFrame with aggregated user data
        """
        # Make a copy to avoid modifying original
        features_copy = features.copy()
        
        # Process each user entry and normalize data
        for idx, row in features_copy.iterrows():
            # Process expertise areas
            if 'expertise_area' in row:
                if row['expertise_area'] is None:
                    features_copy.at[idx, 'expertise_area'] = []
                # Handle both list of strings and list of objects
                elif isinstance(row['expertise_area'], list):
                    if row['expertise_area'] and not isinstance(row['expertise_area'][0], str):
                        try:
                            # Try to extract value or label attributes
                            features_copy.at[idx, 'expertise_area'] = [
                                area.value if hasattr(area, 'value') else 
                                (area.label if hasattr(area, 'label') else str(area))
                                for area in row['expertise_area']
                            ]
                        except Exception as e:
                            # Fallback if extraction fails
                            self.logger.warning(f"Failed to extract expertise area values - converting to strings: {e}")
                            features_copy.at[idx, 'expertise_area'] = [str(area) for area in row['expertise_area']]
                elif row['expertise_area'] and not isinstance(row['expertise_area'], str):
                    # Handle single object
                    try:
                        features_copy.at[idx, 'expertise_area'] = [
                            row['expertise_area'].value if hasattr(row['expertise_area'], 'value') else 
                            (row['expertise_area'].label if hasattr(row['expertise_area'], 'label') else str(row['expertise_area']))
                        ]
                    except Exception as e:
                        self.logger.warning(f"Failed to extract expertise area value - converting to string: {e}")
                        features_copy.at[idx, 'expertise_area'] = [str(row['expertise_area'])]
                elif isinstance(row['expertise_area'], str):
                    # Handle single string by converting to list
                    features_copy.at[idx, 'expertise_area'] = [row['expertise_area']]
                
            # Process interests
            if 'interests' in row:
                if row['interests'] is None:
                    features_copy.at[idx, 'interests'] = []
                # Handle both list of strings and list of objects
                elif isinstance(row['interests'], list):
                    if row['interests'] and not isinstance(row['interests'][0], str):
                        try:
                            # Try to extract label or value attribute
                            features_copy.at[idx, 'interests'] = [
                                interest.label if hasattr(interest, 'label') else 
                                (interest.value if hasattr(interest, 'value') else str(interest))
                                for interest in row['interests']
                            ]
                        except Exception as e:
                            # Fallback if extraction fails
                            self.logger.warning(f"Failed to extract interest labels - converting to strings: {e}")
                            features_copy.at[idx, 'interests'] = [str(interest) for interest in row['interests']]
                elif row['interests'] and not isinstance(row['interests'], str):
                    # Handle single object
                    try:
                        features_copy.at[idx, 'interests'] = [
                            row['interests'].label if hasattr(row['interests'], 'label') else 
                            (row['interests'].value if hasattr(row['interests'], 'value') else str(row['interests']))
                        ]
                    except Exception as e:
                        self.logger.warning(f"Failed to extract interest label - converting to string: {e}")
                        features_copy.at[idx, 'interests'] = [str(row['interests'])]
                elif isinstance(row['interests'], str):
                    # Handle single string by converting to list
                    features_copy.at[idx, 'interests'] = [row['interests']]
                
            # Process skills
            if 'skills' in row:
                if row['skills'] is None:
                    features_copy.at[idx, 'skills'] = []
                # Handle both list of strings and list of objects
                elif isinstance(row['skills'], list):
                    if row['skills'] and not isinstance(row['skills'][0], str):
                        try:
                            # Try to extract label or value attribute
                            features_copy.at[idx, 'skills'] = [
                                skill.label if hasattr(skill, 'label') else 
                                (skill.value if hasattr(skill, 'value') else str(skill))
                                for skill in row['skills']
                            ]
                        except Exception as e:
                            # Fallback if extraction fails
                            self.logger.warning(f"Failed to extract skill labels - converting to strings: {e}")
                            features_copy.at[idx, 'skills'] = [str(skill) for skill in row['skills']]
                elif row['skills'] and not isinstance(row['skills'], str):
                    # Handle single object
                    try:
                        features_copy.at[idx, 'skills'] = [
                            row['skills'].label if hasattr(row['skills'], 'label') else 
                            (row['skills'].value if hasattr(row['skills'], 'value') else str(row['skills']))
                        ]
                    except Exception as e:
                        self.logger.warning(f"Failed to extract skill label - converting to string: {e}")
                        features_copy.at[idx, 'skills'] = [str(row['skills'])]
                elif isinstance(row['skills'], str):
                    # Handle single string by converting to list
                    features_copy.at[idx, 'skills'] = [row['skills']]
                            
            # Process specialisations/specialization (handle both spellings)
            for field in ['specialisations', 'specialisation']:
                if field in row:
                    if row[field] is None:
                        features_copy.at[idx, field] = []
                    # Handle both list of strings and list of objects
                    elif isinstance(row[field], list):
                        if row[field] and not isinstance(row[field][0], str):
                            try:
                                # Try to extract label or value attribute
                                features_copy.at[idx, field] = [
                                    spec.label if hasattr(spec, 'label') else 
                                    (spec.value if hasattr(spec, 'value') else str(spec))
                                    for spec in row[field]
                                ]
                            except Exception as e:
                                # Fallback if extraction fails
                                self.logger.warning(f"Failed to extract {field} labels - converting to strings: {e}")
                                features_copy.at[idx, field] = [str(spec) for spec in row[field]]
                    elif row[field] and not isinstance(row[field], str):
                        # Handle single object
                        try:
                            features_copy.at[idx, field] = [
                                row[field].label if hasattr(row[field], 'label') else 
                                (row[field].value if hasattr(row[field], 'value') else str(row[field]))
                            ]
                        except Exception as e:
                            self.logger.warning(f"Failed to extract {field} label - converting to string: {e}")
                            features_copy.at[idx, field] = [str(row[field])]
                    elif isinstance(row[field], str):
                        # Handle single string by converting to list
                        features_copy.at[idx, field] = [row[field]]
            
            # Process industries/industry (handle both names)
            for field in ['industries', 'industry']:
                if field in row:
                    if row[field] is None:
                        features_copy.at[idx, field] = []
                    # Handle both list of strings and list of objects
                    elif isinstance(row[field], list):
                        if row[field] and not isinstance(row[field][0], str):
                            try:
                                # Try to extract label or value attribute
                                features_copy.at[idx, field] = [
                                    ind.label if hasattr(ind, 'label') else 
                                    (ind.value if hasattr(ind, 'value') else str(ind))
                                    for ind in row[field]
                                ]
                            except Exception as e:
                                # Fallback if extraction fails
                                self.logger.warning(f"Failed to extract {field} labels - converting to strings: {e}")
                                features_copy.at[idx, field] = [str(ind) for ind in row[field]]
                    elif row[field] and not isinstance(row[field], str):
                        # Handle single object
                        try:
                            features_copy.at[idx, field] = [
                                row[field].label if hasattr(row[field], 'label') else 
                                (row[field].value if hasattr(row[field], 'value') else str(row[field]))
                            ]
                        except Exception as e:
                            self.logger.warning(f"Failed to extract {field} label - converting to string: {e}")
                            features_copy.at[idx, field] = [str(row[field])]
                    elif isinstance(row[field], str):
                        # Handle single string by converting to list
                        features_copy.at[idx, field] = [row[field]]
            
            # Process LinkedIn profile
            if 'linkedin_profile' in row and row['linkedin_profile']:
                # Ensure all values in the LinkedIn profile are properly extracted
                try:
                    profile = row['linkedin_profile']
                    
                    # Handle different profile types
                    if hasattr(profile, 'model_dump'):
                        profile_dict = profile.model_dump()
                    elif hasattr(profile, 'dict'):
                        profile_dict = profile.dict()
                    elif isinstance(profile, dict):
                        profile_dict = profile.copy()  # Make a copy to avoid modifying original
                    else:
                        # If not a dictionary or object with dict/model_dump method, convert to string
                        profile_dict = {"raw_data": str(profile)}
                        
                    # Convert any nested dictionaries to properly handle work_experience
                    if 'work_experience' in profile_dict and isinstance(profile_dict['work_experience'], list):
                        # Handle work experience items properly
                        processed_work_exp = []
                        for exp in profile_dict['work_experience']:
                            if isinstance(exp, dict):
                                processed_work_exp.append(exp)
                            elif hasattr(exp, 'dict'):
                                processed_work_exp.append(exp.dict())
                            elif hasattr(exp, 'model_dump'):
                                processed_work_exp.append(exp.model_dump())
                            else:
                                # Convert to string only as last resort
                                processed_work_exp.append({"title": str(exp)})
                        profile_dict['work_experience'] = processed_work_exp
                    
                    # Ensure skills is a list
                    if 'skills' in profile_dict:
                        if profile_dict['skills'] is None:
                            profile_dict['skills'] = []
                        elif not isinstance(profile_dict['skills'], list):
                            profile_dict['skills'] = [str(profile_dict['skills'])]
                    
                    # Ensure languages is a list
                    if 'languages' in profile_dict:
                        if profile_dict['languages'] is None:
                            profile_dict['languages'] = []
                        elif not isinstance(profile_dict['languages'], list):
                            profile_dict['languages'] = [str(profile_dict['languages'])]
                            
                    features_copy.at[idx, 'linkedin_profile'] = profile_dict
                except Exception as e:
                    # If conversion fails, set to an empty dict to avoid further issues
                    self.logger.warning(f"Failed to convert LinkedIn profile: {e}")
                    features_copy.at[idx, 'linkedin_profile'] = {}
            elif 'linkedin_profile' in row and row['linkedin_profile'] is None:
                # Set None profiles to empty dict to avoid errors
                features_copy.at[idx, 'linkedin_profile'] = {}
        
        return features_copy
    
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Generate predictions using heuristic rules"""
        # Aggregate user data
        features = self._aggregate_user_data(features)
        
        # Normalize features
        features = self.normalizer.normalize_features(features)

        # Initialize scores with a reasonable starting value
        scores = np.ones(len(features), dtype=np.float64) * 0.5
        
        # Apply base rules
        scores = self._apply_base_rules(features, scores)
        
        # Apply intent-specific rules
        if "main_intent" in features.columns:
            scores = self._apply_intent_rules(features, scores)
        
        # Apply general post-processing to ensure score consistency
        scores = self._normalize_final_scores(scores, features)
            
        return scores

    def _normalize_final_scores(self, scores: np.ndarray, features: pd.DataFrame) -> np.ndarray:
        """Apply general normalization to final scores based on key attributes"""
        try:
            # Convert to numpy array and ensure it's 1D
            scores = np.asarray(scores).flatten()
            
            # Get main intent type for intent-specific normalization
            main_intent = features["main_intent"].iloc[0] if "main_intent" in features.columns else None
            
            # Apply LinkedIn profile quality boost
            if "linkedin_profile" in features.columns:
                for idx, row in features.iterrows():
                    if idx >= len(scores):
                        continue
                        
                    profile = row.get("linkedin_profile")
                    if profile and isinstance(profile, dict):
                        # Calculate profile quality score
                        follower_count = profile.get("follower_count", 0)
                        has_summary = bool(profile.get("summary"))
                        has_skills = bool(profile.get("skills"))
                        has_experience = bool(profile.get("work_experience"))
                        
                        # Boost score based on profile completeness
                        profile_boost = 0.0
                        if follower_count > 1000:
                            profile_boost += 0.15  # Reduced from 0.2
                        if has_summary:
                            profile_boost += 0.05  # Reduced from 0.1
                        if has_skills:
                            profile_boost += 0.05  # Reduced from 0.1
                        if has_experience:
                            profile_boost += 0.05  # Reduced from 0.1
                            
                        # Apply profile boost with lower cap
                        scores[idx] = min(scores[idx] + profile_boost, 0.9)  # Reduced from 0.95
            
            # Apply location boosting for offline meetings first
            if "main_content" in features.columns and len(features) > 0:
                main_content = features["main_content"].iloc[0]
                if isinstance(main_content, dict) and "meeting_format" in main_content:
                    meeting_format = main_content["meeting_format"]
                    if meeting_format == EFormConnectsMeetingFormat.offline.value:
                        # Location should have higher priority for offline meetings
                        # Apply location-based multipliers to all candidates
                        if "location" in features.columns and "main_location" in features.columns:
                            main_location = features["main_location"].iloc[0]
                            for idx, row in features.iterrows():
                                # Skip indices that are out of bounds
                                if idx >= len(scores):
                                    self.logger.warning(f"Index {idx} out of bounds in scores array of length {len(scores)}")
                                    continue
                                    
                                # Calculate location multiplier
                                if row.get("location") is not None and str(row.get("location")) == str(main_location):
                                    # Match: boost the score significantly for offline meetings
                                    scores[idx] = min(scores[idx] * 1.6, 0.9)  # Reduced from 1.8 and 0.95
                                elif row.get("location") is not None:
                                    # Different location: penalize for offline meetings
                                    scores[idx] *= 0.5  # Same penalty
                                elif row.get("linkedin_location") is not None:
                                    # LinkedIn location might provide partial information
                                    if str(row.get("linkedin_location")) == str(main_location):
                                        scores[idx] = min(scores[idx] * 1.3, 0.85)  # Reduced from 1.4 and 0.9
            
            # Normalize scores to appropriate ranges based on grades and intent type
            if "grade" in features.columns:
                for idx, row in features.iterrows():
                    # Skip indices that are out of bounds
                    if idx >= len(scores):
                        self.logger.warning(f"Index {idx} out of bounds in scores array of length {len(scores)}")
                        continue
                        
                    grade = row.get("grade")
                    if grade:
                        # Higher grades should generally score better
                        grade_str = str(grade).lower()
                        
                        # Intent-specific grade normalization
                        if main_intent == "mentoring_mentee":
                            # Mentees should be junior/middle
                            if any(g in grade_str for g in ["junior", "intern"]):
                                scores[idx] = min(max(scores[idx], 0.5), 0.8)
                            elif "middle" in grade_str:
                                scores[idx] = min(max(scores[idx], 0.4), 0.7)
                            else:
                                scores[idx] *= 0.7  # Penalty for senior mentees
                        elif main_intent == "projects_find_cofounder":
                            # Cofounders should be senior/middle
                            if any(g in grade_str for g in ["senior", "lead", "principal", "head"]):
                                scores[idx] = min(max(scores[idx], 0.6), 0.9)
                            elif "middle" in grade_str:
                                scores[idx] = min(max(scores[idx], 0.5), 0.8)
                            else:
                                scores[idx] *= 0.7  # Penalty for junior cofounders
                        elif main_intent == "projects_pet_project":
                            # Pet projects welcome all levels
                            if any(g in grade_str for g in ["senior", "lead", "principal"]):
                                scores[idx] = min(max(scores[idx], 0.5), 0.85)
                            elif "middle" in grade_str:
                                scores[idx] = min(max(scores[idx], 0.4), 0.8)
                            else:
                                scores[idx] = min(max(scores[idx], 0.3), 0.75)
                        else:
                            # Default grade normalization
                            if any(g in grade_str for g in ["lead", "senior", "principal", "head"]):
                                # Senior and above - ensure good candidates score well
                                if scores[idx] > 0.6:
                                    scores[idx] = min(max(scores[idx], 0.7), 0.9)
                            elif "middle" in grade_str:
                                # Middle grade - moderate scores
                                if scores[idx] > 0.4:
                                    scores[idx] = min(max(scores[idx], 0.5), 0.85)
                            elif any(g in grade_str for g in ["junior", "intern"]):
                                # Junior grade - generally lower scores
                                scores[idx] = min(scores[idx], 0.75)
            
            # Generalized normalization for candidates with good matches
            for idx in range(len(scores)):
                # Extremely low scores (likely errors or missing data)
                if scores[idx] < 0.01:
                    scores[idx] = 0.01  # Minimum floor
                # Very high scores (likely perfect matches)
                elif scores[idx] > 0.99:
                    scores[idx] = 0.99  # Maximum cap
            
            return scores
        except Exception as e:
            self.logger.error(f"Error in final score normalization: {str(e)}")
            return scores
            
    def _ensure_shape_compatibility(self, scores: np.ndarray, rule_scores: np.ndarray, rule: object, rule_name: str) -> np.ndarray:
        """
        Ensure that rule scores have the same shape as the input scores.
        
        Args:
            scores: Original scores array
            rule_scores: Scores from applying a rule
            rule: The rule object that generated the scores
            rule_name: Name of the rule for logging
            
        Returns:
            Rule scores with the correct shape
        """
        # Ensure arrays have the same shape before multiplication
        if len(rule_scores) != len(scores):
            self.logger.warning(f"{rule_name} rule returned scores with different shape: {rule_scores.shape} vs {scores.shape}.")
            # Delegate to the rule's _ensure_score_shape method to handle the reshaping
            return rule._ensure_score_shape(rule_scores, len(scores))
        
        return rule_scores

    def _apply_base_rules(self, features: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
        """Apply base scoring rules"""
        for rule_type in self.rules:
            # Extract rule type name if it's a dictionary
            rule_name = rule_type['type'] if isinstance(rule_type, dict) else rule_type
            if rule_name != "intent_specific":
                try:
                    rule = self.rule_factory.create_rule(rule_name)
                    # Pass rule parameters if available
                    params = rule_type.get('params', {}) if isinstance(rule_type, dict) else {}
                    weight = rule_type.get('weight', 1.0) if isinstance(rule_type, dict) else 1.0
                    
                    rule_scores = rule.apply(features, params)
                    rule_scores = self._ensure_shape_compatibility(scores, rule_scores, rule, rule_name)
                    
                    # Apply weighted combination of scores
                    scores = (1 - weight) * scores + weight * rule_scores
                        
                except Exception as e:
                    self.logger.error(f"Error applying rule {rule_name}: {str(e)}")
                    continue
        
        return scores

    def _apply_intent_rules(self, features: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
        """Apply intent-specific scoring rules"""
        try:
            # Get main intent type
            main_intent = features["main_intent"].iloc[0] if "main_intent" in features.columns else None
            
            if not main_intent:
                return scores
            
            # Apply intent-specific rules based on type
            if main_intent == "mock_interview":
                intent_rule = self.intent_rule_factory.create_rule("mock_interview")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "mentoring_mentor":
                intent_rule = self.intent_rule_factory.create_rule("mentoring")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "mentoring_mentee":
                intent_rule = self.intent_rule_factory.create_rule("mentoring_mentee")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "projects_find_contributor":  # Fixed intent type
                intent_rule = self.intent_rule_factory.create_rule("project")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "projects_find_cofounder":
                intent_rule = self.intent_rule_factory.create_rule("projects_find_cofounder")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "projects_pet_project":
                intent_rule = self.intent_rule_factory.create_rule("projects_pet_project")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "referrals_recommendation":  # Fixed intent type
                intent_rule = self.intent_rule_factory.create_rule("referral")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "professional_networking":
                intent_rule = self.intent_rule_factory.create_rule("professional_networking")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "social_expansion":
                intent_rule = self.intent_rule_factory.create_rule("social_expansion")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "connects":
                # Check for professional networking within connects
                if "main_professional_topic" in features.columns and features["main_professional_topic"].iloc[0] is not None:
                    # Handle professional networking
                    intent_rule = self.intent_rule_factory.create_rule("professional_networking")
                    scores = intent_rule.apply(features, scores)
                else:
                    # Handle social expansion (default for connects)
                    intent_rule = self.intent_rule_factory.create_rule("social_expansion")
                    scores = intent_rule.apply(features, scores)
        
            return scores

        except Exception as e:
            self.logger.error(f"Error applying intent rules: {str(e)}")
            return scores
