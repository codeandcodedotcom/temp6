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
    TableStyle,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors


# -------------------------------------------------
# PAGE LAYOUT
# -------------------------------------------------
def page_layout(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.drawString(40, 820, "Project Charter")
    canvas.drawRightString(550, 820, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    canvas.restoreState()


# -------------------------------------------------
# STYLES
# -------------------------------------------------
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    name="Title",
    fontSize=20,
    leading=24,
    alignment=TA_CENTER,
    spaceAfter=24,
    fontName="Helvetica-Bold"
))

styles.add(ParagraphStyle(
    name="Section",
    fontSize=13,
    leading=16,
    spaceBefore=18,
    spaceAfter=8,
    fontName="Helvetica-Bold"
))

styles.add(ParagraphStyle(
    name="Body",
    fontSize=10,
    leading=14,
    spaceAfter=6
))


# -------------------------------------------------
# HELPER RENDERERS
# -------------------------------------------------
def section(story, title):
    story.append(Paragraph(title, styles["Section"]))


def text(story, value):
    story.append(Paragraph(str(value), styles["Body"]))


def bullet_list(story, items):
    story.append(ListFlowable(
        [ListItem(Paragraph(i, styles["Body"])) for i in items],
        bulletType="bullet"
    ))


def key_value_table(story, data: dict):
    table_data = [["Field", "Value"]]
    for k, v in data.items():
        table_data.append([k.replace("_", " ").title(), str(v)])

    table = Table(table_data, colWidths=[220, 300])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    story.append(table)


# -------------------------------------------------
# MAIN GENERATOR
# -------------------------------------------------
def generate_charter_pdf(json_path: str, output_pdf: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=60,
        bottomMargin=60
    )

    story = []

    # ---------------- COVER ----------------
    story.append(Paragraph("Project Charter", styles["Title"]))

    key_value_table(story, {
        "Project Title": data.get("project_title"),
        "Industry": data.get("industry"),
        "Duration": data.get("duration"),
        "Budget": data.get("budget"),
        "Complexity Score": data.get("complexity_score"),
        "Project Sponsor": data.get("project_sponsor"),
        "Date": data.get("date"),
    })

    # ---------------- DESCRIPTION ----------------
    section(story, "Project Description")
    text(story, data.get("description"))

    # ---------------- CURRENT STATE ----------------
    section(story, "Current State")
    bullet_list(story, data.get("current_state", []))

    # ---------------- OBJECTIVES ----------------
    section(story, "Objectives")
    bullet_list(story, data.get("objectives", []))

    # ---------------- FUTURE STATE ----------------
    section(story, "Future State")
    bullet_list(story, data.get("future_state", []))

    # ---------------- HIGH LEVEL REQUIREMENTS ----------------
    section(story, "High Level Requirements")
    bullet_list(story, data.get("high_level_requirement", []))

    # ---------------- BUSINESS BENEFITS ----------------
    section(story, "Business Benefits")
    bullet_list(story, data.get("business_benefit", []))

    # ---------------- PROJECT SCOPE ----------------
    section(story, "Project Scope")
    text(story, "<b>Scope</b>")
    text(story, data.get("project_scope", {}).get("scope"))

    text(story, "<b>In Scope</b>")
    bullet_list(story, data.get("project_scope", {}).get("in_scope", []))

    text(story, "<b>Out of Scope</b>")
    bullet_list(story, data.get("project_scope", {}).get("out_scope", []))

    # ---------------- BUDGET BREAKDOWN ----------------
    section(story, "Budget Breakdown")
    key_value_table(story, data.get("budget_breakdown", {}).get("allocation", {}))

    # ---------------- TIMELINE ----------------
    section(story, "Project Timeline")
    for phase, details in data.get("timeline", {}).items():
        text(story, f"<b>{phase.replace('_', ' ').title()}</b>")
        text(story, f"Duration: {details.get('duration')}")
        text(story, "Prerequisites:")
        bullet_list(story, details.get("prerequisites", []))
        text(story, "Tasks:")
        bullet_list(story, details.get("tasks", []))

    # ---------------- DEPENDENCIES ----------------
    section(story, "Dependencies")
    bullet_list(story, data.get("dependencies", []))

    # ---------------- RISKS ----------------
    section(story, "Risks and Mitigation")
    for risk in data.get("risks_and_mitigation", []):
        text(story, f"<b>Risk:</b> {risk.get('risk')}")
        text(story, f"<b>Impact:</b> {risk.get('impact')}")
        text(story, f"<b>Mitigation:</b> {risk.get('mitigation')}")
        Spacer(1, 8)

    # ---------------- PM RESOURCE ----------------
    section(story, "PM Resource Recommendation")
    for pm in data.get("pm_resource_recommendation", []):
        text(story, f"<b>Job Profile:</b> {pm.get('job_profile')}")
        text(story, "<b>Skills</b>")
        bullet_list(story, pm.get("skills", []))
        text(story, "<b>Responsibilities</b>")
        bullet_list(story, pm.get("responsibilities", []))
        text(story, "<b>Tasks</b>")
        bullet_list(story, pm.get("tasks", []))

    # ---------------- LESSONS LEARNT ----------------
    section(story, "Lessons Learnt")
    bullet_list(story, data.get("lesson_learnt", []))

    # ---------------- SUCCESS CRITERIA ----------------
    section(story, "Success Criteria")
    bullet_list(story, data.get("success_criteria", []))

    # ---------------- ASSUMPTIONS ----------------
    section(story, "Assumptions")
    bullet_list(story, data.get("assumptions", []))

    doc.build(
        story,
        onFirstPage=page_layout,
        onLaterPages=page_layout
    )


# -------------------------------------------------
# ENTRY POINT
# -------------------------------------------------
if __name__ == "__main__":
    generate_charter_pdf(
        json_path="charter_json2.json",
        output_pdf="project_charter.pdf"
    )
    print("PDF generated successfully.")
