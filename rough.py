gate1_sections = [s for s in parsed if s["GateContent"]]

assert gate1_sections

gate1_contents = []
for s in gate1_sections:
    gate1_contents.extend(s["GateContent"])

assert sorted(gate1_contents) == ["C1", "C1b"]
