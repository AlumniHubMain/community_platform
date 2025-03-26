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
        features_copy = features.copy()
        
        for idx, row in features_copy.iterrows():
            if 'expertise_area' in row:
                if row['expertise_area'] is None:
                    features_copy.at[idx, 'expertise_area'] = []
                elif isinstance(row['expertise_area'], list):
                    if row['expertise_area'] and not isinstance(row['expertise_area'][0], str):
                        try:
                            features_copy.at[idx, 'expertise_area'] = [
                                area.value if hasattr(area, 'value') else 
                                (area.label if hasattr(area, 'label') else str(area))
                                for area in row['expertise_area']
                            ]
                        except Exception as e:
                            self.logger.warning(f"Failed to extract expertise area values - converting to strings: {e}")
                            features_copy.at[idx, 'expertise_area'] = [str(area) for area in row['expertise_area']]
                elif row['expertise_area'] and not isinstance(row['expertise_area'], str):
                    try:
                        features_copy.at[idx, 'expertise_area'] = [
                            row['expertise_area'].value if hasattr(row['expertise_area'], 'value') else 
                            (row['expertise_area'].label if hasattr(row['expertise_area'], 'label') else str(row['expertise_area']))
                        ]
                    except Exception as e:
                        self.logger.warning(f"Failed to extract expertise area value - converting to string: {e}")
                        features_copy.at[idx, 'expertise_area'] = [str(row['expertise_area'])]
                elif isinstance(row['expertise_area'], str):
                    features_copy.at[idx, 'expertise_area'] = [row['expertise_area']]
                
            if 'interests' in row:
                if row['interests'] is None:
                    features_copy.at[idx, 'interests'] = []
                elif isinstance(row['interests'], list):
                    if row['interests'] and not isinstance(row['interests'][0], str):
                        try:
                            features_copy.at[idx, 'interests'] = [
                                interest.label if hasattr(interest, 'label') else 
                                (interest.value if hasattr(interest, 'value') else str(interest))
                                for interest in row['interests']
                            ]
                        except Exception as e:
                            self.logger.warning(f"Failed to extract interest labels - converting to strings: {e}")
                            features_copy.at[idx, 'interests'] = [str(interest) for interest in row['interests']]
                elif row['interests'] and not isinstance(row['interests'], str):
                    try:
                        features_copy.at[idx, 'interests'] = [
                            row['interests'].label if hasattr(row['interests'], 'label') else 
                            (row['interests'].value if hasattr(row['interests'], 'value') else str(row['interests']))
                        ]
                    except Exception as e:
                        self.logger.warning(f"Failed to extract interest label - converting to string: {e}")
                        features_copy.at[idx, 'interests'] = [str(row['interests'])]
                elif isinstance(row['interests'], str):
                    features_copy.at[idx, 'interests'] = [row['interests']]
                
            if 'skills' in row:
                if row['skills'] is None:
                    features_copy.at[idx, 'skills'] = []
                elif isinstance(row['skills'], list):
                    if row['skills'] and not isinstance(row['skills'][0], str):
                        try:
                            features_copy.at[idx, 'skills'] = [
                                skill.label if hasattr(skill, 'label') else 
                                (skill.value if hasattr(skill, 'value') else str(skill))
                                for skill in row['skills']
                            ]
                        except Exception as e:
                            self.logger.warning(f"Failed to extract skill labels - converting to strings: {e}")
                            features_copy.at[idx, 'skills'] = [str(skill) for skill in row['skills']]
                elif row['skills'] and not isinstance(row['skills'], str):
                    try:
                        features_copy.at[idx, 'skills'] = [
                            row['skills'].label if hasattr(row['skills'], 'label') else 
                            (row['skills'].value if hasattr(row['skills'], 'value') else str(row['skills']))
                        ]
                    except Exception as e:
                        self.logger.warning(f"Failed to extract skill label - converting to string: {e}")
                        features_copy.at[idx, 'skills'] = [str(row['skills'])]
                elif isinstance(row['skills'], str):
                    features_copy.at[idx, 'skills'] = [row['skills']]
                            
            for field in ['specialisations', 'specialisation']:
                if field in row:
                    if row[field] is None:
                        features_copy.at[idx, field] = []
                    elif isinstance(row[field], list):
                        if row[field] and not isinstance(row[field][0], str):
                            try:
                                features_copy.at[idx, field] = [
                                    spec.label if hasattr(spec, 'label') else 
                                    (spec.value if hasattr(spec, 'value') else str(spec))
                                    for spec in row[field]
                                ]
                            except Exception as e:
                                self.logger.warning(f"Failed to extract {field} labels - converting to strings: {e}")
                                features_copy.at[idx, field] = [str(spec) for spec in row[field]]
                    elif row[field] and not isinstance(row[field], str):
                        try:
                            features_copy.at[idx, field] = [
                                row[field].label if hasattr(row[field], 'label') else 
                                (row[field].value if hasattr(row[field], 'value') else str(row[field]))
                            ]
                        except Exception as e:
                            self.logger.warning(f"Failed to extract {field} label - converting to string: {e}")
                            features_copy.at[idx, field] = [str(row[field])]
                    elif isinstance(row[field], str):
                        features_copy.at[idx, field] = [row[field]]
            
            for field in ['industries', 'industry']:
                if field in row:
                    if row[field] is None:
                        features_copy.at[idx, field] = []
                    elif isinstance(row[field], list):
                        if row[field] and not isinstance(row[field][0], str):
                            try:
                                features_copy.at[idx, field] = [
                                    ind.label if hasattr(ind, 'label') else 
                                    (ind.value if hasattr(ind, 'value') else str(ind))
                                    for ind in row[field]
                                ]
                            except Exception as e:
                                self.logger.warning(f"Failed to extract {field} labels - converting to strings: {e}")
                                features_copy.at[idx, field] = [str(ind) for ind in row[field]]
                    elif row[field] and not isinstance(row[field], str):
                        try:
                            features_copy.at[idx, field] = [
                                row[field].label if hasattr(row[field], 'label') else 
                                (row[field].value if hasattr(row[field], 'value') else str(row[field]))
                            ]
                        except Exception as e:
                            self.logger.warning(f"Failed to extract {field} label - converting to string: {e}")
                            features_copy.at[idx, field] = [str(row[field])]
                    elif isinstance(row[field], str):
                        features_copy.at[idx, field] = [row[field]]
            
            if 'linkedin_profile' in row and row['linkedin_profile']:
                try:
                    profile = row['linkedin_profile']
                    
                    if hasattr(profile, 'model_dump'):
                        profile_dict = profile.model_dump()
                    elif hasattr(profile, 'dict'):
                        profile_dict = profile.dict()
                    elif isinstance(profile, dict):
                        profile_dict = profile.copy()
                    else:
                        profile_dict = {"raw_data": str(profile)}
                        
                    if 'work_experience' in profile_dict and isinstance(profile_dict['work_experience'], list):
                        processed_work_exp = []
                        for exp in profile_dict['work_experience']:
                            if isinstance(exp, dict):
                                processed_work_exp.append(exp)
                            elif hasattr(exp, 'dict'):
                                processed_work_exp.append(exp.dict())
                            elif hasattr(exp, 'model_dump'):
                                processed_work_exp.append(exp.model_dump())
                            else:
                                processed_work_exp.append({"title": str(exp)})
                        profile_dict['work_experience'] = processed_work_exp
                    
                    if 'skills' in profile_dict:
                        if profile_dict['skills'] is None:
                            profile_dict['skills'] = []
                        elif not isinstance(profile_dict['skills'], list):
                            profile_dict['skills'] = [str(profile_dict['skills'])]
                    
                    if 'languages' in profile_dict:
                        if profile_dict['languages'] is None:
                            profile_dict['languages'] = []
                        elif not isinstance(profile_dict['languages'], list):
                            profile_dict['languages'] = [str(profile_dict['languages'])]
                            
                    features_copy.at[idx, 'linkedin_profile'] = profile_dict
                except Exception as e:
                    self.logger.warning(f"Failed to convert LinkedIn profile: {e}")
                    features_copy.at[idx, 'linkedin_profile'] = {}
            elif 'linkedin_profile' in row and row['linkedin_profile'] is None:
                features_copy.at[idx, 'linkedin_profile'] = {}
        
        return features_copy
    
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Generate predictions using heuristic rules"""
        features = self._aggregate_user_data(features)
        features = self.normalizer.normalize_features(features)
        scores = np.ones(len(features), dtype=np.float64) * 0.5
        scores = self._apply_base_rules(features, scores)
        
        if "main_intent" in features.columns:
            scores = self._apply_intent_rules(features, scores)
        
        scores = self._normalize_final_scores(scores, features)
        return scores

    def _normalize_final_scores(self, scores: np.ndarray, features: pd.DataFrame) -> np.ndarray:
        """Apply general normalization to final scores based on key attributes"""
        try:
            scores = np.asarray(scores).flatten()
            main_intent = features["main_intent"].iloc[0] if "main_intent" in features.columns else None
            
            if "linkedin_profile" in features.columns:
                for idx, row in features.iterrows():
                    if idx >= len(scores):
                        continue
                        
                    profile = row.get("linkedin_profile")
                    if profile and isinstance(profile, dict):
                        follower_count = profile.get("follower_count", 0)
                        has_summary = bool(profile.get("summary"))
                        has_skills = bool(profile.get("skills"))
                        has_experience = bool(profile.get("work_experience"))
                        
                        profile_boost = 0.0
                        if follower_count > 1000:
                            profile_boost += 0.15
                        if has_summary:
                            profile_boost += 0.05
                        if has_skills:
                            profile_boost += 0.05
                        if has_experience:
                            profile_boost += 0.05
                            
                        scores[idx] = min(scores[idx] + profile_boost, 0.9)
            
            if "main_content" in features.columns and len(features) > 0:
                main_content = features["main_content"].iloc[0]
                if isinstance(main_content, dict) and "meeting_format" in main_content:
                    meeting_format = main_content["meeting_format"]
                    if meeting_format == EFormConnectsMeetingFormat.offline.value:
                        if "location" in features.columns and "main_location" in features.columns:
                            main_location = features["main_location"].iloc[0]
                            for idx, row in features.iterrows():
                                if idx >= len(scores):
                                    self.logger.warning(f"Index {idx} out of bounds in scores array of length {len(scores)}")
                                    continue
                                    
                                if row.get("location") is not None and str(row.get("location")) == str(main_location):
                                    scores[idx] = min(scores[idx] * 1.6, 0.9)
                                elif row.get("location") is not None:
                                    scores[idx] *= 0.5
                                elif row.get("linkedin_location") is not None:
                                    if str(row.get("linkedin_location")) == str(main_location):
                                        scores[idx] = min(scores[idx] * 1.3, 0.85)
            
            if "grade" in features.columns:
                for idx, row in features.iterrows():
                    if idx >= len(scores):
                        self.logger.warning(f"Index {idx} out of bounds in scores array of length {len(scores)}")
                        continue
                        
                    grade = row.get("grade")
                    if grade:
                        grade_str = str(grade).lower()
                        
                        if main_intent == "mentoring_mentee":
                            if any(g in grade_str for g in ["junior", "intern"]):
                                scores[idx] = min(max(scores[idx], 0.5), 0.8)
                            elif "middle" in grade_str:
                                scores[idx] = min(max(scores[idx], 0.4), 0.7)
                            else:
                                scores[idx] *= 0.7
                        elif main_intent == "projects_find_cofounder":
                            if any(g in grade_str for g in ["senior", "lead", "principal", "head"]):
                                scores[idx] = min(max(scores[idx], 0.6), 0.9)
                            elif "middle" in grade_str:
                                scores[idx] = min(max(scores[idx], 0.5), 0.8)
                            else:
                                scores[idx] *= 0.7
                        elif main_intent == "projects_pet_project":
                            if any(g in grade_str for g in ["senior", "lead", "principal"]):
                                scores[idx] = min(max(scores[idx], 0.5), 0.85)
                            elif "middle" in grade_str:
                                scores[idx] = min(max(scores[idx], 0.4), 0.8)
                            else:
                                scores[idx] = min(max(scores[idx], 0.3), 0.75)
                        else:
                            if any(g in grade_str for g in ["lead", "senior", "principal", "head"]):
                                if scores[idx] > 0.6:
                                    scores[idx] = min(max(scores[idx], 0.7), 0.9)
                            elif "middle" in grade_str:
                                if scores[idx] > 0.4:
                                    scores[idx] = min(max(scores[idx], 0.5), 0.85)
                            elif any(g in grade_str for g in ["junior", "intern"]):
                                scores[idx] = min(scores[idx], 0.75)
            
            for idx in range(len(scores)):
                if scores[idx] < 0.01:
                    scores[idx] = 0.01
                elif scores[idx] > 0.99:
                    scores[idx] = 0.99
            
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
        if len(rule_scores) != len(scores):
            self.logger.warning(f"{rule_name} rule returned scores with different shape: {rule_scores.shape} vs {scores.shape}.")
            return rule._ensure_score_shape(rule_scores, len(scores))
        
        return rule_scores

    def _apply_base_rules(self, features: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
        """Apply base scoring rules"""
        for rule_type in self.rules:
            rule_name = rule_type['type'] if isinstance(rule_type, dict) else rule_type
            if rule_name != "intent_specific":
                try:
                    rule = self.rule_factory.create_rule(rule_name)
                    params = rule_type.get('params', {}) if isinstance(rule_type, dict) else {}
                    weight = rule_type.get('weight', 1.0) if isinstance(rule_type, dict) else 1.0
                    
                    rule_scores = rule.apply(features, params)
                    rule_scores = self._ensure_shape_compatibility(scores, rule_scores, rule, rule_name)
                    
                    scores = (1 - weight) * scores + weight * rule_scores
                        
                except Exception as e:
                    self.logger.error(f"Error applying rule {rule_name}: {str(e)}")
                    continue
        
        return scores

    def _apply_intent_rules(self, features: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
        """Apply intent-specific scoring rules"""
        try:
            main_intent = features["main_intent"].iloc[0] if "main_intent" in features.columns else None
            
            if not main_intent:
                return scores
            
            if main_intent == "mock_interview":
                intent_rule = self.intent_rule_factory.create_rule("mock_interview")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "mentoring_mentor":
                intent_rule = self.intent_rule_factory.create_rule("mentoring")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "mentoring_mentee":
                intent_rule = self.intent_rule_factory.create_rule("mentoring_mentee")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "projects_find_contributor":
                intent_rule = self.intent_rule_factory.create_rule("project")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "projects_find_cofounder":
                intent_rule = self.intent_rule_factory.create_rule("projects_find_cofounder")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "projects_pet_project":
                intent_rule = self.intent_rule_factory.create_rule("projects_pet_project")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "referrals_recommendation":
                intent_rule = self.intent_rule_factory.create_rule("referral")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "professional_networking":
                intent_rule = self.intent_rule_factory.create_rule("professional_networking")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "social_expansion":
                intent_rule = self.intent_rule_factory.create_rule("social_expansion")
                scores = intent_rule.apply(features, scores)
            elif main_intent == "connects":
                if "main_professional_topic" in features.columns and features["main_professional_topic"].iloc[0] is not None:
                    intent_rule = self.intent_rule_factory.create_rule("professional_networking")
                    scores = intent_rule.apply(features, scores)
                else:
                    intent_rule = self.intent_rule_factory.create_rule("social_expansion")
                    scores = intent_rule.apply(features, scores)
        
            return scores

        except Exception as e:
            self.logger.error(f"Error applying intent rules: {str(e)}")
            return scores
