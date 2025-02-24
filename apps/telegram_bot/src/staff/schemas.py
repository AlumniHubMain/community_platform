from pydantic import EmailStr, ConfigDict
from pydantic_extra_types.phone_numbers import PhoneNumber

from common_db.schemas.base import TimestampedSchema
from tg_bot.src.user.schemas import DTOTgBotUser
from .models import TgBotStaffRole


class DTOTgBotStaffUpdate(DTOTgBotUser):
    id: int


class DTOTgBotStaffRead(DTOTgBotStaffUpdate, TimestampedSchema):
    name: str | None = None
    surname: str | None = None
    bio: str | None = None
    email: EmailStr | str | None = None
    phone_number: PhoneNumber | str | None = None
    role: TgBotStaffRole | None = None

    def appeal(self) -> str:
        return self.name if self.name else self.telegram_name
