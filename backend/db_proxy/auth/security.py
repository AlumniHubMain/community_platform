import os
from datetime import timedelta, datetime
from typing import Optional

from fastapi import Request, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import jwt
import hashlib
import hmac

ACCESS_SECRET_KEY = os.getenv('ACCESS_SECRET_KEY')
ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 3600  # 1 hour
BOT_TOKEN = os.getenv("BOT_TOKEN")



class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: Optional[int] = None
    hash: str


def check_autorization(user_data: dict) -> bool:
    telegram_id = user_data.get("telegram_id")
    # TODO (anemirov) return is_telegram_id_in_white_list(telegram_id) или что-то более сложное с user_data
    return bool(telegram_id)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/basic_auth_for_development")


async def authorize(request: Request, token: str = Depends(oauth2_scheme)):
    header = request.headers.get('Authorization')
    cookie = request.cookies.get("access_token")

    if header:
        try:
            token = header.split()[1]
        except IndexError:
            raise HTTPException(status_code=401, detail="Malformed Authorization header")
    elif cookie:
        token = cookie
    else:
        raise HTTPException(status_code=401, detail="Authorization token missing")

    try:
        user_data = jwt.decode(token, ACCESS_SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token decoding error: {str(e)}")

    if not check_autorization(user_data):
        raise HTTPException(status_code=403, detail="Unauthorized user")


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
    user_data['telegram_id'] = telegram_id
    return user_data


def validate_telegram_data(data: TelegramUser) -> bool:
    """
    https://core.telegram.org/widgets/login#checking-authorization
    """
    if not data:
        return False
    
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(data.dict(exclude={"hash"}).items()))
    
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(calculated_hash, data.hash)


