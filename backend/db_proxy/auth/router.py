import os
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional
from fastapi import (
    Query,
    Depends,
    FastAPI,
    APIRouter,
    Request,
    Response,
    HTTPException,
)
from fastapi.security import OAuth2PasswordBearer

from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
import secrets
from .security import (
    create_access_token,
    validate_telegram_data,
    get_user_by_telegram_id,
    TelegramUser,
    TOKEN_EXPIRY_SECONDS,
)


router = APIRouter(tags=["Simple authentication and authorization"], prefix="/auth")


@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    login_page_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login with Telegram</title>
    </head>
    <body>
        <h1>Login with Telegram</h1>
        <div id="telegram-widget"></div>
        <script async src="https://telegram.org/js/telegram-widget.js?7"
                data-telegram-login="yndx_cofee_bot" 
                data-size="large" 
                data-radius="10" 
                data-auth-url="{request.base_url}/auth/callback"
                data-request-access="write"></script>
        <script type="text/javascript">
          function onTelegramAuth(user) {{
            alert('Logged in as ' + user.first_name + ' ' + user.last_name + ' (' + user.id + (user.username ? ', @' + user.username : '') + ')');
          }}
        </script>
    </body>
    </html>
    """  # TODO (anemirov) пока так с колбэком, как будет фронт надо это переделать с onTelegramAuth
    return HTMLResponse(content=login_page_content)


@router.get("/callback", response_model=dict)
async def callback(
    response: Response,
    id: int = Query(...),
    first_name: str = Query(...),
    last_name: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    photo_url: Optional[str] = Query(None),
    auth_date: Optional[int] = Query(None),
    hash: str = Query(...),
):
    telegram_data = TelegramUser(
        id=id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        photo_url=photo_url,
        auth_date=auth_date,
        hash=hash,
    )

    if validate_telegram_data(telegram_data):
        telegram_id = telegram_data.id
        user_data = get_user_by_telegram_id(telegram_id)

        if user_data:
            access_token = create_access_token(user_data)
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=True,
                samesite="lax",
            )
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": TOKEN_EXPIRY_SECONDS,
                # TODO (anemirov) Обсудить нужен ли refresh token или и так норм
            }
        else:
            raise HTTPException(status_code=404, detail="User not found")
    else:
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}
