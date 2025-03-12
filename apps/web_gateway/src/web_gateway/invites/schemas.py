from pydantic import BaseModel


class InviteCodeResponse(BaseModel):
    code: str
