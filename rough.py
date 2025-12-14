from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from pathlib import Path
from datetime import datetime
import uuid

OUTPUT_DIR = Path("generated_pdfs")
OUTPUT_DIR.mkdir(exist_ok=True)


def json_to_pdf(data: dict, file_name: str | None = None) -> str:
    """
    Converts arbitrary nested JSON into a structured PDF.
    Returns the generated PDF path.
    """

    if not file_name:
        file_name = f"project_charter_{uuid.uuid4().hex}.pdf"

    pdf_path = OUTPUT_DIR / file_name

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontSize=14,
        spaceBefore=12,
        spaceAfter=6,
        leading=16,
        bold=True
    ))
    styles.add(ParagraphStyle(
        name="NormalText",
        fontSize=10,
        spaceAfter=4,
        leading=14
    ))
    styles.add(ParagraphStyle(
        name="SubHeader",
        fontSize=11,
        spaceBefore=8,
        spaceAfter=4,
        leading=14,
        bold=True
    ))

    elements = []

    # Document Title
    elements.append(Paragraph("Project Charter", styles["Title"]))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles["NormalText"]
    ))
    elements.append(Spacer(1, 0.3 * inch))

    def format_key(key: str) -> str:
        return key.replace("_", " ").title()

    def render(value, level=0):
        indent = level * 12

        if isinstance(value, dict):
            for k, v in value.items():
                elements.append(
                    Paragraph(format_key(k), styles["SectionHeader"] if level == 0 else styles["SubHeader"])
                )
                render(v, level + 1)

        elif isinstance(value, list):
            bullets = []
            for item in value:
                if isinstance(item, (dict, list)):
                    render(item, level + 1)
                else:
                    bullets.append(
                        ListItem(
                            Paragraph(str(item), styles["NormalText"]),
                            leftIndent=indent
                        )
                    )
            if bullets:
                elements.append(ListFlowable(
                    bullets,
                    bulletType="bullet",
                    start="circle",
                    leftIndent=indent
                ))

        else:
            elements.append(
                Paragraph(str(value), styles["NormalText"])
            )

    render(data)

    doc.build(elements)

    return str(pdf_path)



from services.json_to_pdf import json_to_pdf
import json

with open("output_template.json") as f:
    data = json.load(f)

pdf_path = json_to_pdf(data)
print("PDF generated at:", pdf_path)
