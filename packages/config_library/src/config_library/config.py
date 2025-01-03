from pydantic import BaseModel


class BaseConfig(BaseModel):
    model_config = dict(validate_default=True)
