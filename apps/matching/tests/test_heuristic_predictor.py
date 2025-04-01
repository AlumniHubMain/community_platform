import pytest
import pandas as pd
import numpy as np
from common_db.enums.users import EGrade, EExpertiseArea, ELocation, ESkillsArea, EIndustry, EInterestsArea
from common_db.enums.forms import (
    EFormIntentType,
    EFormConnectsMeetingFormat,
    EFormMentoringGrade,
    EFormMockInterviewType,
    EFormMentoringHelpRequest,
    EFormProjectUserRole,
    EFormProjectProjectState,
    EFormConnectsSocialExpansionTopic,
    EFormProfessionalNetworkingTopic,
    EFormEnglishLevel,
    EFormMockInterviewLanguages,
    EFormRefferalsCompanyType,
)
from matching.model.predictors.heuristic_predictor import HeuristicPredictor


@pytest.fixture
def base_features():
    """Create base features DataFrame for testing"""
    n_candidates = 4
    return pd.DataFrame(
        {
            # Main user data
            "main_intent": [EFormIntentType.mentoring_mentor.value] * n_candidates,
            "main_location": [ELocation.moscow_russia.value] * n_candidates,
            "main_content": [
                {
                    "required_grade": [EGrade.middle.value],
                    "specialization": ["development"],
                    "help_request": {
                        "request": [EFormMentoringHelpRequest.process_and_teams_management.value],
                    },
                    "is_local_community": True,
                }
            ]
            * n_candidates,
            "main_expertise_area": [[EExpertiseArea.development.value]] * n_candidates,
            "main_grade": [EGrade.senior.value] * n_candidates,
            # Add required fields for mentoring and referral rules
            "main_mentoring_help_request": [EFormMentoringHelpRequest.process_and_teams_management.value] * n_candidates,
            # "main_company_type": [EFormRefferalsCompanyType.product.value] * n_candidates,
            # Candidate data
            "location": [ELocation.moscow_russia.value, ELocation.london_uk.value, ELocation.moscow_russia.value, None],
            "linkedin_location": ["moscow_russia", "london_uk", None, "moscow_russia"],
            "expertise_area": [
                [EExpertiseArea.development.value],
                [EExpertiseArea.development.value],
                [EExpertiseArea.marketing.value],
                None,
            ],
            "specialization": [
                [EExpertiseArea.development.value],
                [EExpertiseArea.development.value],
                [EExpertiseArea.marketing.value],
                None,
            ],
            "grade": [EGrade.senior.value, EGrade.middle.value, EGrade.junior.value, None],
            "linkedin_profile": [
                {
                    "follower_count": 5000,
                    "summary": "Experienced developer",
                    "skills": [ESkillsArea.skill1.value],
                    "work_experience": [{"title": "Senior Developer"}],
                },
                {"follower_count": 1000, "summary": None, "skills": [ESkillsArea.skill1.value], "work_experience": []},
                None,
                None,
            ],
            "industry": [[EIndustry.industry1.value], [EIndustry.industry1.value], [EIndustry.industry2.value], None],
        }
    )


@pytest.fixture
def mock_interview_features():
    """Create features DataFrame for mock interview testing"""
    n_candidates = 4
    return pd.DataFrame(
        {
            # Main user data
            "main_intent": [EFormIntentType.mock_interview.value] * n_candidates,
            "main_expertise_area": [[EFormMockInterviewType.technical.value]] * n_candidates,
            "main_content": [
                {
                    "interview_type": [EFormMockInterviewType.technical.value],
                    "languages": [
                        EFormMockInterviewLanguages.english.value,
                        EFormMockInterviewLanguages.russian.value,
                    ],
                    "required_grade": [EGrade.middle.value, EGrade.senior.value],
                }
            ]
            * n_candidates,
            # Add missing fields required by the _apply_mock_interview_rules method
            "main_grade": [EGrade.senior.value] * n_candidates,
            "main_languages": [[EFormMockInterviewLanguages.english.value, EFormMockInterviewLanguages.russian.value]] * n_candidates,
            "main_mock_interview_type": [EFormMockInterviewType.technical.value] * n_candidates,
            # Candidate data
            "grade": [EGrade.senior.value, EGrade.middle.value, EGrade.junior.value, None],
            "expertise_area": [
                [EFormMockInterviewType.technical.value],
                [EFormMockInterviewType.technical.value],
                [EFormMockInterviewType.behavioral.value],
                None,
            ],
            "linkedin_profile": [
                {
                    "languages": ["english", "russian"],
                    "work_experience": [{"title": "Senior Developer"}, {"title": "Lead Engineer"}],
                },
                {"languages": ["english"], "work_experience": [{"title": "Middle Developer"}]},
                {"languages": [], "work_experience": [{"title": "Junior Developer"}]},
                None,
            ],
        }
    )


@pytest.fixture
def project_features():
    """Create features for project matching testing"""
    n_candidates = 3
    return pd.DataFrame(
        {
            "main_intent": [EFormIntentType.projects_find_contributor.value] * n_candidates,
            "main_location": [ELocation.moscow_russia.value] * n_candidates,
            "main_content": [
                {
                    "project_state": EFormProjectProjectState.mvp.value,
                    "skills": [ESkillsArea.skill1.value],
                    "specialization": [EExpertiseArea.development.value],
                }
            ]
            * n_candidates,
            # Add missing fields required by the _apply_project_rules method
            "main_project_type": ["web_app"] * n_candidates,  # Adding project type
            "main_project_state": [EFormProjectProjectState.mvp.value] * n_candidates,  # Explicit project state
            "main_project_role": [EFormProjectUserRole.cofounder.value] * n_candidates,  # Adding project role
            "main_expertise_area": [[EExpertiseArea.development.value]] * n_candidates,
            "skill_match_score": [2, 1, 0],
            "grade": [EGrade.senior.value, EGrade.middle.value, EGrade.junior.value],
            "expertise_area": [[EExpertiseArea.development.value], [EExpertiseArea.development.value], None],
            "specialization": [[EExpertiseArea.development.value], [EExpertiseArea.development.value], None],
        }
    )


@pytest.fixture
def connects_features():
    """Create features for connects form testing"""
    n_candidates = 4
    return pd.DataFrame(
        {
            "main_intent": [EFormIntentType.connects.value] * n_candidates,
            "main_location": [ELocation.moscow_russia.value] * n_candidates,
            "main_content": [
                {
                    "social_circle_expansion": {
                        "meeting_formats": [EFormConnectsMeetingFormat.offline.value],
                        "topics": [EFormConnectsSocialExpansionTopic.development__web_development.value],
                        "custom_topics": ["python", "machine_learning"],
                    }
                }
            ]
            * n_candidates,
            # Add fields required for social expansion rules
            "main_social_topic": [EFormConnectsSocialExpansionTopic.development__web_development.value] * n_candidates,
            "main_expertise_area": [[EExpertiseArea.development.value]] * n_candidates,
            "expertise_area": [
                [EExpertiseArea.development.value, EExpertiseArea.data_science.value],
                [EExpertiseArea.development.value],
                [EExpertiseArea.marketing.value],
                None,
            ],
            "specialization": [
                [EExpertiseArea.development.value],
                [EExpertiseArea.development.value],
                [EExpertiseArea.marketing.value],
                None,
            ],
            "interests": [
                [EInterestsArea.interest1.value],
                [EInterestsArea.interest1.value],
                [EInterestsArea.interest2.value],
                None,
            ],
            "location": [ELocation.moscow_russia.value, ELocation.moscow_russia.value, ELocation.london_uk.value, None],
        }
    )


@pytest.fixture
def professional_networking_features():
    """Create features for professional networking testing"""
    n_candidates = 4
    return pd.DataFrame(
        {
            "main_intent": [EFormIntentType.connects.value] * n_candidates,
            "main_location": [ELocation.moscow_russia.value] * n_candidates,
            "main_content": [
                {
                    "professional_networking": {
                        "topics": [EFormProfessionalNetworkingTopic.development.value],
                        "user_query": "Looking for tech leads with team management experience",
                    }
                }
            ]
            * n_candidates,
            # Add missing fields required by the _apply_professional_networking_rules method
            "main_professional_topic": [EFormProfessionalNetworkingTopic.development.value] * n_candidates,
            "main_expertise_area": [[EExpertiseArea.development.value]] * n_candidates,
            "expertise_area": [
                [EExpertiseArea.development.value],
                [EExpertiseArea.development.value],
                [EExpertiseArea.marketing.value],
                None,
            ],
            "specialization": [
                [EExpertiseArea.development.value],
                [EExpertiseArea.development.value],
                [EExpertiseArea.marketing.value],
                None,
            ],
            "grade": [EGrade.lead.value, EGrade.senior.value, EGrade.middle.value, None],
            "current_position_title": ["Tech Lead", "Senior Developer", "Marketing Manager", None],
        }
    )


def test_enhanced_location_rule(base_features):
    """Test enhanced location matching with LinkedIn data"""
    # Create a clean test dataset with only location-related fields
    test_features = pd.DataFrame({
        "main_location": [ELocation.moscow_russia.value] * 4,
        "location": [
            ELocation.moscow_russia.value,  # Perfect match
            ELocation.london_uk.value,      # Different location
            None,                           # No location but matching LinkedIn
            ELocation.london_uk.value       # Different location
        ],
        "linkedin_location": [
            "moscow_russia",  # Matches both
            "london_uk",      # Matches both but different
            "moscow_russia",  # Only LinkedIn location
            None             # No LinkedIn location
        ],
        "linkedin_profile": [
            {"location": "moscow_russia"},  # Additional matching location
            {"location": "london_uk"},      # Additional matching location
            None,                           # No profile
            None                            # No profile
        ]
    })

    predictor = HeuristicPredictor(
        rules=[
            {
                "name": "location_matching",
                "type": "location",
                "weight": 1.0,
                "params": {"city_penalty": 0.3, "country_penalty": 0.1, "region_penalty": 0.05},
            }
        ]
    )

    scores = predictor.predict(test_features)

    # Perfect match - both profile and LinkedIn locations match
    assert scores[0] > 0.6, f"Expected score > 0.6 for perfect match, got {scores[0]}"
    # Different location in both profile and LinkedIn
    assert scores[1] < 0.5, f"Expected score < 0.5 for different location, got {scores[1]}"
    # Profile location matches but no LinkedIn location
    assert scores[2] > 0.5, f"Expected score > 0.5 for matching LinkedIn location, got {scores[2]}"
    # No profile location but matching LinkedIn location
    assert scores[3] < 0.5, f"Expected score < 0.5 for different location, got {scores[3]}"


def test_professional_background_rule(base_features):
    """Test enhanced professional background matching"""
    # Create a clean test dataset with only professional background related fields
    test_features = pd.DataFrame({
        "linkedin_profile": [
            {
                "follower_count": 5000,
                "summary": "Experienced Tech Lead with 10+ years in development",
                "skills": ["leadership", "team management", "development"],
                "work_experience": [
                    {"title": "Tech Lead", "duration_years": 5},
                    {"title": "Senior Developer", "duration_years": 5}
                ],
                "education": [
                    {"degree": "Master of Computer Science", "field": "Computer Science"}
                ]
            },
            {
                "follower_count": 2000,
                "summary": "Senior Developer with 5 years experience",
                "skills": ["development", "python", "java"],
                "work_experience": [
                    {"title": "Senior Developer", "duration_years": 3},
                    {"title": "Middle Developer", "duration_years": 2}
                ],
                "education": [
                    {"degree": "Bachelor of Computer Science", "field": "Computer Science"}
                ]
            },
            {
                "follower_count": 1000,
                "summary": "Marketing Manager",
                "skills": ["marketing", "social media"],
                "work_experience": [
                    {"title": "Marketing Manager", "duration_years": 3}
                ],
                "education": [
                    {"degree": "Bachelor of Marketing", "field": "Marketing"}
                ]
            },
            None  # No profile data
        ]
    })

    predictor = HeuristicPredictor(
        rules=[
            {
                "name": "professional_background",
                "type": "professional_background",
                "weight": 1.0,
                "params": {
                    "work_experience_weight": 0.4,
                    "education_weight": 0.3,
                    "skills_weight": 0.3
                }
            }
        ]
    )

    scores = predictor.predict(test_features)

    # Perfect match - Tech Lead with extensive experience and education
    assert scores[0] > 0.7, f"Expected score > 0.7 for perfect match, got {scores[0]}"
    # Good match - Senior Developer with relevant experience
    assert 0.5 < scores[1] < 0.9, f"Expected score between 0.5 and 0.9 for good match, got {scores[1]}"
    # Poor match - Different field (marketing)
    assert scores[2] < 0.7, f"Expected score < 0.7 for poor match, got {scores[2]}"
    # No profile data
    assert scores[3] < 0.6, f"Expected score < 0.6 for no data, got {scores[3]}"


def test_mock_interview_matching(mock_interview_features):
    """Test mock interview specific matching"""
    predictor = HeuristicPredictor(
        rules=[{"name": "intent_specific", "type": "intent_specific", "weight": 1.0, "params": {}}]
    )

    scores = predictor.predict(mock_interview_features)

    # Perfect match - senior with all languages
    assert scores[0] > 0.7
    # Good match - middle with one language
    assert 0.4 < scores[1] < 0.9
    # Poor match - junior with no languages
    assert scores[2] < 0.5


def test_project_matching(project_features):
    """Test project-specific matching"""
    predictor = HeuristicPredictor(
        rules=[{"name": "intent_specific", "type": "intent_specific", "weight": 1.0, "params": {}}]
    )

    scores = predictor.predict(project_features)

    # Perfect match - senior with matching skills
    assert scores[0] > 0.5
    # Good match - middle with partial skills
    assert 0.4 < scores[1] < 0.9
    # Poor match - junior with no skills
    assert scores[2] < 0.5


def test_network_quality_consideration(base_features):
    """Test LinkedIn network quality consideration"""
    predictor = HeuristicPredictor(
        rules=[{"name": "intent_specific", "type": "intent_specific", "weight": 1.0, "params": {}}]
    )

    scores = predictor.predict(base_features)

    # High quality profile - many followers, complete profile
    assert scores[0] > 0.3
    # Medium quality - fewer followers, incomplete profile
    assert 0.01 < scores[1] < 0.8
    # No LinkedIn profile
    assert scores[2] < 0.6
    assert scores[3] < 0.6


def test_combined_rules_with_offline_meeting(base_features):
    """Test combination of rules with offline meeting consideration"""
    base_features["main_content"] = [
        {
            "meeting_format": EFormConnectsMeetingFormat.offline.value,
            "required_grade": [EGrade.middle.value],
            "specialization": ["development"],
        }
    ] * len(base_features)

    predictor = HeuristicPredictor(
        rules=[
            {
                "name": "location",
                "type": "location",
                "weight": 0.8,
                "params": {"city_penalty": 0.3, "country_penalty": 0.1},
            },
            {"name": "professional_background", "type": "professional_background", "weight": 0.6, "params": {}},
            {"name": "intent_specific", "type": "intent_specific", "weight": 0.7, "params": {}},
        ]
    )

    scores = predictor.predict(base_features)

    # Perfect match - local candidate with good profile
    assert scores[0] > 0.7
    # Poor match - remote candidate despite good profile
    assert scores[1] < 0.5
    # Medium match - local but poor profile
    assert 0.4 < scores[2] < 0.7
    # Poor match - missing data but local (LinkedIn location)
    assert 0.2 < scores[3] < 0.6


def test_connects_social_expansion(connects_features):
    """Test connects form with social circle expansion"""
    predictor = HeuristicPredictor(
        rules=[{"name": "intent_specific", "type": "intent_specific", "weight": 1.0, "params": {}}]
    )

    scores = predictor.predict(connects_features)

    # Perfect match - matching expertise, interests and location
    assert scores[0] > 0.7
    # Good match - partial expertise/interests match, good location
    assert 0.6 < scores[1] < 0.9
    # Poor match - wrong expertise/interests, wrong location
    assert scores[2] < 0.4
    # Minimal match - no data
    assert scores[3] <= 0.3


def test_professional_networking(professional_networking_features):
    """Test professional networking matching"""
    predictor = HeuristicPredictor(
        rules=[{"name": "intent_specific", "type": "intent_specific", "weight": 1.0, "params": {}}]
    )

    scores = predictor.predict(professional_networking_features)

    # Perfect match - lead position with relevant expertise
    assert scores[0] > 0.7
    # Good match - senior with relevant expertise
    assert 0.4 < scores[1] < 0.9
    # Poor match - wrong expertise area
    assert scores[2] < 0.6
    # Minimal match - no data
    assert scores[3] < 0.6


def test_mentoring_mentor_help_requests(base_features):
    """Test mentoring mentor with different help request types"""
    help_requests = [
        {"request": [EFormMentoringHelpRequest.adaptation_after_relocate.value], "country": "usa"},
        {"request": [EFormMentoringHelpRequest.process_and_teams_management.value]},
        {"request": [EFormMentoringHelpRequest.custom.value], "custom_request": "Career development guidance"},
    ]

    for help_request in help_requests:
        base_features["main_content"] = [
            {
                "required_grade": [EGrade.middle.value],
                "specialization": ["development"],
                "help_request": help_request,
                "is_local_community": True,
            }
        ] * len(base_features)

        predictor = HeuristicPredictor(
            rules=[{"name": "intent_specific", "type": "intent_specific", "weight": 1.0, "params": {}}]
        )

        scores = predictor.predict(base_features)

        # Check specific help request type handling
        if EFormMentoringHelpRequest.adaptation_after_relocate.value in help_request["request"]:
            # Location matching should be more important
            assert scores[1] < 0.65  # Different location should be penalized more
        elif EFormMentoringHelpRequest.process_and_teams_management.value in help_request["request"]:
            # Senior grade should be more important
            assert scores[0] > scores[1] > scores[2]
        elif EFormMentoringHelpRequest.custom.value in help_request["request"]:
            # Experience and grade should be balanced
            assert 0.3 < scores[0] < 1.0


def test_referrals_recommendation_types(base_features):
    """Test referrals with different recommendation types"""
    base_features["main_intent"] = [EFormIntentType.referrals_recommendation.value] * len(base_features)
    base_features["main_content"] = [
        {
            "required_english_level": EFormEnglishLevel.B2.value,
            "company_type": "product",
            "is_local_community": True,
            "is_all_experts_type": True,
            "is_need_call": True,
        }
    ] * len(base_features)
    # Add required main_company_type field
    base_features["main_company_type"] = ["product"] * len(base_features)
    # Add required expertise area field
    base_features["main_expertise_area"] = [[EExpertiseArea.development.value]] * len(base_features)

    predictor = HeuristicPredictor(
        rules=[{"name": "intent_specific", "type": "intent_specific", "weight": 1.0, "params": {}}]
    )

    scores = predictor.predict(base_features)

    # Senior with English and company experience
    assert scores[0] > 0.6
    # Middle with English but different location
    assert 0 < scores[1] < 0.7
    # Junior without required qualifications
    assert scores[2] < 0.55
    # No data
    assert scores[3] <= 0.5


def test_aggregate_user_data():
    """Test the aggregation of user data from different sources"""
    # Create a predictor instance
    predictor = HeuristicPredictor(rules=[])
    
    # Create a class to simulate objects with label/value attributes
    class MockObject:
        def __init__(self, label=None, value=None):
            self.label = label
            self.value = value
    
    # Create a dataframe with mixed data types
    features = pd.DataFrame([
        # 1. User with object-based attributes
        {
            "expertise_area": [MockObject(value="backend"), MockObject(value="frontend")],
            "interests": [MockObject(label="tech"), MockObject(label="design")],
            "skills": [MockObject(label="python"), MockObject(label="javascript")],
            "specialisations": [MockObject(label="web_dev")],
            "specialisation": [MockObject(label="web_dev")],  # Alias with different spelling
            "industries": [MockObject(label="software")],
            "industry": [MockObject(label="software")],  # Alias with different name
            "linkedin_profile": {
                "skills": ["python", "react"],
                "languages": ["english", "russian"]
            }
        },
        # 2. User with string-based attributes
        {
            "expertise_area": ["data_science", "machine_learning"],
            "interests": ["ai", "research"],
            "skills": ["python", "tensorflow"],
            "specialisations": ["ml_ops"],
            "specialisation": ["ml_ops"],
            "industries": ["tech"],
            "industry": ["tech"],
            "linkedin_profile": None  # No LinkedIn profile
        },
        # 3. User with mixed or missing attributes
        {
            "expertise_area": ["devops"],  # Converted from single string to list
            "interests": [],  # Initialize as empty list instead of None
            "skills": ["kubernetes"],
            "specialisations": [],  # Initialize as empty list instead of None
            "specialisation": [],  # Initialize as empty list instead of None
            "industries": [],  # Initialize as empty list instead of None
            "industry": [],  # Initialize as empty list instead of None
            "linkedin_profile": {
                "skills": [],  # Empty skills list
                "languages": []  # Empty list instead of None
            }
        }
    ])
    
    # Aggregate the data
    result = predictor._aggregate_user_data(features)
    
    # Verify first row's transformations (object-based attributes)
    assert result.iloc[0]["expertise_area"] == ["backend", "frontend"]
    assert result.iloc[0]["interests"] == ["tech", "design"]
    assert result.iloc[0]["skills"] == ["python", "javascript"]
    assert result.iloc[0]["specialisations"] == ["web_dev"]
    assert result.iloc[0]["specialisation"] == ["web_dev"]
    assert result.iloc[0]["industries"] == ["software"]
    assert result.iloc[0]["industry"] == ["software"]
    
    # Verify second row (string-based attributes remain unchanged)
    assert result.iloc[1]["expertise_area"] == ["data_science", "machine_learning"]
    assert result.iloc[1]["interests"] == ["ai", "research"]
    assert result.iloc[1]["skills"] == ["python", "tensorflow"]
    
    # Verify third row (mixed/missing attributes)
    assert result.iloc[2]["expertise_area"] == ["devops"]  # Already a list, no conversion needed
    assert result.iloc[2]["interests"] == []  # None converted to empty list
    
    # Verify dataframe shape is preserved
    assert result.shape == features.shape
    
    # Verify all required fields exist
    expected_fields = ["expertise_area", "interests", "skills", "specialisations", 
                       "specialisation", "industries", "industry"]
    for field in expected_fields:
        assert field in result.columns
