from sqlalchemy import String, JSON, ForeignKey, ARRAY, BIGINT
from sqlalchemy.orm import Mapped, mapped_column
from .base import ObjectTable

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
