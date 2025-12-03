# app/services/questionnaire_service.py

from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Question, QuestionOption
from app.models.pydantic_models import QuestionnaireResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

QUESTIONNAIRE_ID = "questionnaire-v0.1"
QUESTIONNAIRE_TITLE = "Project Charter Questionnaire"


async def load_questionnaire_from_db(session: AsyncSession) -> QuestionnaireResponse:
    """
    Load questionnaire definition from the questions + question_options tables
    and return it in the same shape as questions.json.

    Returns:
        QuestionnaireResponse
    Raises:
        RuntimeError if data cannot be loaded.
    """

    # ---- 1) Load all questions, ordered ----
    try:
        stmt = select(Question).order_by(Question.order_index)
        result = await session.execute(stmt)
        questions = result.scalars().all()
    except Exception:
        logger.exception("Failed to load questions from database")
        raise RuntimeError("Failed to load questions from database")

    if not questions:
        logger.error("No questions found in database")
        raise RuntimeError("No questions found in database")

    # ---- 2) Load all options for these questions in one go ----
    question_ids: List[UUID] = [q.question_id for q in questions]

    try:
        opt_stmt = (
            select(QuestionOption)
            .where(QuestionOption.question_id.in_(question_ids))
            .order_by(QuestionOption.question_id, QuestionOption.order_index)
        )
        opt_result = await session.execute(opt_stmt)
        all_options = opt_result.scalars().all()
    except Exception:
        logger.exception("Failed to load question options from database")
        raise RuntimeError("Failed to load question options from database")

    # Group options by question_id
    options_by_question: Dict[UUID, List[QuestionOption]] = {}
    for opt in all_options:
        options_by_question.setdefault(opt.question_id, []).append(opt)

    # ---- 3) Build questions list in the JSON shape ----
    questions_payload: List[Dict[str, Any]] = []

    for q in questions:
        q_options = options_by_question.get(q.question_id, [])

        options_payload = [
            {
                "id": str(opt.option_id),
                "label": opt.option_text,
                "score": opt.option_score,
                "option_key": opt.option_key or "NA",
                "order_index": opt.order_index,
            }
            for opt in q_options
        ]

        questions_payload.append(
            {
                "id": str(q.question_id),
                "type": q.question_type,
                "text": q.question_text,
                "options": options_payload,
                "order_index": q.order_index,
            }
        )

    questionnaire = QuestionnaireResponse(
        id=QUESTIONNAIRE_ID,
        title=QUESTIONNAIRE_TITLE,
        questions=questions_payload,
    )

    logger.info(
        "Loaded questionnaire from database: %d questions, %d options",
        len(questions_payload),
        len(all_options),
    )

    return questionnaire
