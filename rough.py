import json
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors


# -----------------------------
# PDF PAGE LAYOUT
# -----------------------------
def page_layout(canvas, doc):
    canvas.saveState()

    # Header
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(40, 820, "Project Charter")

    # Footer
    canvas.setFont("Helvetica", 9)
    canvas.drawString(40, 30, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    canvas.restoreState()


# -----------------------------
# STYLE DEFINITIONS
# -----------------------------
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    name="TitleStyle",
    fontSize=18,
    leading=22,
    alignment=TA_CENTER,
    spaceAfter=24,
    fontName="Helvetica-Bold"
))

styles.add(ParagraphStyle(
    name="SectionHeader",
    fontSize=13,
    leading=16,
    spaceBefore=16,
    spaceAfter=8,
    fontName="Helvetica-Bold"
))

styles.add(ParagraphStyle(
    name="BodyTextCustom",
    fontSize=10,
    leading=14,
    spaceAfter=6
))


# -----------------------------
# HELPER RENDER FUNCTIONS
# -----------------------------
def render_key_value(story, title, value):
    story.append(Paragraph(title, styles["SectionHeader"]))
    story.append(Paragraph(str(value), styles["BodyTextCustom"]))


def render_list(story, title, items):
    story.append(Paragraph(title, styles["SectionHeader"]))
    bullets = [
        ListItem(Paragraph(str(item), styles["BodyTextCustom"]))
        for item in items
    ]
    story.append(ListFlowable(bullets, bulletType="bullet"))


def render_table(story, title, data_dict):
    story.append(Paragraph(title, styles["SectionHeader"]))

    table_data = [["Category", "Value"]]
    for k, v in data_dict.items():
        table_data.append([k.replace("_", " ").title(), str(v)])

    table = Table(table_data, colWidths=[250, 250])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]))

    story.append(table)


# -----------------------------
# MAIN PDF GENERATOR
# -----------------------------
def generate_project_charter_pdf(json_path, output_pdf):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=60,
        bottomMargin=60,
    )

    story = []

    # Title
    story.append(Paragraph("Project Charter", styles["TitleStyle"]))

    # Basic Info
    render_key_value(story, "Project Name", data.get("project_name", ""))
    render_key_value(story, "Description", data.get("description", ""))
    render_key_value(story, "Industry", data.get("industry", ""))
    render_key_value(story, "Duration", data.get("duration", ""))
    render_key_value(story, "Budget", data.get("budget", ""))
    render_key_value(story, "Complexity Score", data.get("complexity_score", ""))

    # Objectives
    if "objectives" in data:
        render_list(story, "Objectives", data["objectives"])

    # Scope
    if "project_scope" in data:
        scope = data["project_scope"]
        render_list(story, "In Scope", scope.get("in_scope", []))
        render_list(story, "Out of Scope", scope.get("out_scope", []))

    # Business Benefits
    if "business_benefit" in data:
        render_list(story, "Business Benefits", data["business_benefit"])

    # Budget Breakdown
    if "budget_breakdown" in data:
        render_table(story, "Budget Breakdown", data["budget_breakdown"].get("allocation", {}))

    # Risks
    if "risks_and_mitigation" in data:
        story.append(Paragraph("Risks and Mitigation", styles["SectionHeader"]))
        for risk in data["risks_and_mitigation"]:
            text = (
                f"<b>Risk:</b> {risk.get('risk')}<br/>"
                f"<b>Impact:</b> {risk.get('impact')}<br/>"
                f"<b>Mitigation:</b> {risk.get('mitigation')}"
            )
            story.append(Paragraph(text, styles["BodyTextCustom"]))
            story.append(Spacer(1, 8))

    # Dependencies
    if "dependencies" in data:
        render_list(story, "Dependencies", data["dependencies"])

    # Success Criteria
    if "success_criteria" in data:
        render_list(story, "Success Criteria", data["success_criteria"])

    doc.build(
        story,
        onFirstPage=page_layout,
        onLaterPages=page_layout
    )


# -----------------------------
# ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    input_json = "project_charter.json"   # <-- your JSON file
    output_pdf = "project_charter.pdf"

    generate_project_charter_pdf(input_json, output_pdf)
    print(f"PDF generated successfully: {Path(output_pdf).resolve()}")
