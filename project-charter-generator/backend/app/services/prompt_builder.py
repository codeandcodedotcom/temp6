import json
import os
from typing import Any, Dict
from app.config import Config
from app.utils.logger import get_logger

logger = get_logger(__name__)

def build_prompt(payload: Dict[str, Any], scoring_summary: str) -> str:
    """
    Build prompt string by loading the single-file template and filling placeholders:
      {frontend_json}, {scoring_summary}, {output_schema}
    """
    # serialize frontend payload
    try:
        frontend_json = json.dumps(payload or {}, indent=2, ensure_ascii=False)
    except Exception:
        frontend_json = str(payload or {})

    # load output schema
    output_schema_text = "{}"
    try:
        with open(Config.OUTPUT_SCHEMA_PATH, "r", encoding="utf-8") as fh:
            output_schema_text = fh.read()
    except Exception as e:
        logger.exception("Failed to read OUTPUT_SCHEMA_PATH=%s: %s", Config.OUTPUT_SCHEMA_PATH, e)

    # load prompt template file
    try:
        with open(Config.PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as fh:
            template = fh.read()
    except Exception as e:
        logger.exception("Failed to read PROMPT_TEMPLATE_PATH=%s: %s", Config.PROMPT_TEMPLATE_PATH, e)
        # fallback minimal template to avoid breaking
        template = (
            "USER INPUT:\n{frontend_json}\n\nSCORING SUMMARY:\n{scoring_summary}\n\nOUTPUT SCHEMA:\n{output_schema}\n\n"
            "Return exactly one JSON object (no commentary)."
        )

    # format template
    try:
        prompt = template.format(
            frontend_json=frontend_json,
            scoring_summary=scoring_summary or "",
            output_schema=output_schema_text
        )
    except KeyError as e:
        logger.exception("Prompt template missing placeholder: %s", e)
        # safe fallback
        prompt = f"USER INPUT:\n{frontend_json}\n\nSCORING SUMMARY:\n{scoring_summary}\n\nOUTPUT SCHEMA:\n{output_schema_text}"

    logger.info("Built prompt (chars=%d)", len(prompt))
    return prompt
