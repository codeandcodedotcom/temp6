from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session_new import get_session
from app.schemas.question_option import QuestionOption
from app.utils.logger import get_logger

router = APIRouter(prefix="/questionnaire/options", tags=["Questionnaire"])
logger = get_logger(__name__)

@router.post("/seed")
async def seed_questionnaire_options(options: list[dict], session: AsyncSession = Depends(get_session)):
    added = 0
    updated = 0

    try:
        for o in options:
            oid = o["option_id"]

            existing = await session.execute(
                select(QuestionOption).where(QuestionOption.option_id == oid)
            )
            record = existing.scalar_one_or_none()

            if record:
                record.question_id = o["question_id"]
                record.option_key = o["option_key"]
                record.option_text = o["option_text"]
                record.option_score = o["option_score"]
                record.order_index = o["order_index"]
                updated += 1
            else:
                session.add(QuestionOption(**o))
                added += 1

        await session.commit()
        return {
            "added": added,
            "updated": updated,
            "total": added + updated
        }

    except Exception:
        await session.rollback()
        logger.exception("Option seed failed")
        raise HTTPException(500, "Failed to seed options")
