"""
API router for other services.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from common_db.db_abstract import db_manager

from vacancies.app.data_extractor.structure_vacancy import VacancyStructure as DTOVacancy

from web_gateway.other.manager import VacancyManager

# Настройка логгера для модуля
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/other", tags=["other"])


@router.get("/vacancy/{url}", response_model=DTOVacancy)
async def get_vacancy_by_url(
    url: str,
    session: Annotated[AsyncSession, Depends(db_manager.get_session)]
) -> DTOVacancy:
    """
    Get vacancy by URL.
    
    Args:
        url: Vacancy URL
        session: Database session
        
    Returns:
        Vacancy structure
        
    Raises:
        HTTPException: If vacancy not found or there was an error
    """
    try:
        logger.info("Processing request to get vacancy by URL", extra={"url": url})
        vacancy = await VacancyManager.get_by_url(url, session)
        
        if not vacancy:
            logger.warning("Vacancy not found", extra={"url": url})
            raise HTTPException(status_code=404, detail="Vacancy not found")
            
        logger.info("Vacancy found, returning data", extra={"url": url})
        return DTOVacancy.model_validate(vacancy)
        
    except Exception as e:
        # Логируем ошибку для себя
        logger.error("Error processing request", extra={"url": url, "error": str(e)})
        # Для всех ошибок возвращаем 500
        raise HTTPException(status_code=500, detail="Internal server error")