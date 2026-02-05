gate_sections = [s for s in parsed if s["GateContent"]]
assert gate_sections

all_contents = []
for s in gate_sections:
    all_contents.extend(s["GateContent"])

assert {"C1", "C1b"}.issubset(set(all_contents))
