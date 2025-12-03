#!/usr/bin/env python3
"""
Normalize / enrich src/data/questions.json **in-place** while preserving all existing keys.

Rules enforced by this script:
- Do NOT remove or rename any existing keys.
- For each question dict:
  - If "question_id" missing or empty -> add a UUID string.
  - If "question_type" missing -> add using existing "type" (if present) otherwise leave as None.
  - If "order_index" missing -> set from numeric "id" if present, else use list index+1.
- For each option (items under question["options"]):
  - If "option_id" missing or empty -> add a UUID string.
  - If "option_key" missing -> add "NA".
  - If "option_text" missing -> add from "label" or "text" (if present) otherwise leave None.
  - If "option_score" missing -> if "score" exists copy it, else set None.
  - If "order_index" missing -> set to option index+1.
- Everything else in JSON is left exactly as-is.
- Writes back the file with pretty JSON.

Run from repo root:
    python src/scripts/enrich_questions_keep_keys.py
"""
from pathlib import Path
import json
import uuid
import sys

SRC = Path("src/data/questions.json")
if not SRC.exists():
    print(f"ERROR: {SRC} not found", file=sys.stderr)
    sys.exit(1)

def uid():
    return str(uuid.uuid4())

def ensure_question_fields(q: dict, q_index: int):
    # add question_id if missing or falsy
    if not q.get("question_id"):
        q["question_id"] = uid()

    # add question_type if missing (use existing 'type' if present)
    if "question_type" not in q:
        if "type" in q and q["type"] is not None:
            q["question_type"] = q["type"]
        else:
            # explicitly set to None so key exists (user allowed new keys)
            q["question_type"] = None

    # add order_index if missing
    if "order_index" not in q or q.get("order_index") in (None, ""):
        if isinstance(q.get("id"), int):
            q["order_index"] = q["id"]
        else:
            q["order_index"] = q_index + 1

def ensure_option_fields(opt: dict, opt_index: int):
    # preserve any existing keys; only add missing keys/values
    if not opt.get("option_id"):
        opt["option_id"] = uid()

    if "option_key" not in opt or opt.get("option_key") in (None, ""):
        # user said no option_key in source; set default "NA" if missing
        opt["option_key"] = "NA"

    # option_text: prefer existing key, else copy label or text if present, else None
    if "option_text" not in opt:
        if "label" in opt and opt["label"] is not None:
            opt["option_text"] = opt["label"]
        elif "text" in opt and opt["text"] is not None:
            opt["option_text"] = opt["text"]
        else:
            opt["option_text"] = None

    # option_score: if not present, map from 'score' if available, else set None
    if "option_score" not in opt:
        if "score" in opt:
            opt["option_score"] = opt["score"]
        else:
            opt["option_score"] = None

    # order_index for option
    if "order_index" not in opt or opt.get("order_index") in (None, ""):
        # if source has numeric 'id' for option (rare) prefer it
        if isinstance(opt.get("id"), int):
            opt["order_index"] = opt["id"]
        else:
            opt["order_index"] = opt_index + 1

def main():
    raw = SRC.read_text(encoding="utf-8")
    payload = json.loads(raw)

    # support files that are either {"questions": [...]} or just a list
    if isinstance(payload, dict) and "questions" in payload:
        questions = payload["questions"]
        top_level_is_dict = True
    elif isinstance(payload, list):
        questions = payload
        top_level_is_dict = False
    else:
        print("ERROR: unexpected JSON structure: expected top-level 'questions' array or a list", file=sys.stderr)
        sys.exit(1)

    if not isinstance(questions, list):
        print("ERROR: 'questions' is not a list", file=sys.stderr)
        sys.exit(1)

    # Process each question and its options
    for qi, q in enumerate(questions):
        if not isinstance(q, dict):
            continue  # leave non-dict entries untouched

        ensure_question_fields(q, qi)

        # Ensure options list exists and is a list; if missing, leave as-is but create empty list for processing
        opts = q.get("options")
        if opts is None:
            # do not remove existing keys; add empty list if no key present
            q["options"] = []
            opts = q["options"]

        # If options exists but isn't list, skip processing to avoid data corruption
        if not isinstance(opts, list):
            continue

        for oi, opt in enumerate(opts):
            if not isinstance(opt, dict):
                # wrap non-dict option into a dict with original value preserved in 'raw'
                # but also add the option_id and other fields
                original = opt
                opt_dict = {"raw": original}
                opts[oi] = opt_dict
                opt = opt_dict
            ensure_option_fields(opt, oi)

    # write back, preserving top-level shape
    if top_level_is_dict:
        payload["questions"] = questions
        out = payload
    else:
        out = questions

    SRC.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {SRC} (questions processed: {len(questions)})")

if __name__ == "__main__":
    main()
