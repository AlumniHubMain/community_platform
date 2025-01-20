"""Heuristic predictor"""
import pandas as pd
import numpy as np

from common_db.enums.users import EGrade
from common_db.enums.meeting_intents import EMeetingIntentQueryType, EMeetingIntentMeetingType

from .base import BasePredictor


class HeuristicPredictor(BasePredictor):
    """Heuristic-based predictor"""

    def __init__(self, rules: list[dict]):
        """Initialize with list of rules

        Each rule is a dict with:
        - name: str - rule name
        - type: str - 'location', 'interests', 'expertise', 'grade', 'intent_specific'
        - weight: float - base weight of this rule (0-1)
        - params: dict - additional parameters for the rule
        """
        self.rules = rules

    def _apply_location_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Apply location matching rule"""
        scores = np.ones(len(features))
        main_location = features['main_location'].iloc[0]  # From main user
        
        if not main_location:
            return scores
            
        # Extract city and country from location enum
        def get_city_country(location: str) -> tuple[str, str]:
            if not location:
                return "", ""
            try:
                # Parse location like 'moscow_russia' into ('moscow', 'russia')
                return tuple(location.split('_', 1))
            except:
                return "", ""
        
        main_city, main_country = get_city_country(main_location)
        
        def location_match(location):
            if not location:
                return False, False
            city, country = get_city_country(location)
            return city == main_city, country == main_country
            
        location_scores = features['location'].apply(
            lambda x: 1.0 if x == main_location else
            params.get('city_penalty', 0.3) if location_match(x)[0] else
            params.get('country_penalty', 0.1) if location_match(x)[1] else
            0.05
        )
        
        scores *= location_scores
        return scores

    def _apply_interests_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Apply interests matching rule"""
        scores = np.ones(len(features))
        main_interests = features['main_interests'].iloc[0]  # From main user
        
        if not main_interests:
            return scores
        
        def calculate_overlap(interests):
            if not interests or not main_interests:
                return 0
            overlap = set(interests) & set(main_interests)
            return len(overlap) / max(len(main_interests), len(interests))
        
        interest_scores = features['interests'].apply(calculate_overlap)
        base_score = params.get('base_score', 0.5)
        scores *= (base_score + (1 - base_score) * interest_scores)
        
        return scores

    def _apply_expertise_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Apply expertise area matching rule"""
        scores = np.ones(len(features))
        main_expertise = features['main_expertise_area'].iloc[0]  # From main user
        
        if not main_expertise:
            return scores
        
        def calculate_expertise_match(expertise):
            if not expertise or not main_expertise:
                return 0
            overlap = set(expertise) & set(main_expertise)
            return len(overlap) / max(len(main_expertise), len(expertise))
        
        expertise_scores = features['expertise_area'].apply(calculate_expertise_match)
        base_score = params.get('base_score', 0.6)
        scores *= (base_score + (1 - base_score) * expertise_scores)
        
        return scores

    def _apply_grade_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Apply grade matching rule"""
        scores = np.ones(len(features))
        main_grade = features['main_grade'].iloc[0]  # From main user
        
        if not main_grade:
            return scores
            
        # Grade matching weights based on seniority levels
        grade_weights = {
            EGrade.junior.value: {
                EGrade.junior.value: 1.0, 
                EGrade.middle.value: 0.7,
                EGrade.senior.value: 0.6
            },
            EGrade.middle.value: {
                EGrade.middle.value: 1.0, 
                EGrade.senior.value: 0.8,  # Reduced from 0.9
                EGrade.junior.value: 0.6   # Reduced from 0.7
            },
            EGrade.senior.value: {
                EGrade.senior.value: 1.0, 
                EGrade.middle.value: 0.7,
                EGrade.junior.value: 0.5 
            }
        }
        
        grade_scores = features['grade'].apply(
            lambda x: grade_weights.get(main_grade, {}).get(x, params.get('base_score', 0.7)) if x else params.get('base_score', 0.7)
        )
        
        scores *= grade_scores
        return scores

    def _apply_intent_specific_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Apply intent-specific rules"""
        scores = np.ones(len(features))
        query_type = features['main_query_type'].iloc[0]  # From intent
        meeting_type = features['main_meeting_type'].iloc[0]  # From intent
        
        # Handle different query types
        if query_type == EMeetingIntentQueryType.mentoring.value:
            # For mentoring, prefer higher grade mentors
            mentor_grades = {
                EGrade.senior.value: 1.0,
                EGrade.middle.value: 0.4,
                EGrade.junior.value: 0.1
            }
            
            grade_scores = features['grade'].apply(
                lambda x: mentor_grades.get(x, 0.05) if x else 0.05
            )
            scores *= grade_scores
            
            # Also consider expertise area match for mentoring
            expertise_scores = self._apply_expertise_rule(features, {
                'base_score': params.get('expertise_base_score', 0.4)
            })
            scores = np.maximum(scores * expertise_scores, scores * 0.5)
            
        elif query_type == EMeetingIntentQueryType.cooperative_learning.value:
            # For cooperative learning, strongly prefer matching interests and expertise
            interest_scores = self._apply_interests_rule(features, {
                'base_score': params.get('interest_base_score', 0.3)
            })
            expertise_scores = self._apply_expertise_rule(features, {
                'base_score': params.get('expertise_base_score', 0.3)
            })
            scores *= np.maximum(interest_scores * expertise_scores, 0.3)
            
        # Handle meeting type
        if meeting_type == EMeetingIntentMeetingType.offline.value:
            # For offline meetings, location is critical
            location_scores = self._apply_location_rule(features, {
                'city_penalty': 0.2,
                'country_penalty': 0.05
            })
            scores *= location_scores
            
        return scores

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Apply heuristic rules to make predictions"""
        final_scores = np.ones(len(features))
        
        for rule in self.rules:
            rule_type = rule['type']
            weight = rule['weight']
            params = rule.get('params', {})
            
            if rule_type == 'location':
                scores = self._apply_location_rule(features, params)
            elif rule_type == 'interests':
                scores = self._apply_interests_rule(features, params)
            elif rule_type == 'expertise':
                scores = self._apply_expertise_rule(features, params)
            elif rule_type == 'grade':
                scores = self._apply_grade_rule(features, params)
            elif rule_type == 'intent_specific':
                scores = self._apply_intent_specific_rule(features, params)
            else:
                continue
            final_scores *= (weight * scores + (1 - weight))
            
        return final_scores
