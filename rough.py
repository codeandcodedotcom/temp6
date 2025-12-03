def prepare_options():
    import json
    import uuid

    data = []
    with open("src/data/questions.json", "r") as f:
        read = json.load(f)
        questions = read.get("questions", [])

        for q in questions:
            qid = q.get("id")                        # question id in JSON (should be UUID)
            options = q.get("options", [])
            for idx, opt in enumerate(options, start=1):
                temp = {}
                # use existing id if present, otherwise generate
                temp["option_id"] = opt.get("id") or str(uuid.uuid4())
                temp["question_id"] = qid
                # keep option_key if present, otherwise "NA"
                temp["option_key"] = opt.get("option_key", "NA")
                # label is the visible text (fall back to 'text' if label missing)
                temp["option_text"] = opt.get("label") or opt.get("text") or ""
                # keep whatever score is present (could be null/None)
                temp["option_score"] = opt.get("score")
                # prefer explicit order_index in JSON; otherwise use enumeration index
                temp["order_index"] = opt.get("order_index") if opt.get("order_index") is not None else idx

                data.append(temp)

    print("Option data is prepared successfully")
    return json.dumps(data)
