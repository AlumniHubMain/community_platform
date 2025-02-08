from datetime import timedelta, datetime
from web_gateway.settings import settings
from typing import Annotated

from pydantic import BaseModel
from typing import Optional
from fastapi import Depends, HTTPException, Cookie
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
import logging
from aiogram.utils.web_app import safe_parse_webapp_init_data, WebAppInitData
from aiogram.utils.auth_widget import check_integrity
import secrets


logger = logging.getLogger(__name__)
ACCESS_SECRET_KEY = settings.secrets.access_secret
BOT_TOKEN = settings.secrets.bot_token
ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 3600  # 1 hour

ADMIN_TELEGRAM_IDS = [453529592]


def check_autorization(telegram_id: int) -> bool:
    if telegram_id not in ADMIN_TELEGRAM_IDS:
        logger.warning("Unauthorized user")
        raise HTTPException(status_code=403)


async def get_access_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
    access_token: str = Cookie(None, include_in_schema=False),
) -> str:
    if credentials:
        return credentials.credentials
    elif access_token:
        return access_token
    logger.warning("Authorization token missing")
    raise HTTPException(status_code=401)


def decode_token(token):
    try:
        token_data = jwt.decode(token, ACCESS_SECRET_KEY, algorithms=["HS256"])
    except Exception as e:
        match e:
            case jwt.exceptions.ExpiredSignatureError:
                logger.warning("Token expired")
            case jwt.exceptions.InvalidTokenError:
                logger.warning("Invalid token")
            case jwt.exceptions.DecodeError:
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


def create_refresh_token(user_id):
    # TODO писать refresh в БД
    return secrets.token_urlsafe(32)


class TelegramWidgetData(BaseModel):
    id: int
    first_name: str
    hash: str
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: Optional[datetime] = None


def validate_telegram_widget(data) -> TelegramWidgetData | bool:
    if check_integrity(BOT_TOKEN, data):
        return TelegramWidgetData.model_validate(data)
    return False


def validate_telegram_miniapp(init_string) -> WebAppInitData | bool:
    try:
        return safe_parse_webapp_init_data(BOT_TOKEN, init_string)
    except ValueError:
        return False


async def get_user_roles(token: Annotated[str, Depends(get_access_token)]) -> list[str]:
    token_data = decode_token(token)
    return token_data.get("roles", [])


async def current_user_id(token: Annotated[str, Depends(get_access_token)]) -> int:
    token_data = decode_token(token)
    return int(token_data.get("user_id"))


async def owner_or_admin(user_id: int, token: Annotated[str, Depends(get_access_token)]) -> int:
    token_data = decode_token(token)

    if "admin" in token_data.get("roles", []):
        return user_id
    if user_id == token_data.get("user_id"):
        return user_id

    raise HTTPException(status_code=403)


async def authorize(token: Annotated[str, Depends(get_access_token)]):
    token_data = decode_token(token)

    check_autorization(token_data.get("telegram_id"))
