"""Intent-specific scoring rules implementation"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from datetime import datetime

from .scoring_config import ScoringConfig
from .data_normalizer import DataNormalizer
from .scoring_rules import RuleFactory
from common_db.enums.forms import (
    EFormMentoringGrade,
    EFormMockInterviewType,
    EFormMockInterviewLanguages,
    EFormMentoringHelpRequest,
    EFormEnglishLevel,
    EFormProjectProjectState,
    EFormProjectUserRole,
    EFormConnectsSocialExpansionTopic,
    EFormProfessionalNetworkingTopic,
    EFormRefferalsCompanyType,
    EFormConnectsMeetingFormat,
)

class BaseIntentRule(ABC):
    """Base class for all intent-specific scoring rules"""
    
    def __init__(self, config: ScoringConfig, normalizer: DataNormalizer, rule_factory: RuleFactory):
        self.config = config
        self.normalizer = normalizer
        self.rule_factory = rule_factory
        
    @abstractmethod
    def apply(self, features: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
        """Apply the intent-specific rule to features and scores"""
        pass
        
    def _ensure_shape_compatibility(self, scores: np.ndarray, rule_scores: np.ndarray, rule: object, rule_name: str) -> np.ndarray:
        """Ensure that rule scores have the same shape as the input scores"""
        if len(rule_scores) != len(scores):
            return rule._ensure_score_shape(rule_scores, len(scores))
        return rule_scores
        
    def _calculate_expertise_match(self, candidate_expertise, main_expertise):
        """Calculate expertise match score between candidate and main expertise"""
        if not candidate_expertise or not main_expertise:
            return 0.0
        
        # Convert to sets for easier matching
        candidate_set = set(candidate_expertise) if isinstance(candidate_expertise, list) else {str(candidate_expertise)}
        main_set = set(main_expertise) if isinstance(main_expertise, list) else {str(main_expertise)}
        
        # Calculate Jaccard similarity
        intersection = len(candidate_set.intersection(main_set))
        union = len(candidate_set.union(main_set))
        
        return intersection / union if union > 0 else 0.0
        
    def _normalize_score_range(self, scores, target_range=None):
        """Normalize scores to ensure good use of the range without extreme values"""
        if len(scores) == 0:
            return scores
            
        min_val = np.min(scores)
        max_val = np.max(scores)
        
        # Avoid division by zero
        if max_val == min_val:
            return np.ones_like(scores) * 0.5
        
        # Use provided target range or default
        low, high = (0.2, 0.9) if target_range is None else target_range
        
        # Basic linear normalization
        normalized = low + (high - low) * (scores - min_val) / (max_val - min_val)
        
        # Apply non-linear transformation to increase separation
        mid_point = (low + high) / 2
        normalized = mid_point + (normalized - mid_point) * (1.2 + 0.5 * np.abs(normalized - mid_point))
        
        # Ensure values stay within the target range
        normalized = np.clip(normalized, low, high)
        
        return normalized

    def _combine_scores(self, base_scores: np.ndarray, rule_scores: np.ndarray, weight: float = 0.5) -> np.ndarray:
        """
        Combine base scores with rule scores using weighted average.
        Rule scores are treated as independent factors that can boost or reduce the base score.
        
        Args:
            base_scores: Original scores array
            rule_scores: Scores from applying a rule
            weight: Weight to give to the rule scores (0.0 to 1.0)
            
        Returns:
            Combined scores array
        """
        # Ensure arrays have the same shape
        if len(rule_scores) != len(base_scores):
            rule_scores = self._ensure_shape_compatibility(base_scores, rule_scores, None, "combine_scores")
            
        # Calculate how much the rule scores deviate from 0.5 (neutral point)
        rule_impact = (rule_scores - 0.5) * weight
        
        # Apply the rule impact to base scores
        combined = base_scores + rule_impact
        
        # Ensure scores stay in valid range
        combined = np.clip(combined, 0.0, 1.0)
        
        return combined

    def _apply_rule_with_weight(self, features: pd.DataFrame, scores: np.ndarray, rule_name: str, weight: float = 0.5, params: dict = None) -> np.ndarray:
        """
        Apply a rule with proper weight handling.
        Each rule is treated as an independent factor that can boost or reduce the score.
        
        Args:
            features: Input features DataFrame
            scores: Current scores array
            rule_name: Name of the rule to apply
            weight: Weight to give to the rule (0.0 to 1.0)
            params: Additional parameters for the rule
            
        Returns:
            Updated scores array
        """
        try:
            rule = self.rule_factory.create_rule(rule_name)
            rule_params = params or {}
            rule_scores = rule.apply(features, rule_params)
            
            # Ensure shape compatibility
            rule_scores = self._ensure_shape_compatibility(scores, rule_scores, rule, rule_name)
            
            # Combine scores using the new impact-based approach
            return self._combine_scores(scores, rule_scores, weight)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error applying rule {rule_name}: {str(e)}")
            return scores

class MockInterviewRule(BaseIntentRule):
    """Mock interview specific scoring rule"""
    
    def apply(self, features: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
        try:
            # Get main intent parameters
            main_grade = features["main_grade"].iloc[0] if "main_grade" in features.columns else None
            main_languages = features["main_languages"].iloc[0] if "main_languages" in features.columns else None
            main_expertise = features["main_expertise_area"].iloc[0] if "main_expertise_area" in features.columns else None
            main_type = features["main_mock_interview_type"].iloc[0] if "main_mock_interview_type" in features.columns else None
            
            if not all([main_grade, main_languages, main_expertise, main_type]):
                return scores
            
            # Start with base scores from config
            fresh_scores = np.ones(len(scores)) * self.config.mock_interview.BASE_SCORE
            
            # First, calculate combined grade and expertise scores
            grade_scores = self._apply_rule_with_weight(features, fresh_scores, "grade", weight=self.config.mock_interview.GRADE_WEIGHT)
            expertise_scores = self._apply_rule_with_weight(features, fresh_scores, "expertise", weight=self.config.mock_interview.EXPERTISE_WEIGHT)
            
            # Combine grade and expertise scores with cross-validation
            for idx in range(len(fresh_scores)):
                grade = features.iloc[idx].get("grade") if "grade" in features.columns else None
                expertise = features.iloc[idx].get("expertise_area") if "expertise_area" in features.columns else None
                
                if grade and expertise:
                    grade_str = str(grade).lower()
                    expertise_match = self._calculate_expertise_match(expertise, main_expertise)
                    
                    # Apply grade and expertise combination
                    if expertise_match >= 0.5:
                        if any(g in grade_str for g in ["senior", "lead", "principal"]):
                            fresh_scores[idx] = 0.6 * fresh_scores[idx] + 0.2 * grade_scores[idx] + 0.2 * expertise_scores[idx]
                            fresh_scores[idx] *= self.config.mock_interview.SENIOR_BOOST
                        elif "middle" in grade_str:
                            fresh_scores[idx] = 0.6 * fresh_scores[idx] + 0.2 * grade_scores[idx] + 0.2 * expertise_scores[idx]
                            fresh_scores[idx] *= self.config.mock_interview.MIDDLE_BOOST
                        else:
                            fresh_scores[idx] = 0.6 * fresh_scores[idx] + 0.2 * grade_scores[idx] + 0.2 * expertise_scores[idx]
                    else:
                        fresh_scores[idx] *= self.config.mock_interview.POOR_MATCH_PENALTY
            
            # Apply language matching
            if main_languages:
                language_scores = self._apply_rule_with_weight(features, fresh_scores, "language", weight=self.config.mock_interview.LANGUAGE_WEIGHT)
                for idx in range(len(fresh_scores)):
                    if language_scores[idx] < 0.5:
                        fresh_scores[idx] *= self.config.mock_interview.POOR_MATCH_PENALTY
            
            # Apply type-specific rules
            if main_type == EFormMockInterviewType.behavioral:
                # For behavioral interviews, communication and experience are equally important
                communication_scores = self._apply_rule_with_weight(features, fresh_scores, "communication", weight=self.config.mock_interview.COMMUNICATION_WEIGHT)
                experience_scores = self._apply_rule_with_weight(features, fresh_scores, "project_experience", weight=self.config.mock_interview.EXPERIENCE_WEIGHT)
                
                for idx in range(len(fresh_scores)):
                    # Both communication and experience are important for behavioral interviews
                    if communication_scores[idx] < 0.5 or experience_scores[idx] < 0.5:
                        fresh_scores[idx] *= self.config.mock_interview.POOR_MATCH_PENALTY
                    else:
                        fresh_scores[idx] = 0.6 * fresh_scores[idx] + 0.2 * communication_scores[idx] + 0.2 * experience_scores[idx]
                
            elif main_type == EFormMockInterviewType.technical:
                # For technical interviews, skills and project experience are interdependent
                skill_scores = self._apply_rule_with_weight(features, fresh_scores, "skill", weight=self.config.mock_interview.SKILL_WEIGHT)
                project_scores = self._apply_rule_with_weight(features, fresh_scores, "project_experience", weight=self.config.mock_interview.PROJECT_WEIGHT)
                
                for idx in range(len(fresh_scores)):
                    # Technical interviews require both skills and experience
                    if skill_scores[idx] < 0.5 or project_scores[idx] < 0.5:
                        fresh_scores[idx] *= self.config.mock_interview.POOR_MATCH_PENALTY
                    else:
                        # Strong technical candidates should have both
                        fresh_scores[idx] = 0.5 * fresh_scores[idx] + 0.3 * skill_scores[idx] + 0.2 * project_scores[idx]
                        if skill_scores[idx] > 0.8 and project_scores[idx] > 0.8:
                            fresh_scores[idx] *= self.config.mock_interview.STRONG_TECHNICAL_BOOST
            
            # Ensure minimum scores for good matches
            for idx in range(len(fresh_scores)):
                grade = features.iloc[idx].get("grade") if "grade" in features.columns else None
                expertise = features.iloc[idx].get("expertise_area") if "expertise_area" in features.columns else None
                
                if grade and expertise:
                    grade_str = str(grade).lower()
                    expertise_match = self._calculate_expertise_match(expertise, main_expertise)
                    
                    # Ensure minimum scores for good matches
                    if expertise_match >= 0.5:
                        if any(g in grade_str for g in ["senior", "lead", "principal"]):
                            fresh_scores[idx] = max(fresh_scores[idx], self.config.mock_interview.MIN_SENIOR_SCORE)
                        elif "middle" in grade_str:
                            fresh_scores[idx] = max(fresh_scores[idx], self.config.mock_interview.MIN_MIDDLE_SCORE)
                        else:
                            fresh_scores[idx] = max(fresh_scores[idx], self.config.mock_interview.MIN_JUNIOR_SCORE)
            
            return fresh_scores
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error applying mock interview rules: {str(e)}")
            return scores

class MentoringRule(BaseIntentRule):
    """Mentoring specific scoring rule"""
    
    def apply(self, features: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
        try:
            # Get main intent parameters
            main_grade = features["main_grade"].iloc[0] if "main_grade" in features.columns else None
            main_help_request = features["main_mentoring_help_request"].iloc[0] if "main_mentoring_help_request" in features.columns else None
            
            if not all([main_grade, main_help_request]):
                return scores
                
            # Start with base scores from config
            fresh_scores = np.ones(len(scores)) * self.config.mentoring.BASE_SCORE
                
            # Apply grade matching with mentoring-specific mapping
            grade_rule = self.rule_factory.create_rule("grade")
            grade_scores = grade_rule.apply(features, {"weight": self.config.mentoring.GRADE_WEIGHT})
            grade_scores = self._ensure_shape_compatibility(scores, grade_scores, grade_rule, "grade")
            
            # Apply expertise matching based on help request
            expertise_rule = self.rule_factory.create_rule("expertise")
            expertise_scores = expertise_rule.apply(features, {"weight": self.config.mentoring.EXPERTISE_WEIGHT})
            expertise_scores = self._ensure_shape_compatibility(scores, expertise_scores, expertise_rule, "expertise")
            
            # Apply professional background rule with higher weight for mentoring
            professional_background_rule = self.rule_factory.create_rule("professional_background")
            professional_background_scores = professional_background_rule.apply(
                features,
                {
                    "work_experience_weight": self.config.mentoring.PROF_BACKGROUND_WEIGHT,
                    "education_weight": self.config.mentoring.EDUCATION_WEIGHT,
                    "skills_weight": self.config.mentoring.SKILLS_WEIGHT,
                }
            )
            professional_background_scores = self._ensure_shape_compatibility(
                scores, 
                professional_background_scores, 
                professional_background_rule, 
                "professional_background"
            )
            
            # Combine scores with proper weighting
            for idx in range(len(fresh_scores)):
                # Base score from grade and expertise
                base_score = self.config.mentoring.GRADE_WEIGHT * grade_scores[idx] + self.config.mentoring.EXPERTISE_WEIGHT * expertise_scores[idx]
                
                # Boost based on professional background
                if professional_background_scores[idx] > 0.6:
                    base_score *= self.config.mentoring.PROF_BACKGROUND_BOOST
                
                # Additional boosts based on grade
                grade = features.iloc[idx].get("grade") if "grade" in features.columns else None
                if grade:
                    grade_str = str(grade).lower()
                    if any(g in grade_str for g in ["senior", "lead", "principal"]):
                        base_score *= self.config.mentoring.SENIOR_BOOST
                    elif "middle" in grade_str:
                        base_score *= self.config.mentoring.MIDDLE_BOOST
                
                # Ensure minimum score for good matches
                if base_score > 0.4:
                    base_score = max(base_score, self.config.mentoring.MIN_GOOD_MATCH_SCORE)
                
                fresh_scores[idx] = base_score
            
            return fresh_scores
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error applying mentoring rules: {str(e)}")
            return scores

class ProjectRule(BaseIntentRule):
    """Rule for project matching"""
    
    def apply(self, features: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
        """Apply project matching rules"""
        try:
            # Get main project requirements
            main_content = features["main_content"].iloc[0]
            main_project_type = features["main_project_type"].iloc[0]
            main_project_state = features["main_project_state"].iloc[0]
            main_project_role = features["main_project_role"].iloc[0]
            main_expertise_area = features["main_expertise_area"].iloc[0]
            
            # Calculate project-specific scores
            # Calculate project-specific scores
            project_scores = self._calculate_project_scores(features, main_content, main_project_type, main_project_state, main_project_role, main_expertise_area)
            
            # Apply the project scores to the input scores
            scores = scores * project_scores 
            
            weighted_scores = self._apply_rule_with_weight(
                features,  # Add features parameter
                scores,    # Current scores
                "project", # Add rule_name parameter
                weight=0.8  # High weight for project-specific factors
            )
            
            # Apply grade and expertise scores with cross-validation
            grade_scores = self._apply_rule_with_weight(
                features,  # Add features parameter
                weighted_scores,
                "grade",   # Add rule_name parameter
                weight=0.2
            )
            
            expertise_scores = self._apply_rule_with_weight(
                features,  # Add features parameter
                grade_scores,
                "expertise", # Add rule_name parameter
                weight=0.2
            )
            
            # Normalize final scores with a higher range for better separation
            final_scores = self._normalize_score_range(expertise_scores, (0.4, 0.95))
            
            # Ensure scores are properly shaped
            return self._ensure_shape_compatibility(scores, final_scores, self, "project")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in project rule: {str(e)}")
            return scores
            
    def _calculate_project_scores(self, features: pd.DataFrame, main_content: dict, main_project_type: str, main_project_state: str, main_project_role: str, main_expertise_area: str) -> np.ndarray:
        """Calculate project-specific scores"""
        scores = np.zeros(len(features))
        
        # Extract main requirements
        required_skills = main_content.get("skills", [])
        required_specialization = main_content.get("specialization", [])
        project_state = main_content.get("project_state")
        
        for idx, row in features.iterrows():
            # Get candidate data
            grade = row.get("grade")
            expertise_area = row.get("expertise_area", [])
            specialization = row.get("specialization", [])
            skill_match_score = row.get("skill_match_score")
            
            # Calculate grade score with boost for senior/lead
            grade_score = 0.0
            if grade:
                grade_str = str(grade).lower()
                if any(g in grade_str for g in ["senior", "lead", "principal"]):
                    grade_score = 1.2
                elif "middle" in grade_str:
                    grade_score = 0.8
                else:
                    grade_score = 0.5
            
            # Calculate expertise match with boost for perfect match
            expertise_score = 0.0
            if expertise_area and main_expertise_area:
                expertise_matches = set(expertise_area) & set(main_expertise_area)
                expertise_score = len(expertise_matches) / len(main_expertise_area)
                if expertise_score == 1.0:
                    expertise_score = 1.2
            
            # Calculate specialization match with boost for perfect match
            specialization_score = 0.0
            if specialization and required_specialization:
                spec_matches = set(specialization) & set(required_specialization)
                specialization_score = len(spec_matches) / len(required_specialization)
                if specialization_score == 1.0:
                    specialization_score = 1.2
            
            # Calculate skill match with higher weight for perfect matches
            skill_score = 0.0
            if skill_match_score is not None:
                if skill_match_score >= 2:
                    skill_score = 1.2  # Perfect match
                elif skill_match_score == 1:
                    skill_score = 0.8  # Good match
                else:
                    skill_score = 0.4  # Poor match
            
            # Calculate project state match
            state_score = 0.0
            if project_state:
                candidate_state = row.get("project_state")
                if candidate_state and str(candidate_state) == str(project_state):
                    state_score = 1.2  # Perfect match
                else:
                    state_score = 0.8  # Different state
            
            # Combine scores with adjusted weights
            scores[idx] = (
                0.3 * grade_score +
                0.3 * expertise_score +
                0.2 * specialization_score +
                0.15 * skill_score +
                0.05 * state_score
            )
            
            # Apply additional boost for perfect matches
            if (expertise_score >= 1.0 and specialization_score >= 1.0 and skill_score >= 1.0):
                scores[idx] *= 1.3  # Increased boost for perfect matches
            
        return scores

class ReferralRule(BaseIntentRule):
    """Referral specific scoring rule"""
    
    def apply(self, features: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
        try:
            # Start with base scores from config
            fresh_scores = np.ones(len(scores)) * self.config.referral.BASE_SCORE
            
            # Get main intent parameters
            main_company_type = features["main_company_type"].iloc[0] if "main_company_type" in features.columns else None
            main_expertise = features["main_expertise_area"].iloc[0] if "main_expertise_area" in features.columns else []
            
            # First, calculate expertise matches for all candidates
            expertise_matches = {}
            for idx, row in features.iterrows():
                if idx >= len(fresh_scores):
                    continue
                
                expertise_match = 0.0
                if row.get("expertise_area") is not None:
                    expertise_match = self._calculate_expertise_match(row.get("expertise_area", []), main_expertise)
                expertise_matches[idx] = expertise_match
            
            # Apply expertise rule first with high weight
            expertise_rule = self.rule_factory.create_rule("expertise")
            expertise_scores = expertise_rule.apply(features, {"weight": self.config.referral.EXPERTISE_WEIGHT})
            expertise_scores = self._ensure_shape_compatibility(fresh_scores, expertise_scores, expertise_rule, "expertise")
            
            # Apply expertise scores with high weight
            for idx in range(len(fresh_scores)):
                if idx >= len(expertise_scores):
                    continue
                # Combine scores with higher weight on expertise
                fresh_scores[idx] = (1 - self.config.referral.EXPERTISE_WEIGHT) * fresh_scores[idx] + self.config.referral.EXPERTISE_WEIGHT * expertise_scores[idx]
            
            # Apply professional background with moderate weight
            prof_background_rule = self.rule_factory.create_rule("professional_background")
            prof_background_scores = prof_background_rule.apply(
                features,
                {
                    "work_experience_weight": 0.7,
                    "education_weight": 0.2,
                    "skills_weight": 0.1,
                }
            )
            prof_background_scores = self._ensure_shape_compatibility(
                fresh_scores, 
                prof_background_scores, 
                prof_background_rule, 
                "professional_background"
            )
            
            # Apply professional background scores
            for idx in range(len(fresh_scores)):
                if idx >= len(prof_background_scores):
                    continue
                # Combine scores with higher weight on professional background
                fresh_scores[idx] = (1 - self.config.referral.PROF_BACKGROUND_WEIGHT) * fresh_scores[idx] + self.config.referral.PROF_BACKGROUND_WEIGHT * prof_background_scores[idx]
            
            # Apply network quality with lower weight
            network_rule = self.rule_factory.create_rule("network")
            network_scores = network_rule.apply(features, {"weight": 0.3})
            network_scores = self._ensure_shape_compatibility(fresh_scores, network_scores, network_rule, "network")
            
            # Apply network scores
            for idx in range(len(fresh_scores)):
                if idx >= len(network_scores):
                    continue
                # Combine scores with higher weight on network quality
                fresh_scores[idx] = (1 - self.config.referral.NETWORK_WEIGHT) * fresh_scores[idx] + self.config.referral.NETWORK_WEIGHT * network_scores[idx]
            
            # Apply grade-based boosts and ensure senior candidates meet minimum score
            for idx, row in features.iterrows():
                if idx >= len(fresh_scores):
                    continue
                
                grade = row.get("grade") if "grade" in features.columns else None
                grade_str = str(grade).lower() if grade else ""
                expertise_match = expertise_matches.get(idx, 0.0)
                
                # Apply grade-based boosts
                if expertise_match >= self.config.referral.EXPERTISE_MATCH_THRESHOLD:
                    if any(g in grade_str for g in ["senior", "lead", "principal", "head"]):
                        # Senior+ with matching expertise - highest boost
                        fresh_scores[idx] = max(fresh_scores[idx], self.config.referral.MIN_SENIOR_SCORE)
                        fresh_scores[idx] *= self.config.referral.SENIOR_BOOST
                    elif "middle" in grade_str:
                        # Middle with matching expertise - moderate boost
                        fresh_scores[idx] = max(fresh_scores[idx], self.config.referral.MIN_MIDDLE_SCORE)
                        fresh_scores[idx] *= self.config.referral.MIDDLE_BOOST
                    else:
                        # Junior with matching expertise - small boost
                        fresh_scores[idx] = max(fresh_scores[idx], self.config.referral.MIN_JUNIOR_SCORE)
                else:
                    # Poor expertise match - penalize more aggressively
                    fresh_scores[idx] *= self.config.referral.POOR_MATCH_PENALTY
            
            # Final check to ensure senior candidates with good expertise match exceed minimum score
            for idx, row in features.iterrows():
                if idx >= len(fresh_scores):
                    continue
                
                grade = row.get("grade") if "grade" in features.columns else None
                grade_str = str(grade).lower() if grade else ""
                expertise_match = expertise_matches.get(idx, 0.0)
                
                if any(g in grade_str for g in ["senior", "lead", "principal", "head"]) and expertise_match >= self.config.referral.EXPERTISE_MATCH_THRESHOLD:
                    # For senior candidates with matching expertise, ensure score is at least minimum
                    fresh_scores[idx] = max(fresh_scores[idx], self.config.referral.MIN_SENIOR_SCORE)
            
            return fresh_scores
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in referral rule: {str(e)}")
            return scores

class ProfessionalNetworkingRule(BaseIntentRule):
    """Professional networking specific scoring rule"""
    
    def __init__(self, config: ScoringConfig, normalizer: DataNormalizer, rule_factory: RuleFactory):
        """Initialize the rule with topic-specific scoring rules"""
        super().__init__(config, normalizer, rule_factory)
        
        # Topic-specific scoring rules
        self.professional_topic_rules = {
            # EFormProfessionalNetworkingTopic.CAREER_GROWTH: {
            #     "weight": 1.0,
            #     "required_skills": ["leadership", "career development", "mentoring"],
            # },
            # EFormProfessionalNetworkingTopic.JOB_OPPORTUNITIES: {
            #     "weight": 1.0,
            #     "required_skills": ["recruiting", "hiring", "talent acquisition"],
            # },
            # EFormProfessionalNetworkingTopic.KNOWLEDGE_SHARING: {
            #     "weight": 1.0,
            #     "required_skills": ["teaching", "training", "public speaking"],
            # },
            # EFormProfessionalNetworkingTopic.INDUSTRY_TRENDS: {
            #     "weight": 1.0,
            #     "required_skills": ["research", "analysis", "strategy"],
            # },
        }
    
    def apply(self, features: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
        try:
            # Create a fresh array to avoid compounding effects from prior rule applications
            # Instead of using the input scores, start with a base value of 1.0
            fresh_scores = np.ones(len(scores))
            
            # Get main intent parameters
            main_topic = features["main_professional_topic"].iloc[0] if "main_professional_topic" in features.columns else None
            main_expertise = features["main_expertise_area"].iloc[0] if "main_expertise_area" in features.columns else []
            main_location = features["main_location"].iloc[0] if "main_location" in features.columns else None
            
            # Strong expertise weighting is critical for professional networking
            expertise_rule = self.rule_factory.create_rule("expertise")
            expertise_scores = expertise_rule.apply(features, {"weight": 0.8})
            expertise_scores = self._ensure_shape_compatibility(fresh_scores, expertise_scores, expertise_rule, "expertise")
            
            # Make expertise score have more impact - instead of multiplying by potentially small values
            expertise_scores = 0.3 + 0.7 * expertise_scores  # Ensure min 0.3 base impact
            fresh_scores *= expertise_scores
            
            # Location has secondary importance but should still be significant
            if main_location:
                for idx, row in features.iterrows():
                    if idx >= len(fresh_scores):
                        continue
                        
                    # Check both location and linkedin_location
                    location = row.get("location")
                    linkedin_location = row.get("linkedin_location")
                    
                    # Calculate location match score
                    location_match = False
                    if location and str(location) == str(main_location):
                        location_match = True
                    elif linkedin_location and str(linkedin_location) == str(main_location):
                        location_match = True
                    
                    # Apply location impact
                    if location_match:
                        # Perfect location match should boost score significantly
                        fresh_scores[idx] = min(fresh_scores[idx] * 1.3, 0.95)  # Boost up to 0.95
                    else:
                        # Different location should reduce score
                        fresh_scores[idx] *= 0.7
            
            # Evaluate professional background and network quality independently
            network_rule = self.rule_factory.create_rule("network")
            network_scores = network_rule.apply(features, {"weight": 0.4})
            network_scores = self._ensure_shape_compatibility(fresh_scores, network_scores, network_rule, "network")
            network_scores = 0.7 + 0.3 * network_scores  # Ensure min 0.7 base impact
            fresh_scores *= network_scores
            
            # Grade significantly boosts score for senior roles with relevant expertise
            if "grade" in features.columns:
                for idx, row in features.iterrows():
                    if idx >= len(fresh_scores):
                        continue
                        
                    grade = row.get("grade")
                    if grade is not None:
                        grade_str = str(grade).lower()
                        
                        # Calculate expertise match for grade boosting
                        expertise_match = 0.0
                        if row.get("expertise_area") is not None:
                            expertise_match = self._calculate_expertise_match(row.get("expertise_area", []), main_expertise)
                        
                        # Only apply major boosts if expertise matches
                        if expertise_match >= 0.5:
                            # Lead positions with relevant expertise get the highest boost
                            if "lead" in grade_str:
                                # Squaring makes high values stay high while low values get lower
                                # This creates separation in scores without relying on thresholds
                                fresh_scores[idx] = fresh_scores[idx] ** 0.5  # Square root boosts scores
                                fresh_scores[idx] *= 1.5  # Additional multiplier for leads
                            # Senior positions get a good boost
                            elif "senior" in grade_str:
                                fresh_scores[idx] = fresh_scores[idx] ** 0.7  # Smaller boost than lead
                                fresh_scores[idx] *= 1.2  # Additional multiplier for senior
                            # Middle positions get a modest boost
                            elif "middle" in grade_str:
                                fresh_scores[idx] *= 1.1  # Small boost for middle with relevant expertise
                        else:
                            # Penalize irrelevant expertise
                            fresh_scores[idx] *= 0.6  # Significant penalty regardless of grade
            
            # Apply topic-specific rules if defined
            if main_topic in self.professional_topic_rules:
                topic_rule = self.professional_topic_rules[main_topic]
                
                # Apply skill matching for required skills
                skill_rule = self.rule_factory.create_rule("skill")
                skill_scores = skill_rule.apply(features, {"weight": 0.5})
                skill_scores = self._ensure_shape_compatibility(fresh_scores, skill_scores, skill_rule, "skill")
                skill_scores = 0.7 + 0.3 * skill_scores  # Ensure min 0.7 base impact
                fresh_scores *= skill_scores
            
            # Apply a strong normalization to ensure entire range is used
            # This forces differentiation without hardcoded values
            fresh_scores = self._normalize_score_range(fresh_scores)
            
            return fresh_scores
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error applying professional networking rules: {str(e)}")
            return scores

class SocialExpansionRule(BaseIntentRule):
    """Social expansion specific scoring rule"""
    
    def apply(self, features: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
        try:
            # Start with base scores of 0.5 instead of 1.0
            fresh_scores = np.ones(len(scores)) * 0.5
            
            # Get main intent parameters
            main_topic = features["main_social_topic"].iloc[0] if "main_social_topic" in features.columns else None
            main_expertise = features["main_expertise_area"].iloc[0] if "main_expertise_area" in features.columns else []
            
            # First, calculate base expertise and location matches
            for idx, row in features.iterrows():
                if idx >= len(fresh_scores):
                    continue
                
                # Calculate expertise match
                expertise_match = 0.0
                if row.get("expertise_area") is not None:
                    expertise_match = self._calculate_expertise_match(row.get("expertise_area", []), main_expertise)
                
                # Check location match
                location_match = self._is_matching_location(row, features) if "location" in row else False
                
                # Set base score based on expertise and location
                if expertise_match >= 0.5 and location_match:
                    fresh_scores[idx] = 0.7  # Good base score for matching both
                elif expertise_match >= 0.5 or location_match:
                    fresh_scores[idx] = 0.5  # Moderate base score for matching one
                else:
                    fresh_scores[idx] = 0.3  # Low base score for no matches
            
            # Apply network quality as a modifier
            network_rule = self.rule_factory.create_rule("network")
            network_scores = network_rule.apply(features, {"weight": 0.3})
            network_scores = self._ensure_shape_compatibility(fresh_scores, network_scores, network_rule, "network")
            
            # Apply network as a weighted average with base score
            for idx in range(len(fresh_scores)):
                if idx >= len(network_scores):
                    continue
                fresh_scores[idx] = 0.7 * fresh_scores[idx] + 0.3 * network_scores[idx]
            
            # Apply final normalization to ensure scores are in the right range
            fresh_scores = self._normalize_score_range(fresh_scores, target_range=(0.2, 0.85))
            
            return fresh_scores
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error applying social expansion rules: {str(e)}")
            return scores
            
    def _is_matching_location(self, row, features):
        """Check if row location matches the main location"""
        main_location = features["main_location"].iloc[0] if "main_location" in features.columns else None
        
        if not main_location or not row.get("location"):
            return False
            
        return str(row["location"]) == str(main_location)

class MentoringMenteeRule(BaseIntentRule):
    """Rule for matching mentees with mentors"""
    
    def apply(self, features: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
        try:
            # Get main intent parameters
            main_help_request = features["main_mentoring_help_request"].iloc[0] if "main_mentoring_help_request" in features.columns else None
            main_expertise = features["main_expertise_area"].iloc[0] if "main_expertise_area" in features.columns else []
            
            if not all([main_help_request, main_expertise]):
                return scores
                
            # Start with base scores
            fresh_scores = np.ones(len(scores)) * 0.5
            
            # Apply expertise matching with high weight
            expertise_rule = self.rule_factory.create_rule("expertise")
            expertise_scores = expertise_rule.apply(features, {"weight": 0.8})
            expertise_scores = self._ensure_shape_compatibility(scores, expertise_scores, expertise_rule, "expertise")
            
            # Apply professional background with moderate weight
            prof_background_rule = self.rule_factory.create_rule("professional_background")
            prof_background_scores = prof_background_rule.apply(
                features,
                {
                    "work_experience_weight": 0.4,
                    "education_weight": 0.4,
                    "skills_weight": 0.2,
                }
            )
            prof_background_scores = self._ensure_shape_compatibility(
                scores, 
                prof_background_scores, 
                prof_background_rule, 
                "professional_background"
            )
            
            # Combine scores with proper weighting
            for idx in range(len(fresh_scores)):
                # Base score from expertise and professional background
                base_score = 0.7 * expertise_scores[idx] + 0.3 * prof_background_scores[idx]
                
                # Boost based on grade (mentees should be junior/middle)
                grade = features.iloc[idx].get("grade") if "grade" in features.columns else None
                if grade:
                    grade_str = str(grade).lower()
                    if "junior" in grade_str:
                        base_score *= 1.2  # Boost for junior mentees
                    elif "middle" in grade_str:
                        base_score *= 1.1  # Small boost for middle mentees
                    else:
                        base_score *= 0.8  # Penalty for senior mentees
                
                # Ensure minimum score for good matches
                if base_score > 0.4:
                    base_score = max(base_score, 0.5)
                
                fresh_scores[idx] = base_score
            
            return fresh_scores
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error applying mentoring mentee rules: {str(e)}")
            return scores

class ProjectsFindCofounderRule(BaseIntentRule):
    """Rule for matching cofounders"""
    
    def apply(self, features: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
        try:
            # Get main intent parameters
            main_expertise = features["main_expertise_area"].iloc[0] if "main_expertise_area" in features.columns else []
            main_project_type = features["main_project_type"].iloc[0] if "main_project_type" in features.columns else None
            
            if not all([main_expertise, main_project_type]):
                return scores
                
            # Start with base scores
            fresh_scores = np.ones(len(scores)) * 0.5
            
            # Apply expertise matching with high weight
            expertise_rule = self.rule_factory.create_rule("expertise")
            expertise_scores = expertise_rule.apply(features, {"weight": 0.8})
            expertise_scores = self._ensure_shape_compatibility(scores, expertise_scores, expertise_rule, "expertise")
            
            # Apply professional background with high weight
            prof_background_rule = self.rule_factory.create_rule("professional_background")
            prof_background_scores = prof_background_rule.apply(
                features,
                {
                    "work_experience_weight": 0.5,
                    "education_weight": 0.3,
                    "skills_weight": 0.2,
                }
            )
            prof_background_scores = self._ensure_shape_compatibility(
                scores, 
                prof_background_scores, 
                prof_background_rule, 
                "professional_background"
            )
            
            # Apply project experience with high weight
            project_rule = self.rule_factory.create_rule("project_experience")
            project_scores = project_rule.apply(features, {"weight": 0.7})
            project_scores = self._ensure_shape_compatibility(scores, project_scores, project_rule, "project_experience")
            
            # Combine scores with proper weighting
            for idx in range(len(fresh_scores)):
                # Base score from expertise, professional background, and project experience
                base_score = (
                    0.4 * expertise_scores[idx] +
                    0.3 * prof_background_scores[idx] +
                    0.3 * project_scores[idx]
                )
                
                # Boost based on grade (cofounders should be senior/middle)
                grade = features.iloc[idx].get("grade") if "grade" in features.columns else None
                if grade:
                    grade_str = str(grade).lower()
                    if any(g in grade_str for g in ["senior", "lead", "principal"]):
                        base_score *= 1.3  # Strong boost for senior cofounders
                    elif "middle" in grade_str:
                        base_score *= 1.1  # Moderate boost for middle cofounders
                    else:
                        base_score *= 0.8  # Penalty for junior cofounders
                
                # Boost for entrepreneurial experience
                if features.iloc[idx].get("linkedin_profile"):
                    profile = features.iloc[idx]["linkedin_profile"]
                    if isinstance(profile, dict):
                        # Check for founder/entrepreneur experience
                        work_experience = profile.get("work_experience", [])
                        for exp in work_experience:
                            if isinstance(exp, dict):
                                title = exp.get("title", "").lower()
                                if any(term in title for term in ["founder", "ceo", "entrepreneur", "startup"]):
                                    base_score *= 1.2  # Boost for entrepreneurial experience
                                    break
                
                # Ensure minimum score for good matches
                if base_score > 0.4:
                    base_score = max(base_score, 0.6)
                
                fresh_scores[idx] = base_score
            
            return fresh_scores
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error applying cofounder matching rules: {str(e)}")
            return scores

class ProjectsPetProjectRule(BaseIntentRule):
    """Rule for matching pet project collaborators"""
    
    def apply(self, features: pd.DataFrame, scores: np.ndarray) -> np.ndarray:
        try:
            # Get main intent parameters
            main_expertise = features["main_expertise_area"].iloc[0] if "main_expertise_area" in features.columns else []
            main_project_type = features["main_project_type"].iloc[0] if "main_project_type" in features.columns else None
            
            if not all([main_expertise, main_project_type]):
                return scores
                
            # Start with base scores
            fresh_scores = np.ones(len(scores)) * 0.5
            
            # Apply expertise matching with high weight
            expertise_rule = self.rule_factory.create_rule("expertise")
            expertise_scores = expertise_rule.apply(features, {"weight": 0.7})
            expertise_scores = self._ensure_shape_compatibility(scores, expertise_scores, expertise_rule, "expertise")
            
            # Apply project experience with high weight
            project_rule = self.rule_factory.create_rule("project_experience")
            project_scores = project_rule.apply(features, {"weight": 0.6})
            project_scores = self._ensure_shape_compatibility(scores, project_scores, project_rule, "project_experience")
            
            # Apply skills matching with moderate weight
            skill_rule = self.rule_factory.create_rule("skill")
            skill_scores = skill_rule.apply(features, {"weight": 0.5})
            skill_scores = self._ensure_shape_compatibility(scores, skill_scores, skill_rule, "skill")
            
            # Combine scores with proper weighting
            for idx in range(len(fresh_scores)):
                # Base score from expertise, project experience, and skills
                base_score = (
                    0.4 * expertise_scores[idx] +
                    0.4 * project_scores[idx] +
                    0.2 * skill_scores[idx]
                )
                
                # Boost based on grade (pet projects welcome all levels)
                grade = features.iloc[idx].get("grade") if "grade" in features.columns else None
                if grade:
                    grade_str = str(grade).lower()
                    if any(g in grade_str for g in ["senior", "lead", "principal"]):
                        base_score *= 1.1  # Small boost for senior collaborators
                    elif "middle" in grade_str:
                        base_score *= 1.05  # Very small boost for middle collaborators
                
                # Boost for open source or hobby project experience
                if features.iloc[idx].get("linkedin_profile"):
                    profile = features.iloc[idx]["linkedin_profile"]
                    if isinstance(profile, dict):
                        # Check for open source or hobby project experience
                        projects = profile.get("projects", [])
                        for project in projects:
                            if isinstance(project, dict):
                                project_type = project.get("type", "").lower()
                                if any(term in project_type for term in ["open source", "hobby", "personal"]):
                                    base_score *= 1.2  # Boost for relevant project experience
                                    break
                
                # Ensure minimum score for good matches
                if base_score > 0.4:
                    base_score = max(base_score, 0.5)
                
                fresh_scores[idx] = base_score
            
            return fresh_scores
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error applying pet project matching rules: {str(e)}")
            return scores

class IntentRuleFactory:
    """Factory for creating intent-specific scoring rules"""
    
    def __init__(self, config: ScoringConfig, normalizer: DataNormalizer, rule_factory: RuleFactory):
        """Initialize the factory"""
        self.config = config
        self.normalizer = normalizer
        self.rule_factory = rule_factory
        
        # Map intent types to their rule classes
        self.rule_classes = {
            "mock_interview": MockInterviewRule,
            "mentoring": MentoringRule,
            "mentoring_mentee": MentoringMenteeRule,
            "project": ProjectRule,
            "projects_find_cofounder": ProjectsFindCofounderRule,
            "projects_pet_project": ProjectsPetProjectRule,
            "referral": ReferralRule,
            "professional_networking": ProfessionalNetworkingRule,
            "social_expansion": SocialExpansionRule,
        }
        
    def create_rule(self, intent_type: str) -> BaseIntentRule:
        """Create an intent-specific rule instance by type"""
        if intent_type not in self.rule_classes:
            raise ValueError(f"Unknown intent type: {intent_type}")
            
        return self.rule_classes[intent_type](self.config, self.normalizer, self.rule_factory) 