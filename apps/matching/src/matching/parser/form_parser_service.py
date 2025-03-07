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
            return detected_intent, content
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
                "langluage": {
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
