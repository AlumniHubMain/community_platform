import logging
import os
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse


from fastapi.middleware.cors import CORSMiddleware

from auth.router import router as auth_router
from auth.security import authorize
from media_storage.router import router as mds_router
from meetings.router import router as meetings_router
from users.router import router as users_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Service started")
    yield


app = FastAPI(title="Community platform", lifespan=lifespan)


# ToDo(evseev.dmsr) уточнить, что тут нужно
origins = [
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

app.include_router(auth_router)
app.include_router(users_router, dependencies=[Depends(authorize)])
app.include_router(mds_router, dependencies=[Depends(authorize)])
app.include_router(meetings_router)


@app.get("/", response_class=HTMLResponse)
async def main_page(user=Depends(authorize)):
    main_page_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Main Page</title>
    </head>
    <body>
        <h1>MAIN PAGE</h1>
    </body>
    </html>
    """
    return HTMLResponse(content=main_page_content)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Default to 8000 if not set
    logger.info(f"Starting FastAPI application on port {port}")
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=port)
