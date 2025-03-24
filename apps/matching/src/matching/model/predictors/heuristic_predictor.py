"""Heuristic predictor"""

import logging
import pandas as pd
import numpy as np
from common_db.enums.users import (
    EGrade,
)
from common_db.enums.forms import (
    EFormIntentType,
    EFormConnectsMeetingFormat,
    EFormMentoringGrade,
    EFormProjectUserRole,
    EFormMockInterviewType,
    EFormMentoringHelpRequest,
    EFormEnglishLevel,
    EFormProjectProjectState,
    EFormConnectsSocialExpansionTopic,
    EFormMockInterviewLanguages,
    EFormRefferalsCompanyType,
    EFormProfessionalNetworkingTopic,
)

from .base import BasePredictor
from .scoring_config import ScoringConfig
import traceback
from .data_normalizer import DataNormalizer
from .scoring_rules import RuleFactory

class HeuristicPredictor(BasePredictor):
    """Heuristic-based predictor"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = ScoringConfig()
        self.normalizer = DataNormalizer()
        self.rule_factory = RuleFactory(self.config, self.normalizer)
        
    def predict(self, features: pd.DataFrame, params: dict = None) -> np.ndarray:
        """
        Predict matching scores for users based on features
        
        Args:
            features: DataFrame with user features
            params: Optional parameters for prediction
            
        Returns:
            Array of scores for each user
        """
        if params is None:
            params = {}
            
        # Normalize features
        features = self.normalizer.normalize_features(features)
        
        # Initialize scores
        scores = np.ones(len(features))
        
        # Apply base rules
        scores *= self._apply_base_rules(features, params)
        
        # Apply intent-specific rules
        scores *= self._apply_intent_rules(features, params)
        
        # Ensure scores are between MIN_SCORE and MAX_SCORE
        return np.clip(scores, self.config.MIN_SCORE, self.config.MAX_SCORE)
        
    def _apply_base_rules(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Apply base matching rules"""
        scores = np.ones(len(features))
        
        # Apply location rule
        location_rule = self.rule_factory.create_rule("location")
        scores *= location_rule.apply(features, params)
        
        # Apply grade rule
        grade_rule = self.rule_factory.create_rule("grade")
        scores *= grade_rule.apply(features, params)
        
        # Apply skill rule
        skill_rule = self.rule_factory.create_rule("skill")
        scores *= skill_rule.apply(features, params)
        
        # Apply language rule
        language_rule = self.rule_factory.create_rule("language")
        scores *= language_rule.apply(features, params)
        
        # Apply expertise rule
        expertise_rule = self.rule_factory.create_rule("expertise")
        scores *= expertise_rule.apply(features, params)
        
        # Apply network quality rule
        network_rule = self.rule_factory.create_rule("network")
        scores *= network_rule.apply(features, params)
        
        # Apply project experience rule
        project_rule = self.rule_factory.create_rule("project_experience")
        scores *= project_rule.apply(features, params)
        
        # Apply education rule
        education_rule = self.rule_factory.create_rule("education")
        scores *= education_rule.apply(features, params)
        
        # Apply availability rule
        availability_rule = self.rule_factory.create_rule("availability")
        scores *= availability_rule.apply(features, params)
        
        # Apply communication style rule
        communication_rule = self.rule_factory.create_rule("communication")
        scores *= communication_rule.apply(features, params)
        
        return scores
        
    def _apply_intent_rules(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Apply intent-specific rules"""
        scores = np.ones(len(features))
        
        if "main_intent" not in features.columns:
            return scores
            
        intent_type = self.normalizer.normalize_intent(features["main_intent"].iloc[0])
        if not intent_type:
            return scores
            
        # Get intent-specific weights
        intent_weights = self.config.get_intent_weights(intent_type)
        if not intent_weights:
            return scores
            
        # Apply intent-specific scoring
        if intent_type == "mock_interview":
            scores *= self._apply_mock_interview_rules(features, intent_weights)
        elif intent_type == "mentoring":
            scores *= self._apply_mentoring_rules(features, intent_weights)
        elif intent_type == "project":
            scores *= self._apply_project_rules(features, intent_weights)
        elif intent_type == "referral":
            scores *= self._apply_referral_rules(features, intent_weights)
            
        return scores
        
    def _apply_mock_interview_rules(
        self, features: pd.DataFrame, weights: dict
    ) -> np.ndarray:
        """Apply mock interview specific rules"""
        scores = np.ones(len(features))
        
        # Grade matching with higher weight
        grade_rule = self.rule_factory.create_rule("grade")
        grade_scores = grade_rule.apply(features, {"weight": weights["grade_weight"]})
        scores *= grade_scores
        
        # Language matching with higher weight
        language_rule = self.rule_factory.create_rule("language")
        language_scores = language_rule.apply(features, {"weight": weights["language_weight"]})
        scores *= language_scores
        
        # Expertise matching with higher weight
        expertise_rule = self.rule_factory.create_rule("expertise")
        expertise_scores = expertise_rule.apply(features, {"weight": weights["expertise_weight"]})
        scores *= expertise_scores
        
        # Add senior bonus if applicable
        if "main_grade" in features.columns:
            main_grade = self.normalizer.normalize_grade(features["main_grade"].iloc[0])
            if main_grade == "senior":
                scores *= (1 + weights["senior_bonus"])
                
        return scores
        
    def _apply_mentoring_rules(
        self, features: pd.DataFrame, weights: dict
    ) -> np.ndarray:
        """Apply mentoring specific rules"""
        scores = np.ones(len(features))
        
        # Grade matching with higher weight
        grade_rule = self.rule_factory.create_rule("grade")
        grade_scores = grade_rule.apply(features, {"weight": weights["grade_weight"]})
        scores *= grade_scores
        
        # Specialization matching
        expertise_rule = self.rule_factory.create_rule("expertise")
        expertise_scores = expertise_rule.apply(
            features, {"weight": weights["specialization_weight"]}
        )
        scores *= expertise_scores
        
        # Experience quality consideration
        network_rule = self.rule_factory.create_rule("network")
        network_scores = network_rule.apply(
            features, {"weight": weights["experience_weight"]}
        )
        scores *= network_scores
        
        return scores
        
    def _apply_project_rules(
        self, features: pd.DataFrame, weights: dict
    ) -> np.ndarray:
        """Apply project specific rules"""
    def __init__(self, rules: list[dict], config: ScoringConfig | None = None):
        """Initialize with list of rules and optional configuration

        Args:
            rules: List of rule dictionaries
            config: Optional scoring configuration
        """
        self.rules = rules
        self.logger = logging.getLogger(__name__)
        self.config = config or ScoringConfig()
        
        # Grade mapping between different enum types
        self.grade_mapping = {
            # Form grade to user grade
            EFormMentoringGrade.junior.value: EGrade.junior.value,
            EFormMentoringGrade.middle.value: EGrade.middle.value,
            EFormMentoringGrade.senior.value: EGrade.senior.value,
            EFormMentoringGrade.lead.value: EGrade.senior.value,
            EFormMentoringGrade.head.value: EGrade.senior.value,
            EFormMentoringGrade.executive.value: EGrade.senior.value,
            
            # User grade to form grade
            EGrade.junior.value: EFormMentoringGrade.junior.value,
            EGrade.middle.value: EFormMentoringGrade.middle.value,
            EGrade.senior.value: EFormMentoringGrade.senior.value,
        }

        # Add topic-specific scoring rules
        self.professional_topic_rules = {
            EFormProfessionalNetworkingTopic.development.value: {
                'senior_bonus': self.config.TECHNICAL_WEIGHT,
                'middle_bonus': self.config.NON_TECHNICAL_WEIGHT,
                'required_skills': ['development', 'programming', 'frontend', 'backend'],
                'weight': self.config.MAX_SCORE
            },
            EFormProfessionalNetworkingTopic.analytics.value: {
                'senior_bonus': self.config.TECHNICAL_WEIGHT - 0.1,
                'middle_bonus': self.config.NON_TECHNICAL_WEIGHT,
                'data_science_bonus': self.config.TECHNICAL_WEIGHT - 0.1,
                'required_skills': ['analytics', 'data_science', 'machine_learning'],
                'weight': 0.9
            }
        }
        
        self.social_topic_rules = {
            EFormConnectsSocialExpansionTopic.development__web_development.value: {
                'expertise_weight': self.config.TECHNICAL_WEIGHT + 0.3,
                'interests_weight': self.config.NON_TECHNICAL_WEIGHT,
                'required_skills': ['frontend', 'backend', 'web']
            },
            EFormConnectsSocialExpansionTopic.development__mobile_development.value: {
                'expertise_weight': self.config.TECHNICAL_WEIGHT + 0.3,
                'interests_weight': self.config.NON_TECHNICAL_WEIGHT,
                'required_skills': ['mobile', 'ios', 'android']
            },
            EFormConnectsSocialExpansionTopic.design__design_system_development.value: {
                'expertise_weight': self.config.TECHNICAL_WEIGHT + 0.2,
                'interests_weight': self.config.NON_TECHNICAL_WEIGHT + 0.1,
                'required_skills': ['design', 'ui', 'ux']
            }
        }

    def _normalize_grade(self, grade, target_type="user"):
        """
        Normalize grade between different enum types
        
        Args:
            grade: The grade value to normalize
            target_type: Either 'user' (convert to EGrade) or 'form' (convert to EFormMentoringGrade)
            
        Returns:
            Normalized grade value
        """
        if not grade:
            return None
            
        if target_type == "user":
            return self.grade_mapping.get(grade, grade)
        else:  # target_type == "form"
            # Reverse mapping
            reverse_mapping = {v: k for k, v in self.grade_mapping.items() 
                              if k in [g.value for g in EFormMentoringGrade]}
            return reverse_mapping.get(grade, grade)

    def _apply_location_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Enhanced location matching rule"""
        scores = np.ones(len(features))
        main_location = features["main_location"].iloc[0] if "main_location" in features.columns else None

        # If no main location, try LinkedIn location
        if not main_location and "linkedin_location" in features.columns:
            main_location = features["linkedin_location"].iloc[0]
            
        # If still no location, return base scores
        if not main_location:
            return scores * params.get("base_score", 0.5)

        def get_location_details(location: str) -> tuple[str, str, str]:
            """Extract city, country and region from location"""
            if not location:
                return "", "", ""
                
            parts = location.split("_")
            city = parts[0] if len(parts) > 0 else ""
            country = parts[1] if len(parts) > 1 else ""
            region = parts[2] if len(parts) > 2 else ""
            return city, country, region

        main_city, main_country, main_region = get_location_details(main_location)

        def calculate_location_score(row):
            # Get all possible locations for this user from different sources
            locations = []
            
            # Add profile location
            if row.get("location"):
                locations.append(row["location"])
                
            # Add standalone LinkedIn location
            if row.get("linkedin_location"):
                locations.append(row["linkedin_location"])
                
            # Add LinkedIn profile location
            if row.get("linkedin_profile") and row["linkedin_profile"].get("location"):
                locations.append(row["linkedin_profile"]["location"])
                
            # Add work experience locations from LinkedIn
            if row.get("linkedin_profile") and row["linkedin_profile"].get("work_experience"):
                for exp in row["linkedin_profile"]["work_experience"]:
                    if isinstance(exp, dict) and exp.get("location"):
                        locations.append(exp["location"])
                    elif hasattr(exp, "location") and exp.location:
                        locations.append(exp.location)
                
            # If no locations found, return base score
            if not locations:
                return params.get("base_score", 0.5)
                
            # Find best match among all locations
            best_score = 0.0
            
            for location in locations:
                city, country, region = get_location_details(location)
                
                # Calculate score for this location
                if city == main_city and main_city:
                    best_score = max(best_score, 1.0)
                    break  # If we find an exact city match, no need to check other locations
                elif country == main_country and main_country:
                    best_score = max(best_score, params.get("country_penalty", 0.7))
                elif region == main_region and main_region:
                    best_score = max(best_score, params.get("region_penalty", 0.5))
            
            # Ensure minimum score
            return max(best_score, params.get("base_score", 0.5))

        location_scores = features.apply(calculate_location_score, axis=1)
        scores *= location_scores
        return scores

    def _apply_interests_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """
        Apply interests matching rule using aggregated interests data from multiple sources
        
        Args:
            features: DataFrame with user features
            params: Parameters for the rule
            
        Returns:
            Array of scores for each user
        """
        scores = np.ones(len(features))
        
        # Check if we have the aggregated interests field available
        if "aggregated_interests" in features.columns:
            # Use the pre-calculated interest_match_score if available
            if "interest_match_score" in features.columns:
                interest_scores = features["interest_match_score"].values
            else:
                # Get main user's interests
                main_interests = features["aggregated_interests"].iloc[0] if len(features) > 0 else []
                
                if not main_interests:
                    return scores
                
                # Calculate interest match scores using the aggregated interests
                def calculate_interest_match(row):
                    if not main_interests:
                        return 0
                    
                    interests = row.get("aggregated_interests", [])
                    if not interests:
                        return 0
                    
                    # Calculate Jaccard similarity (intersection / union)
                    overlap = set(interests) & set(main_interests)
                    total = set(interests) | set(main_interests)
                    return len(overlap) / len(total) if total else 0
                
                interest_scores = features.apply(calculate_interest_match, axis=1).values
            
            # Apply scores with base score
            base_score = params.get("base_score", 0.5)
            scores = base_score + (1 - base_score) * interest_scores
        
        # If aggregated interests not available, fall back to the original interests
        else:
            main_interests = features["main_interests"].iloc[0] if len(features) > 0 else []
            
            if not main_interests:
                return scores
                
            def calculate_overlap(row):
                if not main_interests:
                    return 0
                    
                interests = row.get("interests", [])
                if not interests:
                    return 0
                    
                # Handle interests as list of strings or list of Interest objects
                if isinstance(interests, list) and interests and not isinstance(interests[0], str):
                    # For DTOInterestRead objects
                    interests = [interest.label for interest in interests if hasattr(interest, "label")]
                    
                overlap = set(interests) & set(main_interests)
                return len(overlap) / max(len(main_interests), len(interests)) if interests else 0
    
            interest_scores = features.apply(calculate_overlap, axis=1)
            base_score = params.get("base_score", 0.5)
            scores = base_score + (1 - base_score) * interest_scores
        
        return scores

    def _apply_expertise_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Enhanced expertise matching using multiple sources"""
        scores = np.ones(len(features))
        main_expertise = features["main_expertise_area"].iloc[0]

        if not main_expertise:
            return scores

        def calculate_expertise_score(row):
            score = 0.0
            
            # Get expertise from different sources
            expertise_area = row.get("expertise_area", [])
            
            # Handle expertise_area as list of strings or list of ExpertiseArea objects
            if isinstance(expertise_area, list) and expertise_area and not isinstance(expertise_area[0], str):
                expertise_area = [exp.value if hasattr(exp, 'value') else exp for exp in expertise_area]
            
            if expertise_area:
                expertise_matches = set(expertise_area) & set(main_expertise)

                # Calculate weighted match using config weights
                for match in expertise_matches:
                    if match in self.config.TECHNICAL_AREAS:
                        score += self.config.TECHNICAL_WEIGHT
                    else:
                        score += self.config.NON_TECHNICAL_WEIGHT

                score = min(score, self.config.MAX_SCORE)

            return max(score, params.get("base_score", self.config.BASE_SCORE))

        expertise_scores = features.apply(calculate_expertise_score, axis=1)
        scores *= expertise_scores
        return scores

    def _apply_grade_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Enhanced grade matching rule"""
        scores = np.ones(len(features))
        main_grade = features["main_grade"].iloc[0]

        if not main_grade:
            return scores

        # Grade matching weights based on seniority levels
        grade_weights = {
            EGrade.junior.value: {EGrade.junior.value: 1.0, EGrade.middle.value: 0.7, EGrade.senior.value: 0.6},
            EGrade.middle.value: {
                EGrade.middle.value: 1.0,
                EGrade.senior.value: 0.8,
                EGrade.junior.value: 0.6,
            },
            EGrade.senior.value: {EGrade.senior.value: 1.0, EGrade.middle.value: 0.7, EGrade.junior.value: 0.5},
        }

        def get_grade_score(grade_value):
            if not grade_value:
                return params.get("base_score", self.config.BASE_SCORE)
                
            # Handle grade as enum or string
            if hasattr(grade_value, 'value'):
                grade_value = grade_value.value
                
            normalized_grade = self._normalize_grade(grade_value, "user")
            
            # If grade is not in the mapping, use base score
            if normalized_grade not in grade_weights.get(main_grade, {}):
                return params.get("base_score", self.config.BASE_SCORE)
                
            return grade_weights[main_grade][normalized_grade]
        
        grade_scores = features["grade"].apply(get_grade_score)
        scores *= grade_scores
        return scores

    def _apply_skills_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Enhanced skills matching rule"""
        scores = np.ones(len(features))
        main_skills = features["main_skills"].iloc[0] if "main_skills" in features.columns else []

        if not main_skills:
            return scores

        def calculate_skill_score(row):
            # Get skills from different sources
            skills = []
            
            # Add profile skills
            if row.get("skills"):
                if isinstance(row["skills"], list):
                    skills.extend(
                        skill.label if hasattr(skill, "label") else str(skill)
                        for skill in row["skills"]
                    )
                else:
                    skills.append(str(row["skills"]))
                    
            # Add LinkedIn skills
            if row.get("linkedin_profile") and row["linkedin_profile"].get("skills"):
                skills.extend(str(skill).lower() for skill in row["linkedin_profile"]["skills"])
                
            # If no skills found, return base score
            if not skills:
                return params.get("base_score", self.config.BASE_SCORE)
                
            # Calculate skill match ratio
            skill_matches = set(skills) & set(main_skills)
            match_ratio = len(skill_matches) / len(main_skills) if main_skills else 0
            
            # Get skill score from config based on match ratio
            score = self.config.get_skill_score(match_ratio)
                
            # Apply skill weight from params
            skill_weight = params.get("weight", 0.7)
            skill_base_score = params.get("base_score", self.config.BASE_SCORE)
            
            # Calculate final score
            final_score = skill_base_score + (1.0 - skill_base_score) * (score * skill_weight)
            
            return max(final_score, self.config.MIN_SCORE)

        skill_scores = features.apply(calculate_skill_score, axis=1)
        scores *= skill_scores
        return scores

    def _apply_professional_background_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Enhanced professional background matching using LinkedIn data"""
        scores = np.ones(len(features))  # Initialize scores

        # Get weights from params with defaults
        employment_weight = params.get("employment_weight", 0.8)
        position_weight = params.get("position_weight", 0.7)
        industry_weight = params.get("industry_weight", 0.6)

        # Initialize component scores with base values
        employment_scores = np.full(len(features), self.config.BASE_SCORE)  # Use config base score
        position_scores = np.full(len(features), 0.4)  # Base score
        industry_scores = np.full(len(features), 0.4)  # Base score

        # Track if we have any data for each candidate
        has_any_data = np.zeros(len(features), dtype=bool)

        # Check employment status from LinkedIn profile
        if "linkedin_profile" in features.columns:
            def check_employment(profile):
                if profile is None:
                    return 0.3  # No data
                has_any_data[features.index] = True
                return 1.0 if profile.get("work_experience") else self.config.BASE_SCORE

            employment_scores = features["linkedin_profile"].apply(check_employment)

        # Position matching using LinkedIn work experience
        if "linkedin_profile" in features.columns:
            def position_similarity(profile):
                if profile is None:
                    return 0.3  # No data
                has_any_data[features.index] = True

                if not profile.get("work_experience"):
                    return 0.4  # Has profile but no experience

                current_position = ""
                if profile["work_experience"] and len(profile["work_experience"]) > 0:
                    if isinstance(profile["work_experience"][0], dict):
                        current_position = profile["work_experience"][0].get("title", "").lower()
                    else:
                        # Assume it's a model object with attributes
                        current_position = getattr(profile["work_experience"][0], "title", "").lower()
                        
                if not current_position:
                    return 0.4

                # Direct match with main grade
                if "main_grade" in features.columns:
                    main_grade = features["main_grade"].iloc[0]
                    if main_grade == EGrade.senior.value and any(
                        level in current_position for level in ["senior", "lead", "head", "principal"]
                    ):
                        return 1.0
                    if main_grade == EGrade.middle.value and "middle" in current_position:
                        return 1.0
                    if main_grade == EGrade.junior.value and "junior" in current_position:
                        return 1.0

                # Level-based scoring
                if any(level in current_position for level in ["senior", "lead", "head", "principal"]):
                    return 0.95
                if any(level in current_position for level in ["middle", "staff"]):
                    return 0.8
                if "junior" in current_position:
                    return 0.6

                # Domain match only
                if any(domain in current_position for domain in ["developer", "engineer", "architect", "manager"]):
                    return 0.7

                return 0.4

            position_scores = features["linkedin_profile"].apply(position_similarity)

        # Industry matching
        if "industry" in features.columns and "main_industry" in features.columns:
            def calculate_industry_match(row):
                if not row.get("industry") or not row.get("main_industry"):
                    return 0.3  # No data
                has_any_data[features.index] = True

                # Handle industry as list of strings or list of Industry objects
                user_industries = row["industry"]
                if isinstance(user_industries, list) and user_industries and hasattr(user_industries[0], 'label'):
                    user_industries = [ind.label for ind in user_industries if ind.label]
                    
                main_industries = row["main_industry"]
                if isinstance(main_industries, list) and main_industries and hasattr(main_industries[0], 'label'):
                    main_industries = [ind.label for ind in main_industries if ind.label]

                overlap = set(user_industries) & set(main_industries)
                match_ratio = len(overlap) / len(set(main_industries)) if main_industries else 0
                return 0.4 + (0.6 * match_ratio)  # Scale between 0.4 and 1.0

            industry_scores = features.apply(calculate_industry_match, axis=1)

        # Calculate weighted average
        weighted_sum = (
            employment_weight * employment_scores
            + position_weight * position_scores
            + industry_weight * industry_scores
        )
        total_weight = employment_weight + position_weight + industry_weight
        final_scores = weighted_sum / total_weight

        # Scale scores differently based on data availability
        final_scores = np.where(
            has_any_data,
            0.4 + (0.6 * final_scores),  # Scale poor matches to 0.4-1.0
            0.2 + (0.2 * final_scores),  # Scale no data to 0.2-0.4
        )

        # Ensure scores are between 0 and 1
        final_scores = np.clip(final_scores, 0.0, 1.0)

        self.logger.debug(
            "Professional background scores - Employment: %s, Position: %s, Industry: %s, Has data: %s, Final: %s",
            employment_scores,
            position_scores,
            industry_scores,
            has_any_data,
            final_scores,
        )

        return final_scores

    def _apply_language_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Enhanced language matching rule"""
        scores = np.ones(len(features))
        main_languages = features["main_languages"].iloc[0]

        if not main_languages:
            return scores

        def calculate_language_score(row):
            score = 0.0
            
            # Get languages from different sources
            languages = row.get("languages", [])
            linkedin_languages = row.get("linkedin_languages", [])
            
            # Combine all languages
            all_languages = set(languages + linkedin_languages)
            
            if not all_languages:
                return self.config.MIN_SCORE

            # Calculate language matches using config weights
            language_matches = set(all_languages) & set(main_languages)
            
            if language_matches:
                # Check for country-specific language matches
                for lang in language_matches:
                    found_country_match = False
                    for country_langs in self.config.language.COUNTRY_LANGUAGES.values():
                        if lang.lower() in [l.lower() for l in country_langs]:
                            score = max(score, self.config.language.WEIGHTS["country_specific"])
                            found_country_match = True
                            break
                    
                    if not found_country_match:
                        score = max(score, self.config.language.WEIGHTS["standard"])

            return max(score, self.config.MIN_SCORE)

        language_scores = features.apply(calculate_language_score, axis=1)
        scores *= language_scores
        return scores

    def _calculate_network_quality(self, profile: dict) -> float:
        """Calculate network quality score from LinkedIn profile"""
        if not profile:
            return 0.4  # Base score for having no profile

        score = self.config.BASE_SCORE  # Base score from config for having a profile

        # Consider follower count (max 0.2)
        followers = profile.get("follower_count", 0) or 0
        follower_score = min(0.2, followers / 5000)  # Cap at 0.2 for 5000+ followers
        score += follower_score

        # Consider profile completeness (max 0.3)
        completeness_score = 0.0
        if profile.get("summary"):
            completeness_score += 0.1
        if profile.get("skills"):
            completeness_score += 0.1
        if profile.get("work_experience"):
            completeness_score += 0.1
        score += completeness_score

        # Consider work experience quality (max 0.2)
        if profile.get("work_experience"):
            experience = profile["work_experience"]
            # Check if it's a list of dicts or objects with title attribute
            job_titles = []
            for job in experience:
                if isinstance(job, dict):
                    job_title = job.get("title", "")
                else:
                    # Assume it's a model object with attributes
                    job_title = getattr(job, "title", "")
                job_titles.append(job_title.lower() if isinstance(job_title, str) else "")
                
            if any(title.startswith(("senior", "lead", "head")) for title in job_titles if title):
                score += 0.2
            elif len(experience) > 2:  # Multiple experiences
                score += 0.1

        return min(score, self.config.MAX_SCORE)  # Cap at MAX_SCORE

    def _apply_intent_specific_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Apply intent-specific matching rules"""
        scores = np.ones(len(features))

        if "main_intent" not in features.columns:
            return scores

        intent_type = features["main_intent"].iloc[0]
        content = features["main_content"].iloc[0] if "main_content" in features.columns else {}

        # Add network quality consideration for all intents
        if "linkedin_profile" in features.columns:
            network_scores = features["linkedin_profile"].apply(self._calculate_network_quality)
            self.logger.debug("Network quality scores: %s", network_scores)
            
            # Apply network quality scores with higher minimum threshold
            scores *= np.maximum(network_scores, 0.4)

        # Mock Interview specific matching
        if intent_type == EFormIntentType.mock_interview.value:
            interview_type = content.get("interview_type", [])
            languages = content.get("language", {}).get("langs", []) if content.get("language") else []
            required_grade = content.get("required_grade", [])

            self.logger.debug(
                "Mock interview requirements - types: %s, languages: %s, grades: %s",
                interview_type,
                languages,
                required_grade,
            )

            def calculate_mock_interview_score(row):
                score = 0.0
                score_breakdown = []

                # Grade matching (max 0.4)
                grade_score = 0.0
                if row.get("grade"):
                    user_grade = row["grade"]
                    if hasattr(user_grade, 'value'):
                        user_grade = user_grade.value
                        
                    if user_grade in required_grade:
                        grade_score = 0.4
                    elif user_grade in [
                        EFormMentoringGrade.senior.value,
                        EFormMentoringGrade.lead.value,
                        EFormMentoringGrade.head.value,
                    ]:
                        grade_score = 0.35
                    elif user_grade == EFormMentoringGrade.middle.value:
                        grade_score = 0.3
                score += grade_score
                score_breakdown.append(f"Grade: {grade_score}")

                # Language matching (max 0.4) - Increased from 0.3
                lang_score = 0.0
                if row.get("linkedin_profile") and row["linkedin_profile"].get("languages"):
                    profile_languages = set(lang.lower() for lang in row["linkedin_profile"].get("languages", []))
                    required_langs = set()
                    for lang in languages:
                        if lang != EFormMockInterviewLanguages.custom.value:
                            try:
                                required_langs.add(EFormMockInterviewLanguages[lang].value.lower())
                            except (KeyError, AttributeError):
                                # Handle the case where the language is already a value
                                required_langs.add(lang.lower())
                    
                    if required_langs:
                        match_ratio = len(profile_languages & required_langs) / len(required_langs)
                        lang_score = 0.4 * match_ratio  # Increased weight
                score += lang_score
                score_breakdown.append(f"Language: {lang_score}")

                # Expertise matching (max 0.4) - Increased from 0.3
                exp_score = 0.0
                if row.get("expertise_area") and interview_type:
                    expertise_areas = row["expertise_area"]
                    # Convert expertise areas to strings if they're objects
                    if expertise_areas and not isinstance(expertise_areas[0], str):
                        expertise_areas = [area.value if hasattr(area, 'value') else str(area) for area in expertise_areas]
                    
                    # Convert interview types to values if needed
                    interview_type_values = []
                    for itype in interview_type:
                        if hasattr(itype, 'value'):
                            interview_type_values.append(itype.value)
                        else:
                            try:
                                interview_type_values.append(EFormMockInterviewType[itype].value)
                            except (KeyError, AttributeError):
                                interview_type_values.append(itype)
                    
                    expertise_match = set(expertise_areas) & set(interview_type_values)
                    if expertise_match:
                        exp_score = 0.4  # Increased base score
                        if (EFormMockInterviewType.technical.value in expertise_match and 
                            row.get("grade") in [
                                EFormMentoringGrade.senior.value,
                                EFormMentoringGrade.lead.value,
                        ]):
                            exp_score += 0.1
                score += exp_score
                score_breakdown.append(f"Expertise: {exp_score}")

                # Senior experience bonus (max 0.2)
                senior_score = 0.0
                if row.get("linkedin_profile") and row["linkedin_profile"].get("work_experience"):
                    experience = row["linkedin_profile"]["work_experience"]
                    # Check if experience is a list of dicts or objects with title attribute
                    is_senior = False
                    for job in experience:
                        job_title = ""
                        if isinstance(job, dict):
                            job_title = job.get("title", "")
                        else:
                            # Assume it's a model object with attributes
                            job_title = getattr(job, "title", "")
                        
                        if job_title and isinstance(job_title, str) and job_title.lower().startswith(("senior", "lead", "head")):
                            is_senior = True
                            break
                            
                    if is_senior:
                        senior_score = 0.2
                score += senior_score
                score_breakdown.append(f"Senior bonus: {senior_score}")

                # Base score to ensure minimum matching
                final_score = max(0.3, score)

                self.logger.debug(
                    "Score breakdown for row %s: %s | Final: %s",
                    features.index[features.apply(lambda x: x.equals(row), axis=1)][0],
                    " | ".join(score_breakdown),
                    final_score,
                )

                return final_score

            mock_scores = features.apply(calculate_mock_interview_score, axis=1)
            scores *= mock_scores

            self.logger.debug("Final mock interview scores: %s", mock_scores)

        # Extract meeting format based on intent type
        meeting_format = None
        if isinstance(content, dict):
            if intent_type == EFormIntentType.connects.value:
                # For connects form, meeting format is in social_circle_expansion or professional_networking
                if "social_circle_expansion" in content:
                    social_expansion = content["social_circle_expansion"]
                    meeting_format = social_expansion.get("meeting_formats", [None])[0]

                    # Initialize base score for social expansion
                    social_scores = np.ones(len(features)) * 0.5  # Start with 0.5 base score
                    score_components = []

                    # Consider topics for better matching
                    topics = social_expansion.get("topics", [])
                    if topics:
                        # Match topics against both expertise_area and interests
                        def calculate_topic_score(row):
                            expertise_match = 0
                            interest_match = 0
                            
                            # Check expertise areas
                            if row.get("expertise_area"):
                                expertise_area = row["expertise_area"]
                                # Convert expertise areas to strings if they're objects
                                if expertise_area and not isinstance(expertise_area[0], str):
                                    expertise_area = [area.value if hasattr(area, 'value') else str(area) 
                                                    for area in expertise_area]
                                
                                expertise_match = len(set(expertise_area or []) & set(topics)) / len(topics) if topics else 0
                            
                            # Check interests
                            if row.get("interests"):
                                interests = row["interests"]
                                # Convert interests to strings if they're objects
                                if interests and not isinstance(interests[0], str):
                                    interests = [interest.label if hasattr(interest, 'label') else str(interest) 
                                                for interest in interests]
                                
                                interest_match = len(set(interests or []) & set(topics)) / len(topics) if topics else 0
                            
                            # Return the better of the two matches
                            return max(expertise_match, interest_match)
                        
                        topic_scores = features.apply(calculate_topic_score, axis=1)
                        topic_contribution = 0.3 * topic_scores
                        social_scores += topic_contribution
                        score_components.append(("Topics", topic_contribution))

                    # Handle custom topics if present
                    custom_topic_value = next((t for t in topics if t.endswith("custom")), None)
                    if custom_topic_value:
                        custom_topics = social_expansion.get("custom_topics", [])
                        if custom_topics:
                            # Match custom topics against expertise and interests
                            def calculate_custom_topic_score(row):
                                expertise_match = 0
                                interest_match = 0
                                
                                # Check expertise areas
                                if row.get("expertise_area"):
                                    expertise_area = row["expertise_area"]
                                    # Convert expertise areas to strings if they're objects
                                    if expertise_area and not isinstance(expertise_area[0], str):
                                        expertise_area = [area.value if hasattr(area, 'value') else str(area) 
                                                        for area in expertise_area]
                                    
                                    expertise_match = len(set(expertise_area or []) & set(custom_topics)) / len(custom_topics) if custom_topics else 0
                                
                                # Check interests
                                if row.get("interests"):
                                    interests = row["interests"]
                                    # Convert interests to strings if they're objects
                                    if interests and not isinstance(interests[0], str):
                                        interests = [interest.label if hasattr(interest, 'label') else str(interest) 
                                                    for interest in interests]
                                    
                                    interest_match = len(set(interests or []) & set(custom_topics)) / len(custom_topics) if custom_topics else 0
                                
                                # Return the better of the two matches
                                return max(expertise_match, interest_match)
                                
                            custom_scores = features.apply(calculate_custom_topic_score, axis=1)
                            custom_contribution = 0.2 * custom_scores
                            social_scores += custom_contribution
                            score_components.append(("Custom Topics", custom_contribution))

                    # Consider location for offline meetings
                    if meeting_format == EFormConnectsMeetingFormat.offline.value:
                        location_scores = self._apply_location_rule(
                            features, {"city_penalty": 0.3, "country_penalty": 0.1}
                        )
                        location_contribution = 0.2 * location_scores
                        social_scores += location_contribution
                        score_components.append(("Location", location_contribution))

                    # Consider network quality
                    if "linkedin_profile" in features.columns:
                        network_scores = features["linkedin_profile"].apply(
                            lambda p: 0.2 if p and p.get("work_experience") and p.get("skills") else 0.1
                        )
                        social_scores += network_scores
                        score_components.append(("Network", network_scores))

                    # Log score components
                    for component_name, component_scores in score_components:
                        self.logger.debug("Social expansion %s scores: %s", component_name, component_scores)

                    # Ensure minimum score of 0.3 and maximum of 1.0
                    social_scores = np.clip(social_scores, 0.3, 1.0)

                    self.logger.debug("Final social expansion scores: %s", social_scores)

                    # Apply social expansion scores
                    scores *= social_scores

                elif "professional_networking" in content:
                    prof_networking = content["professional_networking"]
                    topics = prof_networking.get("topics", [])

                    # Initialize base score
                    base_scores = np.ones(len(features)) * 0.6

                    # Topic matching with hybrid approach
                    if topics:
                        def calculate_professional_topic_score(row):
                            if not row.get("expertise_area"):
                                return 0.0

                            # Get expertise areas as strings
                            expertise_area = row["expertise_area"]
                            if expertise_area and not isinstance(expertise_area[0], str):
                                expertise_area = [area.value if hasattr(area, 'value') else str(area) 
                                                for area in expertise_area]

                            # Validate topics are from the enum or convert to enum values
                            valid_topics = []
                            for topic in topics:
                                if hasattr(topic, 'value'):
                                    valid_topics.append(topic.value)
                                else:
                                    try:
                                        # Try to convert string to enum value
                                        valid_topics.append(EFormProfessionalNetworkingTopic[topic].value)
                                    except (KeyError, AttributeError):
                                        # If it's already a value
                                        if topic in [e.value for e in EFormProfessionalNetworkingTopic]:
                                            valid_topics.append(topic)
                            
                            if not valid_topics:
                                return 0.0
                                
                            topic_matches = set(expertise_area) & set(valid_topics)
                            if not topic_matches:
                                return 0.0
                                
                            # Calculate base score from matches
                            score = 0.0
                            total_weight = 0.0
                            
                            # Apply topic-specific scoring
                            for topic in topic_matches:
                                if topic in self.professional_topic_rules:
                                    rules = self.professional_topic_rules[topic]
                                    topic_score = 0.6  # Base score for match
                                    
                                    # Grade-based bonuses
                                    if row.get("grade"):
                                        user_grade = row["grade"]
                                        if hasattr(user_grade, 'value'):
                                            user_grade = user_grade.value
                                            
                                        if user_grade in [
                                            EFormMentoringGrade.senior.value,
                                            EFormMentoringGrade.lead.value,
                                            EFormMentoringGrade.head.value
                                        ]:
                                            topic_score += rules['senior_bonus']
                                        elif user_grade == EFormMentoringGrade.middle.value:
                                            topic_score += rules['middle_bonus']
                                    
                                    # Skill-specific bonuses
                                    if row.get("specialisation") or row.get("specialisations"):
                                        specialisations = row.get("specialisation") or row.get("specialisations") or []
                                        # Convert specialisations to strings if they're objects
                                        if specialisations and hasattr(specialisations[0], 'label'):
                                            specialisations = [spec.label if spec.label else "" for spec in specialisations]
                                            
                                        if any(skill in spec.lower() for spec in specialisations for skill in rules['required_skills']):
                                            topic_score = min(1.0, topic_score + 0.2)
                                            
                                    # Add weighted topic score
                                    score += topic_score * rules.get('weight', 1.0)
                                    total_weight += rules.get('weight', 1.0)
                            
                            return score / total_weight if total_weight > 0 else 0.0

                        topic_scores = features.apply(calculate_professional_topic_score, axis=1)
                        scores *= np.maximum(topic_scores, 0.5)
                        self.logger.debug("Professional networking topic scores: %s", topic_scores)

                    # Consider user query with enhanced position matching
                    if prof_networking.get("user_query"):
                        query = prof_networking["user_query"].lower()

                        def calculate_expertise_score(row):
                            score = 0.0

                            # Grade-based scoring
                            if row.get("grade"):
                                user_grade = row["grade"]
                                if hasattr(user_grade, 'value'):
                                    user_grade = user_grade.value
                                    
                                if user_grade == EFormMentoringGrade.lead.value:
                                    score = 1.0
                                elif user_grade == EFormMentoringGrade.senior.value:
                                    score = 0.9
                                elif user_grade == EFormMentoringGrade.middle.value:
                                    score = 0.7

                            # Position title matching from LinkedIn profile
                            if row.get("linkedin_profile") and row["linkedin_profile"].get("current_position_title"):
                                title = row["linkedin_profile"]["current_position_title"].lower()
                                if any(role in title for role in ["lead", "head", "principal", "architect"]):
                                    score = max(score, 1.0)
                                elif "senior" in title:
                                    score = max(score, 0.9)

                            # Specialization matching
                            specialisations = row.get("specialisation") or row.get("specialisations") or []
                            if specialisations:
                                # Convert specialisations to strings if they're objects
                                if hasattr(specialisations[0], 'label'):
                                    specialisations = [spec.label if spec.label else "" for spec in specialisations]
                                    
                                spec_matches = [
                                    spec
                                    for spec in specialisations
                                    if any(term in spec.lower() for term in query.split())
                                ]
                                if spec_matches:
                                    score = max(score, 0.8)

                            return score

                        expertise_scores = features.apply(calculate_expertise_score, axis=1)
                        scores *= np.maximum(expertise_scores, 0.7)  # Higher minimum for expertise

                        self.logger.debug("Professional networking expertise scores: %s", expertise_scores)

                    # Apply base scores
                    scores *= base_scores

            elif intent_type == EFormIntentType.mentoring_mentor.value:
                # Extract all relevant fields from form content
                required_grade = content.get("required_grade", [])
                specialization = content.get("specialization", [])
                help_request = content.get("help_request", {})
                is_local_community = content.get("is_local_community", False)

                # Initialize base scores
                mentor_scores = np.ones(len(features)) * 0.5
                score_components = []

                # Grade matching with proper enum handling
                if required_grade:

                    def calculate_grade_score(row):
                        if not row.get("grade"):
                            return 0.3

                        grade = row["grade"]
                        if grade in required_grade:
                            return 1.0

                        # Map grades to numeric values for comparison
                        grade_values = {
                            EFormMentoringGrade.junior.value: 1,
                            EFormMentoringGrade.middle.value: 2,
                            EFormMentoringGrade.senior.value: 3,
                            EFormMentoringGrade.lead.value: 4,
                            EFormMentoringGrade.head.value: 5,
                            EFormMentoringGrade.executive.value: 6,
                        }

                        required_levels = [grade_values.get(g, 0) for g in required_grade]
                        current_level = grade_values.get(grade, 0)

                        # Higher grade than required is better than lower
                        if current_level > max(required_levels):
                            return 0.9
                        if current_level < min(required_levels):
                            return 0.5
                        return 0.7

                    grade_scores = features.apply(calculate_grade_score, axis=1)
                    mentor_scores *= grade_scores
                    score_components.append(("Grade", grade_scores))

                # Specialization matching using EFormSpecialization
                if specialization:

                    def calculate_spec_score(row):
                        if not row.get("specialization"):
                            return 0.3

                        # REFACTORED: Remove dependency on string format with underscores
                        # Instead, use direct matching and a category-based approach
                        
                        # Direct matches get highest score
                        direct_matches = set(row["specialization"]) & set(specialization)
                        if direct_matches:
                            return 1.0
                            
                        # For partial matches, we'll use a category-based approach
                        # Extract main categories from specializations
                        req_categories = set()
                        for spec in specialization:
                            parts = spec.split("__") if "__" in spec else [spec]
                            req_categories.add(parts[0])
                            
                        user_categories = set()
                        for spec in row["specialization"]:
                            parts = spec.split("__") if "__" in spec else [spec]
                            user_categories.add(parts[0])
                            
                        # Category matches get a good score
                        category_matches = req_categories & user_categories
                        if category_matches:
                            return 0.8
                            
                        return 0.3

                    spec_scores = features.apply(calculate_spec_score, axis=1)
                    mentor_scores *= np.maximum(spec_scores, 0.4)
                    score_components.append(("Specialization", spec_scores))

                # Handle help request types with proper enum usage
                if help_request:
                    request_types = help_request.get("request", [])

                    if EFormMentoringHelpRequest.adaptation_after_relocate.value in request_types:
                        target_country = help_request.get("country")
                        if target_country:
                            # ENHANCED: More comprehensive location matching for relocation
                            def calculate_relocation_score(row):
                                score = 0.3  # Base score
                                
                                # Check main location
                                if row.get("location") and target_country in row["location"]:
                                    score = max(score, 1.0)
                                    
                                # Check LinkedIn location
                                if row.get("linkedin_profile") and row["linkedin_profile"].get("location"):
                                    if target_country in row["linkedin_profile"]["location"]:
                                        score = max(score, 0.9)
                                
                                # Check work experience in target country
                                if row.get("linkedin_profile") and row["linkedin_profile"].get("work_experience"):
                                    for exp in row["linkedin_profile"]["work_experience"]:
                                        if exp.get("location") and target_country in exp["location"]:
                                            score = max(score, 0.8)
                                                
                                # Check language match for the country
                                if row.get("linkedin_profile") and row["linkedin_profile"].get("languages"):
                                    # Simple mapping of countries to languages
                                    country_languages = {
                                        "usa": ["english"],
                                        "uk": ["english"],
                                        "germany": ["german"],
                                        "france": ["french"],
                                        "spain": ["spanish"],
                                        # Add more as needed
                                    }
                                    
                                    target_languages = country_languages.get(target_country.lower(), [])
                                    if target_languages:
                                        user_languages = [lang.lower() for lang in row["linkedin_profile"]["languages"]]
                                        if any(lang in user_languages for lang in target_languages):
                                            score = max(score, 0.7)
                                
                                return score
                                
                            relocation_scores = features.apply(calculate_relocation_score, axis=1)
                            mentor_scores *= np.maximum(relocation_scores, 0.4)
                            score_components.append(("Relocation", relocation_scores))

                    if EFormMentoringHelpRequest.process_and_teams_management.value in request_types:

                        def calculate_management_score(row):
                            score = 0.3  # Base score

                            # Grade-based scoring
                            if row.get("grade"):
                                if row["grade"] in [
                                    EFormMentoringGrade.lead.value,
                                    EFormMentoringGrade.head.value,
                                    EFormMentoringGrade.executive.value,
                                ]:
                                    score = 1.0
                                elif row["grade"] == EFormMentoringGrade.senior.value:
                                    score = 0.8

                            # Position-based bonus
                            if row.get("current_position_title"):
                                title = row["current_position_title"].lower()
                                if any(role in title for role in ["lead", "head", "cto", "vp"]):
                                    score = max(score, 1.0)
                                elif "manager" in title or "team lead" in title:
                                    score = max(score, 0.9)

                            return score

                        management_scores = features.apply(calculate_management_score, axis=1)
                        mentor_scores *= np.maximum(management_scores, 0.5)
                        score_components.append(("Management", management_scores))

                    if EFormMentoringHelpRequest.custom.value in request_types:
                        custom_request = help_request.get("custom_request", "").lower()

                        # Add specialized scoring for common custom request patterns
                        def calculate_custom_score(row):
                            score = 0.4  # Base score

                            # Match expertise areas against custom request
                            if row.get("expertise_area"):
                                if any(area.lower() in custom_request for area in row["expertise_area"]):
                                    score = max(score, 0.8)

                            # Match specializations
                            if row.get("specialization"):
                                if any(spec.lower() in custom_request for spec in row["specialization"]):
                                    score = max(score, 0.9)

                            return score

                        custom_scores = features.apply(calculate_custom_score, axis=1)
                        mentor_scores *= np.maximum(custom_scores, 0.4)
                        score_components.append(("Custom", custom_scores))

                # Log score components
                for component_name, component_scores in score_components:
                    self.logger.debug("Mentoring %s scores: %s", component_name, component_scores)

                # Apply final mentor scores
                scores *= np.clip(mentor_scores, 0.3, 1.0)

            elif intent_type == EFormIntentType.mentoring_mentee.value:
                mentor_specialization = content.get("mentor_specialization", [])
                mentee_grade = content.get("grade", [])
                help_request = content.get("help_request", {})

                # Initialize mentee scores
                mentee_scores = np.ones(len(features)) * 0.5
                score_components = []

                # Specialization matching with hierarchical consideration
                if mentor_specialization:

                    def calculate_mentor_spec_score(row):
                        if not row.get("specialization"):
                            return 0.3

                        # REFACTORED: Use the same approach as mentor specialization matching
                        # Direct matches get highest score
                        direct_matches = set(row["specialization"]) & set(mentor_specialization)
                        if direct_matches:
                            return 1.0
                            
                        # For partial matches, use a category-based approach
                        # Extract main categories from specializations
                        req_categories = set()
                        for spec in mentor_specialization:
                            parts = spec.split("__") if "__" in spec else [spec]
                            req_categories.add(parts[0])
                            
                        user_categories = set()
                        for spec in row["specialization"]:
                            parts = spec.split("__") if "__" in spec else [spec]
                            user_categories.add(parts[0])
                            
                        # Category matches get a good score
                        category_matches = req_categories & user_categories
                        if category_matches:
                            return 0.8
                            
                        return 0.3

                    spec_scores = features.apply(calculate_mentor_spec_score, axis=1)
                    mentee_scores *= np.maximum(spec_scores, 0.4)
                    score_components.append(("Specialization", spec_scores))

                # Grade matching with proper enum handling
                if mentee_grade:

                    def calculate_mentee_grade_score(row):
                        if not row.get("grade"):
                            return 0.3

                        grade_values = {
                            EFormMentoringGrade.junior.value: 1,
                            EFormMentoringGrade.middle.value: 2,
                            EFormMentoringGrade.senior.value: 3,
                            EFormMentoringGrade.lead.value: 4,
                            EFormMentoringGrade.head.value: 5,
                            EFormMentoringGrade.executive.value: 6,
                        }

                        mentee_level = grade_values.get(mentee_grade[0], 0)
                        mentor_level = grade_values.get(row["grade"], 0)

                        if mentor_level > mentee_level + 1:
                            return 1.0  # Significantly more experienced
                        if mentor_level > mentee_level:
                            return 0.9  # More experienced
                        if mentor_level == mentee_level:
                            return 0.6  # Same level
                        return 0.3  # Less experienced

                    grade_scores = features.apply(calculate_mentee_grade_score, axis=1)
                    mentee_scores *= grade_scores
                    score_components.append(("Grade", grade_scores))

                # Handle help request types
                if help_request:
                    request_types = help_request.get("request", [])

                    if EFormMentoringHelpRequest.adaptation_after_relocate.value in request_types:
                        target_country = help_request.get("country")
                        if target_country:

                            def calculate_relocation_score(row):
                                score = 0.3  # Base score

                                # Location matching
                                if row.get("location") and target_country in row["location"]:
                                    score = max(score, 1.0)
                                elif row.get("linkedin_profile"):
                                    if (
                                        row["linkedin_profile"].get("location")
                                        and target_country in row["linkedin_profile"]["location"]
                                    ):
                                        score = max(score, 0.9)

                                # Experience with relocation
                                if row.get("linkedin_profile") and row["linkedin_profile"].get("work_experience"):
                                    locations = set()
                                    for exp in row["linkedin_profile"]["work_experience"]:
                                        if exp.get("location"):
                                            locations.add(exp["location"])
                                    if len(locations) > 1:  # Has worked in multiple locations
                                        score = max(score, 0.8)

                                return score

                            relocation_scores = features.apply(calculate_relocation_score, axis=1)
                            mentee_scores *= np.maximum(relocation_scores, 0.4)
                            score_components.append(("Relocation", relocation_scores))

                # Log score components
                for component_name, component_scores in score_components:
                    self.logger.debug("Mentee matching %s scores: %s", component_name, component_scores)

                # Apply final mentee scores
                scores *= np.clip(mentee_scores, 0.3, 1.0)

            elif intent_type in [
                EFormIntentType.projects_find_contributor.value,
                EFormIntentType.projects_find_cofounder.value,
            ]:
                project_state = content.get("project_state")
                project_skills = content.get("skills", [])
                project_specialization = content.get("specialization", [])
                project_role = (
                    EFormProjectUserRole.cofounder
                    if intent_type == EFormIntentType.projects_find_cofounder.value
                    else EFormProjectUserRole.contributor
                )

                # Initialize project scores with higher base score
                project_scores = np.ones(len(features)) * 0.6  # Increased from 0.5
                score_components = []

                # Skills matching with proper enum handling
                if project_skills:

                    def calculate_skill_score(row):
                        if not row.get("skill_match_score"):
                            return 0.3

                        # Start with normalized skill score
                        base_score = row["skill_match_score"] / max(features["skill_match_score"])

                        # Different scoring based on role
                        if project_role == EFormProjectUserRole.cofounder:
                            # Cofounders need broader expertise
                            if row.get("grade") in [EFormMentoringGrade.senior.value, EFormMentoringGrade.lead.value]:
                                base_score = min(1.0, base_score + 0.4)  # Increased bonus
                        else:  # Contributor
                            # Contributors need specific skills
                            if project_state == EFormProjectProjectState.scaling.value:
                                if row.get("grade") in [
                                    EFormMentoringGrade.senior.value,
                                    EFormMentoringGrade.lead.value,
                                ]:
                                    base_score = min(1.0, base_score + 0.3)
                            elif project_state == EFormProjectProjectState.mvp.value:
                                if row.get("grade") == EFormMentoringGrade.senior.value:
                                    base_score = min(1.0, base_score + 0.2)

                        # Add expertise bonus
                        if row.get("expertise_area"):
                            expertise_match = any(exp in project_specialization for exp in row["expertise_area"])
                            if expertise_match:
                                base_score = min(1.0, base_score + 0.2)

                        return base_score

                    skill_scores = features.apply(calculate_skill_score, axis=1)
                    project_scores *= np.maximum(skill_scores, 0.5)  # Increased minimum from 0.4
                    score_components.append(("Skills", skill_scores))

                # Log score components
                for component_name, component_scores in score_components:
                    self.logger.debug("Project matching %s scores: %s", component_name, component_scores)

                # Apply final project scores with higher minimum
                scores *= np.clip(project_scores, 0.4, 1.0)  # Increased minimum from 0.3

            elif intent_type == EFormIntentType.referrals_recommendation.value:
                english_level = content.get("required_english_level")
                company_type = content.get("company_type")
                is_local_community = content.get("is_local_community", False)
                is_all_experts_type = content.get("is_all_experts_type", False)

                # Initialize referral scores
                referral_scores = np.ones(len(features)) * 0.5
                score_components = []

                # English level matching
                if english_level and english_level != EFormEnglishLevel.not_required.value:

                    def calculate_english_score(row):
                        if not row.get("linkedin_profile"):
                            return 0.3

                        # Map English levels to numeric values
                        level_values = {
                            EFormEnglishLevel.A1.value: 1,
                            EFormEnglishLevel.A2.value: 2,
                            EFormEnglishLevel.B1.value: 3,
                            EFormEnglishLevel.B2.value: 4,
                            EFormEnglishLevel.C1.value: 5,
                            EFormEnglishLevel.C2.value: 6,
                            EFormEnglishLevel.native.value: 7,
                        }

                        required_level = level_values.get(english_level, 0)  # pylint: disable=unused-variable

                        # Check LinkedIn languages
                        if row["linkedin_profile"].get("languages"):
                            for lang in row["linkedin_profile"]["languages"]:
                                if "english" in lang.lower():
                                    return 1.0  # Has English listed

                        # Check work experience in English-speaking countries
                        if row["linkedin_profile"].get("work_experience"):
                            english_countries = {"usa", "uk", "canada", "australia", "new zealand"}
                            if any(
                                exp.get("location", "").lower() in english_countries
                                for exp in row["linkedin_profile"]["work_experience"]
                            ):
                                return 0.9  # Work experience in English-speaking country

                        return 0.5  # Default score if no clear English indicators

                    english_scores = features.apply(calculate_english_score, axis=1)
                    referral_scores *= np.maximum(english_scores, 0.4)
                    score_components.append(("English", english_scores))

                # Company type matching
                if company_type:

                    def calculate_company_score(row):
                        score = 0.3  # Base score

                        if row.get("current_company_label"):
                            if company_type == EFormRefferalsCompanyType.dummy.value:  # Replace with actual enum values
                                # Add specific company type matching logic here
                                pass

                        # Consider company size and type from LinkedIn
                        if row.get("linkedin_profile"):
                            company = row["linkedin_profile"].get("current_company", {})
                            if company:
                                if company.get("size", 0) > 1000:
                                    score = max(score, 0.8)  # Large company experience
                                elif company.get("type") == "startup":
                                    score = max(score, 0.7)  # Startup experience

                        return score

                    company_scores = features.apply(calculate_company_score, axis=1)
                    referral_scores *= np.maximum(company_scores, 0.4)
                    score_components.append(("Company", company_scores))

                # Local community consideration
                if is_local_community:
                    location_scores = self._apply_location_rule(
                        features, {"city_penalty": 0.2, "country_penalty": 0.1, "region_penalty": 0.05}
                    )
                    referral_scores *= np.maximum(location_scores, 0.5)
                    score_components.append(("Location", location_scores))

                # Expert type consideration
                if is_all_experts_type:

                    def calculate_expert_score(row):  # pylint: disable=unused-variable
                        score = 0.3  # Base score # pylint: disable=unused-variable

                        # Grade-based scoring
                        if row.get("grade"):
                            if row["grade"] in [
                                EFormMentoringGrade.senior.value,
                                EFormMentoringGrade.lead.value,
                                EFormMentoringGrade.head.value,
                                EFormMentoringGrade.executive.value,
                            ]:
                                score = 1.0
                            elif row["grade"] == EFormMentoringGrade.middle.value:
                                score = 0.7

                        # Experience-based bonus
                        if row.get("linkedin_profile") and row["linkedin_profile"].get("work_experience"):
                            experience = row["linkedin_profile"]["work_experience"]
                            years = sum(exp.get("duration_years", 0) for exp in experience)  # pylint: disable=unused-variable

        # Handle meeting format
        if meeting_format == EFormConnectsMeetingFormat.offline.value:
            location_scores = self._apply_location_rule(features, {"city_penalty": 0.2, "country_penalty": 0.05})
            scores *= location_scores

        # Add enhanced professional background consideration for relevant intents
        if intent_type in [
            EFormIntentType.mentoring_mentor.value,
            EFormIntentType.mentoring_mentee.value,
            EFormIntentType.referrals_recommendation.value,
            EFormIntentType.projects_find_cofounder.value,
        ]:
            prof_scores = self._apply_professional_background_rule(
                features, {"employment_weight": 0.8, "position_weight": 0.7, "industry_weight": 0.6}
            )
            scores *= np.maximum(prof_scores, 0.6)

        return scores

    # ADDED: Function to aggregate user data from different sources
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
                    if hasattr(row['linkedin_profile'], 'model_dump'):
                        features_copy.at[idx, 'linkedin_profile'] = row['linkedin_profile'].model_dump()
                    elif hasattr(row['linkedin_profile'], 'dict'):
                        features_copy.at[idx, 'linkedin_profile'] = row['linkedin_profile'].dict()
                except Exception as e:
                    # Leave as is if conversion fails
                    self.logger.warning(f"Failed to convert LinkedIn profile: {e}")
                    pass
        
        return features_copy
    
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """
        Make predictions for a given set of features using heuristic rules

        Args:
            features: DataFrame with features

        Returns:
            numpy array with scores for each row in features
        """
        # First, aggregate user data to ensure consistent format
        features = self._aggregate_user_data(features)

        # Initialize scores
        scores = np.ones(len(features))
        
        # Apply rules with weighted combination
        total_weight = 0
        weighted_scores = np.zeros(len(features))
        
        for rule in self.rules:
            rule_type = rule["type"]
            rule_weight = rule["weight"]
            total_weight += rule_weight
            
            try:
                if rule_type == "location":
                    rule_scores = self._apply_location_rule(features, rule["params"])
                elif rule_type == "interests":
                    rule_scores = self._apply_interests_rule(features, rule["params"])
                elif rule_type == "expertise":
                    rule_scores = self._apply_expertise_rule(features, rule["params"])
                elif rule_type == "grade":
                    rule_scores = self._apply_grade_rule(features, rule["params"])
                elif rule_type == "skills":
                    rule_scores = self._apply_skills_rule(features, rule["params"])
                elif rule_type == "professional_background":
                    rule_scores = self._apply_professional_background_rule(features, rule["params"])
                elif rule_type == "language":
                    rule_scores = self._apply_language_rule(features, rule["params"])
                elif rule_type == "intent_specific":
                    rule_scores = self._apply_intent_specific_rule(features, rule["params"])
                else:
                    # Unknown rule type
                    self.logger.warning("Unknown rule type: %s", rule_type)
                    rule_scores = np.ones(len(features))
                    
                # Add weighted rule scores
                weighted_scores += rule_scores * rule_weight
                
            except Exception as e:
                # If rule application fails, log error and use neutral scores
                self.logger.error("Error applying rule %s: %s", rule["name"], str(e))
                traceback_str = traceback.format_exc()
                self.logger.debug("Traceback: %s", traceback_str)
                continue
        
        # Calculate final scores based on the weighted contributions
        if total_weight > 0:
            scores = weighted_scores / total_weight
        else:
            scores = np.ones(len(features))
            
        # Ensure scores are in 0-1 range
        scores = np.clip(scores, 0, 1)
        
        return scores

    def _extract_meeting_format(self, intent_type: str, content: dict) -> str | None:
        """Extract meeting format based on form type"""
        if not content:
            return None

        if intent_type == EFormIntentType.connects.value:
            if "social_circle_expansion" in content:
                meeting_formats = content["social_circle_expansion"].get("meeting_formats", [])
                if meeting_formats:
                    meeting_format = meeting_formats[0]
                    # Handle enum object or string value
                    if hasattr(meeting_format, 'value'):
                        return meeting_format.value
                    return meeting_format

        return content.get("meeting_format")

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        if not text1 or not text2:
            return 0.0
            
        # Convert to lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
