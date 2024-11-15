from typing import Literal
from sqlalchemy import ARRAY, ForeignKey, String, BIGINT, JSON
from sqlalchemy.orm import mapped_column, Mapped

from .db_abstract import ObjectTable


class ORMUserProfile(ObjectTable):
    """
    Модель таблицы (шаблон) пользователей.
    """

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)

    avatars: Mapped[list[str] | None] = mapped_column(ARRAY(String(300)))

    city_live: Mapped[str | None] = mapped_column(String(200))
    country_live: Mapped[str | None] = mapped_column(String(100))
    phone_number: Mapped[str | None] = mapped_column(String(20))
    linkedin_link: Mapped[str | None] = mapped_column(String(100))

    telegram_name: Mapped[str | None] = mapped_column(String(200))
    telegram_id: Mapped[int | None] = mapped_column(BIGINT)

    requests_to_society: Mapped[list[str] |
                                None] = mapped_column(ARRAY(String(100)))
    professional_interests: Mapped[list[str] |
                                   None] = mapped_column(ARRAY(String(100)))

class ORMLinkedInProfile(ObjectTable):
    """
    Модель таблицы (шаблон) LinkedIn profiles.
    """

    __tablename__ = "linkedin_profiles"

    user_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("users.id"), primary_key=True)

    profile_url: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String(100))

    headline: Mapped[str | None] = mapped_column(String(100))
    location_name: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(100))
    summary: Mapped[str | None] = mapped_column(String(1000))
    
    experience: Mapped[list[dict] | None] = mapped_column(ARRAY(JSON))
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
    education: Mapped[list[dict] | None] = mapped_column(ARRAY(JSON))
    # Each dict in the list has the following structure:
    # {
    #   "name": str | None        # Education name
    #   "degree": str | None          # Education degree
    #   "fos": str | None         # Education Field of study
    #   "start_date": str | None  # Start date
    #   "end_date": str | None    # End date
    #   "description": str | None # Education description
    # }
    languages: Mapped[list[dict] | None] = mapped_column(ARRAY(JSON))
    # Each dict in the list has the following structure:
    # {
    #   "name": str | None        # language name
    #   "proficiency": str | None          # language proficiency
    # }
    skills: Mapped[dict | None] = mapped_column(JSON)
    # Dict has the following structure:
    # {
    #   "skill": weight 
    # }
    connections: Mapped[dict | None] = mapped_column(JSON)
    # Dict has the following structure:
    # {
    #   "type_of_connection(twitter/tg)": link 
    # }


class ORMMeetingIntents(ObjectTable):
    """
    Модель таблицы (шаблон) LinkedIn profiles.
    """

    __tablename__ = "meeting_intents"

    user_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("users.id"))

    meeting_type: Mapped[Literal['online', 'offline', 'both']] = mapped_column(String(100))

    query_type: Mapped[
        Literal[
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
        ]] = mapped_column(String(100))
    
    help_request_type: Mapped[
        Literal[
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
        ] | None] = mapped_column(String(100))
    
    looking_for_type: Mapped[
        Literal[
            'work',
            'part_time',
            'recommendation',
            'pet_project',
            'mock_interview_partner',
            'mentor',
            'mentee',
            'cofounder',
            'contributor',
        ] | None] = mapped_column(String(100))
    
    text_intent: Mapped[str | None] = mapped_column(String(500))
    