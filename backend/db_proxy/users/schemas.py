from __future__ import annotations

from typing import List

from pydantic import BaseModel


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


class SUserProfileUpdate(UserProfile):
    id: int


class SUserProfileRead(SUserProfileUpdate):
    class Config:
        from_attributes = True
