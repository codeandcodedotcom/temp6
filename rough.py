def json_to_markdown(data, level=1):
    md = ""

    if isinstance(data, dict):
        for key, value in data.items():
            md += f"\n{'#' * level} {key.replace('_', ' ').title()}\n\n"
            md += json_to_markdown(value, level + 1)

    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                md += json_to_markdown(item, level)
            else:
                md += f"- {item}\n"
        md += "\n"

    else:
        md += f"{data}\n\n"

    return md

-----

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, ListFlowable, ListItem, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import re

def markdown_to_pdf(markdown_text, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="H1", fontSize=16, spaceAfter=10, spaceBefore=14, bold=True
    ))
    styles.add(ParagraphStyle(
        name="H2", fontSize=14, spaceAfter=8, spaceBefore=12, bold=True
    ))
    styles.add(ParagraphStyle(
        name="H3", fontSize=12, spaceAfter=6, spaceBefore=10, bold=True
    ))
    styles.add(ParagraphStyle(
        name="Body", fontSize=10, spaceAfter=6
    ))

    story = []
    lines = markdown_text.split("\n")

    bullet_buffer = []

    def flush_bullets():
        nonlocal bullet_buffer
        if bullet_buffer:
            story.append(
                ListFlowable(
                    [ListItem(Paragraph(item, styles["Body"])) for item in bullet_buffer],
                    bulletType="bullet",
                    start="circle",
                )
            )
            story.append(Spacer(1, 8))
            bullet_buffer = []

    for line in lines:
        line = line.strip()

        if not line:
            flush_bullets()
            continue

        if line.startswith("### "):
            flush_bullets()
            story.append(Paragraph(line[4:], styles["H3"]))

        elif line.startswith("## "):
            flush_bullets()
            story.append(Paragraph(line[3:], styles["H2"]))

        elif line.startswith("# "):
            flush_bullets()
            story.append(Paragraph(line[2:], styles["H1"]))

        elif line.startswith("- "):
            bullet_buffer.append(line[2:])

        else:
            flush_bullets()
            story.append(Paragraph(line, styles["Body"]))

    flush_bullets()
    doc.build(story)



----

def generate_charter_pdf(charter_json, output_pdf_path):
    markdown = json_to_markdown(charter_json)
    markdown_to_pdf(markdown, output_pdf_path)



generate_charter_pdf(
    charter_json=charter_data,
    output_pdf_path="project_charter.pdf"
                                      )


