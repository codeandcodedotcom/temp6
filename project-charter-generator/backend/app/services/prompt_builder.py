import json
from typing import List, Dict, Any
from app.config import Config
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Default max context length used to truncate context_text if very large
DEFAULT_MAX_CONTEXT_CHARS = 8000

def build_context_block(docs: List[Dict]) -> str:
    """
    Join retrieved docs into a single context block.
    Each doc is expected to have either 'content' or 'text'.
    """
    parts = []
    for i, d in enumerate(docs, start=1):
        text = d.get("content") or d.get("text") or ""
        if not text:
            logger.warning(f"Document {i} missing 'content'/'text' field")
            continue
        source = d.get("source")
        doc_id = d.get("doc_id") or d.get("id")
        header = f"[{source}::{doc_id}]" if source or doc_id else f"[doc:{i}]"
        parts.append(f"{header} {text}".strip())
    ctx = "\n\n".join(parts)
    logger.info(f"Built context block with {len(parts)} segments (chars={len(ctx)})")
    return ctx

def _truncate_text(s: str, max_chars: int) -> str:
    if len(s) <= max_chars:
        return s
    logger.info(f"Truncating context from {len(s)} to {max_chars} chars")
    # keep head and tail for context variety
    head = s[: max_chars // 2]
    tail = s[- (max_chars // 2) :]
    return head + "\n\n...TRUNCATED...\n\n" + tail

def build_prompt(questions: Any, docs: List[Dict], scoring_summary: Any = "", instructions: str = "") -> str:
    """
    Build the final prompt expected by the LLM.

    - questions: list of question objects received from frontend (will be serialized to JSON)
    - docs: list of retrieved context documents (each must contain 'text' or 'content')
    - instructions: optional extra instructions appended to the PROMPT_TEMPLATE's default
    """
    try:
        answers_json = json.dumps(questions or [], indent=2, ensure_ascii=False)
    except Exception as e:
        logger.exception(f"Failed to serialize questions to JSON: {e}")
        answers_json = "[]"

    context_block = build_context_block(docs or [])
    # max_context = getattr(Config, "PROMPT_MAX_CONTEXT_CHARS", DEFAULT_MAX_CONTEXT_CHARS)
    # try:
    #     max_context = int(max_context)
    # except Exception:
    #     max_context = DEFAULT_MAX_CONTEXT_CHARS

    # context_text = _truncate_text(context_block, max_context)

    try:
        prompt = Config.PROMPT_TEMPLATE.format(
            answers_json=answers_json,
            context_text=context_block,
            scoring_summary=scoring_summary or "",
            instructions=instructions or ""
        )
    except KeyError as e:
        logger.exception(f"PROMPT_TEMPLATE missing expected placeholder: {e}")
        # Fallback: build a minimal prompt
        prompt = (
            "You are a project-charter generator.\n\n"
            "User answers:\n"
            f"{answers_json}\n\n"
            "Context:\n"
            f"{context_block}\n\n"
            "Produce a single valid JSON object matching the schema."
        )

    logger.info(f"Prompt built: context_chars={len(context_block)}, answers_chars={len(answers_json)}")
    return prompt
