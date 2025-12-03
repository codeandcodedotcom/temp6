# src/app/db/services/add_options_data.py
"""
Script to add question option rows into the DB.

Expectations:
- A function `prepare_options()` will be available in `src.data.prepare_data`
  that returns a list of option dicts with keys:
    - option_id
    - question_id
    - option_key
    - option_text
    - option_score
    - order_index

Usage:
- Run from project root:
    python -m src.app.db.services.add_options_data
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Iterable

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

# Adjust these imports if your working import path differs.
from src.app.db.session_new import AsyncSessionLocal
from src.app.schemas.question_option import QuestionOption  # SQLAlchemy model

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def add_question_options(options_input: Iterable[Dict[str, Any]]):
    """
    Insert a list of option dicts into DB.

    options_input may be:
      - a Python list of dicts (preferred)
      - or a JSON string representing that list

    Each dict must contain keys matching the QuestionOption model.
    """
    # If input is a JSON string, parse it
    if isinstance(options_input, str):
        try:
            options_data = json.loads(options_input)
        except Exception as e:
            logger.error("Failed to parse JSON input for options: %s", e)
            raise HTTPException(status_code=400, detail="Invalid JSON input for options")
    else:
        options_data = list(options_input)

    if not isinstance(options_data, list):
        logger.error("Options input must be a list of objects.")
        raise HTTPException(status_code=400, detail="Options input must be a list")

    async with AsyncSessionLocal() as session:
        added_options = []
        try:
            for o in options_data:
                # Create model instance - ensure keys match your model definitions.
                option = QuestionOption(
                    option_id=o.get("option_id"),
                    question_id=o.get("question_id"),
                    option_key=o.get("option_key"),
                    option_text=o.get("option_text"),
                    option_score=o.get("option_score"),
                    order_index=o.get("order_index"),
                )
                session.add(option)
                added_options.append(option)

            # commit all inserts at once
            await session.commit()

            # refresh to fetch DB-populated fields (timestamps/defaults)
            for opt in added_options:
                try:
                    await session.refresh(opt)
                except Exception:
                    # non-fatal: continue but log
                    logger.debug("Could not refresh option: %s", getattr(opt, "option_id", None))

            logger.info("Inserted %d option(s) successfully.", len(added_options))
            return added_options

        except SQLAlchemyError as e:
            await session.rollback()
            logger.exception("Database error while inserting options: %s", e)
            raise HTTPException(status_code=500, detail="Database error while inserting options")
        except Exception as e:
            await session.rollback()
            logger.exception("Unexpected error while inserting options: %s", e)
            raise HTTPException(status_code=500, detail="Unexpected server error")


if __name__ == "__main__":
    # This will call prepare_options() in src.data.prepare_data.
    # Implement prepare_options() there to return the required list.
    try:
        from src.data.prepare_data import prepare_options  # user will implement
    except Exception as e:
        logger.error("Could not import prepare_options(): %s", e)
        raise

    prepared = prepare_options()
    logger.info("Prepared %d option(s) to insert.", len(prepared) if prepared else 0)

    # Run insertion
    asyncio.run(add_question_options(prepared))
