import pytest
import pandas as pd
import numpy as np
from common_db.enums.users import EGrade
from common_db.enums.meeting_intents import EMeetingIntentQueryType, EMeetingIntentMeetingType
from matching.model.predictors.heuristic_predictor import HeuristicPredictor


@pytest.fixture
def base_features():
    """Create base features DataFrame for testing"""
    n_candidates = 4  # Number of candidates to test
    
    return pd.DataFrame({
        # Main user data - repeated for each candidate
        'main_location': ['moscow_russia'] * n_candidates,
        'main_interests': [['development', 'ai', 'cloud']] * n_candidates,
        'main_expertise_area': [['development', 'data_science']] * n_candidates,
        'main_grade': [EGrade.middle.value] * n_candidates,
        'main_query_type': [EMeetingIntentQueryType.mentoring.value] * n_candidates,
        'main_meeting_type': [EMeetingIntentMeetingType.offline.value] * n_candidates,
        
        # Candidate data - different for each candidate
        'location': ['moscow_russia', 'london_uk', 'moscow_russia', None],
        'interests': [
            ['development', 'ai'],
            ['cloud', 'databases'],
            ['marketing', 'sales'],
            None
        ],
        'expertise_area': [
            ['development', 'data_science'],
            ['development'],
            ['marketing'],
            None
        ],
        'grade': [
            EGrade.senior.value,
            EGrade.middle.value,
            EGrade.junior.value,
            None
        ]
    })


@pytest.fixture
def null_features():
    """Create a DataFrame with all None values for testing edge cases"""
    return pd.DataFrame({
        'main_location': [None],
        'main_interests': [None],
        'main_expertise_area': [None],
        'main_grade': [None],
        'main_query_type': [None],
        'main_meeting_type': [None],
        'location': [None],
        'interests': [None],
        'expertise_area': [None],
        'grade': [None]
    })


def test_location_rule(base_features):
    """Test location matching rule"""
    predictor = HeuristicPredictor(rules=[{
        'name': 'location_matching',
        'type': 'location',
        'weight': 1.0,
        'params': {
            'city_penalty': 0.3,
            'country_penalty': 0.1
        }
    }])
    
    scores = predictor.predict(base_features)
    
    # Perfect match for same location
    assert scores[0] == pytest.approx(1.0)
    # Different city and country
    assert scores[1] == pytest.approx(0.05)
    # Same location
    assert scores[2] == pytest.approx(1.0)
    # None location should get minimum score
    assert scores[3] == pytest.approx(0.05)


def test_interests_rule(base_features):
    """Test interests matching rule"""
    predictor = HeuristicPredictor(rules=[{
        'name': 'interests_matching',
        'type': 'interests',
        'weight': 1.0,
        'params': {
            'base_score': 0.5
        }
    }])
    
    scores = predictor.predict(base_features)
    
    # 2/3 interests match
    assert scores[0] > 0.8
    # 1/3 interests match
    assert scores[1] > 0.6
    # No interests match
    assert scores[2] == pytest.approx(0.5)
    # None interests should get base score
    assert scores[3] == pytest.approx(0.5)


def test_expertise_rule(base_features):
    """Test expertise matching rule"""
    predictor = HeuristicPredictor(rules=[{
        'name': 'expertise_matching',
        'type': 'expertise',
        'weight': 1.0,
        'params': {
            'base_score': 0.6
        }
    }])
    
    scores = predictor.predict(base_features)
    
    # Perfect expertise match
    assert scores[0] == pytest.approx(1.0)
    # Partial expertise match
    assert scores[1] > 0.7
    # No expertise match
    assert scores[2] == pytest.approx(0.6)
    # None expertise should get base score
    assert scores[3] == pytest.approx(0.6)


def test_grade_rule(base_features):
    """Test grade matching rule"""
    predictor = HeuristicPredictor(rules=[{
        'name': 'grade_matching',
        'type': 'grade',
        'weight': 1.0,
        'params': {
            'base_score': 0.7
        }
    }])
    
    scores = predictor.predict(base_features)
    
    # Senior to middle relationship
    assert scores[0] >= 0.8
    # Same grade (middle)
    assert scores[1] == pytest.approx(1.0)
    # Junior to middle relationship
    assert scores[2] < 0.8
    # None grade should get base score
    assert scores[3] == pytest.approx(0.7)


def test_intent_specific_mentoring(base_features):
    """Test intent-specific rule for mentoring"""
    predictor = HeuristicPredictor(rules=[{
        'name': 'intent_specific',
        'type': 'intent_specific',
        'weight': 1.0,
        'params': {
            'non_mentor_penalty': 0.5,
            'expertise_base_score': 0.4
        }
    }])
    
    scores = predictor.predict(base_features)
    
    # Senior with matching expertise - best mentor match
    assert scores[0] == pytest.approx(1.0)
    # Middle grade - acceptable mentor but penalized
    assert 0 < scores[1] < 0.6
    # Junior - heavily penalized for mentoring
    assert scores[2] < 0.4


def test_combined_rules(base_features):
    """Test combination of all rules"""
    predictor = HeuristicPredictor(rules=[
        {
            'name': 'location_matching',
            'type': 'location',
            'weight': 0.8,
            'params': {'city_penalty': 0.3, 'country_penalty': 0.1}
        },
        {
            'name': 'interests_matching',
            'type': 'interests',
            'weight': 0.6,
            'params': {'base_score': 0.5}
        },
        {
            'name': 'expertise_matching',
            'type': 'expertise',
            'weight': 0.7,
            'params': {'base_score': 0.6}
        },
        {
            'name': 'grade_matching',
            'type': 'grade',
            'weight': 0.5,
            'params': {'base_score': 0.7}
        },
        {
            'name': 'intent_specific',
            'type': 'intent_specific',
            'weight': 0.9,
            'params': {
                'non_mentor_penalty': 0.5,
                'expertise_base_score': 0.4,
                'interest_base_score': 0.3
            }
        }
    ])
    
    scores = predictor.predict(base_features)
    
    # Best match: Senior, same location, matching interests and expertise
    assert scores[0] > 0.8
    # Medium match: Middle grade, different location, some matching interests
    assert 0 < scores[1] < 0.7
    # Poor match: Junior, same location but no matching interests/expertise
    assert scores[2] < 0.5
    # Worst match: None values
    assert scores[3] < 0.3


def test_edge_cases(base_features):
    """Test edge cases and null handling"""
    # Create a row with all None values
    null_row = pd.DataFrame({
        'main_location': [None],
        'main_interests': [None],
        'main_expertise_area': [None],
        'main_grade': [None],
        'main_query_type_intent': [None],
        'main_meeting_type_intent': [None],
        'location': [None],
        'interests': [None],
        'expertise_area': [None],
        'grade': [None]
    })
    
    predictor = HeuristicPredictor(rules=[
        {'name': 'location_matching', 'type': 'location', 'weight': 1.0, 'params': {}},
        {'name': 'interests_matching', 'type': 'interests', 'weight': 1.0, 'params': {}},
        {'name': 'expertise_matching', 'type': 'expertise', 'weight': 1.0, 'params': {}},
        {'name': 'grade_matching', 'type': 'grade', 'weight': 1.0, 'params': {}}
    ])
    
    # Should not raise exceptions and return default scores
    scores = predictor.predict(null_row)
    assert all(0 <= score <= 1 for score in scores) 