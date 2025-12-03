#!/usr/bin/env python3
"""
Normalize and add required fields to src/data/questions.json.

What it does (clean / no backups):
- Ensures each question has: question_id, question_text, question_type, order_index
- Ensures each option has: option_id, option_key, option_text, option_score, order_index
- Preserves existing fields (doesn't remove original keys like "id" / "text" / "label")
- Writes the file back with pretty JSON

Run from repository root:
    python src/scripts/normalize_questions.py
"""
from pathlib import Path
import json
import uuid
import sys

SRC = Path("src/data/questions.json")
if not SRC.exists():
    print(f"ERROR: {SRC} not found", file=sys.stderr)
    sys.exit(1)

data = json.loads(SRC.read_text(encoding="utf-8"))
questions = data.get("questions")
if not isinstance(questions, list):
    print("ERROR: top-level 'questions' array not found or invalid", file=sys.stderr)
    sys.exit(1)

for q_index, q in enumerate(questions):
    # question_id
    if not q.get("question_id"):
        q["question_id"] = str(uuid.uuid4())

    # question_text <- prefer existing normalized key, else copy from "text"
    if not q.get("question_text") and q.get("text"):
        q["question_text"] = q["text"]

    # question_type <- prefer existing normalized key, else copy from "type"
    if not q.get("question_type") and q.get("type"):
        q["question_type"] = q["type"]

    # order_index <- keep if exists; else numeric id if present; else use list index+1
    if not q.get("order_index"):
        if isinstance(q.get("id"), int):
            q["order_index"] = q["id"]
        else:
            q["order_index"] = q_index + 1

    # normalize options list
    opts = q.get("options")
    if opts is None:
        q["options"] = []
        opts = q["options"]

    for o_index, opt in enumerate(opts):
        # option_id
        if not opt.get("option_id"):
            opt["option_id"] = str(uuid.uuid4())

        # option_key (source doesn't have it) - keep existing or set "NA"
        if not opt.get("option_key"):
            opt["option_key"] = "NA"

        # option_text <- prefer existing normalized key, else copy from "label"
        if not opt.get("option_text") and opt.get("label"):
            opt["option_text"] = opt["label"]

        # option_score <- map from 'score' if present; otherwise keep existing or set null
        if "option_score" not in opt:
            if "score" in opt:
                opt["option_score"] = opt["score"]
            else:
                opt["option_score"] = None

        # order_index for option
        if not opt.get("order_index"):
            opt["order_index"] = o_index + 1

# write back (pretty)
SRC.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote normalized data to {SRC}")
