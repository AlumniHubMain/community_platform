from datetime import datetime, UTC

from pydantic import BaseModel, Field, EmailStr, model_validator
from pydantic_extra_types.timezone_name import TimeZoneName

from typing_extensions import Self

from .notification_params import type_params, DTOEmptyParams
from ..enums.notifications import ENotificationType


class DTOGeneralNotification(BaseModel):
    """General notification schema.

    This model validates that the provided parameters (params) match the expected schema
    for the given notification_type. The validation rules are:

    1. notification_type must exist in type_params dictionary
    2. if type_params[notification_type] is DTOEmptyParams, params become None
    3. for all other cases, params must be a Pydantic model that matches the schema
       defined in type_params[notification_type]

    Attributes:
        notification_type: Type of notification from ENotificationType enum
        params: Pydantic model containing notification parameters. Must match the schema
               defined in type_params for the given notification_type
        timestamp: Optional timestamp of the notification
    """
    notification_type: ENotificationType
    params: BaseModel | None = None
    timestamp: datetime | None = None

    @model_validator(mode='after')
    def check_params(self) -> Self:
        """
        Schema validator (check if the set of parameters matches the specified type)
        """
        params_schema: type[BaseModel] | None = type_params.get(self.notification_type)
        if params_schema is None:
            raise ValueError(
                f'There is no key "{self.notification_type}" in the dictionary "notification_params.type_params". '
                f'Check that you entered the notification type correctly or add it to the dictionary.')
        if params_schema is DTOEmptyParams:
            self.params = None
            return self
        if self.params is None:
            raise ValueError(f'The set of parameters (params) cannot be None for this notification type')
        try:
            params_schema(**self.params.model_dump())
        except Exception:
            raise ValueError(f'The set of parameters (params) does not correspond to the notification type.')
        return self


class DTONotifiedUserProfile(BaseModel):
    """The schema of the notified use"""
    id: int
    name: str
    surname: str
    email: EmailStr
    linkedin_link: str | None = None
    telegram_name: str | None = None
    telegram_id: int | None = None
    is_tg_bot_blocked: bool | None = Field(default=None, exclude=True)
    timezone: TimeZoneName | None = Field(default=None, exclude=True)
    is_tg_notify: bool | None = Field(default=None, exclude=True)
    is_email_notify: bool | None = Field(default=None, exclude=True)
    is_push_notify: bool | None = Field(default=None, exclude=True)


class DTOUserNotification(DTOGeneralNotification):
    """The schema of the prepared notification"""
    user: DTONotifiedUserProfile
    timestamp: datetime = datetime.now(UTC)
