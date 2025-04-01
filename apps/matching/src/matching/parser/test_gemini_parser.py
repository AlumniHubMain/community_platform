"""
Test script to evaluate Gemini's parsing capabilities for form content.
"""

import os
import sys
from typing import Any

from common_db.enums.forms import EFormIntentType
from common_db.schemas.forms import (
    FormConnects,
    FormMentoringMentor,
    FormMentoringMentee,
    FormReferralsRecommendation,
    FormMockInterview,
    FormProjectsFindHead,
    FormProjectPetProject,
)
from matching.parser.gemini_parser import GeminiParser


def get_schema_class(intent_type: EFormIntentType) -> type:
    """Get the corresponding schema class for the intent type."""
    schema_map = {
        EFormIntentType.connects: FormConnects,
        EFormIntentType.mentoring_mentor: FormMentoringMentor,
        EFormIntentType.mentoring_mentee: FormMentoringMentee,
        EFormIntentType.referrals_recommendation: FormReferralsRecommendation,
        EFormIntentType.mock_interview: FormMockInterview,
        EFormIntentType.projects_find_cofounder: FormProjectsFindHead,
        EFormIntentType.projects_find_contributor: FormProjectsFindHead,
        EFormIntentType.projects_pet_project: FormProjectPetProject,
    }
    return schema_map.get(intent_type)


def test_parser() -> None:
    """Test the Gemini parser with various test cases."""
    # Initialize parser
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT environment variable is required")
        sys.exit(1)
    
    try:
        parser = GeminiParser(project_id=project_id)
        parser.initialize()
    except Exception as e:
        print(f"Error initializing parser: {str(e)}")
        sys.exit(1)

    # Test cases with different intents
    test_cases = [
        {
            "name": "Social Networking",
            "text": """
            I'm looking to expand my professional network in the tech industry. 
            I'm particularly interested in connecting with senior developers and product managers.
            I prefer online meetings and would like to discuss topics like system design, 
            cloud architecture, and product strategy. I'm open to both local and remote connections.
            """,
            "expected_intent": EFormIntentType.connects,
            "expected_fields": {
                "is_local_community": bool,
                "social_circle_expansion": {
                    "meeting_formats": list,
                    "topics": list,
                    "details": str
                }
            }
        },
        {
            "name": "Mentoring Mentor",
            "text": """
            I'm a senior backend developer with 8 years of experience in Python and cloud technologies.
            I'd like to mentor junior developers who are interested in backend development.
            I can help with career growth, technical skills, and system design.
            I'm available for both online and in-person mentoring sessions.
            """,
            "expected_intent": EFormIntentType.mentoring_mentor,
            "expected_fields": {
                "is_local_community": bool,
                "required_grade": list,
                "specialization": list,
                "help_request": {
                    "request": list
                },
                "about": str
            }
        },
        {
            "name": "Mock Interview",
            "text": """
            I need help preparing for technical interviews. I'm a junior developer
            looking to practice coding interviews and system design questions.
            I have my resume ready and would prefer online sessions in English.
            I'm particularly interested in backend development roles.
            """,
            "expected_intent": EFormIntentType.mock_interview,
            "expected_fields": {
                "interview_type": list,
                "language": {
                    "langs": list
                },
                "resume": str,
                "details": str,
                "public_interview": bool
            }
        },
        {
            "name": "Project Co-founder",
            "text": """
            I have an idea for a new AI-powered productivity tool. Looking for a co-founder
            who has experience in frontend development and UI/UX design. The project is in
            the idea stage, and I have some initial wireframes ready. We'll be using React
            and Python for the implementation.
            """,
            "expected_intent": EFormIntentType.projects_find_cofounder,
            "expected_fields": {
                "project_description": str,
                "specialization": list,
                "skills": list,
                "project_state": str
            }
        },
    ]

    # Run tests
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print("=" * 80)
        print(f"Input text:\n{test_case['text']}")
        print("-" * 80)

        try:
            # Parse the text
            detected_intent, content = parser.parse_text_to_form_content(
                test_case["text"]
            )

            # Print results
            print(f"Detected intent: {detected_intent}")
            print(f"Expected intent: {test_case['expected_intent']}")
            
            # Validate intent detection
            intent_success = detected_intent == test_case["expected_intent"]
            print(f"\nIntent Detection: {'✅ Success' if intent_success else '❌ Failed'}")

            # Validate schema
            schema_class = get_schema_class(detected_intent)
            if schema_class:
                try:
                    validated_data = schema_class.model_validate(content)
                    print("\nSchema Validation: ✅ Success")
                    print("\nValidated Content:")
                    print_json(validated_data.model_dump())
                except Exception as e:
                    print(f"\nSchema Validation: ❌ Failed")
                    print(f"Validation Error: {str(e)}")
                    print("\nRaw Content:")
                    print_json(content)
            else:
                print("\nSchema Validation: ❌ Failed - No schema class found for intent")

            # Validate expected fields
            print("\nField Validation:")
            field_validation_results = validate_expected_fields(content, test_case["expected_fields"])
            for field, result in field_validation_results.items():
                print(f"{'✅' if result else '❌'} {field}")

        except Exception as e:
            print(f"\n❌ Error processing test case: {str(e)}")
            print("Stack trace:")
            import traceback
            traceback.print_exc()


def validate_expected_fields(content: dict, expected_fields: dict, prefix: str = "") -> dict[str, bool]:
    """Validate that content contains all expected fields with correct types."""
    results = {}
    
    for field, expected_type in expected_fields.items():
        full_field = f"{prefix}{field}" if prefix else field
        if field not in content:
            results[full_field] = False
            continue
            
        value = content[field]
        if isinstance(expected_type, dict):
            # Recursively validate nested structure
            nested_results = validate_expected_fields(value, expected_type, f"{full_field}.")
            results.update(nested_results)
        else:
            # Check if value is of expected type
            if expected_type == list:
                results[full_field] = isinstance(value, list)
            elif expected_type == bool:
                results[full_field] = isinstance(value, bool)
            elif expected_type == str:
                results[full_field] = isinstance(value, str)
            else:
                results[full_field] = False
                
    return results


def print_json(data: Any, indent: int = 2) -> None:
    """Pretty print JSON data with proper enum handling."""
    import json
    class EnumEncoder(json.JSONEncoder):
        def default(self, obj):
            if hasattr(obj, "value"):
                return obj.value
            return super().default(obj)
    
    print(json.dumps(data, indent=indent, cls=EnumEncoder))


if __name__ == "__main__":
    test_parser()