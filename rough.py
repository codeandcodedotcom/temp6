from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

def page_layout(canvas, doc, project_title: str):
    canvas.saveState()

    # ===== HEADER =====
    canvas.setFont("Helvetica", 9)
    canvas.drawString(40, A4[1] - 40, project_title)
    canvas.drawRightString(
        A4[0] - 40,
        A4[1] - 40,
        f"Generated: {datetime.now().strftime('%d %b %Y')}"
    )

    # ===== FOOTER (PAGE NUMBER) =====
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(
        A4[0] - 40,   # right aligned
        30,           # bottom margin
        f"Page {canvas.getPageNumber()}"
    )

    canvas.restoreState()
