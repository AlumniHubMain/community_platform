import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from users.router import router as users_router
from media_storage.router import router as mds_router


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Service started")
    yield


app = FastAPI(title="Community platform", lifespan=lifespan)


BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# ToDo(evseev.dmsr) уточнить, что тут нужно
origins = [
    BASE_URL,
    "http://localhost:5173",
    "https://platform-web-flax.vercel.app",
    "https://platform-web-flax.vercel.app:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(mds_router)

@app.get("/", response_class=HTMLResponse)
async def login_page():
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
                data-auth-url="{BASE_URL}/auth/callback"
                data-request-access="write"></script>
        <script type="text/javascript">
          function onTelegramAuth(user) {{
            alert('Logged in as ' + user.first_name + ' ' + user.last_name + ' (' + user.id + (user.username ? ', @' + user.username : '') + ')');
          }}
        </script>
    </body>
    </html>
    """  # TODO (anemirov) пока так, как будет фронт надо это туда утащить
    return HTMLResponse(content=login_page_content)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    user_data = request.query_params
    logger.info(f"Received user data: {user_data}")

    return {"message": "Successfully authenticated", "user": user_data}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Default to 8000 if not set
    logger.info(f"Starting FastAPI application on port {port}")
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=port)
