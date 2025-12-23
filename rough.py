from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session_new import get_session
from app.schemas.question import Question
from app.utils.logger import get_logger

router = APIRouter(prefix="/questionnaire", tags=["Questionnaire"])
logger = get_logger(__name__)

@router.post("/seed")
async def seed_questionnaire(questions: list[dict], session: AsyncSession = Depends(get_session)):
    added = 0
    updated = 0

    try:
        for q in questions:
            qid = q["question_id"]

            existing = await session.execute(
                select(Question).where(Question.question_id == qid)
            )
            record = existing.scalar_one_or_none()

            if record:
                record.question_text = q["question_text"]
                record.question_type = q["question_type"]
                record.order_index = q["order_index"]
                updated += 1
            else:
                session.add(Question(**q))
                added += 1

        await session.commit()
        return {
            "added": added,
            "updated": updated,
            "total": added + updated
        }

    except Exception as e:
        await session.rollback()
        logger.exception("Questionnaire seed failed")
        raise HTTPException(500, "Failed to seed questionnaire")
