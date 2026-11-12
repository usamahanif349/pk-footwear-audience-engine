"""
One-page client report (PDF) for a brand or agency workspace: the deliverable a
marketing team could be sold. Built with reportlab and the built-in Helvetica font,
so it works on Streamlit Cloud without extra font files.
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

VIOLET = colors.HexColor("#5B4BDB")
VIOLET_SOFT = colors.HexColor("#EEEBFF")
ORANGE = colors.HexColor("#F26B3A")
INK = colors.HexColor("#14142B")
MUTED = colors.HexColor("#6E6E85")
LINE = colors.HexColor("#E6E6EF")
W, H = A4
M = 16 * mm


def _wrap(c, text, font, size, width):
    text = str(text).replace("≈", "~").replace("–", "-").replace("’", "'")
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if c.stringWidth(trial, font, size) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _para(c, x, y, text, font="Helvetica", size=9.5, color=INK, width=None, leading=None):
    width = width or (W - 2 * M)
    leading = leading or size * 1.35
    c.setFont(font, size)
    c.setFillColor(color)
    for line in _wrap(c, text, font, size, width):
        c.drawString(x, y, line)
        y -= leading
    return y


def build_report(ctx):
    """ctx keys: workspace, date, kpis [(label, value, note)], actions [(title, why)],
    segments [(name, people, line)], cities [(city, n)], creators [(channel, brand, n)],
    assumptions (str), source (str), url (str)."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Joota Pulse client report: {ctx['workspace']}")

    # header band
    c.setFillColor(VIOLET)
    c.rect(0, H - 34 * mm, W, 34 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(M, H - 12 * mm, "JOOTA PULSE  |  Audience intelligence for Pakistani footwear brands")
    c.setFont("Helvetica-Bold", 20)
    c.drawString(M, H - 22 * mm, f"Client snapshot: {ctx['workspace']}")
    c.setFont("Helvetica", 9.5)
    c.drawString(M, H - 28.5 * mm, f"Based on real public YouTube comments  |  {ctx['date']}")

    # KPI cards
    y = H - 42 * mm
    n = len(ctx["kpis"])
    gap = 4 * mm
    cw = (W - 2 * M - gap * (n - 1)) / n
    for i, (label, value, note) in enumerate(ctx["kpis"]):
        x = M + i * (cw + gap)
        c.setFillColor(colors.white)
        c.setStrokeColor(LINE)
        c.roundRect(x, y - 24 * mm, cw, 24 * mm, 3 * mm, stroke=1, fill=1)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8.5)
        c.drawString(x + 4 * mm, y - 6 * mm, label)
        c.setFillColor(ORANGE if i == 0 else INK)
        c.setFont("Helvetica-Bold", 17)
        c.drawString(x + 4 * mm, y - 14 * mm, value)
        _para(c, x + 4 * mm, y - 19.5 * mm, note, size=7.5, color=MUTED, width=cw - 8 * mm, leading=9)
    y -= 32 * mm

    def section(title, y):
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 12.5)
        c.drawString(M, y, title)
        c.setStrokeColor(LINE)
        c.line(M, y - 2.5 * mm, W - M, y - 2.5 * mm)
        return y - 8 * mm

    # actions
    y = section("Do these first", y)
    for i, (title, why) in enumerate(ctx["actions"], 1):
        c.setFillColor(VIOLET_SOFT)
        c.circle(M + 3 * mm, y + 1.2 * mm, 3 * mm, stroke=0, fill=1)
        c.setFillColor(VIOLET)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(M + 3 * mm, y, str(i))
        y = _para(c, M + 9 * mm, y, title, font="Helvetica-Bold", size=10, width=W - 2 * M - 9 * mm)
        y = _para(c, M + 9 * mm, y + 0.5 * mm, why, size=8.8, color=MUTED, width=W - 2 * M - 9 * mm) - 2.5 * mm
    y -= 2 * mm

    # two columns: segments | cities + creators
    y = section("Who your customers are", y)
    col_w = (W - 2 * M - 8 * mm) / 2
    ly = y
    for name, people, line in ctx["segments"]:
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(M, ly, name)
        c.setFillColor(VIOLET)
        c.drawRightString(M + col_w, ly, f"{people:,} people")
        ly = _para(c, M, ly - 4.2 * mm, line, size=8.3, color=MUTED, width=col_w) - 2 * mm
    rx, ry = M + col_w + 8 * mm, y
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(rx, ry, "Cities shoppers ask about")
    ry -= 5 * mm
    for city, n in ctx["cities"]:
        c.setFont("Helvetica", 9)
        c.setFillColor(INK)
        c.drawString(rx, ry, city)
        c.drawRightString(rx + col_w, ry, f"{n} mentions")
        ry -= 4.6 * mm
    ry -= 3 * mm
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(rx, ry, "Creators whose viewers ask to buy")
    ry -= 5 * mm
    for ch, brand, n in ctx["creators"]:
        c.setFont("Helvetica", 9)
        c.drawString(rx, ry, f"{ch[:30]} ({brand})")
        c.drawRightString(rx + col_w, ry, f"{n} buyers")
        ry -= 4.6 * mm

    # footer
    c.setStrokeColor(LINE)
    c.line(M, 22 * mm, W - M, 22 * mm)
    _para(c, M, 17 * mm, ctx["assumptions"], size=7.5, color=MUTED)
    _para(c, M, 12.5 * mm, ctx["source"], size=7.5, color=MUTED)
    c.setFillColor(VIOLET)
    c.setFont("Helvetica", 7.5)
    c.drawString(M, 8 * mm, ctx["url"])
    c.showPage()
    c.save()
    return buf.getvalue()
