from enum import Enum
from sqlalchemy import Enum as PGEnum

class EFormQueryType(Enum):
    interests_chatting = "interests_chatting"
    offline_meeting = "offline_meeting"
    news_discussion = "news_discussion"
    startup_discussion = "startup_discussion"
    feedback = "feedback"
    cooperative_learning = "cooperative_learning"
    practical_discussion = "practical_discussion"
    tools_discussion = "tools_discussion"
    exam_preparation = "exam_preparation"
    help_request = "help_request"
    looking_for = "looking_for"
    mentoring = "mentoring"
    other = "other"


class EFormHelpRequestType(Enum):
    management = "management"
    product = "product"
    development = "development"
    design = "design"
    marketing = "marketing"
    sales = "sales"
    finance = "finance"
    entrepreneurship = "entrepreneurship"
    hr = "hr"
    business_development = "business_development"
    law = "law"
    other = "other"


class EFormMeetingType(Enum):
    online = "online"
    offline = "offline"
    both = "both"


class EFormLookingForType(Enum):
    work = "work"
    part_time = "part_time"
    recommendation = "recommendation"
    pet_project = "pet_project"
    mock_interview_partner = "mock_interview_partner"
    mentor = "mentor"
    mentee = "mentee"
    cofounder = "cofounder"
    contributor = "contributor"


# PostgreSQL Enum types
FormMeetingTypePGEnum = PGEnum(
    EFormMeetingType,
    name="form_meeting_type_enum",
    inherit_schema=True,
)

FormQueryTypePGEnum = PGEnum(
    EFormQueryType,
    name="form_query_type_enum",
    inherit_schema=True,
)

FormHelpRequestTypePGEnum = PGEnum(
    EFormHelpRequestType,
    name="form_help_request_type_enum",
    inherit_schema=True,
)

FormLookingForTypePGEnum = PGEnum(
    EFormLookingForType,
    name="form_looking_for_type_enum",
    inherit_schema=True,
)
