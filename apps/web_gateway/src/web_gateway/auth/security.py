from datetime import timedelta, datetime
from web_gateway.settings import settings
from typing import Annotated

from fastapi import Depends, HTTPException, Cookie
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
import logging
from aiogram.utils.web_app import safe_parse_webapp_init_data, WebAppInitData
from aiogram.utils.auth_widget import check_integrity
import secrets


logger = logging.getLogger(__name__)
ACCESS_SECRET_KEY = settings.access_secret_file
BOT_TOKEN = settings.bot_token_file

ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 3600  # 1 hour

ADMIN_TELEGRAM_IDS = []


def check_autorization(user_data: dict) -> bool:
    telegram_id = user_data.get("user_id")
    if telegram_id in ADMIN_TELEGRAM_IDS:
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


def validate_telegram_widget(data) -> dict | bool:
    
    if check_integrity(BOT_TOKEN, data):
        res = data.copy()
        res.pop('hash')
        return res
    return False

def validate_telegram_miniapp(init_string) -> WebAppInitData | bool:
    try:
        return safe_parse_webapp_init_data(BOT_TOKEN, init_string)
    except ValueError:
        return False


async def get_user_roles(user_id: str) -> list[str]:
    if user_id in ADMIN_TELEGRAM_IDS:
        return ["admin"]
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
