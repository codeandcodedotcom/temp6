# app/api/questionnaire.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pydantic_models import QuestionnaireResponse
from app.services.questionnaire_service import load_questionnaire_from_db
from app.db.session_new import get_db_session
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/questionnaire", response_model=QuestionnaireResponse)
async def get_questionnaire(
    session: AsyncSession = Depends(get_db_session),
) -> QuestionnaireResponse:
    """
    Return the questionnaire JSON (now built from Postgres tables).
    """
    try:
        return await load_questionnaire_from_db(session)
    except RuntimeError as e:
        logger.error("Questionnaire load error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load questionnaire")
