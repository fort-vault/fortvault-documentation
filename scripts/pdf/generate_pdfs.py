#!/usr/bin/env python3
"""Generate the ISO 27001 partner PDFs from their Markdown sources."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DOCS_DIR = Path(__file__).resolve().parents[2]
BASE_DIR = DOCS_DIR / "security" / "iso-27001"
OUTPUT_DIR = DOCS_DIR / "output" / "pdf"

FORTVAULT_BLUE = colors.HexColor("#003087")
DARK = colors.HexColor("#0B1739")
MUTED = colors.HexColor("#6F7182")
LINE = colors.HexColor("#DDE3EE")
LIGHT_BLUE = colors.HexColor("#EEF4FF")
LIGHT_GREEN = colors.HexColor("#EEF8F2")
LIGHT_AMBER = colors.HexColor("#FFF7E8")
LIGHT_RED = colors.HexColor("#FFF0F0")
LIGHT_PURPLE = colors.HexColor("#F3F0FF")


def register_fonts() -> tuple[str, str]:
    regular = Path("/System/Library/Fonts/Supplemental/Verdana.ttf")
    bold = Path("/System/Library/Fonts/Supplemental/Verdana Bold.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("FortVaultSans", str(regular)))
        pdfmetrics.registerFont(TTFont("FortVaultSans-Bold", str(bold)))
        return "FortVaultSans", "FortVaultSans-Bold"
    return "Helvetica", "Helvetica-Bold"


FONT_REGULAR, FONT_BOLD = register_fonts()


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="FVTitle",
            fontName=FONT_BOLD,
            fontSize=24,
            leading=29,
            textColor=DARK,
            spaceAfter=5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FVSubtitle",
            fontName=FONT_REGULAR,
            fontSize=13,
            leading=18,
            textColor=FORTVAULT_BLUE,
            spaceAfter=6 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FVH2",
            fontName=FONT_BOLD,
            fontSize=15,
            leading=19,
            textColor=DARK,
            spaceBefore=6 * mm,
            spaceAfter=3 * mm,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FVH3",
            fontName=FONT_BOLD,
            fontSize=10.5,
            leading=14,
            textColor=FORTVAULT_BLUE,
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FVBody",
            fontName=FONT_REGULAR,
            fontSize=8.5,
            leading=12.4,
            textColor=DARK,
            spaceAfter=2.4 * mm,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FVTable",
            fontName=FONT_REGULAR,
            fontSize=6.9,
            leading=9.4,
            textColor=DARK,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FVTableHeader",
            fontName=FONT_BOLD,
            fontSize=7,
            leading=9.5,
            textColor=colors.white,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FVDiagramTitle",
            fontName=FONT_BOLD,
            fontSize=9,
            leading=12,
            textColor=DARK,
            alignment=TA_CENTER,
            spaceAfter=2 * mm,
        )
    )
    return styles


STYLES = build_styles()


def inline_markup(value: str) -> str:
    escaped = html.escape(value.strip())
    escaped = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(
        r"`([^`]+)`",
        rf"<font name='{FONT_REGULAR}' color='#003087'>\1</font>",
        escaped,
    )
    return escaped


def node(
    drawing: Drawing,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    fill: colors.Color,
    stroke: colors.Color,
) -> None:
    drawing.add(Rect(x, y, w, h, rx=5, ry=5, fillColor=fill, strokeColor=stroke, strokeWidth=1))
    lines = label.split("\n")
    line_height = 8.5
    start_y = y + h / 2 + (len(lines) - 1) * line_height / 2 - 2.5
    for index, line in enumerate(lines):
        drawing.add(
            String(
                x + w / 2,
                start_y - index * line_height,
                line,
                textAnchor="middle",
                fontName=FONT_BOLD if index == 0 else FONT_REGULAR,
                fontSize=6.2 if len(line) < 26 else 5.6,
                fillColor=DARK,
            )
        )


def arrow(drawing: Drawing, x1: float, y1: float, x2: float, y2: float) -> None:
    drawing.add(Line(x1, y1, x2, y2, strokeColor=MUTED, strokeWidth=0.8))
    angle_x = x2 - x1
    angle_y = y2 - y1
    length = max((angle_x * angle_x + angle_y * angle_y) ** 0.5, 1)
    ux, uy = angle_x / length, angle_y / length
    px, py = -uy, ux
    size = 3.2
    drawing.add(
        Polygon(
            [
                x2,
                y2,
                x2 - ux * size + px * size * 0.55,
                y2 - uy * size + py * size * 0.55,
                x2 - ux * size - px * size * 0.55,
                y2 - uy * size - py * size * 0.55,
            ],
            fillColor=MUTED,
            strokeColor=MUTED,
        )
    )


def custody_diagram(width: float = 500, height: float = 330) -> Drawing:
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, rx=8, ry=8, fillColor=colors.white, strokeColor=LINE))

    box_w, box_h = 92, 34
    xs = [14, 135, 256, 377]
    ys = [276, 208, 130, 52]

    node(d, xs[0], ys[0], box_w, box_h, "Authorized user", LIGHT_BLUE, FORTVAULT_BLUE)
    node(d, xs[1], ys[0], box_w, box_h, "Frontend", LIGHT_GREEN, colors.HexColor("#27865D"))
    node(d, xs[2], ys[0], box_w, box_h, "Backend", LIGHT_GREEN, colors.HexColor("#27865D"))
    node(d, xs[3], ys[0], box_w, box_h, "Backend PostgreSQL\nbusiness + audit state", LIGHT_AMBER, colors.HexColor("#B7791F"))

    node(d, xs[1], ys[1], box_w, box_h, "Redis Streams\ntransport only", LIGHT_AMBER, colors.HexColor("#B7791F"))
    node(d, xs[2], ys[1], box_w, box_h, "Custody Processing\nexecution + broadcast", LIGHT_GREEN, colors.HexColor("#27865D"))
    node(d, xs[3], ys[1], box_w, box_h, "Processing PostgreSQL\nrequests + inbox/outbox", LIGHT_AMBER, colors.HexColor("#B7791F"))

    node(d, xs[0], ys[2], box_w, box_h, "Listener\nchain event ingestion", LIGHT_GREEN, colors.HexColor("#27865D"))
    node(d, xs[1], ys[2], box_w, box_h, "Listener PostgreSQL\ntracking + deduplication", LIGHT_AMBER, colors.HexColor("#B7791F"))
    node(d, xs[2], ys[2], box_w, box_h, "Partner MPC cluster\nthreshold signing", LIGHT_RED, colors.HexColor("#B83232"))
    node(d, xs[3], ys[2], box_w, box_h, "MPC node storage\nkey shares + sessions", LIGHT_AMBER, colors.HexColor("#B7791F"))

    node(d, xs[0], ys[3], box_w, box_h, "Blockchain providers\nand networks", LIGHT_PURPLE, colors.HexColor("#6B46C1"))
    node(d, xs[1], ys[3], box_w, box_h, "Policy contracts\nverification state", LIGHT_PURPLE, colors.HexColor("#6B46C1"))
    node(d, xs[2], ys[3], box_w, box_h, "Notification service\nemail + Telegram", LIGHT_GREEN, colors.HexColor("#27865D"))
    node(d, xs[3], ys[3], box_w, box_h, "Approved secret store", LIGHT_RED, colors.HexColor("#B83232"))

    arrow(d, xs[0] + box_w, ys[0] + 17, xs[1], ys[0] + 17)
    arrow(d, xs[1] + box_w, ys[0] + 17, xs[2], ys[0] + 17)
    arrow(d, xs[2] + box_w, ys[0] + 17, xs[3], ys[0] + 17)
    arrow(d, xs[2] + 46, ys[0], xs[1] + 46, ys[1] + box_h)
    arrow(d, xs[1] + box_w, ys[1] + 17, xs[2], ys[1] + 17)
    arrow(d, xs[2] + box_w, ys[1] + 17, xs[3], ys[1] + 17)
    arrow(d, xs[2] + 46, ys[1], xs[2] + 46, ys[2] + box_h)
    arrow(d, xs[2] + box_w, ys[2] + 17, xs[3], ys[2] + 17)
    arrow(d, xs[2] + 18, ys[1], xs[0] + 60, ys[3] + box_h)
    arrow(d, xs[0] + 46, ys[3] + box_h, xs[0] + 46, ys[2])
    arrow(d, xs[0] + box_w, ys[2] + 17, xs[1], ys[2] + 17)
    arrow(d, xs[2] + 20, ys[2], xs[1] + 65, ys[3] + box_h)
    arrow(d, xs[1] + 65, ys[1], xs[1] + 65, ys[3] + box_h)
    arrow(d, xs[1] + 18, ys[1], xs[2] + 40, ys[3] + box_h)
    arrow(d, xs[3] + 46, ys[3] + box_h, xs[3] + 20, ys[1])

    d.add(String(14, 315, "Custody control and execution boundaries", fontName=FONT_BOLD, fontSize=8, fillColor=FORTVAULT_BLUE))
    return d


def exchange_diagram(width: float = 500, height: float = 295) -> Drawing:
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, rx=8, ry=8, fillColor=colors.white, strokeColor=LINE))

    box_w, box_h = 92, 34
    xs = [14, 135, 256, 377]
    ys = [242, 169, 96, 23]

    node(d, xs[0], ys[0], box_w, box_h, "Authorized user", LIGHT_BLUE, FORTVAULT_BLUE)
    node(d, xs[1], ys[0], box_w, box_h, "Frontend", LIGHT_GREEN, colors.HexColor("#27865D"))
    node(d, xs[2], ys[0], box_w, box_h, "Backend", LIGHT_GREEN, colors.HexColor("#27865D"))
    node(d, xs[3], ys[0], box_w, box_h, "Backend PostgreSQL\naccounts + synced data", LIGHT_AMBER, colors.HexColor("#B7791F"))

    node(d, xs[0], ys[1], box_w, box_h, "Approved secret store\nraw credentials", LIGHT_RED, colors.HexColor("#B83232"))
    node(d, xs[1], ys[1], box_w, box_h, "Redis Streams\nopaque references only", LIGHT_AMBER, colors.HexColor("#B7791F"))
    node(d, xs[2], ys[1], box_w, box_h, "Exchange Processing\nprovider execution", LIGHT_GREEN, colors.HexColor("#27865D"))
    node(d, xs[3], ys[1], box_w, box_h, "Processing PostgreSQL\nrequests + attempts", LIGHT_AMBER, colors.HexColor("#B7791F"))

    node(d, xs[0], ys[2], box_w, box_h, "Partner MPC cluster\nBinance Ed25519", LIGHT_RED, colors.HexColor("#B83232"))
    node(d, xs[1], ys[2], box_w, box_h, "MPC node storage\nkey shares + sessions", LIGHT_AMBER, colors.HexColor("#B7791F"))
    node(d, xs[2], ys[2], box_w, box_h, "Provider adapters\nnormalized requests", LIGHT_GREEN, colors.HexColor("#27865D"))
    node(d, xs[3], ys[2], box_w, box_h, "Rate limits + retries\nfenced leases", LIGHT_GREEN, colors.HexColor("#27865D"))

    node(d, xs[0], ys[3], box_w, box_h, "Binance API", LIGHT_PURPLE, colors.HexColor("#6B46C1"))
    node(d, xs[1], ys[3], box_w, box_h, "Gate API", LIGHT_PURPLE, colors.HexColor("#6B46C1"))
    node(d, xs[2], ys[3], box_w, box_h, "MEXC API", LIGHT_PURPLE, colors.HexColor("#6B46C1"))
    node(d, xs[3], ys[3], box_w, box_h, "Sanitized completion\nto Backend", LIGHT_BLUE, FORTVAULT_BLUE)

    arrow(d, xs[0] + box_w, ys[0] + 17, xs[1], ys[0] + 17)
    arrow(d, xs[1] + box_w, ys[0] + 17, xs[2], ys[0] + 17)
    arrow(d, xs[2] + box_w, ys[0] + 17, xs[3], ys[0] + 17)
    arrow(d, xs[2] + 20, ys[0], xs[1] + 46, ys[1] + box_h)
    arrow(d, xs[1] + box_w, ys[1] + 17, xs[2], ys[1] + 17)
    arrow(d, xs[2] + box_w, ys[1] + 17, xs[3], ys[1] + 17)
    arrow(d, xs[0] + box_w, ys[1] + 17, xs[2], ys[1] + 17)
    arrow(d, xs[2] + 18, ys[1], xs[0] + 46, ys[2] + box_h)
    arrow(d, xs[0] + box_w, ys[2] + 17, xs[1], ys[2] + 17)
    arrow(d, xs[2] + 46, ys[1], xs[2] + 46, ys[2] + box_h)
    arrow(d, xs[2] + box_w, ys[2] + 17, xs[3], ys[2] + 17)
    arrow(d, xs[2] + 20, ys[2], xs[0] + 46, ys[3] + box_h)
    arrow(d, xs[2] + 46, ys[2], xs[1] + 46, ys[3] + box_h)
    arrow(d, xs[2] + 70, ys[2], xs[2] + 46, ys[3] + box_h)
    arrow(d, xs[2] + box_w, ys[1], xs[3] + 46, ys[3] + box_h)
    arrow(d, xs[3] + 46, ys[3] + box_h, xs[1] + box_w, ys[1] + 5)

    d.add(String(14, 280, "Exchange business, secret, execution, and supplier boundaries", fontName=FONT_BOLD, fontSize=8, fillColor=FORTVAULT_BLUE))
    return d


def parse_table(lines: list[str], start: int, available_width: float):
    raw_rows = []
    index = start
    while index < len(lines) and lines[index].strip().startswith("|"):
        raw_rows.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
        index += 1
    if len(raw_rows) > 1 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in raw_rows[1]):
        raw_rows.pop(1)

    column_count = max(len(row) for row in raw_rows)
    if column_count == 2:
        widths = [available_width * 0.28, available_width * 0.72]
    elif column_count == 3:
        widths = [available_width * 0.22, available_width * 0.43, available_width * 0.35]
    else:
        widths = [available_width / column_count] * column_count

    rows = []
    for row_index, row in enumerate(raw_rows):
        style = STYLES["FVTableHeader"] if row_index == 0 else STYLES["FVTable"]
        rows.append([Paragraph(inline_markup(cell), style) for cell in row])

    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), FORTVAULT_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
                ("GRID", (0, 0), (-1, -1), 0.45, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table, index


def markdown_to_story(source: Path, product: str, available_width: float):
    lines = source.read_text(encoding="utf-8").splitlines()
    story = []
    index = 0
    diagram_added = False

    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue

        if line.startswith("```mermaid"):
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                index += 1
            index += 1
            diagram = custody_diagram() if product == "Custody" else exchange_diagram()
            if diagram.width > available_width:
                scale = available_width / diagram.width
                diagram.scale(scale, scale)
                diagram.width *= scale
                diagram.height *= scale
            story.append(KeepTogether([Paragraph("High-level architecture", STYLES["FVDiagramTitle"]), diagram]))
            story.append(Spacer(1, 3 * mm))
            diagram_added = True
            continue

        if line.startswith("# "):
            story.append(Spacer(1, 5 * mm))
            story.append(Paragraph(inline_markup(line[2:]), STYLES["FVTitle"]))
            index += 1
            continue
        if line.startswith("## "):
            text = line[3:]
            if text.startswith("2. Architecture") and not diagram_added:
                story.append(PageBreak())
            story.append(Paragraph(inline_markup(text), STYLES["FVH2"]))
            index += 1
            continue
        if line.startswith("### "):
            story.append(Paragraph(inline_markup(line[4:]), STYLES["FVH3"]))
            index += 1
            continue

        if line.startswith("|"):
            table, index = parse_table(lines, index, available_width)
            story.append(table)
            story.append(Spacer(1, 3 * mm))
            continue

        if line.startswith("- "):
            items = []
            while index < len(lines) and lines[index].strip().startswith("- "):
                items.append(
                    ListItem(
                        Paragraph(inline_markup(lines[index].strip()[2:]), STYLES["FVBody"]),
                        leftIndent=8,
                    )
                )
                index += 1
            story.append(
                ListFlowable(
                    items,
                    bulletType="bullet",
                    start="circle",
                    leftIndent=14,
                    bulletFontName=FONT_REGULAR,
                    bulletFontSize=6,
                    bulletColor=FORTVAULT_BLUE,
                    spaceAfter=2 * mm,
                )
            )
            continue

        if re.match(r"^\d+\.\s", line):
            items = []
            while index < len(lines) and re.match(r"^\d+\.\s", lines[index].strip()):
                item_text = re.sub(r"^\d+\.\s+", "", lines[index].strip())
                items.append(ListItem(Paragraph(inline_markup(item_text), STYLES["FVBody"]), leftIndent=10))
                index += 1
            story.append(
                ListFlowable(
                    items,
                    bulletType="1",
                    leftIndent=18,
                    bulletFontName=FONT_BOLD,
                    bulletFontSize=7,
                    bulletColor=FORTVAULT_BLUE,
                    spaceAfter=2 * mm,
                )
            )
            continue

        paragraph_lines = [line]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if (
                not candidate
                or candidate.startswith("#")
                or candidate.startswith("|")
                or candidate.startswith("-")
                or candidate.startswith("```")
                or re.match(r"^\d+\.\s", candidate)
            ):
                break
            paragraph_lines.append(candidate)
            index += 1
        story.append(Paragraph(inline_markup(" ".join(paragraph_lines)), STYLES["FVBody"]))

    return story


def draw_logo(canvas, x: float, y: float) -> None:
    canvas.saveState()
    canvas.setStrokeColor(FORTVAULT_BLUE)
    canvas.setLineWidth(2)
    canvas.circle(x, y, 6, stroke=1, fill=0)
    canvas.circle(x, y, 2, stroke=1, fill=0)
    for dx, dy in [(0, 9), (0, -9), (9, 0), (-9, 0), (6.4, 6.4), (-6.4, 6.4), (6.4, -6.4), (-6.4, -6.4)]:
        canvas.line(x + dx * 0.62, y + dy * 0.62, x + dx, y + dy)
    canvas.restoreState()


def page_decorator(product: str):
    def decorate(canvas, doc):
        canvas.saveState()
        width, height = A4
        draw_logo(canvas, doc.leftMargin, height - 16 * mm)
        canvas.setFont(FONT_BOLD, 8)
        canvas.setFillColor(DARK)
        canvas.drawString(doc.leftMargin + 13, height - 17.2 * mm, "FortVault")
        canvas.setFont(FONT_REGULAR, 6.5)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(width - doc.rightMargin, height - 17.2 * mm, f"{product} Technical Overview | Confidential")
        canvas.setStrokeColor(LINE)
        canvas.line(doc.leftMargin, height - 21 * mm, width - doc.rightMargin, height - 21 * mm)
        canvas.line(doc.leftMargin, 14 * mm, width - doc.rightMargin, 14 * mm)
        canvas.setFont(FONT_REGULAR, 6.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(doc.leftMargin, 9 * mm, "Supporting document for ISO/IEC 27001 implementation")
        canvas.drawRightString(width - doc.rightMargin, 9 * mm, f"Page {doc.page}")
        canvas.restoreState()

    return decorate


def generate(source_name: str, output_name: str, product: str) -> None:
    source = BASE_DIR / source_name
    output = OUTPUT_DIR / output_name
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=27 * mm,
        bottomMargin=20 * mm,
        title=f"FortVault {product} - Technical and Security Overview for ISO 27001 Implementation",
        author="FortVault",
        subject="Confidential technical architecture and security overview",
    )
    story = markdown_to_story(source, product, A4[0] - doc.leftMargin - doc.rightMargin)
    doc.build(story, onFirstPage=page_decorator(product), onLaterPages=page_decorator(product))


if __name__ == "__main__":
    generate(
        "FORTVAULT_CUSTODY_TECHNICAL_OVERVIEW.md",
        "FORTVAULT_CUSTODY_TECHNICAL_OVERVIEW.pdf",
        "Custody",
    )
    generate(
        "FORTVAULT_EXCHANGE_TECHNICAL_OVERVIEW.md",
        "FORTVAULT_EXCHANGE_TECHNICAL_OVERVIEW.pdf",
        "Exchange",
    )
