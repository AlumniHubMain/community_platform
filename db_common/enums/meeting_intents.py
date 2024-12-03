from enum import Enum
from sqlalchemy import Enum as PGEnum

class EMeetingIntentQueryType(Enum):
    interests_chatting = 'interests_chatting'
    offline_meeting = 'offline_meeting'
    news_discussion = 'news_discussion'
    startup_discussion = 'startup_discussion'
    feedback = 'feedback'
    cooperative_learning = 'cooperative_learning'
    practical_discussion = 'practical_discussion'
    tools_discussion = 'tools_discussion'
    exam_preparation = 'exam_preparation'
    help_request = 'help_request'
    looking_for = 'looking_for'
    mentoring = 'mentoring'
    other = 'other'

class EMeetingIntentHelpRequestType(Enum):
    management = 'management'
    product = 'product'
    development = 'development'
    design = 'design'
    marketing = 'marketing'
    sales = 'sales'
    finance = 'finance'
    entrepreneurship = 'entrepreneurship'
    hr = 'hr'
    business_development = 'business_development'
    law = 'law'
    other = 'other'

class EMeetingIntentMeetingType(Enum):
    online = 'online'
    offline = 'offline'
    both = 'both'

class EMeetingIntentLookingForType(Enum):
    work = 'work'
    part_time = 'part_time'
    recommendation = 'recommendation'
    pet_project = 'pet_project'
    mock_interview_partner = 'mock_interview_partner'
    mentor = 'mentor'
    mentee = 'mentee'
    cofounder = 'cofounder'
    contributor = 'contributor'

# PostgreSQL Enum types
MeetingIntentMeetingTypePGEnum = PGEnum(EMeetingIntentMeetingType, name='meeting_intent_meeting_type', inherit_schema=True)
MeetingIntentQueryTypePGEnum = PGEnum(EMeetingIntentQueryType, name='meeting_intent_query_type', inherit_schema=True)
MeetingIntentHelpRequestTypePGEnum = PGEnum(EMeetingIntentHelpRequestType, name='meeting_intent_help_request_type', inherit_schema=True)
MeetingIntentLookingForTypePGEnum = PGEnum(EMeetingIntentLookingForType, name='meeting_intent_looking_for_type', inherit_schema=True)
