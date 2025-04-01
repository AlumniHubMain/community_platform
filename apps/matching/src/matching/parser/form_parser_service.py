"""
Service for parsing text descriptions into structured form content.
"""

import logging

from common_db.enums.forms import EFormIntentType
from matching.config import matching_settings
from matching.parser.gemini_parser import GeminiParser

logger = logging.getLogger(__name__)


class FormParserService:
    """
    Service for parsing text descriptions into structured form content.
    """

    def __init__(self):
        """Initialize the form parser service."""
        self.parser = None
        self.initialized = False

    async def initialize(self):
        """Initialize the parser."""
        if not self.initialized:
            self.parser = GeminiParser(
                project_id=matching_settings.matching.project_id,  # pylint: disable=no-member
            )
            await self.parser.initialize()
            self.initialized = True

    async def parse_text_to_form_content(
        self, text: str, intent_type: EFormIntentType | None = None
    ) -> tuple[EFormIntentType, dict]:
        """
        Parse text description into structured form content.

        Args:
            text: The text description to parse
            intent_type: The form intent type (optional, will be detected if not provided)

        Returns:
            Tuple of (detected_intent_type, structured_content)
        """
        if not self.initialized:
            await self.initialize()

        try:
            # Use the enhanced parser that can detect intent type
            detected_intent, content = await self.parser.parse_text_to_form_content(text, intent_type)
            
            # Normalize the content to ensure compatibility with both old and new schemas
            normalized_content = self._normalize_object_types(content)
            
            return detected_intent, normalized_content
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error parsing form text: %s", str(e))
            # If intent_type was provided, use it; otherwise default to connects
            final_intent = intent_type or EFormIntentType.connects
            # Return a minimal valid structure based on intent type
            return final_intent, self._create_fallback_content(final_intent)

    def _create_fallback_content(self, intent_type: EFormIntentType) -> dict:
        """
        Create a minimal valid content structure for the given intent type.

        Args:
            intent_type: The form intent type

        Returns:
            A minimal valid content structure
        """
        # Define minimal valid content for each intent type
        if intent_type == EFormIntentType.connects:
            return {
                "is_local_community": True,
                "social_circle_expansion": {
                    "meeting_formats": ["online"],
                    "topics": ["general_networking"],
                    "details": "Generated from text description (parsing failed)",
                },
            }
        if intent_type == EFormIntentType.mentoring_mentor:
            return {
                "is_local_community": False,
                "required_grade": ["junior"],
                "specialization": ["development__backend"],
                "help_request": {
                    "request": ["career_growth"],
                },
                "about": "Generated from text description (parsing failed)",
            }
        if intent_type == EFormIntentType.mentoring_mentee:
            return {
                "grade": ["junior"],
                "mentor_specialization": ["development__backend"],
                "help_request": {
                    "request": ["career_growth"],
                },
                "details": "Generated from text description (parsing failed)",
            }
        if intent_type == EFormIntentType.referrals_recommendation:
            return {
                "is_local_community": False,
                "is_all_experts_type": True,
                "is_need_call": False,
                "required_english_level": "B2",
                "job_link": "https://example.com/job",
                "company_type": "product",
            }
        if intent_type == EFormIntentType.mock_interview:
            return {
                "interview_type": ["technical"],
                "language": {
                    "langs": ["english"],
                },
                "resume": "https://example.com/resume",
                "details": "Generated from text description (parsing failed)",
                "public_interview": False,
            }
        if intent_type in [EFormIntentType.projects_find_cofounder, EFormIntentType.projects_find_contributor]:
            return {
                "project_description": "Generated from text description (parsing failed)",
                "specialization": ["development__backend"],
                "skills": ["python"],
                "project_state": "idea",
            }
        if intent_type == EFormIntentType.projects_pet_project:
            return {
                "project_description": "Generated from text description (parsing failed)",
                "specialization": ["development__backend"],
                "skills": ["python"],
                "role": "developer",
            }
        return {"note": "Fallback content - parsing failed"}

    def _normalize_object_types(self, content: dict) -> dict:
        """
        Normalize object types in the form content to ensure they're compatible with both old and new schemas.
        
        Args:
            content: The form content to normalize
            
        Returns:
            Normalized form content
        """
        if content is None:
            return {}
            
        # Define transformations for specialized fields
        transforms = {
            "expertise_area": lambda v: v if isinstance(v, list) else [v] if v else [],
            "specialization": lambda v: v if isinstance(v, list) else [v] if v else [],
            "skills": lambda v: v if isinstance(v, list) else [v] if v else [],
            "languages": lambda v: v if isinstance(v, list) else [v] if v else [],
            "industries": lambda v: v if isinstance(v, list) else [v] if v else [],
            "interests": lambda v: v if isinstance(v, list) else [v] if v else [],
            "required_grade": lambda v: v if isinstance(v, list) else [v] if v else [],
            "grade": lambda v: v if isinstance(v, list) else [v] if v else [],
            "meeting_formats": lambda v: v if isinstance(v, list) else [v] if v else [],
            "topics": lambda v: v if isinstance(v, list) else [v] if v else [],
            "interview_type": lambda v: v if isinstance(v, list) else [v] if v else [],
        }
        
        # Apply transformations to top-level fields
        for field, transform in transforms.items():
            if field in content:
                content[field] = transform(content[field])
        
        # Process nested fields
        for key, value in list(content.items()):
            if isinstance(value, dict):
                content[key] = self._normalize_object_types(value)
            elif isinstance(value, list):
                # Process list of dictionaries
                if value and isinstance(value[0], dict):
                    content[key] = [self._normalize_object_types(item) if item is not None else {} for item in value]
                
        return content
