from pydantic import BaseModel


class AvatarData(BaseModel):
    orig: str
    webp: str
