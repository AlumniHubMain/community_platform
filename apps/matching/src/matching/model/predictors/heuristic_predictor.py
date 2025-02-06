"""Heuristic predictor"""
import pandas as pd
import numpy as np

from common_db.enums.users import EGrade
from common_db.enums.forms import EFormQueryType, EFormMeetingType, EFormLookingForType

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
        """Apply professional background matching using LinkedIn data"""
        scores = np.ones(len(features))
        
        # Check employment status
        if 'is_currently_employed' in features.columns:
            employment_weight = params.get('employment_weight', 0.8)
            scores *= np.where(features['is_currently_employed'], employment_weight, 1.0)
        
        # Check current position relevance
        if 'current_position_title' in features.columns and 'main_current_position_title' in features.columns:
            position_weight = params.get('position_weight', 0.7)
            
            def position_similarity(pos1, pos2):
                if not pos1 or not pos2:
                    return 0.5
                # Simple string matching - could be improved with NLP
                pos1_lower = str(pos1).lower()
                pos2_lower = str(pos2).lower()
                if pos1_lower == pos2_lower:
                    return 1.0
                elif pos1_lower in pos2_lower or pos2_lower in pos1_lower:
                    return 0.8
                return 0.5
            
            position_scores = features.apply(
                lambda x: position_similarity(
                    x['current_position_title'], 
                    x['main_current_position_title']
                ),
                axis=1
            )
            scores *= (1 - position_weight + position_weight * position_scores)
        
        return scores

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
        """Apply intent-specific rules"""
        scores = np.ones(len(features))
        query_type = features['main_query_type'].iloc[0]
        meeting_type = features['main_meeting_type'].iloc[0]
        looking_for_type = features['main_looking_for_type'].iloc[0] if 'main_looking_for_type' in features.columns else None
        
        if query_type == EFormQueryType.mentoring.value:
            # Determine mentor/mentee role from looking_for_type
            is_looking_for_mentor = (looking_for_type == EFormLookingForType.mentor.value)
            is_looking_for_mentee = (looking_for_type == EFormLookingForType.mentee.value)
            
            if is_looking_for_mentor:
                # User is mentee looking for mentor
                # Grade requirements are strict - need more senior mentor
                main_grade = features['main_grade'].iloc[0]
                mentor_grades = {
                    EGrade.junior.value: {
                        EGrade.middle.value: 0.8,
                        EGrade.senior.value: 1.0,
                        EGrade.junior.value: 0.1  # Strongly discourage same/lower grade
                    },
                    EGrade.middle.value: {
                        EGrade.senior.value: 1.0,
                        EGrade.middle.value: 0.3,
                        EGrade.junior.value: 0.1
                    },
                    EGrade.senior.value: {
                        EGrade.senior.value: 1.0,
                        EGrade.middle.value: 0.2,
                        EGrade.junior.value: 0.1
                    }
                }
                grade_scores = features['grade'].apply(
                    lambda x: mentor_grades.get(main_grade, {}).get(x, 0.05) if x else 0.05
                )
                scores *= grade_scores
                
                # Professional background is very important for mentee
                if 'current_position_title' in features.columns:
                    prof_scores = self._apply_professional_background_rule(features, {
                        'employment_weight': 0.9,  # Strong preference for employed mentors
                        'position_weight': 0.8     # Position relevance is important
                    })
                    scores *= np.maximum(prof_scores, 0.5)  # Moderate penalty if no match
                    
                # Skills and expertise should align with mentee's interests
                expertise_scores = self._apply_expertise_rule(features, {
                    'base_score': params.get('expertise_base_score', 0.6)  # Higher base score
                })
                scores = np.maximum(scores * expertise_scores, scores * 0.6)
                
                if 'skill_match_score' in features.columns:
                    skill_scores = self._apply_skills_rule(features, {
                        'base_score': params.get('skill_base_score', 0.4)
                    })
                    scores = np.maximum(scores * skill_scores, scores * 0.7)
                    
            elif is_looking_for_mentee:
                # User is mentor looking for mentee
                # Grade requirements are reversed - need more junior mentee
                main_grade = features['main_grade'].iloc[0]
                mentee_grades = {
                    EGrade.senior.value: {
                        EGrade.middle.value: 0.9,
                        EGrade.junior.value: 1.0,
                        EGrade.senior.value: 0.2  # Discourage same grade
                    },
                    EGrade.middle.value: {
                        EGrade.junior.value: 1.0,
                        EGrade.middle.value: 0.3,
                        EGrade.senior.value: 0.1
                    },
                    EGrade.junior.value: {
                        EGrade.junior.value: 0.4,  # Allow peer mentoring but with lower score
                        EGrade.middle.value: 0.2,
                        EGrade.senior.value: 0.1
                    }
                }
                grade_scores = features['grade'].apply(
                    lambda x: mentee_grades.get(main_grade, {}).get(x, 0.05) if x else 0.05
                )
                scores *= grade_scores
                
                # For mentors, interest alignment is more important than exact skill match
                interest_scores = self._apply_interests_rule(features, {
                    'base_score': params.get('interest_base_score', 0.5)
                })
                scores *= np.maximum(interest_scores, 0.6)
                
                # Consider expertise area but with lower weight
                expertise_scores = self._apply_expertise_rule(features, {
                    'base_score': params.get('expertise_base_score', 0.4)
                })
                scores = np.maximum(scores * expertise_scores, scores * 0.7)
                
                # Professional background is less critical when looking for mentee
                if 'current_position_title' in features.columns:
                    prof_scores = self._apply_professional_background_rule(features, {
                        'employment_weight': 0.6,  # Less emphasis on employment
                        'position_weight': 0.5     # Position match less critical
                    })
                    scores = np.maximum(scores * prof_scores, scores * 0.8)
            
            else:
                # Fallback if role is not specified - use balanced scoring
                expertise_scores = self._apply_expertise_rule(features, {
                    'base_score': params.get('expertise_base_score', 0.6)
                })
                scores *= np.maximum(expertise_scores, 0.5)
            
        elif query_type == EFormQueryType.cooperative_learning.value:
            # For cooperative learning, combine interests, expertise, and skills
            
            # Base score from interests and expertise
            interest_scores = self._apply_interests_rule(features, {
                'base_score': params.get('interest_base_score', 0.3)
            })
            expertise_scores = self._apply_expertise_rule(features, {
                'base_score': params.get('expertise_base_score', 0.3)
            })
            scores *= np.maximum(interest_scores * expertise_scores, 0.3)
            
            # Enrich with LinkedIn data if available
            if 'skill_match_score' in features.columns:
                skill_scores = self._apply_skills_rule(features, {
                    'base_score': params.get('skill_base_score', 0.4)
                })
                scores = np.maximum(scores * skill_scores, scores * 0.4)
                
            if 'language_match_score' in features.columns:
                language_scores = self._apply_language_rule(features, {
                    'base_score': params.get('language_base_score', 0.5)
                })
                scores *= np.maximum(language_scores, 0.7)  # Language match is important but not critical
                
            # Consider grade similarity for better peer matching
            if 'grade' in features.columns:
                main_grade = features['main_grade'].iloc[0]
                grade_similarity = features['grade'].apply(
                    lambda x: 1.0 if x == main_grade else 0.7 if abs(
                        list(EGrade).index(x) - list(EGrade).index(main_grade)
                    ) == 1 else 0.4
                )
                scores *= np.maximum(grade_similarity, 0.5)  # Prefer similar grades but don't exclude others
        
        elif query_type == EFormQueryType.interests_chatting.value:
            # For casual chatting, interests match is most important
            interest_scores = self._apply_interests_rule(features, {
                'base_score': params.get('interest_base_score', 0.4)
            })
            scores *= np.maximum(interest_scores, 0.3)
            
            # Language match is important for chatting
            if 'language_match_score' in features.columns:
                language_scores = self._apply_language_rule(features, {
                    'base_score': params.get('language_base_score', 0.7)
                })
                scores *= np.maximum(language_scores, 0.5)
                
        elif query_type == EFormQueryType.news_discussion.value:
            # For news discussion, combine interests and expertise
            interest_scores = self._apply_interests_rule(features, {
                'base_score': params.get('interest_base_score', 0.5)
            })
            expertise_scores = self._apply_expertise_rule(features, {
                'base_score': params.get('expertise_base_score', 0.4)
            })
            scores *= np.maximum(interest_scores * expertise_scores, 0.4)
            
            # Language is critical for news discussion
            if 'language_match_score' in features.columns:
                language_scores = self._apply_language_rule(features, {
                    'base_score': params.get('language_base_score', 0.8)
                })
                scores *= language_scores
                
        elif query_type == EFormQueryType.startup_discussion.value:
            # For startup discussion, professional background is important
            if 'current_position_title' in features.columns:
                prof_scores = self._apply_professional_background_rule(features, {
                    'employment_weight': 0.7,
                    'position_weight': 0.6
                })
                scores *= np.maximum(prof_scores, 0.5)
                
            # Experience level matters
            grade_scores = self._apply_grade_rule(features, {
                'base_score': params.get('grade_base_score', 0.6)
            })
            scores *= np.maximum(grade_scores, 0.4)
            
        elif query_type == EFormQueryType.feedback.value:
            # For feedback, prefer more experienced users
            main_grade = features['main_grade'].iloc[0]
            grade_scores = features['grade'].apply(
                lambda x: 1.0 if x > main_grade else 0.6 if x == main_grade else 0.3
            )
            scores *= grade_scores
            
            # Expertise match is important
            expertise_scores = self._apply_expertise_rule(features, {
                'base_score': params.get('expertise_base_score', 0.7)
            })
            scores *= np.maximum(expertise_scores, 0.5)
            
        elif query_type == EFormQueryType.practical_discussion.value:
            # For practical discussion, skills and expertise are key
            expertise_scores = self._apply_expertise_rule(features, {
                'base_score': params.get('expertise_base_score', 0.6)
            })
            scores *= np.maximum(expertise_scores, 0.4)
            
            if 'skill_match_score' in features.columns:
                skill_scores = self._apply_skills_rule(features, {
                    'base_score': params.get('skill_base_score', 0.7)
                })
                scores *= np.maximum(skill_scores, 0.5)
                
        elif query_type == EFormQueryType.tools_discussion.value:
            # For tools discussion, focus on skills and experience
            if 'skill_match_score' in features.columns:
                skill_scores = self._apply_skills_rule(features, {
                    'base_score': params.get('skill_base_score', 0.8)
                })
                scores *= np.maximum(skill_scores, 0.4)
                
            # Professional background adds context
            if 'current_position_title' in features.columns:
                prof_scores = self._apply_professional_background_rule(features, {
                    'employment_weight': 0.6,
                    'position_weight': 0.7
                })
                scores *= np.maximum(prof_scores, 0.6)
                
        elif query_type == EFormQueryType.exam_preparation.value:
            # For exam prep, prefer similar grade levels
            main_grade = features['main_grade'].iloc[0]
            grade_similarity = features['grade'].apply(
                lambda x: 1.0 if x == main_grade else 
                         0.8 if abs(list(EGrade).index(x) - list(EGrade).index(main_grade)) == 1 
                         else 0.4
            )
            scores *= np.maximum(grade_similarity, 0.5)
            
            # Expertise match is important
            expertise_scores = self._apply_expertise_rule(features, {
                'base_score': params.get('expertise_base_score', 0.8)
            })
            scores *= np.maximum(expertise_scores, 0.6)
            
        elif query_type == EFormQueryType.help_request.value:
            # For help requests, prefer more experienced users
            main_grade = features['main_grade'].iloc[0]
            grade_scores = features['grade'].apply(
                lambda x: 1.0 if x > main_grade else 0.7 if x == main_grade else 0.4
            )
            scores *= grade_scores
            
            # Skills and expertise are critical
            expertise_scores = self._apply_expertise_rule(features, {
                'base_score': params.get('expertise_base_score', 0.8)
            })
            if 'skill_match_score' in features.columns:
                skill_scores = self._apply_skills_rule(features, {
                    'base_score': params.get('skill_base_score', 0.7)
                })
                scores *= np.maximum(expertise_scores * skill_scores, 0.5)
            else:
                scores *= np.maximum(expertise_scores, 0.5)
                
        elif query_type == EFormQueryType.looking_for.value:
            # Enhanced looking_for matching based on specific type
            if looking_for_type == EFormLookingForType.work.value:
                # For job seeking, emphasize professional background and experience
                if 'current_position_title' in features.columns:
                    prof_scores = self._apply_professional_background_rule(features, {
                        'employment_weight': 0.9,
                        'position_weight': 0.9
                    })
                    scores *= np.maximum(prof_scores, 0.4)
                
                # Skills are critical for job matching
                if 'skill_match_score' in features.columns:
                    skill_scores = self._apply_skills_rule(features, {
                        'base_score': params.get('skill_base_score', 0.8)
                    })
                    scores *= np.maximum(skill_scores, 0.5)
                    
            elif looking_for_type == EFormLookingForType.part_time.value:
                # For part-time work, similar to work but more flexible
                if 'current_position_title' in features.columns:
                    prof_scores = self._apply_professional_background_rule(features, {
                        'employment_weight': 0.7,
                        'position_weight': 0.7
                    })
                    scores *= np.maximum(prof_scores, 0.5)
                    
            elif looking_for_type == EFormLookingForType.mock_interview_partner.value:
                # For mock interviews, match expertise and experience level
                expertise_scores = self._apply_expertise_rule(features, {
                    'base_score': params.get('expertise_base_score', 0.7)
                })
                scores *= np.maximum(expertise_scores, 0.5)
                
                # Prefer similar or slightly higher grade
                main_grade = features['main_grade'].iloc[0]
                grade_scores = features['grade'].apply(
                    lambda x: 1.0 if x >= main_grade else 0.6
                )
                scores *= grade_scores
                
            elif looking_for_type == EFormLookingForType.pet_project.value:
                # For pet projects, focus on skills and interests
                interest_scores = self._apply_interests_rule(features, {
                    'base_score': params.get('interest_base_score', 0.7)
                })
                scores *= np.maximum(interest_scores, 0.4)
                
                if 'skill_match_score' in features.columns:
                    skill_scores = self._apply_skills_rule(features, {
                        'base_score': params.get('skill_base_score', 0.7)
                    })
                    scores *= np.maximum(skill_scores, 0.5)
                    
            elif looking_for_type == EFormLookingForType.cofounder.value:
                # For cofounders, combine multiple factors
                if 'current_position_title' in features.columns:
                    prof_scores = self._apply_professional_background_rule(features, {
                        'employment_weight': 0.8,
                        'position_weight': 0.7
                    })
                    scores *= np.maximum(prof_scores, 0.5)
                
                # Skills and expertise are important
                expertise_scores = self._apply_expertise_rule(features, {
                    'base_score': params.get('expertise_base_score', 0.7)
                })
                if 'skill_match_score' in features.columns:
                    skill_scores = self._apply_skills_rule(features, {
                        'base_score': params.get('skill_base_score', 0.7)
                    })
                    scores *= np.maximum(expertise_scores * skill_scores, 0.6)
                
                # Consider grade/experience level
                grade_scores = self._apply_grade_rule(features, {
                    'base_score': params.get('grade_base_score', 0.6)
                })
                scores *= np.maximum(grade_scores, 0.5)
                
            elif looking_for_type == EFormLookingForType.contributor.value:
                # For contributors, focus on skills and expertise
                expertise_scores = self._apply_expertise_rule(features, {
                    'base_score': params.get('expertise_base_score', 0.7)
                })
                if 'skill_match_score' in features.columns:
                    skill_scores = self._apply_skills_rule(features, {
                        'base_score': params.get('skill_base_score', 0.8)
                    })
                    scores *= np.maximum(expertise_scores * skill_scores, 0.5)
                
            elif looking_for_type == EFormLookingForType.recommendation.value:
                # For recommendations, prefer more experienced users
                main_grade = features['main_grade'].iloc[0]
                grade_scores = features['grade'].apply(
                    lambda x: 1.0 if x > main_grade else 0.7 if x == main_grade else 0.4
                )
                scores *= grade_scores
                
                # Professional background is important
                if 'current_position_title' in features.columns:
                    prof_scores = self._apply_professional_background_rule(features, {
                        'employment_weight': 0.8,
                        'position_weight': 0.7
                    })
                    scores *= np.maximum(prof_scores, 0.5)
        
        # Handle meeting type
        if meeting_type == EFormMeetingType.offline.value:
            # For offline meetings, location is critical
            location_scores = self._apply_location_rule(features, {
                'city_penalty': 0.2,
                'country_penalty': 0.05
            })
            scores *= location_scores
            
            # If LinkedIn location data is available, use it as additional signal
            if 'location' in features.columns and 'main_location' in features.columns:
                linkedin_location_match = (features['location'] == features['main_location']).astype(float)
                linkedin_location_match = linkedin_location_match.replace(0, 0.8)  # Less strict penalty
                scores *= linkedin_location_match
        
        return scores

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """Apply heuristic rules to make predictions"""
        final_scores = np.ones(len(features))
        
        # Apply base rules first
        for rule in self.rules:
            rule_type = rule['type']
            weight = rule['weight']
            params = rule.get('params', {})
            
            if rule_type in ['location', 'interests', 'expertise', 'grade']:
                scores = getattr(self, f'_apply_{rule_type}_rule')(features, params)
                final_scores *= (weight * scores + (1 - weight))
        
        # Apply LinkedIn-enriched rules
        for rule in self.rules:
            rule_type = rule['type']
            weight = rule['weight']
            params = rule.get('params', {})
            
            if rule_type in ['skills', 'professional_background', 'language']:
                scores = getattr(self, f'_apply_{rule_type}_rule')(features, params)
                # LinkedIn rules are treated as bonus signals
                final_scores = np.maximum(final_scores * (weight * scores + (1 - weight)), 
                                       final_scores * 0.7)
        
        # Apply intent-specific rules last
        for rule in self.rules:
            if rule['type'] == 'intent_specific':
                scores = self._apply_intent_specific_rule(features, rule.get('params', {}))
                final_scores *= (rule['weight'] * scores + (1 - rule['weight']))
        
        return final_scores
