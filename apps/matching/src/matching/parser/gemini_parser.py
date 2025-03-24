"""
Text field parser using Google Cloud's Gemini to extract structured form data from text descriptions.
"""

import re
import json
import logging
from typing import Type
import vertexai
from vertexai.generative_models import GenerativeModel
from pydantic import BaseModel

from common_db.enums.forms import EFormIntentType
from common_db.schemas.forms import (
    FormConnects,
    FormMentoringMentor,
    FormMentoringMentee,
    FormReferralsRecommendation,
    FormMockInterview,
    FormProjectsFindHead,
    FormProjectPetProject,
    FormFieldSocialSircleExpansion,
    FormFieldProfessionalNetworking,
    FormMentoringHelpRequest,
)


logger = logging.getLogger(__name__)


class GeminiParser:
    """
    Parser that uses Google Cloud's Gemini to extract structured form data from text descriptions.
    """

    def __init__(self, project_id: str, location: str = "us-central1", model_name: str = "gemini-1.5-pro"):
        """
        Initialize the Gemini parser.

        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
            model_name: Gemini model name to use
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.model = None
        self.initialized = False

        # Map of intent types to their nested field classes for better schema generation
        self.nested_field_classes = {
            EFormIntentType.connects: {
                "social_circle_expansion": FormFieldSocialSircleExpansion,
                "professional_networking": FormFieldProfessionalNetworking,
            },
            EFormIntentType.mentoring_mentor: {
                "help_request": FormMentoringHelpRequest,
            },
            EFormIntentType.mentoring_mentee: {
                "help_request": FormMentoringHelpRequest,
            },
        }
        
        # Map of data types we need to handle specially for new schemas
        self.special_data_types = {
            "expertise_area": lambda value: value if isinstance(value, list) else [value] if value else [],
            "grade": lambda value: value if isinstance(value, str) else value.value if hasattr(value, "value") else None,
            "interests": lambda value: [i.label if hasattr(i, "label") else (i.value if hasattr(i, "value") else i) for i in value] if isinstance(value, list) else [],
            "skills": lambda value: [s.label if hasattr(s, "label") else (s.value if hasattr(s, "value") else s) for s in value] if isinstance(value, list) else [],
            "specialisations": lambda value: [s.label if hasattr(s, "label") else (s.value if hasattr(s, "value") else s) for s in value] if isinstance(value, list) else [],
            "languages": lambda value: [l.label if hasattr(l, "label") else (l.value if hasattr(l, "value") else l) for l in value] if isinstance(value, list) else [],
            "industries": lambda value: [i.label if hasattr(i, "label") else (i.value if hasattr(i, "value") else i) for i in value] if isinstance(value, list) else [],
            "specialization": lambda value: value if isinstance(value, list) else [value] if value else [],
            "meeting_formats": lambda value: value if isinstance(value, list) else [value] if value else [],
            "topics": lambda value: value if isinstance(value, list) else [value] if value else [],
            "required_grade": lambda value: value if isinstance(value, list) else [value] if value else [],
            "interview_type": lambda value: value if isinstance(value, list) else [value] if value else [],
        }

    async def initialize(self):
        """Initialize the Gemini client"""
        if not self.initialized:
            # Initialize Vertex AI with project and location
            vertexai.init(project=self.project_id, location=self.location)

            # Load the generative model
            self.model = GenerativeModel(self.model_name)
            self.initialized = True
            logger.info("Initialized Gemini parser with model %s", self.model_name)

    async def detect_intent_type(self, text: str) -> EFormIntentType:
        """
        Detect the intent type from the text description.

        Args:
            text: The text description to analyze

        Returns:
            The detected intent type
        """
        if not self.initialized:
            await self.initialize()

        prompt = f"""
        You are a specialized parser that analyzes text to determine the user's intent.
        
        Based on the following text, determine which of these form types best matches the user's intent:
        
        1. connects - For social connections and networking
        2. mentoring_mentor - User wants to be a mentor
        3. mentoring_mentee - User wants to find a mentor
        4. referrals_recommendation - User wants job referrals
        5. mock_interview - User wants to practice interviews
        6. projects_find_cofounder - User wants to find a cofounder for a project
        7. projects_find_contributor - User wants to find contributors for a project
        8. projects_pet_project - User wants to join a project
        
        
        Text to analyze:
        "{text}"
        
        Return ONLY the intent type (e.g., "connects", "mentoring_mentor", etc.) without any additional text or explanation.
        """

        try:
            response = await self.model.generate_content(prompt)
            intent_str = response.text.strip().lower()

            # Map the response to an enum value
            intent_map = {
                "connects": EFormIntentType.connects,
                "mentoring_mentor": EFormIntentType.mentoring_mentor,
                "mentoring_mentee": EFormIntentType.mentoring_mentee,
                "referrals_recommendation": EFormIntentType.referrals_recommendation,
                "mock_interview": EFormIntentType.mock_interview,
                "projects_find_cofounder": EFormIntentType.projects_find_cofounder,
                "projects_find_contributor": EFormIntentType.projects_find_contributor,
                "projects_pet_project": EFormIntentType.projects_pet_project,
            }

            # Default to connects if we can't determine
            intent_type = intent_map.get(intent_str, EFormIntentType.connects)
            logger.info("Detected intent type: %s from text", intent_type)
            return intent_type

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error detecting intent type: %s", str(e))
            # Default to connects if there's an error
            return EFormIntentType.connects

    async def parse_text_to_form_content(
        self, text: str, intent_type: EFormIntentType | None = None
    ) -> tuple[EFormIntentType, dict]:
        """
        Parse text description into structured form content based on intent type.

        Args:
            text: The text description to parse
            intent_type: The form intent type (optional, will be detected if not provided)

        Returns:
            Tuple of (detected_intent_type, structured_content)
        """
        if not self.initialized:
            await self.initialize()

        # If intent_type is not provided, detect it
        if intent_type is None:
            intent_type = await self.detect_intent_type(text)

        # Get the schema class for the intent type
        schema_class = self._get_schema_class_for_intent(intent_type)
        if not schema_class:
            raise ValueError(f"No schema class found for intent type: {intent_type}")

        # Create prompt for the intent type
        prompt = self._create_prompt_for_intent(text, intent_type, schema_class)

        # Generate response from Gemini
        try:
            response = await self.model.generate_content(prompt)
            parsed_content = self._extract_json_from_response(response.text)
            
            # Process nested fields for special data types
            self._process_special_data_types(parsed_content)
            
            # Validate against schema
            try:
                schema_class.model_validate(parsed_content)
            except Exception as e:
                logger.warning(f"Schema validation failed for {intent_type}: {e}")
                # We continue even if validation fails - it might just be a few missing fields
                # that have sensible defaults

            return intent_type, parsed_content

        except Exception as e:
            logger.error(f"Failed to generate form content: {e}")
            raise

    def _process_special_data_types(self, content: dict) -> None:
        """
        Process special data types in the parsed content to match expected schema formats.
        
        Args:
            content: The parsed content to process
        """
        if content is None:
            return
            
        # Process each field in the content
        for field_name, value in list(content.items()):
            # Handle None values
            if value is None:
                content[field_name] = []
                continue
            
            # Handle lists of objects
            if isinstance(value, list):
                # Skip if the list is empty
                if not value:
                    continue
                    
                # Check if the list contains objects with special attributes
                if any(hasattr(item, "__dict__") or (not isinstance(item, dict) and not isinstance(item, str)) 
                      for item in value if item is not None):
                    # Process each item in the list
                    new_list = []
                    for item in value:
                        if item is None:
                            continue
                        if hasattr(item, "label") and item.label is not None:
                            new_list.append(item.label)
                        elif hasattr(item, "value") and item.value is not None:
                            new_list.append(item.value)
                        else:
                            # Keep original strings or other types as is
                            new_list.append(item)
                    content[field_name] = new_list
            
            # Handle single objects with attributes
            elif not isinstance(value, dict) and not isinstance(value, str) and hasattr(value, "__dict__"):
                if hasattr(value, "value") and value.value is not None:
                    content[field_name] = value.value
                elif hasattr(value, "label") and value.label is not None:
                    content[field_name] = value.label
                else:
                    # Keep as original type
                    content[field_name] = str(value)
            
            # Process nested dictionaries
            elif isinstance(value, dict):
                self._process_special_data_types(value)
        
        # Process nested lists of dictionaries
        for key, value in content.items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                for item in value:
                    if item is not None:
                        self._process_special_data_types(item)

    def _get_schema_class_for_intent(self, intent_type: EFormIntentType) -> Type[BaseModel] | None:
        """Get the appropriate schema class for the given intent type."""
        intent_schema_map = {
            EFormIntentType.connects: FormConnects,
            EFormIntentType.mentoring_mentor: FormMentoringMentor,
            EFormIntentType.mentoring_mentee: FormMentoringMentee,
            EFormIntentType.referrals_recommendation: FormReferralsRecommendation,
            EFormIntentType.mock_interview: FormMockInterview,
            EFormIntentType.projects_find_cofounder: FormProjectsFindHead,
            EFormIntentType.projects_find_contributor: FormProjectsFindHead,
            EFormIntentType.projects_pet_project: FormProjectPetProject,
        }
        return intent_schema_map.get(intent_type)

    def _create_prompt_for_intent(self, text: str, intent_type: EFormIntentType, schema_class: Type[BaseModel]) -> str:
        """
        Create a prompt for Gemini based on the intent type and schema.

        Args:
            text: The text description to parse
            intent_type: The form intent type
            schema_class: The Pydantic schema class for the form

        Returns:
            A prompt string for Gemini
        """
        # Get schema information
        schema_info = self._get_schema_info(schema_class)

        # Create base prompt
        base_prompt = f"""
        You are a specialized parser that extracts structured form data from text descriptions.
        
        Parse the following text into a JSON object that matches this schema:
        
        {schema_info}
        
        Text to parse:
        "{text}"
        
        Return ONLY the JSON object without any additional text or explanation.
        Format the JSON according to the schema above.
        """

        # Add intent-specific instructions
        if intent_type == EFormIntentType.connects:
            base_prompt += """
            For the "connects" form, determine if the person is looking for:
            1. Social circle expansion (casual meetings, making friends)
            2. Professional networking (career-focused connections)
            
            Then extract details about preferred meeting formats and topics of interest.
            
            The form should include either a "social_circle_expansion" or "professional_networking" field (or both).
            Each of these fields should have:
            - meeting_formats (array of strings): ["online", "offline", "both"]
            - topics (array of strings): Topic areas of interest
            - details (string): Additional details about what they're looking for
            """
        elif intent_type in [EFormIntentType.mentoring_mentor, EFormIntentType.mentoring_mentee]:
            base_prompt += """
            For mentoring forms, extract information about:
            - Specialization areas
            - Grade/seniority level
            - Specific help requests
            - Whether it's for a local community
            
            The "help_request" field should include:
            - request (array of strings): Types of help needed
            """
        elif intent_type == EFormIntentType.referrals_recommendation:
            base_prompt += """
            For referrals forms, extract information about:
            - Required English level
            - Company type (product, outsource, etc.)
            - Whether they need a call
            - Whether it's for a local community
            """
        elif intent_type == EFormIntentType.mock_interview:
            base_prompt += """
            For mock interview forms, extract information about:
            - Interview type (technical, behavioral, etc.)
            - Languages
            - Resume link (use a placeholder if not provided)
            - Whether the interview should be public
            """
        elif intent_type in [EFormIntentType.projects_find_cofounder, EFormIntentType.projects_find_contributor]:
            base_prompt += """
            For project forms, extract information about:
            - Project description
            - Required specializations
            - Required skills
            - Project state (idea, prototype, etc.)
            """
        elif intent_type == EFormIntentType.projects_pet_project:
            base_prompt += """
            For pet project forms, extract information about:
            - Project description
            - User's specialization
            - User's skills
            - User's preferred role in the project
            """

        return base_prompt

    def _get_schema_info(self, schema_class: Type[BaseModel]) -> str:
        """
        Get a string representation of the schema fields and their types.

        Args:
            schema_class: The Pydantic schema class

        Returns:
            A formatted string describing the schema
        """
        schema = schema_class.model_json_schema()

        # Format the schema information in a more readable way
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        schema_info = []
        for field_name, field_info in properties.items():
            field_type = field_info.get("type", "unknown")
            field_enum = field_info.get("enum", [])
            field_items = field_info.get("items", {})
            is_required = field_name in required

            # Handle nested objects
            if field_type == "object" and "properties" in field_info:
                nested_props = []
                for nested_name, nested_info in field_info["properties"].items():
                    nested_type = nested_info.get("type", "unknown")
                    nested_props.append(f"    - {nested_name} ({nested_type})")

                field_desc = f"- {field_name} (object):"
                if is_required:
                    field_desc += " [REQUIRED]"
                field_desc += "\n" + "\n".join(nested_props)

                # Add more detailed info for special nested fields
                if field_name in self.nested_field_classes.get(schema_class.model_fields.get("intent", None), {}):
                    nested_class = self.nested_field_classes[schema_class.model_fields.get("intent")][field_name]
                    nested_schema = nested_class.model_json_schema()
                    nested_props = nested_schema.get("properties", {})
                    for prop_name, prop_info in nested_props.items():
                        if "enum" in prop_info:
                            field_desc += (
                                f"\n    - {prop_name} valid values: {', '.join(str(v) for v in prop_info['enum'])}"
                            )

            # Handle arrays
            elif field_type == "array":
                item_type = field_items.get("type", "unknown")
                field_desc = f"- {field_name} (array of {item_type})"
                if is_required:
                    field_desc += " [REQUIRED]"

                # If array items have enum values
                if "enum" in field_items:
                    field_desc += f"\n  Valid values: {', '.join(str(v) for v in field_items['enum'])}"

            # Handle simple fields
            else:
                field_desc = f"- {field_name} ({field_type})"
                if is_required:
                    field_desc += " [REQUIRED]"

                if field_enum:
                    field_desc += f"\n  Valid values: {', '.join(str(v) for v in field_enum)}"

            schema_info.append(field_desc)

        return "\n".join(schema_info)

    def _extract_json_from_response(self, response_text: str) -> dict:
        """
        Extract JSON from the model response text.

        Args:
            response_text: The raw text response from Gemini

        Returns:
            Parsed JSON as a dictionary
        """
        # Clean up the response to extract just the JSON part
        # First, try to find JSON between triple backticks

        json_match = re.search(r"```(?:json)?(.*?)```", response_text, re.DOTALL)

        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # If no code blocks, try to extract anything that looks like JSON
            # Find the first { and the last }
            start = response_text.find("{")
            end = response_text.rfind("}")

            if start != -1 and end != -1 and end > start:
                json_str = response_text[start : end + 1].strip()
            else:
                # If all else fails, use the whole response
                json_str = response_text.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from response: %s", e)
            logger.debug("Response text: %s", response_text)
            raise ValueError(f"Could not extract valid JSON from Gemini response: {e}") from e
