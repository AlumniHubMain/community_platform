from __future__ import annotations

from pydantic import BaseModel

from typing import List


class UserProfile(BaseModel):
    name: str
    surname: str
    email: str

    avatars: List[str] | None

    city_live: str | None
    country_live: str | None
    phone_number: str | None
    linkedin_link: str | None

    telegram_name: str | None
    telegram_id: int | None

    requests_to_society: List[str] | None
    professional_interests: List[str] | None


class SUserProfileRead(UserProfile):
    id: int

    class Config:
        from_attributes = True
