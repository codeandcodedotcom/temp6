#!/usr/bin/env python3
"""
Update src/data/questions.json in-place per instructions.

For each question (in the top-level questions list):
- replace the question "Id" value with a newly generated UUID string
- add (or replace) "order_index" with the question's 1-based position in the list

For each option inside a question (question["options"] expected to be a list):
- replace the option "Id" value with a newly generated UUID string
- add (or replace) "option_key" with the string "NA"
- add (or replace) "order_index" with the option's 1-based position within its question

No other keys are added/removed/renamed. Everything else in the JSON is preserved exactly.

Run from repository root:
    python scripts/update_ids_and_indexes.py
"""
from pathlib import Path
import json
import uuid
import sys

SRC = Path("src/data/questions.json")
if not SRC.exists():
    print(f"ERROR: file not found: {SRC}", file=sys.stderr)
    sys.exit(1)


def new_uuid() -> str:
    return str(uuid.uuid4())


def process():
    raw = SRC.read_text(encoding="utf-8")
    payload = json.loads(raw)

    # support both {"questions": [...]} and a top-level list
    if isinstance(payload, dict) and "questions" in payload and isinstance(payload["questions"], list):
        questions = payload["questions"]
        top_is_dict = True
    elif isinstance(payload, list):
        questions = payload
        top_is_dict = False
    else:
        print("ERROR: unexpected JSON structure. Expected top-level 'questions' array or a list.", file=sys.stderr)
        sys.exit(1)

    q_count = 0
    opt_count = 0

    for qi, q in enumerate(questions):
        # only process dict entries; skip other types
        if not isinstance(q, dict):
            continue

        # 1) update question Id with uuid
        q["Id"] = new_uuid()

        # 2) add/replace order_index (1-based)
        q["order_index"] = qi + 1

        q_count += 1

        # process options array if present and is a list
        opts = q.get("options")
        if not isinstance(opts, list):
            # if options key exists but not a list, skip modifying options for safety
            continue

        for oi, opt in enumerate(opts):
            if not isinstance(opt, dict):
                # keep non-dict option as-is (per instructions we only update "Id" when present
                # and add keys only if option is dict). Skip otherwise.
                continue

            # update option "Id" with uuid
            opt["Id"] = new_uuid()

            # add option_key with "NA" (replace if exists)
            opt["option_key"] = "NA"

            # add/replace option order_index (1-based within question)
            opt["order_index"] = oi + 1

            opt_count += 1

    # write back preserving shape
    if top_is_dict:
        payload["questions"] = questions
        out = payload
    else:
        out = questions

    SRC.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Processed {q_count} question(s) and {opt_count} option(s). File updated: {SRC}")


if __name__ == "__main__":
    process()
