from .base import TimestampedSchema


class LinkedInProfile(TimestampedSchema):
    user_id: int
    profile_url: str
    email: str | None = None
    headline: str | None = None
    location_name: str | None = None
    industry: str | None = None
    summary: str | None = None
    experience: list[dict] | None = None
    education: list[dict] | None = None
    languages: list[dict] | None = None
    skills: dict | None = None
    connections: dict | None = None


class SLinkedInProfileRead(LinkedInProfile):
    class Config:
        from_attributes = True
