# app/services/answer_service.py

import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Answer
from app.utils.logger import get_logger

logger = get_logger(__name__)

_BOOLEAN_TRUE = {"yes", "y", "true", "t", "1"}
_BOOLEAN_FALSE = {"no", "n", "false", "f", "0"}

_NUMERIC_RE = re.compile(r"^[+-]?\d+(\.\d+)?$")  # pure number


def _split_answer_value(raw) -> Tuple[Optional[str], Optional[Decimal], Optional[bool]]:
    """
    Decide whether the raw answer should go into text_value, numeric_value or boolean_value.
    Returns (text_value, numeric_value, boolean_value).
    """
    if raw is None:
        return None, None, None

    # If frontend somehow sends real bool, handle that directly
    if isinstance(raw, bool):
        return None, None, raw

    s = str(raw).strip()
    if not s:
        return None, None, None

    low = s.lower()

    # boolean?
    if low in _BOOLEAN_TRUE:
        return None, None, True
    if low in _BOOLEAN_FALSE:
        return None, None, False

    # numeric? only if it is a clean number, not "2-3 years" etc.
    if _NUMERIC_RE.match(s):
        try:
            return None, Decimal(s), None
        except Exception:
            # fall back to text if Decimal fails for some reason
            pass

    # otherwise treat as text
    return s, None, None


async def create_answers_bulk(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    raw_questions: Iterable[dict],
) -> List[Answer]:
    """
    Take the `questions` list from the /generation/ask payload and create answer rows.

    Expects each item `q` in raw_questions to roughly look like:
      {
        "id": "<question_uuid>",
        "text": "...",
        "answer": "Yes",
        "score": 0,
        "selected_option_id": "<option_uuid>"   # optional, frontend can add this
      }
    """

    created: List[Answer] = []
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    for q in raw_questions:
        # --- question id ---
        raw_qid = q.get("id")
        try:
            question_id = uuid.UUID(str(raw_qid))
        except Exception:
            logger.warning("Skipping question without valid UUID id: %s", q)
            continue

        # --- selected option id (optional) ---
        selected_option_id = None
        raw_opt_id = q.get("selected_option_id")
        if raw_opt_id:
            try:
                selected_option_id = uuid.UUID(str(raw_opt_id))
            except Exception:
                logger.warning(
                    "Invalid selected_option_id for question %s: %s",
                    question_id,
                    raw_opt_id,
                )

        # --- answer value ---
        raw_answer = q.get("answer")
        text_value, numeric_value, boolean_value = _split_answer_value(raw_answer)

        db_answer = Answer(
            answer_id=uuid.uuid4(),
            project_id=project_id,
            question_id=question_id,
            selected_option_id=selected_option_id,
            answered_by_user_id=user_id,
            text_value=text_value,
            numeric_value=numeric_value,
            boolean_value=boolean_value,
            answered_at=now,
        )

        session.add(db_answer)
        created.append(db_answer)

    if created:
        await session.flush()
        logger.info(
            "Stored %d answers for project %s and user %s",
            len(created),
            project_id,
            user_id,
        )
    else:
        logger.info(
            "No answers stored for project %s and user %s (empty/invalid questions list)",
            project_id,
            user_id,
        )

    return created


-------

from app.services.answer_service import create_answers_bulk

# questions already extracted from `data`
await create_answers_bulk(
    session=session,
    project_id=project.project_id,
    user_id=user_id,
    raw_questions=questions,
)


