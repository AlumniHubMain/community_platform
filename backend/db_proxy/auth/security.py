import os
from datetime import timedelta, datetime
from common_db.config import settings
from typing import Optional, Annotated

from fastapi import Request, Depends, HTTPException, Cookie, Header
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import jwt
import hashlib
import hmac
import logging



logger = logging.getLogger(__name__)
ACCESS_SECRET_KEY = None
BOT_TOKEN = None

try:
    with open(settings.access_secret_file) as f:
        ACCESS_SECRET_KEY = f.read()
except Exception as e:
    logger.critical(f"Unable to read access secret file {settings.access_secret_file}")
    raise

try:
    with open(settings.bot_token_file) as f:
        BOT_TOKEN = f.read()
except Exception as e:
    logger.critical(f"Unable to read telegram token file {settings.bot_token_file}")
    raise

ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 3600  # 1 hour


class TelegramUser(BaseModel):
    id: str
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: Optional[str] = None
    hash: str


def check_autorization(user_data: dict) -> bool:
    telegram_id = user_data.get("user_id")
    # TODO (anemirov) return is_telegram_id_in_whitelist(telegram_id) или что-то более сложное с user_data
    if not telegram_id:
        logger.warning("Unauthorized user")
        raise HTTPException(status_code=401)


async def get_access_token(
    access_token: str = Cookie(None, include_in_schema=False), 
    authorization: str = Header(None, include_in_schema=False)
) -> str:
    if access_token:
        return access_token
    BEARER_PREFIX = "Bearer "
    if authorization and authorization.startswith(BEARER_PREFIX):
        return authorization[len(BEARER_PREFIX):]

    logger.warning("Authorization token missing")
    raise HTTPException(status_code=401)


def decode_token(token):
    try:
        token_data = jwt.decode(token, ACCESS_SECRET_KEY, algorithms=["HS256"])
    except Exception as e:
        match e:
            case jwt.ExpiredSignatureError:
                logger.warning("Token expired")
            case jwt.InvalidTokenError:
                logger.warning("Invalid token")
            case jwt.DecodeError:
                logger.warning("Token decoding error")
            case _:
                logger.warning(f"Undexpected token decoding error: {str(e)}")
        raise HTTPException(status_code=401)
    return token_data
    


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(seconds=TOKEN_EXPIRY_SECONDS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, ACCESS_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def validate_telegram_data(data: TelegramUser) -> bool:
    """
    https://core.telegram.org/widgets/login#checking-authorization
    """
    if not data:
        return False

    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    data_check_string = "\n".join(sorted(f"{key}={value}" for key, value in data.dict(exclude={"hash"}).items() if value))

    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(calculated_hash, data.hash)


async def get_user_roles(user_id: str) -> list[str]:
    return []


async def current_user_id(token: Annotated[str, Depends(get_access_token)]) -> int:
    token_data = decode_token(token)
    return int(token_data.get("user_id"))
    

async def owner_or_admin(
    user_id: int,
    current_user_id: int = Depends(current_user_id),
    roles: list[str] = Depends(get_user_roles),
) -> int:
    if "admin" in roles:
        return current_user_id
    if user_id == current_user_id:
        return current_user_id

    raise HTTPException(status_code=403)

async def authorize(user_id = Depends(current_user_id)):
    assert user_id is not None 