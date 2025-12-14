from pathlib import Path
import uuid

OUTPUT_DIR = Path("generated_markdown")
OUTPUT_DIR.mkdir(exist_ok=True)


def json_to_markdown(data: dict, file_name: str | None = None) -> str:
    """
    Converts arbitrary nested JSON to Markdown.
    Returns markdown file path.
    """

    if not file_name:
        file_name = f"project_charter_{uuid.uuid4().hex}.md"

    md_path = OUTPUT_DIR / file_name
    lines = []

    def format_key(key: str) -> str:
        return key.replace("_", " ").title()

    def render(value, level=1):
        prefix = "#" * min(level + 1, 6)

        if isinstance(value, dict):
            for k, v in value.items():
                lines.append(f"{prefix} {format_key(k)}\n")
                render(v, level + 1)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, (dict, list)):
                    render(item, level + 1)
                else:
                    lines.append(f"- {item}\n")
            lines.append("\n")

        else:
            lines.append(f"{value}\n\n")

    # Document title
    lines.append("# Project Charter\n\n")
    render(data)

    md_path.write_text("".join(lines), encoding="utf-8")
    return str(md_path)
    -----

import subprocess
from pathlib import Path


def markdown_to_pdf(md_path: str) -> str:
    md_path = Path(md_path)
    pdf_path = md_path.with_suffix(".pdf")

    subprocess.run(
        [
            "pandoc",
            str(md_path),
            "-o",
            str(pdf_path),
            "--pdf-engine=xelatex"
        ],
        check=True
    )

    return str(pdf_path)

------


from json_to_markdown import json_to_markdown
from markdown_to_pdf import markdown_to_pdf
import json

with open("output_template.json") as f:
    data = json.load(f)

md_path = json_to_markdown(data)
pdf_path = markdown_to_pdf(md_path)

print("PDF generated:", pdf_path)
