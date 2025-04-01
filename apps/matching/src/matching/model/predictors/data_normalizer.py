"""Data normalization utilities for predictors"""
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import logging

class DataNormalizer:
    """Handles data normalization for predictors"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def normalize_list_field(self, value: Any, field_name: str) -> List[str]:
        """Normalize a field that is expected to be a list of strings"""
        if value is None:
            return []
            
        try:
            if isinstance(value, list):
                # Process each item which might be an enum or string
                result = []
                for item in value:
                    if item is None:
                        continue
                    if hasattr(item, 'value'):  # It's an enum
                        result.append(item.value)
                    elif hasattr(item, 'label'):  # It has a label attribute
                        result.append(item.label)
                    else:  # It's a string or other type
                        result.append(str(item).lower())
                return result
            elif hasattr(value, 'value'):  # Single enum
                return [value.value]
            elif hasattr(value, 'label'):  # Single object with label
                return [value.label]
            elif isinstance(value, str):  # Single string
                return [value.lower()]
            else:  # Other type
                return [str(value).lower()]
        except Exception as e:
            self.logger.warning(f"Error normalizing {field_name}: {e}")
            return []

    def normalize_linkedin_profile(self, profile: Any) -> Dict[str, Any]:
        """Normalize LinkedIn profile data"""
        if not profile:
            return {}
            
        try:
            if hasattr(profile, 'model_dump'):
                return profile.model_dump()
            elif hasattr(profile, 'dict'):
                return profile.dict()
            elif isinstance(profile, dict):
                return profile
            return {}
        except Exception as e:
            self.logger.warning(f"Failed to normalize LinkedIn profile: {e}")
            return {}

    def normalize_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Normalize all features in the DataFrame"""
        features_copy = features.copy()
        
        # List of fields to normalize
        list_fields = [
            'expertise_area',
            'interests',
            'skills',
            'specialisations',
            'specialisation',
            'industries',
            'industry'
        ]
        
        # Process each user entry
        for idx, row in features_copy.iterrows():
            # Normalize list fields
            for field in list_fields:
                if field in row:
                    features_copy.at[idx, field] = self.normalize_list_field(row[field], field)
            
            # Normalize LinkedIn profile
            if 'linkedin_profile' in row:
                features_copy.at[idx, 'linkedin_profile'] = self.normalize_linkedin_profile(row['linkedin_profile'])
                
        return features_copy

    def normalize_grade(self, grade: Any) -> Optional[str]:
        """Normalize grade value"""
        if not grade:
            return None
            
        if hasattr(grade, 'value'):
            return grade.value
            
        return str(grade)

    def normalize_location(self, location: Any) -> Optional[str]:
        """Normalize location value"""
        if not location:
            return None
            
        if isinstance(location, str):
            return location
            
        if hasattr(location, 'value'):
            return location.value
            
        return str(location)

    def normalize_intent(self, intent: Any) -> Optional[str]:
        """Normalize intent value"""
        if not intent:
            return None
            
        if hasattr(intent, 'value'):
            return intent.value
            
        return str(intent) 