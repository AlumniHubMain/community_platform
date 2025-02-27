import sys

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from loguru import logger


def setup_logger():
    """Configure loguru logger"""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    logger.add(
        "logs/notifications.log",
        rotation="100 MB",
        retention="14 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )


def setup_logging_middleware(app: FastAPI):
    """Add logging middleware to FastAPI app"""

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        try:
            response = await call_next(request)
            logger.info(f"{request.method} {request.url.path} - {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"Request failed: {request.method} {request.url.path} - {str(e)}")
            raise


def setup_exception_handlers(app: FastAPI):
    """Add exception handlers to FastAPI app"""

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )
