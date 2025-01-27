from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Annotated

from linkedin_verifier.app.db.base import get_async_session
from linkedin_verifier.app.schemas.linkedin import ProfileResponse, LimitsResponse
from linkedin_verifier.app.db.models.limits import LinkedInApiLimits
from linkedin_verifier.app.linkedin.service import LinkedInService
from linkedin_verifier.app.linkedin.factory import LinkedInRepositoryFactory
from linkedin_verifier.config import settings
from linkedin_verifier.app.pubsub.base import PubSubClient
from linkedin_verifier.app.db.models.linkedin import LinkedInRepository

router = APIRouter()


async def get_linkedin_service(
        session: Annotated[AsyncSession, Depends(get_async_session)]
) -> LinkedInService:
    """
    Создает и возвращает сервис LinkedIn с настроенным репозиторием.
    Используется как зависимость FastAPI.
    """
    try:
        repository = await LinkedInRepositoryFactory.create(session)
        return LinkedInService(repository=repository, db=session)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize LinkedIn service: {str(e)}"
        )


@router.get("/limits", response_model=List[LimitsResponse])
async def get_limits(
        session: Annotated[AsyncSession, Depends(get_async_session)]
):
    """Get current API limits for all keys"""
    result = await session.execute(select(LinkedInApiLimits))
    limits = result.scalars().all()
    return limits


@router.post("/profile/{username}", response_model=ProfileResponse)
async def parse_profile(
    username: str,
    repository: LinkedInRepository = Depends(get_repository),
    session: AsyncSession = Depends(get_async_session)
):
    # Создаем сервис с репозиторием
    service = LinkedInService(repository=repository, db=session)
    
    # Парсим профиль
    return await service.parse_profile(username)


@router.get("/health")
async def health_check():
    """Service health check"""
    return {"status": "ok"}
