"""
API router for other services.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from common_db.db_abstract import db_manager

from vacancies.app.data_extractor.structure_vacancy import VacancyStructure as DTOVacancy

from web_gateway.other.manager import VacancyManager

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
        HTTPException: If vacancy not found
    """
    vacancy = await VacancyManager.get_by_url(url)
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    return DTOVacancy.model_validate(vacancy)