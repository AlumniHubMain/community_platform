"""Heuristic predictor"""
import pandas as pd
import numpy as np
import logging
from common_db.enums.users import (
    EGrade, EExpertiseArea,
)
from common_db.enums.forms import (
    EFormIntentType, EFormConnectsMeetingFormat, EFormMentoringGrade,
    EFormProjectUserRole, EFormMockInterviewType, EFormMentoringHelpRequest,
    EFormEnglishLevel, EFormProjectProjectState, EFormConnectsSocialExpansionTopic,
    EFormMockInterviewLangluages, EFormRefferalsCompanyType, EFormProfessionalNetworkingTopic
)

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
        self.logger = logging.getLogger(__name__)

    def _apply_location_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Enhanced location matching rule"""
        scores = np.ones(len(features))
        main_location = features['main_location'].iloc[0]
        
        if not main_location:
            # If no main location, check LinkedIn location
            if 'linkedin_location' in features.columns:
                main_location = features['linkedin_location'].iloc[0]
            if not main_location:
                return scores
            
        def get_location_details(location: str) -> tuple[str, str, str]:
            """Extract city, country and region from location"""
            parts = location.split('_')
            city = parts[0] if len(parts) > 0 else ""
            country = parts[1] if len(parts) > 1 else ""
            region = parts[2] if len(parts) > 2 else ""
            return city, country, region
        
        main_city, main_country, main_region = get_location_details(main_location)
        
        def calculate_location_score(row):
            score = 0.0
            # Check user profile location
            if row.get('location'):
                city, country, region = get_location_details(row['location'])
                if city == main_city:
                    score = max(score, 1.0)
                elif country == main_country:
                    score = max(score, params.get('country_penalty', 0.3))
                elif region == main_region:
                    score = max(score, params.get('region_penalty', 0.2))
            
            # Check LinkedIn location if available
            if row.get('linkedin_location'):
                li_city, li_country, li_region = get_location_details(row['linkedin_location'])
                if li_city == main_city:
                    score = max(score, 1.0)
                elif li_country == main_country:
                    score = max(score, params.get('country_penalty', 0.3))
                elif li_region == main_region:
                    score = max(score, params.get('region_penalty', 0.2))
            
            return max(score, 0.05)  # Minimum score
        
        location_scores = features.apply(calculate_location_score, axis=1)
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
        """Enhanced expertise matching using multiple sources"""
        scores = np.ones(len(features))
        main_expertise = features['main_expertise_area'].iloc[0]
        
        def calculate_expertise_score(row):
            score = 0.0
            if row.get('expertise_area'):
                expertise_matches = set(row['expertise_area']) & set(main_expertise)
                
                # Give higher weights to core technical areas
                tech_areas = {
                    EExpertiseArea.development.value,
                    EExpertiseArea.devops.value,
                    EExpertiseArea.data_science.value,
                    EExpertiseArea.cyber_security.value
                }
                
                # Calculate weighted match
                for match in expertise_matches:
                    if match in tech_areas:
                        score += 0.4  # Higher weight for technical matches
                    else:
                        score += 0.3  # Standard weight for other matches
                
                score = min(1.0, score)  # Cap at 1.0
            
            return max(score, params.get('base_score', 0.3))
        
        expertise_scores = features.apply(calculate_expertise_score, axis=1)
        scores *= expertise_scores
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

    def _apply_skills_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Apply skills matching rule using LinkedIn data"""
        scores = np.ones(len(features))
        
        if 'skill_match_score' not in features.columns:
            return scores
            
        # Normalize skill match score to 0-1 range
        max_skills = features['skill_match_score'].max()
        if max_skills > 0:
            skill_scores = features['skill_match_score'] / max_skills
        else:
            skill_scores = features['skill_match_score']
            
        base_score = params.get('base_score', 0.5)
        scores *= (base_score + (1 - base_score) * skill_scores)
        
        return scores

    def _apply_professional_background_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Enhanced professional background matching using LinkedIn data"""
        scores = np.ones(len(features))
        
        # Get weights from params with defaults
        employment_weight = params.get('employment_weight', 0.8)
        position_weight = params.get('position_weight', 0.7)
        industry_weight = params.get('industry_weight', 0.6)
        
        # Initialize component scores with base values
        employment_scores = np.full(len(features), 0.5)  # Base score
        position_scores = np.full(len(features), 0.4)    # Base score
        industry_scores = np.full(len(features), 0.4)    # Base score
        
        # Track if we have any data for each candidate
        has_any_data = np.zeros(len(features), dtype=bool)
        
        # Check employment status from LinkedIn profile
        if 'linkedin_profile' in features.columns:
            def check_employment(profile):
                if profile is None:
                    return 0.3  # No data
                has_any_data[features.index] = True
                return 1.0 if profile.get('work_experience') else 0.5
            
            employment_scores = features['linkedin_profile'].apply(check_employment)
        
        # Position matching using LinkedIn work experience
        if 'linkedin_profile' in features.columns:
            def position_similarity(profile):
                if profile is None:
                    return 0.3  # No data
                has_any_data[features.index] = True
                
                if not profile.get('work_experience'):
                    return 0.4  # Has profile but no experience
                
                current_position = profile['work_experience'][0]['title'].lower()
                
                # Direct match with main grade
                if 'main_grade' in features.columns:
                    main_grade = features['main_grade'].iloc[0]
                    if main_grade == EGrade.senior.value and any(level in current_position 
                        for level in ['senior', 'lead', 'head', 'principal']):
                        return 1.0
                    elif main_grade == EGrade.middle.value and 'middle' in current_position:
                        return 1.0
                    elif main_grade == EGrade.junior.value and 'junior' in current_position:
                        return 1.0
                
                # Level-based scoring
                if any(level in current_position for level in ['senior', 'lead', 'head', 'principal']):
                    return 0.95
                elif any(level in current_position for level in ['middle', 'staff']):
                    return 0.8
                elif 'junior' in current_position:
                    return 0.6
                
                # Domain match only
                if any(domain in current_position for domain in ['developer', 'engineer', 'architect', 'manager']):
                    return 0.7
                
                return 0.4
            
            position_scores = features['linkedin_profile'].apply(position_similarity)
        
        # Industry matching
        if 'industry' in features.columns and 'main_industry' in features.columns:
            def calculate_industry_match(row):
                if pd.isna(row['industry']).all() or pd.isna(row['main_industry']).all():
                    return 0.3  # No data
                has_any_data[features.index] = True
                
                if not row['industry'] or not row['main_industry']:
                    return 0.4  # Has some data but empty
                
                overlap = set(row['industry']) & set(row['main_industry'])
                match_ratio = len(overlap) / len(set(row['main_industry']))
                return 0.4 + (0.6 * match_ratio)  # Scale between 0.4 and 1.0
            
            industry_scores = features.apply(calculate_industry_match, axis=1)
        
        # Calculate weighted average
        weighted_sum = (
            employment_weight * employment_scores +
            position_weight * position_scores +
            industry_weight * industry_scores
        )
        total_weight = employment_weight + position_weight + industry_weight
        final_scores = weighted_sum / total_weight
        
        # Scale scores differently based on data availability
        final_scores = np.where(
            has_any_data,
            0.4 + (0.6 * final_scores),  # Scale poor matches to 0.4-1.0
            0.2 + (0.2 * final_scores)   # Scale no data to 0.2-0.4
        )
        
        # Ensure scores are between 0 and 1
        final_scores = np.clip(final_scores, 0.0, 1.0)
        
        self.logger.debug(f"Professional background scores - Employment: {employment_scores}, "
                         f"Position: {position_scores}, Industry: {industry_scores}, "
                         f"Has data: {has_any_data}, Final: {final_scores}")
        
        return final_scores

    def _apply_language_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Apply language matching rule using LinkedIn data"""
        scores = np.ones(len(features))
        
        if 'language_match_score' not in features.columns:
            return scores
            
        # Normalize language match score to 0-1 range
        max_languages = features['language_match_score'].max()
        if max_languages > 0:
            language_scores = features['language_match_score'] / max_languages
        else:
            language_scores = features['language_match_score']
            
        base_score = params.get('base_score', 0.6)
        scores *= (base_score + (1 - base_score) * language_scores)
        
        return scores

    def _apply_intent_specific_rule(self, features: pd.DataFrame, params: dict) -> np.ndarray:
        """Apply intent-specific matching rules"""
        scores = np.ones(len(features))
        
        if 'main_intent' not in features.columns:
            return scores
        
        intent_type = features['main_intent'].iloc[0]
        content = features['main_content'].iloc[0] if 'main_content' in features.columns else {}
        
        # Add network quality consideration for all intents
        if 'linkedin_profile' in features.columns:
            def calculate_network_score(profile):
                if not profile:
                    return 0.5
                    
                score = 0.5  # Base score for having a profile
                
                # Consider follower count (max 0.2)
                followers = profile.get('follower_count', 0) or 0
                follower_score = min(0.2, followers / 5000)  # Cap at 0.2 for 5000+ followers
                score += follower_score
                
                # Consider profile completeness (max 0.3)
                completeness_score = 0.0
                if profile.get('summary'):
                    completeness_score += 0.1
                if profile.get('skills'):
                    completeness_score += 0.1
                if profile.get('work_experience'):
                    completeness_score += 0.1
                score += completeness_score
                
                # Consider work experience quality (max 0.2)
                if profile.get('work_experience'):
                    experience = profile['work_experience']
                    if any(job.get('title', '').lower().startswith(('senior', 'lead', 'head')) 
                          for job in experience):
                        score += 0.2
                    elif len(experience) > 2:  # Multiple experiences
                        score += 0.1
                
                self.logger.debug(f"Network quality breakdown - Base: 0.5, Followers: {follower_score}, "
                                f"Completeness: {completeness_score}, Experience: {0.2 if score > 0.8 else 0.1 if score > 0.7 else 0.0}")
                
                return score

            network_scores = features['linkedin_profile'].apply(calculate_network_score)
            self.logger.debug(f"Network quality scores: {network_scores}")
            
            # Apply network quality scores with higher minimum threshold
            scores *= np.maximum(network_scores, 0.4)  # Increased minimum from 0.3 to 0.4

        # Mock Interview specific matching
        if intent_type == EFormIntentType.mock_interview.value:
            interview_type = content.get('interview_type', [])
            required_languages = content.get('languages', [])
            required_grade = content.get('required_grade', [])
            
            self.logger.debug(f"Mock interview requirements - types: {interview_type}, "
                             f"languages: {required_languages}, grades: {required_grade}")
            
            def calculate_mock_interview_score(row):
                score = 0.0
                score_breakdown = []
                
                # Grade matching (max 0.4)
                grade_score = 0.0
                if row.get('grade'):
                    if row['grade'] in required_grade:
                        grade_score = 0.4
                    elif row['grade'] in [
                        EFormMentoringGrade.senior.value,
                        EFormMentoringGrade.lead.value,
                        EFormMentoringGrade.head.value
                    ]:
                        grade_score = 0.35
                    elif row['grade'] == EFormMentoringGrade.middle.value:
                        grade_score = 0.3
                score += grade_score
                score_breakdown.append(f"Grade: {grade_score}")
                
                # Language matching (max 0.4) - Increased from 0.3
                lang_score = 0.0
                if row.get('linkedin_profile') and row['linkedin_profile'].get('languages'):
                    profile_languages = set(lang.lower() for lang in row['linkedin_profile'].get('languages', []))
                    required_langs = set(lang.value.lower() for lang in [
                        EFormMockInterviewLangluages[lang] for lang in required_languages 
                        if lang != EFormMockInterviewLangluages.custom.value
                    ])
                    if required_langs:
                        match_ratio = len(profile_languages & required_langs) / len(required_langs)
                        lang_score = 0.4 * match_ratio  # Increased weight
                score += lang_score
                score_breakdown.append(f"Language: {lang_score}")
                
                # Expertise matching (max 0.4) - Increased from 0.3
                exp_score = 0.0
                if row.get('expertise_area') and interview_type:
                    interview_types = set(EFormMockInterviewType[t].value for t in interview_type)
                    expertise_match = set(row['expertise_area']) & interview_types
                    if expertise_match:
                        exp_score = 0.4  # Increased base score
                        if (EFormMockInterviewType.technical.value in expertise_match and
                            row.get('grade') in [EFormMentoringGrade.senior.value, EFormMentoringGrade.lead.value]):
                            exp_score += 0.1
                score += exp_score
                score_breakdown.append(f"Expertise: {exp_score}")
                
                # Senior experience bonus (max 0.2)
                senior_score = 0.0
                if row.get('linkedin_profile') and row['linkedin_profile'].get('work_experience'):
                    experience = row['linkedin_profile']['work_experience']
                    if any(job.get('title', '').lower().startswith(('senior', 'lead', 'head')) 
                          for job in experience):
                        senior_score = 0.2
                score += senior_score
                score_breakdown.append(f"Senior bonus: {senior_score}")
                
                # Base score to ensure minimum matching
                final_score = max(0.3, score)
                
                self.logger.debug(f"Score breakdown for row {features.index[features.apply(lambda x: x.equals(row), axis=1)][0]}: "
                                f"{' | '.join(score_breakdown)} | Final: {final_score}")
                
                return final_score
            
            mock_scores = features.apply(calculate_mock_interview_score, axis=1)
            scores *= mock_scores
            
            self.logger.debug(f"Final mock interview scores: {mock_scores}")
        
        # Extract meeting format based on intent type
        meeting_format = None
        if isinstance(content, dict):
            if intent_type == EFormIntentType.connects.value:
                # For connects form, meeting format is in social_circle_expansion or professional_networking
                if 'social_circle_expansion' in content:
                    social_expansion = content['social_circle_expansion']
                    meeting_format = social_expansion.get('meeting_formats', [None])[0]
                    
                    # Initialize base score for social expansion
                    social_scores = np.ones(len(features)) * 0.5  # Start with 0.5 base score
                    score_components = []
                    
                    # Consider topics for better matching
                    topics = social_expansion.get('topics', [])
                    if topics:
                        topic_scores = features['expertise_area'].apply(
                            lambda x: len(set(x or []) & set(topics)) / len(topics) if x else 0
                        )
                        topic_contribution = 0.3 * topic_scores
                        social_scores += topic_contribution
                        score_components.append(('Topics', topic_contribution))

                    # Handle custom topics if present
                    if EFormConnectsSocialExpansionTopic.custom.value in topics:
                        custom_topics = social_expansion.get('custom_topics', [])
                        if custom_topics:
                            # Match custom topics against expertise and interests
                            custom_scores = features.apply(
                                lambda row: max(
                                    len(set(row.get('expertise_area', []) or []) & set(custom_topics)) / len(custom_topics),
                                    len(set(row.get('interests', []) or []) & set(custom_topics)) / len(custom_topics)
                                ),
                                axis=1
                            )
                            custom_contribution = 0.2 * custom_scores
                            social_scores += custom_contribution
                            score_components.append(('Custom Topics', custom_contribution))

                    # Consider location for offline meetings
                    if meeting_format == EFormConnectsMeetingFormat.offline.value:
                        location_scores = self._apply_location_rule(features, {
                            'city_penalty': 0.3,
                            'country_penalty': 0.1
                        })
                        location_contribution = 0.2 * location_scores
                        social_scores += location_contribution
                        score_components.append(('Location', location_contribution))

                    # Consider network quality
                    if 'linkedin_profile' in features.columns:
                        network_scores = features['linkedin_profile'].apply(
                            lambda p: 0.2 if p and p.get('work_experience') and p.get('skills') else 0.1
                        )
                        social_scores += network_scores
                        score_components.append(('Network', network_scores))

                    # Log score components
                    for component_name, component_scores in score_components:
                        self.logger.debug(f"Social expansion {component_name} scores: {component_scores}")

                    # Ensure minimum score of 0.3 and maximum of 1.0
                    social_scores = np.clip(social_scores, 0.3, 1.0)
                    
                    self.logger.debug(f"Final social expansion scores: {social_scores}")
                    
                    # Apply social expansion scores
                    scores *= social_scores

                elif 'professional_networking' in content:
                    prof_networking = content['professional_networking']
                    topics = prof_networking.get('topics', [])
                    
                    # Initialize base score
                    base_scores = np.ones(len(features)) * 0.6  # Increased base score
                    
                    # Topic matching with proper enum handling
                    if topics:
                        def calculate_topic_score(row):
                            if not row.get('expertise_area'):
                                return 0.0
                                
                            # Direct topic matches
                            topic_matches = set(row['expertise_area']) & set(topics)
                            if topic_matches:
                                # Check for specific development expertise
                                if EFormProfessionalNetworkingTopic.development.value in topic_matches:
                                    if row.get('grade') in [
                                        EFormMentoringGrade.senior.value,
                                        EFormMentoringGrade.lead.value,
                                        EFormMentoringGrade.head.value
                                    ]:
                                        return 1.0
                                    elif row.get('grade') == EFormMentoringGrade.middle.value:
                                        return 0.8
                                
                                # Check for analytics expertise
                                if EFormProfessionalNetworkingTopic.analytics.value in topic_matches:
                                    if row.get('specialization') and any(
                                        spec.startswith('development__data_science')
                                        for spec in row.get('specialization', [])
                                    ):
                                        return 0.9
                                
                            return len(topic_matches) / len(topics) if topics else 0.0
                        
                        topic_scores = features.apply(calculate_topic_score, axis=1)
                        scores *= np.maximum(topic_scores, 0.5)
                        
                        self.logger.debug(f"Professional networking topic scores: {topic_scores}")

                    # Consider user query with enhanced position matching
                    if prof_networking.get('user_query'):
                        query = prof_networking['user_query'].lower()
                        
                        def calculate_expertise_score(row):
                            score = 0.0
                            
                            # Grade-based scoring
                            if row.get('grade'):
                                if row['grade'] == EFormMentoringGrade.lead.value:
                                    score = 1.0
                                elif row['grade'] == EFormMentoringGrade.senior.value:
                                    score = 0.9
                                elif row['grade'] == EFormMentoringGrade.middle.value:
                                    score = 0.7
                            
                            # Position title matching
                            if row.get('current_position_title'):
                                title = row['current_position_title'].lower()
                                if any(role in title for role in ['lead', 'head', 'principal', 'architect']):
                                    score = max(score, 1.0)
                                elif 'senior' in title:
                                    score = max(score, 0.9)
                            
                            # Specialization matching
                            if row.get('specialization'):
                                spec_matches = [
                                    spec for spec in row['specialization']
                                    if any(term in spec.lower() for term in query.split())
                                ]
                                if spec_matches:
                                    score = max(score, 0.8)
                            
                            return score
                        
                        expertise_scores = features.apply(calculate_expertise_score, axis=1)
                        scores *= np.maximum(expertise_scores, 0.7)  # Higher minimum for expertise
                        
                        self.logger.debug(f"Professional networking expertise scores: {expertise_scores}")

                    # Apply base scores
                    scores *= base_scores

            elif intent_type == EFormIntentType.mentoring_mentor.value:
                # Extract all relevant fields from form content
                required_grade = content.get('required_grade', [])
                specialization = content.get('specialization', [])
                help_request = content.get('help_request', {})
                is_local_community = content.get('is_local_community', False)
                
                # Initialize base scores
                mentor_scores = np.ones(len(features)) * 0.5
                score_components = []
                
                # Grade matching with proper enum handling
                if required_grade:
                    def calculate_grade_score(row):
                        if not row.get('grade'):
                            return 0.3
                        
                        grade = row['grade']
                        if grade in required_grade:
                            return 1.0
                        
                        # Map grades to numeric values for comparison
                        grade_values = {
                            EFormMentoringGrade.junior.value: 1,
                            EFormMentoringGrade.middle.value: 2,
                            EFormMentoringGrade.senior.value: 3,
                            EFormMentoringGrade.lead.value: 4,
                            EFormMentoringGrade.head.value: 5,
                            EFormMentoringGrade.executive.value: 6
                        }
                        
                        required_levels = [grade_values.get(g, 0) for g in required_grade]
                        current_level = grade_values.get(grade, 0)
                        
                        # Higher grade than required is better than lower
                        if current_level > max(required_levels):
                            return 0.9
                        elif current_level < min(required_levels):
                            return 0.5
                        return 0.7
                    
                    grade_scores = features.apply(calculate_grade_score, axis=1)
                    mentor_scores *= grade_scores
                    score_components.append(('Grade', grade_scores))
                
                # Specialization matching using EFormSpecialization
                if specialization:
                    def calculate_spec_score(row):
                        if not row.get('specialization'):
                            return 0.3
                        
                        spec_matches = []
                        for spec in row['specialization']:
                            for req_spec in specialization:
                                # Check exact match
                                if spec == req_spec:
                                    spec_matches.append(1.0)
                                # Check parent category match (e.g., development__frontend matches development__frontend__react)
                                elif req_spec.startswith(spec + '__'):
                                    spec_matches.append(0.8)
                                # Check child category match
                                elif spec.startswith(req_spec + '__'):
                                    spec_matches.append(0.9)
                        
                        return max(spec_matches) if spec_matches else 0.3
                    
                    spec_scores = features.apply(calculate_spec_score, axis=1)
                    mentor_scores *= np.maximum(spec_scores, 0.4)
                    score_components.append(('Specialization', spec_scores))

                # Handle help request types with proper enum usage
                if help_request:
                    request_types = help_request.get('request', [])
                    
                    if EFormMentoringHelpRequest.adaptation_after_relocate.value in request_types:
                        target_country = help_request.get('country')
                        if target_country:
                            location_scores = features['location'].apply(
                                lambda x: 1.0 if x and target_country in x else 0.3
                            )
                            mentor_scores *= np.maximum(location_scores, 0.4)
                            score_components.append(('Location', location_scores))

                    if EFormMentoringHelpRequest.process_and_teams_management.value in request_types:
                        def calculate_management_score(row):
                            score = 0.3  # Base score
                            
                            # Grade-based scoring
                            if row.get('grade'):
                                if row['grade'] in [
                                    EFormMentoringGrade.lead.value,
                                    EFormMentoringGrade.head.value,
                                    EFormMentoringGrade.executive.value
                                ]:
                                    score = 1.0
                                elif row['grade'] == EFormMentoringGrade.senior.value:
                                    score = 0.8
                            
                            # Position-based bonus
                            if row.get('current_position_title'):
                                title = row['current_position_title'].lower()
                                if any(role in title for role in ['lead', 'head', 'cto', 'vp']):
                                    score = max(score, 1.0)
                                elif 'manager' in title or 'team lead' in title:
                                    score = max(score, 0.9)
                            
                            return score
                        
                        management_scores = features.apply(calculate_management_score, axis=1)
                        mentor_scores *= np.maximum(management_scores, 0.5)
                        score_components.append(('Management', management_scores))

                    if EFormMentoringHelpRequest.custom.value in request_types:
                        custom_request = help_request.get('custom_request', '').lower()
                        # Add specialized scoring for common custom request patterns
                        def calculate_custom_score(row):
                            score = 0.4  # Base score
                            
                            # Match expertise areas against custom request
                            if row.get('expertise_area'):
                                if any(area.lower() in custom_request for area in row['expertise_area']):
                                    score = max(score, 0.8)
                            
                            # Match specializations
                            if row.get('specialization'):
                                if any(spec.lower() in custom_request for spec in row['specialization']):
                                    score = max(score, 0.9)
                            
                            return score
                        
                        custom_scores = features.apply(calculate_custom_score, axis=1)
                        mentor_scores *= np.maximum(custom_scores, 0.4)
                        score_components.append(('Custom', custom_scores))

                # Log score components
                for component_name, component_scores in score_components:
                    self.logger.debug(f"Mentoring {component_name} scores: {component_scores}")
                
                # Apply final mentor scores
                scores *= np.clip(mentor_scores, 0.3, 1.0)

            elif intent_type == EFormIntentType.mentoring_mentee.value:
                mentor_specialization = content.get('mentor_specialization', [])
                mentee_grade = content.get('grade', [])
                help_request = content.get('help_request', {})

                # Initialize mentee scores
                mentee_scores = np.ones(len(features)) * 0.5
                score_components = []

                # Specialization matching with hierarchical consideration
                if mentor_specialization:
                    def calculate_mentor_spec_score(row):
                        if not row.get('specialization'):
                            return 0.3
                        
                        spec_matches = []
                        for spec in row['specialization']:
                            for req_spec in mentor_specialization:
                                # Check exact match
                                if spec == req_spec:
                                    spec_matches.append(1.0)
                                # Check parent category match
                                elif req_spec.startswith(spec + '__'):
                                    spec_matches.append(0.8)
                                # Check child category match
                                elif spec.startswith(req_spec + '__'):
                                    spec_matches.append(0.9)
                                # Check same root category (e.g., development)
                                elif spec.split('__')[0] == req_spec.split('__')[0]:
                                    spec_matches.append(0.6)
                        
                        return max(spec_matches) if spec_matches else 0.3
                    
                    spec_scores = features.apply(calculate_mentor_spec_score, axis=1)
                    mentee_scores *= np.maximum(spec_scores, 0.4)
                    score_components.append(('Specialization', spec_scores))

                # Grade matching with proper enum handling
                if mentee_grade:
                    def calculate_mentee_grade_score(row):
                        if not row.get('grade'):
                            return 0.3
                        
                        grade_values = {
                            EFormMentoringGrade.junior.value: 1,
                            EFormMentoringGrade.middle.value: 2,
                            EFormMentoringGrade.senior.value: 3,
                            EFormMentoringGrade.lead.value: 4,
                            EFormMentoringGrade.head.value: 5,
                            EFormMentoringGrade.executive.value: 6
                        }
                        
                        mentee_level = grade_values.get(mentee_grade[0], 0)
                        mentor_level = grade_values.get(row['grade'], 0)
                        
                        if mentor_level > mentee_level + 1:
                            return 1.0  # Significantly more experienced
                        elif mentor_level > mentee_level:
                            return 0.9  # More experienced
                        elif mentor_level == mentee_level:
                            return 0.6  # Same level
                        return 0.3  # Less experienced
                    
                    grade_scores = features.apply(calculate_mentee_grade_score, axis=1)
                    mentee_scores *= grade_scores
                    score_components.append(('Grade', grade_scores))

                # Handle help request types
                if help_request:
                    request_types = help_request.get('request', [])
                    
                    if EFormMentoringHelpRequest.adaptation_after_relocate.value in request_types:
                        target_country = help_request.get('country')
                        if target_country:
                            def calculate_relocation_score(row):
                                score = 0.3  # Base score
                                
                                # Location matching
                                if row.get('location') and target_country in row['location']:
                                    score = max(score, 1.0)
                                elif row.get('linkedin_profile'):
                                    if row['linkedin_profile'].get('location') and target_country in row['linkedin_profile']['location']:
                                        score = max(score, 0.9)
                                
                                # Experience with relocation
                                if row.get('linkedin_profile') and row['linkedin_profile'].get('work_experience'):
                                    locations = set()
                                    for exp in row['linkedin_profile']['work_experience']:
                                        if exp.get('location'):
                                            locations.add(exp['location'])
                                    if len(locations) > 1:  # Has worked in multiple locations
                                        score = max(score, 0.8)
                                
                                return score
                            
                            relocation_scores = features.apply(calculate_relocation_score, axis=1)
                            mentee_scores *= np.maximum(relocation_scores, 0.4)
                            score_components.append(('Relocation', relocation_scores))

                # Log score components
                for component_name, component_scores in score_components:
                    self.logger.debug(f"Mentee matching {component_name} scores: {component_scores}")
                
                # Apply final mentee scores
                scores *= np.clip(mentee_scores, 0.3, 1.0)

            elif intent_type in [
                EFormIntentType.projects_find_contributor.value, 
                EFormIntentType.projects_find_cofounder.value
            ]:
                project_state = content.get('project_state')
                project_skills = content.get('skills', [])
                project_specialization = content.get('specialization', [])
                project_role = (EFormProjectUserRole.cofounder 
                               if intent_type == EFormIntentType.projects_find_cofounder.value 
                               else EFormProjectUserRole.contributor)
                
                # Initialize project scores with higher base score
                project_scores = np.ones(len(features)) * 0.6  # Increased from 0.5
                score_components = []
                
                # Skills matching with proper enum handling
                if project_skills:
                    def calculate_skill_score(row):
                        if not row.get('skill_match_score'):
                            return 0.3
                        
                        # Start with normalized skill score
                        base_score = row['skill_match_score'] / max(features['skill_match_score'])
                        
                        # Different scoring based on role
                        if project_role == EFormProjectUserRole.cofounder:
                            # Cofounders need broader expertise
                            if row.get('grade') in [EFormMentoringGrade.senior.value, 
                                                  EFormMentoringGrade.lead.value]:
                                base_score = min(1.0, base_score + 0.4)  # Increased bonus
                        else:  # Contributor
                            # Contributors need specific skills
                            if project_state == EFormProjectProjectState.scaling.value:
                                if row.get('grade') in [EFormMentoringGrade.senior.value, 
                                                      EFormMentoringGrade.lead.value]:
                                    base_score = min(1.0, base_score + 0.3)
                            elif project_state == EFormProjectProjectState.mvp.value:
                                if row.get('grade') == EFormMentoringGrade.senior.value:
                                    base_score = min(1.0, base_score + 0.2)
                        
                        # Add expertise bonus
                        if row.get('expertise_area'):
                            expertise_match = any(exp in project_specialization for exp in row['expertise_area'])
                            if expertise_match:
                                base_score = min(1.0, base_score + 0.2)
                        
                        return base_score
                    
                    skill_scores = features.apply(calculate_skill_score, axis=1)
                    project_scores *= np.maximum(skill_scores, 0.5)  # Increased minimum from 0.4
                    score_components.append(('Skills', skill_scores))
                
                # Log score components
                for component_name, component_scores in score_components:
                    self.logger.debug(f"Project matching {component_name} scores: {component_scores}")
                
                # Apply final project scores with higher minimum
                scores *= np.clip(project_scores, 0.4, 1.0)  # Increased minimum from 0.3

            elif intent_type == EFormIntentType.referrals_recommendation.value:
                english_level = content.get('required_english_level')
                company_type = content.get('company_type')
                is_local_community = content.get('is_local_community', False)
                is_all_experts_type = content.get('is_all_experts_type', False)
                is_need_call = content.get('is_need_call', False)
                
                # Initialize referral scores
                referral_scores = np.ones(len(features)) * 0.5
                score_components = []
                
                # English level matching
                if english_level and english_level != EFormEnglishLevel.not_required.value:
                    def calculate_english_score(row):
                        if not row.get('linkedin_profile'):
                            return 0.3
                            
                        # Map English levels to numeric values
                        level_values = {
                            EFormEnglishLevel.A1.value: 1,
                            EFormEnglishLevel.A2.value: 2,
                            EFormEnglishLevel.B1.value: 3,
                            EFormEnglishLevel.B2.value: 4,
                            EFormEnglishLevel.C1.value: 5,
                            EFormEnglishLevel.C2.value: 6,
                            EFormEnglishLevel.native.value: 7
                        }
                        
                        required_level = level_values.get(english_level, 0)
                        
                        # Check LinkedIn languages
                        if row['linkedin_profile'].get('languages'):
                            for lang in row['linkedin_profile']['languages']:
                                if 'english' in lang.lower():
                                    return 1.0  # Has English listed
                        
                        # Check work experience in English-speaking countries
                        if row['linkedin_profile'].get('work_experience'):
                            english_countries = {'usa', 'uk', 'canada', 'australia', 'new zealand'}
                            if any(exp.get('location', '').lower() in english_countries 
                                  for exp in row['linkedin_profile']['work_experience']):
                                return 0.9  # Work experience in English-speaking country
                        
                        return 0.5  # Default score if no clear English indicators
                    
                    english_scores = features.apply(calculate_english_score, axis=1)
                    referral_scores *= np.maximum(english_scores, 0.4)
                    score_components.append(('English', english_scores))
                
                # Company type matching
                if company_type:
                    def calculate_company_score(row):
                        score = 0.3  # Base score
                        
                        if row.get('current_company_label'):
                            if company_type == EFormRefferalsCompanyType.dummy.value:  # Replace with actual enum values
                                # Add specific company type matching logic here
                                pass
                        
                        # Consider company size and type from LinkedIn
                        if row.get('linkedin_profile'):
                            company = row['linkedin_profile'].get('current_company', {})
                            if company:
                                if company.get('size', 0) > 1000:
                                    score = max(score, 0.8)  # Large company experience
                                elif company.get('type') == 'startup':
                                    score = max(score, 0.7)  # Startup experience
                        
                        return score
                    
                    company_scores = features.apply(calculate_company_score, axis=1)
                    referral_scores *= np.maximum(company_scores, 0.4)
                    score_components.append(('Company', company_scores))
                
                # Local community consideration
                if is_local_community:
                    location_scores = self._apply_location_rule(features, {
                        'city_penalty': 0.2,
                        'country_penalty': 0.1,
                        'region_penalty': 0.05
                    })
                    referral_scores *= np.maximum(location_scores, 0.5)
                    score_components.append(('Location', location_scores))
                
                # Expert type consideration
                if is_all_experts_type:
                    def calculate_expert_score(row):
                        score = 0.3  # Base score
                        
                        # Grade-based scoring
                        if row.get('grade'):
                            if row['grade'] in [
                                EFormMentoringGrade.senior.value,
                                EFormMentoringGrade.lead.value,
                                EFormMentoringGrade.head.value,
                                EFormMentoringGrade.executive.value
                            ]:
                                score = 1.0
                            elif row['grade'] == EFormMentoringGrade.middle.value:
                                score = 0.7
                        
                        # Experience-based bonus
                        if row.get('linkedin_profile') and row['linkedin_profile'].get('work_experience'):
                            experience = row['linkedin_profile']['work_experience']
                            years = sum(exp.get('duration_years', 0) for exp in experience)

        # Handle meeting format
        if meeting_format == EFormConnectsMeetingFormat.offline.value:
            location_scores = self._apply_location_rule(features, {
                'city_penalty': 0.2,
                'country_penalty': 0.05
            })
            scores *= location_scores

        # Add enhanced professional background consideration for relevant intents
        if intent_type in [
            EFormIntentType.mentoring_mentor.value,
            EFormIntentType.mentoring_mentee.value,
            EFormIntentType.referrals_recommendation.value,
            EFormIntentType.projects_find_cofounder.value
        ]:
            prof_scores = self._apply_professional_background_rule(features, {
                'employment_weight': 0.8,
                'position_weight': 0.7,
                'industry_weight': 0.6
            })
            scores *= np.maximum(prof_scores, 0.6)

        return scores

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Apply heuristic rules to make predictions"""
        final_scores = np.ones(len(features))
        self.logger.debug("Starting prediction with initial scores set to 1.0")

        # Track individual rule scores for weighted combination
        rule_scores = []
        rule_weights = []

        # Apply each rule and collect scores
        for rule in self.rules:
            rule_type = rule['type']
            weight = rule.get('weight', 1.0)
            params = rule.get('params', {})
            
            # Get the rule method
            rule_method = getattr(self, f'_apply_{rule_type}_rule')
            
            # Apply the rule and store results
            scores = rule_method(features, params)
            rule_scores.append(scores)
            rule_weights.append(weight)
            
            self.logger.debug(f"Applied rule '{rule_type}' with weight {weight}, scores: {scores}")

        # Combine all scores using weighted average
        if rule_scores:
            rule_scores = np.array(rule_scores)
            rule_weights = np.array(rule_weights)
            
            # Normalize weights
            rule_weights = rule_weights / np.sum(rule_weights)
            
            # Calculate weighted average
            final_scores = np.sum(rule_scores * rule_weights[:, np.newaxis], axis=0)
            
            # Ensure scores are in 0-1 range
            final_scores = np.clip(final_scores, 0.0, 1.0)
            
            self.logger.debug(f"Combined scores after weighting: {final_scores}")

        return final_scores

    def _extract_meeting_format(self, intent_type: str, content: dict) -> str | None:
        """Extract meeting format based on form type"""
        if not content:
            return None
        
        if intent_type == EFormIntentType.connects.value:
            if 'social_circle_expansion' in content:
                return content['social_circle_expansion'].get('meeting_formats', [None])[0]
        
        return content.get('meeting_format')

