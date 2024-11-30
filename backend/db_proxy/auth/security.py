import os
from datetime import timedelta, datetime
from common_db.config import settings
from typing import Optional

from fastapi import Request, Depends, HTTPException
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
    telegram_id = user_data.get("telegram_id")
    # TODO (anemirov) return is_telegram_id_in_whitelist(telegram_id) или что-то более сложное с user_data
    return bool(telegram_id)


async def authorize(request: Request):
    unauthorized_exception = HTTPException(status_code=401, detail="Unathorized")
    
    header = request.headers.get("Authorization")
    cookie = request.cookies.get("access_token")
    if header:
        try:
            token = header.split()[1]
        except IndexError:
            logger.warning("Malformed Authorization header")
            raise unauthorized_exception
    elif cookie:
        token = cookie
    else:
        logger.warning("Authorization token missing")
        raise unauthorized_exception

    try:
        user_data = jwt.decode(token, ACCESS_SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise unauthorized_exception
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        raise unauthorized_exception
    except Exception as e:
        logger.warning("Token decoding error: {str(e)}")
        raise unauthorized_exception

    if not check_autorization(user_data):
        logger.warning("Unauthorized user")
        raise unauthorized_exception


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(seconds=TOKEN_EXPIRY_SECONDS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, ACCESS_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_telegram_id(telegram_id: str):
    user_data = {}
    # TODO (anemirov) user_data = get_user_data_from_db(telegram_id)
    user_data["telegram_id"] = telegram_id
    return user_data


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
