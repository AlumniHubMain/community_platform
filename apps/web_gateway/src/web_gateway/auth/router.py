from typing import Annotated

from fastapi import (
    Depends,
    APIRouter,
    Request,
    Response,
    HTTPException,
)
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from common_db.db_abstract import db_manager

from web_gateway.users.user_profile_manager import UserProfileManager
from web_gateway.settings import settings
from .security import (
    create_access_token,
    create_refresh_token,
    validate_telegram_widget,
    validate_telegram_miniapp,
    TOKEN_EXPIRY_SECONDS,
)

import os

if os.getenv("env") == "staging":
    BOT_NAME = "yndx_coffee_staging_bot"
else:
    BOT_NAME = "yndx_cofee_bot"


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
                data-telegram-login="{BOT_NAME}" 
                data-size="large" 
                data-radius="10" 
                data-auth-url="{request.base_url}/auth/telegram/widget/token"
                data-request-access="write">
        </script>
        <script type="text/javascript">
          function onTelegramAuth(user) {{
            alert('Logged in as ' + user.first_name + ' ' + user.last_name + ' (' + user.id + (user.username ? ', @' + user.username : '') + ')');
          }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=login_page_content)


async def token_response(session: AsyncSession, telegram_id, response: Response):
    user_id = await UserProfileManager.get_user_id_by_telegram_id(session, telegram_id)

    if not user_id:
        raise HTTPException(status=404)

    user_data = {"user_id": user_id, "telegram_id": telegram_id}
    if user_data:
        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_id)
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
            "refresh_token": refresh_token,
        }


@router.get("/telegram/widget/token")
async def telegram_widget_token(
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(db_manager.get_session)],
):
    data = dict(request.query_params)
    if data := validate_telegram_widget(data):
        telegram_id = data.id
        return await token_response(session, telegram_id, response)

    raise HTTPException(status_code=401, detail="Authentication failed")


@router.post("/telegram/miniapp/token")
async def telegram_miniapp_token(
    auth: str,
    response: Response,
    session: Annotated[AsyncSession, Depends(db_manager.get_session)],
):
    if data := validate_telegram_miniapp(auth):
        telegram_id = data.user.id
        return await token_response(session, telegram_id, response)

    raise HTTPException(status_code=401, detail="Authentication failed")


@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


if settings.environment == "dev":

    @router.get("/dev/token")
    async def dev_token(
        telegram_id: int,
        telegram_bot_token: str,
        response: Response,
        session: Annotated[AsyncSession, Depends(db_manager.get_session)],
    ):
        from .security import BOT_TOKEN

        if telegram_bot_token == BOT_TOKEN:
            return await token_response(session, telegram_id, response)
        raise HTTPException(status_code=401, detail="Authentication failed")
