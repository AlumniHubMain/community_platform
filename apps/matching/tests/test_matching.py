import sys
from pathlib import Path
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)
from matching.matching import process_matching_request
from matching.model.model_settings import (
    ModelType,
    FilterType,
    DiversificationType,
    HeuristicModelSettings,
    DiversificationSettings,
    FilterSettings,
)
from common_db.schemas import (
    SUserProfileRead,
    FormRead,
)
from common_db.enums.forms import (
    EFormIntentType,
    EFormMentoringHelpRequest,
    EFormConnectsMeetingFormat,
    EFormSpecialization,
    EFormSkills,
)
from common_db.enums.users import EExpertiseArea, EIndustry, EGrade, ELocation


# Test data fixtures
@pytest.fixture
def mock_users():
    """Create mock user profiles with proper enums"""
    current_time = datetime.now()

    def create_linkedin_profile(user_id: int, **kwargs) -> dict:
        """Helper to create a complete LinkedIn profile"""
        base_profile = {
            "id": user_id,
            "users_id_fk": user_id,
            # Required string fields with defaults
            "public_identifier": f"user{user_id}",
            "linkedin_identifier": f"li{user_id}",
            "member_identifier": f"member{user_id}",
            "linkedin_url": f"https://linkedin.com/in/user{user_id}",
            "first_name": kwargs.get("first_name", ""),
            "last_name": kwargs.get("last_name", ""),
            "headline": kwargs.get("headline", ""),
            "location": kwargs.get("location", ""),
            "photo_url": "",
            "background_url": "",
            "pronoun": "",
            # Required dictionary fields
            "recommendations": {},
            "certifications": {},
            # Company and position info
            "current_company_label": kwargs.get("company", ""),
            "current_company_linkedin_id": "",
            "current_position_title": kwargs.get("position", ""),
            "current_company_linkedin_url": "",
            "target_company_label": "",
            "target_company_linkedin_id": "",
            "target_position_title": "",
            "target_company_linkedin_url": "",
            # Additional fields
            "skills": kwargs.get("skills", []),
            "languages": kwargs.get("languages", []),
            "follower_count": kwargs.get("follower_count", 0),
            "summary": kwargs.get("summary", ""),
            "work_experience": kwargs.get("work_experience", []),
            "created_at": current_time,
            "updated_at": current_time,
            # Additional fields needed by predictor
            "main_location": kwargs.get("location", ""),
            "expertise_area": kwargs.get("expertise_area", []),
            "grade": kwargs.get("grade", None),
        }
        return base_profile

    return [
        SUserProfileRead(
            id=1,
            name="John",
            surname="Doe",
            email="john@example.com",
            expertise_area=[EExpertiseArea.development.value],
            industries=[EIndustry.industry1.value],
            grade=EGrade.senior.value,
            location=ELocation.moscow_russia.value,
            created_at=current_time,
            updated_at=current_time,
            specialisations=[EFormSpecialization.development__backend__python.value],
            skills=[EFormSkills.development__frontend.value],
            languages=["english", "russian"],
            current_position_title="Senior Developer",
            is_currently_employed=True,
            linkedin_profile=create_linkedin_profile(
                user_id=1,
                first_name="John",
                last_name="Doe",
                headline="Senior Developer",
                company="Tech Corp",
                position="Senior Developer",
                location=ELocation.moscow_russia.value,
                expertise_area=[EExpertiseArea.development.value],
                grade=EGrade.senior.value,
                skills=["python", "backend"],
                languages=["english", "russian"],
                follower_count=500,
                summary="Experienced developer",
                work_experience=[
                    {
                        "company": "Tech Corp",
                        "title": "Senior Developer",
                        "startEndDate": {"start": {"year": 2020, "month": 1}, "end": {"year": 2023, "month": 12}},
                        "description": "Some experience",
                    }
                ],
            ),
        ),
        SUserProfileRead(
            id=2,
            name="Jane",
            surname="Smith",
            email="jane@example.com",
            expertise_area=[EExpertiseArea.development.value],
            industries=[EIndustry.industry1.value],
            grade=EGrade.middle.value,
            location=ELocation.moscow_russia.value,
            created_at=current_time,
            updated_at=current_time,
            specialisations=[EFormSpecialization.development__backend__python.value],
            skills=[EFormSkills.development__frontend.value],
            languages=["english"],
            current_position_title="Middle Developer",
            is_currently_employed=True,
            linkedin_profile=create_linkedin_profile(
                user_id=2,
                first_name="Jane",
                last_name="Smith",
                headline="Middle Developer",
                company="Dev Inc",
                position="Middle Developer",
                location=ELocation.moscow_russia.value,
                expertise_area=[EExpertiseArea.development.value],
                grade=EGrade.middle.value,
                skills=["python", "frontend"],
                languages=["english"],
                follower_count=300,
                summary="Growing developer",
                work_experience=[
                    {
                        "company": "Dev Inc",
                        "title": "Middle Developer",
                        "startEndDate": {"start": {"year": 2021, "month": 6}, "end": None},
                        "description": "Some experience",
                    }
                ],
            ),
        ),
        SUserProfileRead(
            id=3,
            name="Bob",
            surname="Wilson",
            email="bob@example.com",
            expertise_area=[EExpertiseArea.marketing.value],
            industries=[EIndustry.industry2.value],
            grade=EGrade.junior.value,
            location=ELocation.london_uk.value,
            created_at=current_time,
            updated_at=current_time,
            specialisations=[EFormSpecialization.development__frontend__react.value],
            skills=[EFormSkills.design_ui_ux.value],
            languages=["english"],
            current_position_title="Junior Marketing Specialist",
            is_currently_employed=False,
            linkedin_profile=create_linkedin_profile(
                user_id=3,
                first_name="Bob",
                last_name="Wilson",
                headline="Marketing enthusiast",
                company="Marketing Co",
                position="Junior Marketing Specialist",
                location=ELocation.london_uk.value,
                expertise_area=[EExpertiseArea.marketing.value],
                grade=EGrade.junior.value,
                skills=["marketing", "social media"],
                languages=["english"],
                follower_count=100,
                summary="Marketing enthusiast",
                work_experience=[],
            ),
        ),
    ]


@pytest.fixture
def mock_form():
    """Create mock form with proper enums"""
    return FormRead(
        id=1,
        user_id=1,
        intent=EFormIntentType.mentoring_mentor.value,
        content={
            "meeting_format": EFormConnectsMeetingFormat.offline.value,
            "help_request": {"request": [EFormMentoringHelpRequest.process_and_teams_management.value]},
            "required_grade": [EGrade.middle.value],
            "specialization": [EFormSpecialization.development__backend__python.value],
            "is_local_community": True,
            "about": "Looking for mentoring opportunities",
            "location": ELocation.moscow_russia.value,
            "expertise_area": [EExpertiseArea.development.value],
            "grade": EGrade.senior.value,
        },
        calendar="available",
        description="Test form",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_session(mock_users, mock_form):
    """Create mock database session"""

    class MockAsyncSession:
        def __init__(self):
            self._id_counter = 1
            self._stored_objects = {}
            self.mock_users = mock_users
            self.mock_form = mock_form
            self.committed = False
            self.rolled_back = False

        def add(self, obj):
            # Fix the relationship property name
            if hasattr(obj, "requests_community"):  # Changed from requests_to_community
                obj.requests_community = []  # Initialize empty relationship
            self._stored_objects[id(obj)] = obj

        async def commit(self):
            self.committed = True
            for obj in self._stored_objects.values():
                if not hasattr(obj, "id"):
                    setattr(obj.__class__, "id", property(lambda self: self._id))
                    setattr(obj, "_id", self._id_counter)
                    self._id_counter += 1

        async def rollback(self):
            self.rolled_back = True

        async def close(self):
            pass

        async def refresh(self, obj):
            stored_obj = self._stored_objects.get(id(obj))
            if stored_obj is not None and not hasattr(stored_obj, "_id"):
                setattr(obj.__class__, "id", property(lambda self: self._id))
                setattr(stored_obj, "_id", self._id_counter)
                self._id_counter += 1

        async def execute(self, statement):
            """Enhanced execute method to handle different query types"""
            from sqlalchemy import Select, Insert, Update
            from common_db.models import (
                ORMUserProfile,
                ORMForm,
                ORMMatchingResult,
                ORMLinkedInProfile,
                ORMRequestsCommunity,
            )

            class MockResult:
                def __init__(self, results):
                    self._results = results

                def scalar_one_or_none(self):
                    return self._results[0] if self._results else None

                def scalars(self):
                    class MockScalars:
                        def __init__(self, results):
                            self._results = results

                        def all(self):
                            return self._results

                        def unique(self):
                            return self

                    return MockScalars(self._results)

            if isinstance(statement, Select):
                entity = statement.column_descriptions[0]["entity"]

                # Handle user profile queries
                if entity == ORMUserProfile:
                    # For single user query
                    if hasattr(statement, "whereclause") and statement.whereclause is not None:
                        user_id = statement.whereclause.right.value
                        matching_users = [u for u in self.mock_users if u.id == user_id]
                        return MockResult(matching_users)
                    # For all users query
                    return MockResult(self.mock_users)

                # Handle form queries
                elif entity == ORMForm:
                    if hasattr(statement, "whereclause") and statement.whereclause is not None:
                        form_id = statement.whereclause.right.value
                        if form_id == self.mock_form.id:
                            return MockResult([self.mock_form])
                        return MockResult([])
                    return MockResult([self.mock_form])

                # Handle LinkedIn profile queries
                elif entity == ORMLinkedInProfile:
                    linkedin_profiles = []
                    for user in self.mock_users:
                        if user.linkedin_profile:
                            # Create a mock ORM object with all required attributes
                            profile = MagicMock()
                            for key, value in user.linkedin_profile.items():
                                # For primitive types, just set the attribute
                                if isinstance(value, (int, str, list, dict, bool)) or value is None:
                                    setattr(profile, key, value)
                                else:
                                    # For complex objects, create a new mock with return value
                                    attr_mock = MagicMock()
                                    attr_mock.return_value = value
                                    setattr(profile, key, attr_mock)
                            # Ensure location data is properly set
                            if not hasattr(profile, "main_location"):
                                setattr(profile, "main_location", profile.location)
                            linkedin_profiles.append(profile)
                    return MockResult(linkedin_profiles)

                # Handle requests community queries
                elif entity == ORMRequestsCommunity:
                    return MockResult([])

                # Handle matching results queries
                elif entity == ORMMatchingResult:
                    matching_results = [
                        obj for obj in self._stored_objects.values() if isinstance(obj, ORMMatchingResult)
                    ]
                    return MockResult(matching_results)

            elif isinstance(statement, Insert):
                # Handle inserts
                if hasattr(statement, "parameters"):
                    entity = statement.table.name
                    if entity == "matching_results":
                        result = ORMMatchingResult(**statement.parameters)
                        self.add(result)
                        return MockResult([result])

            return MockResult([])

    class AsyncSessionContextManager:
        def __init__(self, session):
            self.session = session

        async def __aenter__(self):
            return self.session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            await self.session.close()

    def session_factory():
        return AsyncSessionContextManager(MockAsyncSession())

    return session_factory  # Return the factory function instead of the class


@pytest.fixture
def mock_data_loader(mock_users, mock_form):
    """Create mock data loader"""
    with patch("matching.data_loader.DataLoader") as mock:
        mock.get_all_user_profiles = AsyncMock(return_value=mock_users)
        mock.get_form = AsyncMock(return_value=mock_form)
        mock.get_all_linkedin_profiles = AsyncMock(return_value=[])
        yield mock


@pytest.fixture
def mock_model_settings():
    """Create mock model settings"""
    with patch("matching.matching.model_settings_presets") as mock:
        settings = HeuristicModelSettings(
            model_type=ModelType.HEURISTIC,
            settings_name="heuristic",
            rules=[
                {
                    "name": "location",
                    "type": "location",
                    "weight": 0.8,
                    "params": {"city_penalty": 0.3, "country_penalty": 0.1},
                },
                {"name": "expertise", "type": "expertise", "weight": 0.7, "params": {"base_score": 0.5}},
            ],
            filters=[],
            diversifications=[],
        )
        mock.__getitem__.return_value = settings
        mock.__contains__.return_value = True
        yield mock


@pytest.mark.asyncio
async def test_process_matching_basic(mock_session, mock_data_loader, mock_model_settings):
    """Test basic matching process"""
    match_id, predictions = await process_matching_request(
        db_session_callable=mock_session,
        psclient=None,
        logger=MagicMock(),
        user_id=1,
        form_id=1,
        model_settings_preset="heuristic",
        n=2,
        use_limits=False,
    )

    assert match_id > 0
    assert len(predictions) == 2
    assert all(isinstance(p, int) for p in predictions)


@pytest.mark.asyncio
async def test_process_matching_with_filters(mock_session, mock_data_loader):
    """Test matching process with filters"""
    with patch("matching.matching.model_settings_presets") as mock_model_settings:
        settings = HeuristicModelSettings(
            model_type=ModelType.HEURISTIC,
            settings_name="heuristic",
            rules=[],
            filters=[
                FilterSettings(
                    filter_type=FilterType.STRICT,
                    filter_name="expertise_filter",
                    filter_column="expertise_area",
                    filter_rule=EExpertiseArea.development.value,
                )
            ],
            diversifications=[],
        )
        mock_model_settings.__getitem__.return_value = settings
        mock_model_settings.__contains__.return_value = True

        match_id, predictions = await process_matching_request(
            db_session_callable=mock_session,
            psclient=None,
            logger=MagicMock(),
            user_id=1,
            form_id=1,
            model_settings_preset="heuristic",
            n=5,
            use_limits=False,
        )

        assert 3 not in predictions  # User 3 should be filtered out (marketing expertise)


@pytest.mark.asyncio
async def test_process_matching_with_diversification(
    mock_session,
    mock_data_loader,
    mock_model_settings,
):
    """Test matching process with diversification"""
    # Modify the mock settings to use diversification
    mock_model_settings.__getitem__.return_value.diversifications = [
        DiversificationSettings(
            diversification_type=DiversificationType.PROPORTIONAL,
            diversification_name="industry_div",
            diversification_column="industries",
            diversification_value=2,
        )
    ]

    match_id, predictions = await process_matching_request(
        db_session_callable=mock_session,
        psclient=None,
        logger=MagicMock(),
        user_id=1,
        form_id=1,
        model_settings_preset="heuristic",
        n=3,
        use_limits=False,
    )

    assert len(predictions) <= 3
    # Should include at least one user from a different industry for diversity
    assert any(uid in predictions for uid in [2, 3])


@pytest.mark.asyncio
async def test_process_matching_error_handling(
    mock_session,
    mock_data_loader,
    mock_model_settings,
):
    """Test error handling in matching process"""
    with patch("matching.matching.DataLoader") as mock_dl:
        mock_dl.get_all_user_profiles.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await process_matching_request(
                db_session_callable=mock_session,  # Pass the factory function directly
                psclient=None,
                logger=MagicMock(),
                user_id=1,
                form_id=1,
                model_settings_preset="heuristic",
                n=2,
            )


@pytest.mark.asyncio
async def test_process_matching_invalid_preset(
    mock_session,
    mock_data_loader,
):
    """Test handling of invalid model preset"""
    with pytest.raises(ValueError, match="Invalid model settings preset"):
        await process_matching_request(
            db_session_callable=mock_session,
            psclient=None,
            logger=MagicMock(),
            user_id=1,
            form_id=1,
            model_settings_preset="invalid_preset",
            n=2,
        )


@pytest.mark.asyncio
async def test_process_matching_with_filters_context_manager(mock_session, mock_data_loader):
    """Test matching process with strict filters"""
    with patch("matching.matching.model_settings_presets") as mock_model_settings:
        # Create settings with explicit filter
        settings = HeuristicModelSettings(
            model_type=ModelType.HEURISTIC,
            settings_name="heuristic",
            rules=[],
            filters=[
                FilterSettings(
                    filter_type=FilterType.STRICT,
                    filter_name="expertise_filter",
                    filter_column="expertise_area",
                    filter_rule=EExpertiseArea.development.value,
                )
            ],
            diversifications=[],
        )
        mock_model_settings.__getitem__.return_value = settings
        mock_model_settings.__contains__.return_value = True

        match_id, predictions = await process_matching_request(
            db_session_callable=mock_session,
            psclient=None,
            logger=MagicMock(),
            user_id=1,
            form_id=1,
            model_settings_preset="heuristic",
            n=5,
        )

        assert 3 not in predictions  # User 3 should be filtered out (no development expertise)
