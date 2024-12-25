from pydantic import BaseModel


class EnumValues(BaseModel):
    values: list[str]
