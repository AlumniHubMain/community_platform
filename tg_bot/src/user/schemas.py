from datetime import datetime

from pydantic import BaseModel, field_validator, EmailStr
from pydantic_extra_types.country import CountryAlpha2, CountryAlpha3
from pydantic_extra_types.phone_numbers import PhoneNumber


class DTOTgBotUser(BaseModel):
    telegram_name: str | None = None
    telegram_id: int | None = None

    @field_validator('telegram_name')
    @classmethod
    def tg_names_uniformity(cls, v: str) -> str:
        """
        Валидируем телеграм ник (оставляем только непосредственно ник)
        """
        if v is not None:
            return v.split("/")[-1].replace("@", "").strip().casefold()


class DTOTgBotUserUpdate(DTOTgBotUser):
    id: int


class DTOTgBotUserRead(DTOTgBotUserUpdate):
    name: str | None = None
    surname: str | None = None
    city_live: str | None
    country_live: CountryAlpha2 | CountryAlpha3 | str | None = None
    email: EmailStr | str | None = None
    phone_number: PhoneNumber | str | None = None
    linkedin_link: str | None
    requests_to_society: list[str] | None = None
    professional_interests: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    def appeal(self) -> str:
        return self.name if self.name else self.telegram_name
