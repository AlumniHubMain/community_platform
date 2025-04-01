"""Scoring configuration for heuristic predictor"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from common_db.enums.users import (
    EExpertiseArea,
)

@dataclass
class BaseScoreConfig:
    """Base configuration for scoring parameters"""
    MIN_SCORE: float = 0.3
    BASE_SCORE: float = 0.5
    MAX_SCORE: float = 1.0

@dataclass
class NetworkQualityConfig:
    """Configuration for network quality scoring"""
    FOLLOWER_THRESHOLD: int = 5000
    MAX_FOLLOWER_SCORE: float = 0.2
    MAX_COMPLETENESS_SCORE: float = 0.3
    MAX_EXPERIENCE_SCORE: float = 0.2
    COMPLETENESS_WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        "summary": 0.1,
        "skills": 0.1,
        "work_experience": 0.1
    })
    EXPERIENCE_WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        "senior": 0.2,
        "multiple": 0.1
    })

@dataclass
class ExperienceConfig:
    """Configuration for experience scoring"""
    MAX_YEARS: int = 10
    YEARS_WEIGHT: float = 0.6
    QUALITY_WEIGHT: float = 0.4
    ROLE_WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        "senior": 1.0,
        "junior": 0.3,
        "default": 0.6
    })

@dataclass
class SkillsConfig:
    """Configuration for skills scoring"""
    MAX_SKILLS: int = 10
    MAX_ENDORSEMENTS: int = 50
    SKILLS_WEIGHT: float = 0.7
    ENDORSEMENTS_WEIGHT: float = 0.3

@dataclass
class ReferralRuleConfig:
    """Configuration for referral rule scoring"""
    BASE_SCORE: float = 0.3
    EXPERTISE_WEIGHT: float = 0.8
    PROF_BACKGROUND_WEIGHT: float = 0.85
    NETWORK_WEIGHT: float = 0.9
    MIN_SENIOR_SCORE: float = 0.5
    MIN_MIDDLE_SCORE: float = 0.45
    MIN_JUNIOR_SCORE: float = 0.35
    EXPERTISE_MATCH_THRESHOLD: float = 0.4
    SENIOR_BOOST: float = 1.1
    MIDDLE_BOOST: float = 1.05
    POOR_MATCH_PENALTY: float = 0.6

@dataclass
class MockInterviewRuleConfig:
    """Configuration for mock interview rule scoring"""
    BASE_SCORE: float = 0.6
    GRADE_WEIGHT: float = 0.4
    EXPERTISE_WEIGHT: float = 0.4
    LANGUAGE_WEIGHT: float = 0.3
    COMMUNICATION_WEIGHT: float = 0.3
    EXPERIENCE_WEIGHT: float = 0.3
    SKILL_WEIGHT: float = 0.4
    PROJECT_WEIGHT: float = 0.3
    MIN_SENIOR_SCORE: float = 0.6
    MIN_MIDDLE_SCORE: float = 0.5
    MIN_JUNIOR_SCORE: float = 0.4
    SENIOR_BOOST: float = 1.2
    MIDDLE_BOOST: float = 1.1
    POOR_MATCH_PENALTY: float = 0.8
    STRONG_TECHNICAL_BOOST: float = 1.2

@dataclass
class MentoringRuleConfig:
    """Configuration for mentoring rule scoring"""
    BASE_SCORE: float = 0.5
    GRADE_WEIGHT: float = 0.4
    EXPERTISE_WEIGHT: float = 0.4
    PROF_BACKGROUND_WEIGHT: float = 0.6
    EDUCATION_WEIGHT: float = 0.3
    SKILLS_WEIGHT: float = 0.1
    MIN_GOOD_MATCH_SCORE: float = 0.5
    SENIOR_BOOST: float = 1.3
    MIDDLE_BOOST: float = 1.1
    PROF_BACKGROUND_BOOST: float = 1.2

@dataclass
class LocationScoreConfig:
    """Configuration for location scoring"""
    WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        "city_match": 1.0,
        "country_match": 0.7,
        "region_match": 0.5,
        "base_score": 0.5
    })
    ENGLISH_SPEAKING_COUNTRIES: set = field(default_factory=lambda: {
        "usa", "uk", "canada", "australia", "new zealand"
    })

@dataclass
class GradeScoreConfig:
    """Configuration for grade scoring"""
    WEIGHTS: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "junior": {"junior": 1.0, "middle": 0.7, "senior": 0.6},
        "middle": {"middle": 1.0, "senior": 0.8, "junior": 0.6},
        "senior": {"senior": 1.0, "middle": 0.7, "junior": 0.5}
    })
    LEVEL_VALUES: Dict[str, int] = field(default_factory=lambda: {
        "junior": 1,
        "middle": 2,
        "senior": 3,
        "lead": 4,
        "head": 5,
        "executive": 6
    })

@dataclass
class SkillScoreConfig:
    """Configuration for skill scoring"""
    THRESHOLDS: Dict[str, float] = field(default_factory=lambda: {
        "excellent": 0.8,
        "good": 0.6,
        "fair": 0.4,
        "poor": 0.0
    })
    WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        "excellent": 1.0,
        "good": 0.8,
        "fair": 0.6,
        "poor": 0.4
    })

@dataclass
class LanguageScoreConfig:
    """Configuration for language scoring"""
    WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        "country_specific": 1.0,
        "standard": 0.8,
        "base_score": 0.4
    })
    COUNTRY_LANGUAGES: Dict[str, List[str]] = field(default_factory=lambda: {
        "usa": ["english"],
        "uk": ["english"],
        "germany": ["german"],
        "france": ["french"],
        "spain": ["spanish"]
    })

@dataclass
class IntentScoreConfig:
    """Configuration for intent-specific scoring"""
    MOCK_INTERVIEW: Dict[str, float] = field(default_factory=lambda: {
        "grade_weight": 0.4,
        "language_weight": 0.4,
        "expertise_weight": 0.4,
        "senior_bonus": 0.2
    })
    MENTORING: Dict[str, float] = field(default_factory=lambda: {
        "grade_weight": 0.4,
        "specialization_weight": 0.4,
        "experience_weight": 0.3
    })
    PROJECT: Dict[str, float] = field(default_factory=lambda: {
        "skill_weight": 0.4,
        "expertise_weight": 0.3,
        "grade_weight": 0.3
    })
    REFERRAL: Dict[str, float] = field(default_factory=lambda: {
        "english_weight": 0.4,
        "company_weight": 0.3,
        "location_weight": 0.3
    })

@dataclass
class ScoringConfig:
    """Main configuration class combining all scoring parameters"""
    base: BaseScoreConfig = field(default_factory=BaseScoreConfig)
    network_quality: NetworkQualityConfig = field(default_factory=NetworkQualityConfig)
    experience: ExperienceConfig = field(default_factory=ExperienceConfig)
    skills: SkillsConfig = field(default_factory=SkillsConfig)
    referral: ReferralRuleConfig = field(default_factory=ReferralRuleConfig)
    mock_interview: MockInterviewRuleConfig = field(default_factory=MockInterviewRuleConfig)
    mentoring: MentoringRuleConfig = field(default_factory=MentoringRuleConfig)
    location: LocationScoreConfig = field(default_factory=LocationScoreConfig)
    grade: GradeScoreConfig = field(default_factory=GradeScoreConfig)
    skill: SkillScoreConfig = field(default_factory=SkillScoreConfig)
    language: LanguageScoreConfig = field(default_factory=LanguageScoreConfig)
    intent: IntentScoreConfig = field(default_factory=IntentScoreConfig)
    
    # Technical areas configuration
    TECHNICAL_AREAS: set = field(default_factory=lambda: {
        "development", "devops", "data_science", "cyber_security"
    })
    TECHNICAL_WEIGHT: float = 0.4
    NON_TECHNICAL_WEIGHT: float = 0.3
    
    # Similarity thresholds
    TEXT_SIMILARITY_THRESHOLD: float = 0.6
    BACKGROUND_SIMILARITY_THRESHOLD: float = 0.7

    @property
    def MAX_SCORE(self) -> float:
        """Backward compatibility for MAX_SCORE"""
        return self.base.MAX_SCORE

    @property
    def MIN_SCORE(self) -> float:
        """Backward compatibility for MIN_SCORE"""
        return self.base.MIN_SCORE

    @property
    def BASE_SCORE(self) -> float:
        """Backward compatibility for BASE_SCORE"""
        return self.base.BASE_SCORE

    def get_intent_weights(self, intent_type: str) -> Dict[str, float]:
        """Get weights for a specific intent type"""
        intent_map = {
            "mock_interview": self.intent.MOCK_INTERVIEW,
            "mentoring": self.intent.MENTORING,
            "project": self.intent.PROJECT,
            "referral": self.intent.REFERRAL
        }
        return intent_map.get(intent_type, {})

    def get_grade_weight(self, from_grade: str, to_grade: str) -> float:
        """Get weight for grade matching"""
        return self.grade.WEIGHTS.get(from_grade, {}).get(to_grade, self.base.MIN_SCORE)

    def get_skill_score(self, match_ratio: float) -> float:
        """Get skill score based on match ratio"""
        if match_ratio >= self.skill.THRESHOLDS["excellent"]:
            return self.skill.WEIGHTS["excellent"]
        elif match_ratio >= self.skill.THRESHOLDS["good"]:
            return self.skill.WEIGHTS["good"]
        elif match_ratio >= self.skill.THRESHOLDS["fair"]:
            return self.skill.WEIGHTS["fair"]
        return self.skill.WEIGHTS["poor"]