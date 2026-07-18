import io

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def render_packet_pdf(profile: dict, calculation: dict, checklist: list[dict]) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    y = 740

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "RealDoor Application-Readiness Packet")
    y -= 30

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Confirmed Profile")
    c.setFont("Helvetica", 10)
    for name, value in profile.items():
        y -= 16
        c.drawString(60, y, f"{name}: {value}")

    y -= 24
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Income vs. Threshold")
    c.setFont("Helvetica", 10)
    for label in ("confirmed_value", "threshold", "formula", "source_citation", "effective_date"):
        y -= 16
        c.drawString(60, y, f"{label}: {calculation.get(label)}")

    y -= 24
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Checklist")
    c.setFont("Helvetica", 10)
    for item in checklist:
        y -= 16
        c.drawString(60, y, f"[{item['status']}] {item['label']}")

    c.showPage()
    c.save()
    return buffer.getvalue()
