"""Base classes for scoring rules"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from datetime import datetime
from .scoring_config import ScoringConfig
from .data_normalizer import DataNormalizer

class BaseRule(ABC):
    """Base class for all scoring rules"""
    
    def __init__(self, config: ScoringConfig, normalizer: DataNormalizer):
        self.config = config
        self.normalizer = normalizer
        
    @abstractmethod
    def apply(self, features: pd.DataFrame, params: Dict[str, Any]) -> np.ndarray:
        """Apply the rule to features"""
        pass
        
    def get_base_score(self, params: Dict[str, Any]) -> float:
        """Get base score from params or config"""
        return params.get("base_score", self.config.BASE_SCORE)

class LocationRule(BaseRule):
    """Location matching rule"""
    
    def apply(self, features: pd.DataFrame, params: Dict[str, Any]) -> np.ndarray:
        scores = np.ones(len(features))
        main_location = self._get_main_location(features)
        
        if not main_location:
            return scores * self.get_base_score(params)
            
        main_city, main_country, main_region = self._parse_location(main_location)
        location_scores = features.apply(
            lambda row: self._calculate_location_score(
                row, main_city, main_country, main_region, params
            )
        )
        
        return scores * location_scores
        
    def _get_main_location(self, features: pd.DataFrame) -> str:
        """Get main location from features"""
        if "main_location" in features.columns:
            return self.normalizer.normalize_location(features["main_location"].iloc[0])
        if "linkedin_location" in features.columns:
            return self.normalizer.normalize_location(features["linkedin_location"].iloc[0])
        return None
        
    def _parse_location(self, location: str) -> tuple[str, str, str]:
        """Parse location string into components"""
        if not location:
            return "", "", ""
            
        parts = location.split("_")
        city = parts[0] if len(parts) > 0 else ""
        country = parts[1] if len(parts) > 1 else ""
        region = parts[2] if len(parts) > 2 else ""
        return city, country, region
        
    def _calculate_location_score(
        self, row: pd.Series, main_city: str, main_country: str, main_region: str, params: Dict[str, Any]
    ) -> float:
        """Calculate location score for a single row"""
        locations = self._get_all_locations(row)
        
        if not locations:
            return self.get_base_score(params)
            
        best_score = 0.0
        for location in locations:
            city, country, region = self._parse_location(location)
            
            if city == main_city and main_city:
                best_score = max(best_score, 1.0)
                break
            elif country == main_country and main_country:
                best_score = max(best_score, params.get("country_penalty", 0.7))
            elif region == main_region and main_region:
                best_score = max(best_score, params.get("region_penalty", 0.5))
                
        return max(best_score, self.get_base_score(params))
        
    def _get_all_locations(self, row: pd.Series) -> List[str]:
        """Get all locations from different sources"""
        locations = []
        
        if row.get("location"):
            locations.append(self.normalizer.normalize_location(row["location"]))
            
        if row.get("linkedin_location"):
            locations.append(self.normalizer.normalize_location(row["linkedin_location"]))
            
        if row.get("linkedin_profile"):
            profile = row["linkedin_profile"]
            if profile.get("location"):
                locations.append(self.normalizer.normalize_location(profile["location"]))
                
            if profile.get("work_experience"):
                for exp in profile["work_experience"]:
                    if isinstance(exp, dict) and exp.get("location"):
                        locations.append(self.normalizer.normalize_location(exp["location"]))
                    elif hasattr(exp, "location") and exp.location:
                        locations.append(self.normalizer.normalize_location(exp.location))
                        
        return [loc for loc in locations if loc]

class GradeRule(BaseRule):
    """Grade matching rule"""
    
    def apply(self, features: pd.DataFrame, params: Dict[str, Any]) -> np.ndarray:
        scores = np.ones(len(features))
        main_grade = self._get_main_grade(features)
        
        if not main_grade:
            return scores
            
        grade_scores = features["grade"].apply(
            lambda grade: self._calculate_grade_score(grade, main_grade, params)
        )
        
        return scores * grade_scores
        
    def _get_main_grade(self, features: pd.DataFrame) -> str:
        """Get main grade from features"""
        if "main_grade" not in features.columns:
            return None
        return self.normalizer.normalize_grade(features["main_grade"].iloc[0])
        
    def _calculate_grade_score(self, grade: Any, main_grade: str, params: Dict[str, Any]) -> float:
        """Calculate grade score"""
        if not grade:
            return self.get_base_score(params)
            
        normalized_grade = self.normalizer.normalize_grade(grade)
        return self.config.get_grade_weight(main_grade, normalized_grade)

class SkillRule(BaseRule):
    """Skill matching rule"""
    
    def apply(self, features: pd.DataFrame, params: Dict[str, Any]) -> np.ndarray:
        scores = np.ones(len(features))
        main_skills = self._get_main_skills(features)
        
        if not main_skills:
            return scores
            
        skill_scores = features.apply(
            lambda row: self._calculate_skill_score(row, main_skills, params)
        )
        
        return scores * skill_scores
        
    def _get_main_skills(self, features: pd.DataFrame) -> List[str]:
        """Get main skills from features"""
        if "main_skills" not in features.columns:
            return []
        return self.normalizer.normalize_list_field(
            features["main_skills"].iloc[0], "main_skills"
        )
        
    def _calculate_skill_score(
        self, row: pd.Series, main_skills: List[str], params: Dict[str, Any]
    ) -> float:
        """Calculate skill score for a single row"""
        skills = self._get_all_skills(row)
        
        if not skills:
            return self.get_base_score(params)
            
        skill_matches = set(skills) & set(main_skills)
        match_ratio = len(skill_matches) / len(main_skills) if main_skills else 0
        
        base_score = self.config.get_skill_score(match_ratio)
        skill_weight = params.get("weight", 0.7)
        
        final_score = self.get_base_score(params) + (1.0 - self.get_base_score(params)) * (base_score * skill_weight)
        return max(final_score, self.config.MIN_SCORE)
        
    def _get_all_skills(self, row: pd.Series) -> List[str]:
        """Get all skills from different sources"""
        skills = []
        
        if row.get("skills"):
            skills.extend(self.normalizer.normalize_list_field(row["skills"], "skills"))
            
        if row.get("linkedin_profile") and row["linkedin_profile"].get("skills"):
            skills.extend(
                self.normalizer.normalize_list_field(
                    row["linkedin_profile"]["skills"], "linkedin_skills"
                )
            )
            
        return skills

class LanguageRule(BaseRule):
    """Language matching rule"""
    
    def apply(self, features: pd.DataFrame, params: Dict[str, Any]) -> np.ndarray:
        scores = np.ones(len(features))
        main_languages = self._get_main_languages(features)
        
        if not main_languages:
            return scores * self.get_base_score(params)
            
        language_scores = features.apply(
            lambda row: self._calculate_language_score(row, main_languages, params)
        )
        
        return scores * language_scores
        
    def _get_main_languages(self, features: pd.DataFrame) -> List[str]:
        """Get main languages from features"""
        if "main_languages" not in features.columns:
            return []
        return self.normalizer.normalize_list_field(
            features["main_languages"].iloc[0], "main_languages"
        )
        
    def _calculate_language_score(
        self, row: pd.Series, main_languages: List[str], params: Dict[str, Any]
    ) -> float:
        """Calculate language score for a single row"""
        languages = self._get_all_languages(row)
        
        if not languages:
            return self.get_base_score(params)
            
        language_matches = set(languages) & set(main_languages)
        if not language_matches:
            return self.get_base_score(params)
            
        # Check for country-specific languages
        best_score = self.config.language.WEIGHTS["standard"]
        for lang in language_matches:
            for country_langs in self.config.language.COUNTRY_LANGUAGES.values():
                if lang.lower() in [l.lower() for l in country_langs]:
                    best_score = max(best_score, self.config.language.WEIGHTS["country_specific"])
                    break
                    
        language_weight = params.get("weight", 0.7)
        final_score = self.get_base_score(params) + (1.0 - self.get_base_score(params)) * (best_score * language_weight)
        return max(final_score, self.config.MIN_SCORE)
        
    def _get_all_languages(self, row: pd.Series) -> List[str]:
        """Get all languages from different sources"""
        languages = []
        
        if row.get("languages"):
            languages.extend(self.normalizer.normalize_list_field(row["languages"], "languages"))
            
        if row.get("linkedin_profile") and row["linkedin_profile"].get("languages"):
            languages.extend(
                self.normalizer.normalize_list_field(
                    row["linkedin_profile"]["languages"], "linkedin_languages"
                )
            )
            
        return languages

class ExpertiseRule(BaseRule):
    """Expertise matching rule"""
    
    def apply(self, features: pd.DataFrame, params: Dict[str, Any]) -> np.ndarray:
        scores = np.ones(len(features))
        main_expertise = self._get_main_expertise(features)
        
        if not main_expertise:
            return scores * self.get_base_score(params)
            
        expertise_scores = features.apply(
            lambda row: self._calculate_expertise_score(row, main_expertise, params)
        )
        
        return scores * expertise_scores
        
    def _get_main_expertise(self, features: pd.DataFrame) -> List[str]:
        """Get main expertise areas from features"""
        if "main_expertise_area" not in features.columns:
            return []
        
        # Handle the expertise areas which can be EExpertiseArea enums or their values
        main_expertise = features["main_expertise_area"].iloc[0]
        
        # Normalize expertise areas
        if isinstance(main_expertise, list):
            # Process each element which might be an enum instance or string value
            normalized_expertise = []
            for expertise in main_expertise:
                if hasattr(expertise, 'value'):  # It's an enum
                    normalized_expertise.append(expertise.value)
                else:  # It's already a string value
                    normalized_expertise.append(expertise)
            return self.normalizer.normalize_list_field(normalized_expertise, "main_expertise_area")
        else:
            return []
        
    def _calculate_expertise_score(
        self, row: pd.Series, main_expertise: List[str], params: Dict[str, Any]
    ) -> float:
        """Calculate expertise score for a single row"""
        expertise_areas = self._get_all_expertise(row)
        
        if not expertise_areas:
            return self.get_base_score(params)
            
        # Normalize main_expertise for comparison
        normalized_main_expertise = [exp.lower() if isinstance(exp, str) else exp for exp in main_expertise]
        
        # Normalize expertise_areas for comparison
        normalized_expertise_areas = [exp.lower() if isinstance(exp, str) else exp for exp in expertise_areas]
        
        # Find matches (case-insensitive)
        expertise_matches = set()
        for area1 in normalized_main_expertise:
            for area2 in normalized_expertise_areas:
                if area1 == area2:
                    expertise_matches.add(area1)
        
        if not expertise_matches:
            return self.get_base_score(params)
            
        # Calculate weighted match
        score = 0.0
        for match in expertise_matches:
            if match in self.config.TECHNICAL_AREAS:
                score += self.config.TECHNICAL_WEIGHT
            else:
                score += self.config.NON_TECHNICAL_WEIGHT
                
        score = min(score, self.config.MAX_SCORE)
        expertise_weight = params.get("weight", 0.7)
        final_score = self.get_base_score(params) + (1.0 - self.get_base_score(params)) * (score * expertise_weight)
        return max(final_score, self.config.MIN_SCORE)
        
    def _get_all_expertise(self, row: pd.Series) -> List[str]:
        """Get all expertise areas from different sources"""
        expertise = []
        
        if row.get("expertise_area"):
            # Handle potential enum values
            expertise_area = row["expertise_area"]
            if isinstance(expertise_area, list):
                for area in expertise_area:
                    if hasattr(area, 'value'):  # It's an enum
                        expertise.append(area.value)
                    else:  # It's already a string value
                        expertise.append(area)
            elif hasattr(expertise_area, 'value'):  # Single enum value
                expertise.append(expertise_area.value)
            else:  # Single string value or other
                expertise.append(str(expertise_area))
                
        if row.get("linkedin_profile"):
            profile = row["linkedin_profile"]
            if profile.get("headline"):
                expertise.extend(self._extract_expertise_from_headline(profile["headline"]))
            if profile.get("summary"):
                expertise.extend(self._extract_expertise_from_summary(profile["summary"]))
                
        return expertise
        
    def _extract_expertise_from_headline(self, headline: str) -> List[str]:
        """Extract expertise areas from LinkedIn headline"""
        if not headline:
            return []
            
        # Simple extraction based on common patterns
        expertise = []
        headline_lower = headline.lower()
        
        for area in self.config.TECHNICAL_AREAS:
            if area.lower() in headline_lower:
                expertise.append(area)
                
        return expertise
        
    def _extract_expertise_from_summary(self, summary: str) -> List[str]:
        """Extract expertise areas from LinkedIn summary"""
        if not summary:
            return []
            
        # Simple extraction based on common patterns
        expertise = []
        summary_lower = summary.lower()
        
        for area in self.config.TECHNICAL_AREAS:
            if area.lower() in summary_lower:
                expertise.append(area)
                
        return expertise

class NetworkQualityRule(BaseRule):
    """Network quality scoring rule"""
    
    def apply(self, features: pd.DataFrame, params: Dict[str, Any]) -> np.ndarray:
        scores = np.ones(len(features))
        
        if "linkedin_profile" not in features.columns:
            return scores * self.get_base_score(params)
            
        network_scores = features["linkedin_profile"].apply(
            lambda profile: self._calculate_network_score(profile, params)
        )
        
        return scores * network_scores
        
    def _calculate_network_score(self, profile: Dict[str, Any], params: Dict[str, Any]) -> float:
        """Calculate network quality score"""
        if not profile:
            return self.get_base_score(params)
            
        score = 0.5  # Base score for having a profile
        
        # Consider follower count (max 0.2)
        followers = profile.get("follower_count", 0) or 0
        follower_score = min(0.2, followers / 5000)  # Cap at 5000 followers
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
            job_titles = []
            for job in experience:
                if isinstance(job, dict):
                    job_title = job.get("title", "")
                else:
                    job_title = getattr(job, "title", "")
                job_titles.append(job_title.lower() if isinstance(job_title, str) else "")
                
            if any(title.startswith(("senior", "lead", "head")) for title in job_titles if title):
                score += 0.2
            elif len(experience) > 2:  # Multiple experiences
                score += 0.1
                
        network_weight = params.get("weight", 0.7)
        final_score = self.get_base_score(params) + (1.0 - self.get_base_score(params)) * (score * network_weight)
        return max(final_score, self.config.MIN_SCORE)

class ProjectExperienceRule(BaseRule):
    """Project experience matching rule"""
    
    def apply(self, features: pd.DataFrame, params: Dict[str, Any]) -> np.ndarray:
        """Apply project experience matching rule"""
        scores = np.ones(len(features))
        main_project_type = features["main_project_type"].iloc[0] if "main_project_type" in features.columns else None
        
        if not main_project_type:
            return scores * self.get_base_score(params)
            
        def calculate_project_score(row):
            score = self.get_base_score(params)
            
            if not row.get("linkedin_profile"):
                return score
                
            profile = row["linkedin_profile"]
            
            # Check projects section
            projects = profile.get("projects", [])
            if projects:
                # Project count scoring
                project_count = len(projects)
                if project_count >= 5:
                    score += 0.2
                elif project_count >= 3:
                    score += 0.1
                    
                # Project relevance scoring
                relevant_projects = 0
                for project in projects:
                    project_type = project.get("type", "")
                    if project_type == main_project_type:
                        relevant_projects += 1
                        
                if relevant_projects >= 3:
                    score += 0.3
                elif relevant_projects >= 1:
                    score += 0.2
                    
            # Check work experience for project-related roles
            if profile.get("work_experience"):
                project_related_exp = 0
                for exp in profile["work_experience"]:
                    title = exp.get("title", "").lower()
                    if any(term in title for term in ["project", "product", "manager", "lead"]):
                        project_related_exp += 1
                        
                if project_related_exp >= 2:
                    score += 0.2
                elif project_related_exp >= 1:
                    score += 0.1
                    
            return min(score, 1.0)
            
        project_scores = features.apply(calculate_project_score, axis=1)
        scores *= project_scores
        return scores

class EducationRule(BaseRule):
    """Education matching rule"""
    
    def apply(self, features: pd.DataFrame, params: Dict[str, Any]) -> np.ndarray:
        """Apply education matching rule"""
        scores = np.ones(len(features))
        main_field = features["main_education_field"].iloc[0] if "main_education_field" in features.columns else None
        
        if not main_field:
            return scores * self.get_base_score(params)
            
        def calculate_education_score(row):
            score = self.get_base_score(params)
            
            if not row.get("linkedin_profile"):
                return score
                
            profile = row["linkedin_profile"]
            education = profile.get("education", [])
            
            if not education:
                return score
                
            # Field matching
            field_match = False
            for edu in education:
                field = edu.get("field", "").lower()
                if main_field.lower() in field:
                    field_match = True
                    score += 0.3
                    break
                    
            # Degree level scoring
            highest_degree = "none"
            for edu in education:
                degree = edu.get("degree", "").lower()
                if "phd" in degree or "doctorate" in degree:
                    highest_degree = "phd"
                    break
                elif "master" in degree:
                    highest_degree = "master"
                elif "bachelor" in degree and highest_degree not in ["phd", "master"]:
                    highest_degree = "bachelor"
                    
            # Add degree bonus
            if highest_degree == "phd":
                score += 0.3
            elif highest_degree == "master":
                score += 0.2
            elif highest_degree == "bachelor":
                score += 0.1
                
            # Add bonus for recent graduates if looking for junior positions
            if "main_grade" in features.columns and features["main_grade"].iloc[0] == "junior":
                most_recent_year = max((edu.get("end_year", 0) for edu in education), default=0)
                if most_recent_year >= datetime.now().year - 2:  # Within last 2 years
                    score += 0.2
                    
            return min(score, 1.0)
            
        education_scores = features.apply(calculate_education_score, axis=1)
        scores *= education_scores
        return scores

class AvailabilityRule(BaseRule):
    """Availability matching rule"""
    
    def apply(self, features: pd.DataFrame, params: Dict[str, Any]) -> np.ndarray:
        """Apply availability matching rule"""
        scores = np.ones(len(features))
        required_hours = features["main_required_hours"].iloc[0] if "main_required_hours" in features.columns else None
        
        if not required_hours:
            return scores * self.get_base_score(params)
            
        def calculate_availability_score(row):
            score = self.get_base_score(params)
            
            # Check available hours
            if row.get("available_hours"):
                available = row["available_hours"]
                if available >= required_hours:
                    score += 0.3
                elif available >= required_hours * 0.8:
                    score += 0.2
                elif available >= required_hours * 0.5:
                    score += 0.1
                    
            # Check schedule flexibility
            if row.get("schedule_flexibility"):
                flexibility = row["schedule_flexibility"]
                if flexibility == "high":
                    score += 0.2
                elif flexibility == "medium":
                    score += 0.1
                    
            # Check time zone compatibility
            if row.get("timezone") and features["main_timezone"].iloc[0]:
                time_diff = abs(row["timezone"] - features["main_timezone"].iloc[0])
                if time_diff <= 2:
                    score += 0.2
                elif time_diff <= 4:
                    score += 0.1
                    
            return min(score, 1.0)
            
        availability_scores = features.apply(calculate_availability_score, axis=1)
        scores *= availability_scores
        return scores

class CommunicationStyleRule(BaseRule):
    """Communication style matching rule"""
    
    def apply(self, features: pd.DataFrame, params: Dict[str, Any]) -> np.ndarray:
        """Apply communication style matching rule"""
        scores = np.ones(len(features))
        preferred_style = features["main_communication_style"].iloc[0] if "main_communication_style" in features.columns else None
        
        if not preferred_style:
            return scores * self.get_base_score(params)
            
        def calculate_communication_score(row):
            score = self.get_base_score(params)
            
            # Direct style matching
            if row.get("communication_style") == preferred_style:
                score += 0.3
                
            # Check communication indicators from LinkedIn
            if row.get("linkedin_profile"):
                profile = row["linkedin_profile"]
                
                # Check recommendations and endorsements
                if profile.get("recommendations_count", 0) > 5:
                    score += 0.2
                elif profile.get("recommendations_count", 0) > 2:
                    score += 0.1
                    
                # Check activity and engagement
                if profile.get("activity_score", 0) > 80:
                    score += 0.2
                elif profile.get("activity_score", 0) > 50:
                    score += 0.1
                    
                # Check writing style from summary
                if profile.get("summary"):
                    summary = profile["summary"].lower()
                    if preferred_style == "detailed":
                        if len(summary.split()) > 100:  # Long, detailed summary
                            score += 0.2
                    elif preferred_style == "concise":
                        if len(summary.split()) < 50:  # Short, concise summary
                            score += 0.2
                            
            return min(score, 1.0)
            
        communication_scores = features.apply(calculate_communication_score, axis=1)
        scores *= communication_scores
        return scores

class RuleFactory:
    """Factory for creating rule instances"""
    
    def __init__(self, config: ScoringConfig, normalizer: DataNormalizer):
        self.config = config
        self.normalizer = normalizer
        self.rules = {
            "location": LocationRule,
            "grade": GradeRule,
            "skill": SkillRule,
            "language": LanguageRule,
            "expertise": ExpertiseRule,
            "network": NetworkQualityRule,
            "project_experience": ProjectExperienceRule,
            "education": EducationRule,
            "availability": AvailabilityRule,
            "communication": CommunicationStyleRule,
        }
        
    def create_rule(self, rule_type: str) -> BaseRule:
        """Create a rule instance by type"""
        if rule_type not in self.rules:
            raise ValueError(f"Unknown rule type: {rule_type}")
            
        return self.rules[rule_type](self.config, self.normalizer) 