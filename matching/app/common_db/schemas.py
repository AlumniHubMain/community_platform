from __future__ import annotations
from typing import Literal
from pydantic import BaseModel


class UserProfile(BaseModel):
    name: str
    surname: str
    email: str

    avatars: list[str] | None

    city_live: str | None
    country_live: str | None
    phone_number: str | None
    linkedin_link: str | None

    telegram_name: str | None
    telegram_id: int | None

    requests_to_society: list[str] | None
    professional_interests: list[str] | None


class SUserProfileRead(UserProfile):
    id: int

    class Config:
        from_attributes = True


class LinkedInProfile(BaseModel):
    user_id: int

    profile_url: str
    email: str | None

    headline: str | None
    location_name: str | None
    industry: str | None
    summary: str | None

    experience: list[dict] | None
    # Each dict in the list has the following structure:
    # {
    #   "name": str | None        # Company name
    #   "id": str | None          # Company ID
    #   "url": str | None         # Company URL
    #   "title": str | None       # Job title
    #   "start_date": str | None  # Start date
    #   "end_date": str | None    # End date
    #   "description": str | None # Role description
    #   "location": str | None    # Job location
    #   "website": str | None     # Company website
    #   "domain": str | None      # Company domain/industry
    #   "position_description": str | None # Detailed position info
    # }
    education: list[dict] | None
    # Each dict in the list has the following structure:
    # {
    #   "name": str | None        # Education name
    #   "degree": str | None          # Education degree
    #   "fos": str | None         # Education Field of study
    #   "start_date": str | None  # Start date
    #   "end_date": str | None    # End date
    #   "description": str | None # Education description
    # }
    languages: list[dict] | None
    # Each dict in the list has the following structure:
    # {
    #   "name": str | None        # language name
    #   "proficiency": str | None          # language proficiency
    # }
    skills: dict | None
    # Dict has the following structure:
    # {
    #   "skill": weight 
    # }
    connections: dict | None


class SLinkedInProfileRead(LinkedInProfile):

    class Config:
        from_attributes = True


class MeetingIntent(BaseModel):
    """
    Модель таблицы (шаблон) LinkedIn profiles.
    """

    __tablename__ = "meeting_intents"

    user_id: int

    meeting_type: Literal['online', 'offline', 'both']

    query_type: Literal[
            'interests_chatting',
            'offline_meeting',
            'news_discussion',
            'startup_discussion',
            'feedback',
            'cooperative_learning',
            'practical_discussion',
            'tools_discussion',
            'exam_preparation',
            'help_request',
            'looking_for',
            'mentoring',
            'other',
        ]
    
    help_request_type: Literal[
            'management',
            'product',
            'development',
            'design',
            'marketing',
            'sales',
            'finance',
            'enterpreneurship',
            'hr',
            'business development',
            'law',
            'other',
        ] | None
    
    looking_for_type: Literal[
            'work',
            'part_time',
            'recommendation',
            'pet_project',
            'mock_interview_partner',
            'mentor',
            'mentee',
            'cofounder',
            'contributor',
        ] | None
    
    text_intent: str | None

class SMeetingIntentRead(MeetingIntent):
    id: int

    class Config:
        from_attributes = True