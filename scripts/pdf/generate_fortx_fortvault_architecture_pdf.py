#!/usr/bin/env python3
"""Generate the FortX and FortVault platform architecture PDF."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


DOCS_DIR = Path(__file__).resolve().parents[2]
OUTPUT = DOCS_DIR / "output" / "pdf" / "FortVault_FortX_Platform_Architecture.pdf"

FORTVAULT_BLUE = colors.HexColor("#003087")
DARK = colors.HexColor("#0B1739")
MUTED = colors.HexColor("#6F7182")
LINE = colors.HexColor("#DDE3EE")
CLIENT = colors.HexColor("#EEF4FF")
SERVICE = colors.HexColor("#EEF8F2")
STORE = colors.HexColor("#FFF7E8")
SECURITY = colors.HexColor("#FFF0F0")
EXTERNAL = colors.HexColor("#F3F0FF")
FUTURE = colors.HexColor("#F5F5F7")


def register_fonts() -> tuple[str, str]:
    regular = Path("/System/Library/Fonts/Supplemental/Verdana.ttf")
    bold = Path("/System/Library/Fonts/Supplemental/Verdana Bold.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("FortVaultSans", str(regular)))
        pdfmetrics.registerFont(TTFont("FortVaultSans-Bold", str(bold)))
        return "FortVaultSans", "FortVaultSans-Bold"
    return "Helvetica", "Helvetica-Bold"


REGULAR, BOLD = register_fonts()


def text(c: Canvas, value: str, x: float, y: float, size: float, font: str, color=DARK) -> None:
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawString(x, y, value)


def centered(c: Canvas, value: str, x: float, y: float, size: float, font: str, color=DARK) -> None:
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawCentredString(x, y, value)


def wrapped(c: Canvas, value: str, x: float, y: float, width: float, size: float, font: str, color=DARK, leading: float | None = None) -> float:
    leading = leading or size * 1.34
    words = value.split()
    line = ""
    lines: list[str] = []
    c.setFont(font, size)
    for word in words:
        candidate = word if not line else f"{line} {word}"
        if c.stringWidth(candidate, font, size) <= width:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    c.setFillColor(color)
    for index, line in enumerate(lines):
        c.drawString(x, y - index * leading, line)
    return y - len(lines) * leading


def box(c: Canvas, x: float, y: float, w: float, h: float, title: str, subtitle: str, fill, dashed: bool = False) -> None:
    c.saveState()
    c.setFillColor(fill)
    c.setStrokeColor(FORTVAULT_BLUE if not dashed else MUTED)
    c.setLineWidth(1.1)
    if dashed:
        c.setDash(5, 4)
    c.roundRect(x, y, w, h, 5 * mm, stroke=1, fill=1)
    c.restoreState()
    centered(c, title, x + w / 2, y + h - 15 * mm, 10.2, BOLD)
    lines = subtitle.split("\n")
    for index, line in enumerate(lines):
        centered(c, line, x + w / 2, y + h - 22 * mm - index * 4.6 * mm, 7.1, REGULAR, MUTED)


def arrow(c: Canvas, x1: float, y1: float, x2: float, y2: float, label: str = "", dashed: bool = False) -> None:
    c.saveState()
    c.setStrokeColor(MUTED)
    c.setFillColor(MUTED)
    c.setLineWidth(0.9)
    if dashed:
        c.setDash(4, 3)
    c.line(x1, y1, x2, y2)
    angle = __import__("math").atan2(y2 - y1, x2 - x1)
    size = 5
    points = [
        (x2, y2),
        (x2 - size * __import__("math").cos(angle - 0.45), y2 - size * __import__("math").sin(angle - 0.45)),
        (x2 - size * __import__("math").cos(angle + 0.45), y2 - size * __import__("math").sin(angle + 0.45)),
    ]
    path = c.beginPath()
    path.moveTo(*points[0])
    path.lineTo(*points[1])
    path.lineTo(*points[2])
    path.close()
    c.drawPath(path, stroke=0, fill=1)
    c.restoreState()
    if label:
        centered(c, label, (x1 + x2) / 2, (y1 + y2) / 2 + 4, 6.4, REGULAR, MUTED)


def section(c: Canvas, title: str, x: float, y: float, w: float, color) -> None:
    c.setFillColor(color)
    c.roundRect(x, y, w, 20, 7, stroke=0, fill=1)
    text(c, title, x + 10, y + 6.3, 8.6, BOLD, DARK)


def component_card(
    c: Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: list[str],
    fill,
    dashed: bool = False,
    title_size: float = 10.5,
    body_size: float = 7.6,
) -> None:
    """Draw a deliberately sparse component card for the overview page."""
    c.saveState()
    c.setFillColor(fill)
    c.setStrokeColor(MUTED if dashed else FORTVAULT_BLUE)
    c.setLineWidth(1.2)
    if dashed:
        c.setDash(5, 4)
    c.roundRect(x, y, w, h, 5 * mm, stroke=1, fill=1)
    c.restoreState()

    title_y = y + h - 22
    centered(c, title, x + w / 2, title_y, title_size, BOLD)
    if body:
        start_y = title_y - 20
        for index, line in enumerate(body):
            centered(c, line, x + w / 2, start_y - index * 12, body_size, REGULAR, MUTED)


def footer(c: Canvas, page: int, width: float) -> None:
    c.setStrokeColor(LINE)
    c.line(18 * mm, 16 * mm, width - 18 * mm, 16 * mm)
    text(c, "FortVault + FortX Platform Architecture | Confidential", 18 * mm, 9 * mm, 6.8, REGULAR, MUTED)
    c.drawRightString(width - 18 * mm, 9 * mm, f"Page {page}")


def draw_page_one(c: Canvas, width: float, height: float) -> None:
    text(c, "FortVault + FortX Platform Architecture", 18 * mm, height - 21 * mm, 22, BOLD)
    text(c, "High-level custody and product boundary. Dashed components are planned, not deployed flows.", 18 * mm, height - 29 * mm, 10, REGULAR, FORTVAULT_BLUE)

    left = 18 * mm
    right = width - 18 * mm
    core_y = height - 108 * mm
    card_w = 172
    card_h = 37 * mm
    gap = 11.2
    core_x = [left + index * (card_w + gap) for index in range(6)]

    text(c, "Primary product and custody path", left, core_y + card_h + 14 * mm, 11, BOLD)
    component_card(c, core_x[0], core_y, card_w, card_h, "FortX Clients", ["Mobile and web", "end-user interface"], CLIENT)
    component_card(c, core_x[1], core_y, card_w, card_h, "Identity and KYC", ["Keycloak", "Sumsub"], EXTERNAL)
    component_card(c, core_x[2], core_y, card_w, card_h, "FortX Backend", ["Current foundation", "API, KYC, health"], SERVICE)
    component_card(c, core_x[3], core_y, card_w, card_h, "Financial Domain", ["Ledger, deposits,", "swaps and withdrawals"], FUTURE, dashed=True)
    component_card(c, core_x[4], core_y, card_w, card_h, "FortVault Control", ["Backend", "actions and approvals"], SERVICE)
    component_card(c, core_x[5], core_y, card_w, card_h, "Custody Boundary", ["Processing and", "partner MPC cluster"], SECURITY)

    for index in range(5):
        arrow(c, core_x[index] + card_w, core_y + card_h / 2, core_x[index + 1], core_y + card_h / 2, dashed=index == 2)
    centered(c, "planned FortX to FortVault integration", core_x[3] + card_w / 2, core_y - 13, 7.2, REGULAR, MUTED)

    c.setStrokeColor(LINE)
    c.line(left, core_y - 30, right, core_y - 30)
    text(c, "Current FortVault supporting components", left, core_y - 49, 11, BOLD)

    support_y = core_y - 150
    support_w = 205
    support_h = 25 * mm
    support_gap = 15.75
    support_x = [left + index * (support_w + support_gap) for index in range(5)]
    component_card(c, support_x[0], support_y, support_w, support_h, "FortVault Frontend", ["partner and administrator dashboard"], CLIENT, title_size=9.4, body_size=6.9)
    component_card(c, support_x[1], support_y, support_w, support_h, "Backend PostgreSQL", ["business and audit system of record"], STORE, title_size=9.4, body_size=6.9)
    component_card(c, support_x[2], support_y, support_w, support_h, "Redis Streams", ["typed asynchronous transport only"], STORE, title_size=9.4, body_size=6.9)
    component_card(c, support_x[3], support_y, support_w, support_h, "Listener and Notification", ["chain events; email and Telegram"], SERVICE, title_size=9.4, body_size=6.9)
    component_card(c, support_x[4], support_y, support_w, support_h, "Exchange Processing", ["current read-only account synchronization"], SERVICE, title_size=9.4, body_size=6.9)

    text(c, "Custody dependencies and external execution", left, support_y - 34, 11, BOLD)
    external_y = support_y - 130
    external_w = 172
    external_h = 24 * mm
    external_gap = 11.2
    external_x = [left + index * (external_w + external_gap) for index in range(6)]
    component_card(c, external_x[0], external_y, external_w, external_h, "MPC Storage", ["key shares and session state"], STORE, title_size=8.6, body_size=6.2)
    component_card(c, external_x[1], external_y, external_w, external_h, "Policy Contracts", ["on-chain policy and verification"], EXTERNAL, title_size=8.6, body_size=6.2)
    component_card(c, external_x[2], external_y, external_w, external_h, "Secret Store", ["runtime secret material only"], SECURITY, title_size=8.6, body_size=6.2)
    component_card(c, external_x[3], external_y, external_w, external_h, "Blockchain RPC", ["broadcast, confirmations, chain data"], EXTERNAL, title_size=8.6, body_size=6.2)
    component_card(c, external_x[4], external_y, external_w, external_h, "External Exchanges", ["read-only provider integration"], EXTERNAL, title_size=8.6, body_size=6.2)
    component_card(c, external_x[5], external_y, external_w, external_h, "Notification Channels", ["email and Telegram suppliers"], EXTERNAL, title_size=8.3, body_size=6.0)

    note_y = 110
    c.setFillColor(FUTURE)
    c.setStrokeColor(MUTED)
    c.setDash(4, 3)
    c.roundRect(left, note_y, right - left, 27, 5, stroke=1, fill=1)
    c.setDash()
    text(c, "Scope note", left + 10, note_y + 16, 8.4, BOLD)
    text(c, "FortX financial operations and its FortVault API integration are planned. Current FortVault Exchange Processing is read-only exchange-account synchronization.", left + 70, note_y + 16, 7.7, REGULAR, MUTED)
    footer(c, 1, width)


def draw_page_two(c: Canvas, width: float, height: float) -> None:
    text(c, "Ownership and Trust Boundaries", 18 * mm, height - 21 * mm, 22, BOLD)
    text(c, "Interpretation notes for the FortX + FortVault platform diagram", 18 * mm, height - 29 * mm, 10, REGULAR, FORTVAULT_BLUE)

    rows = [
        ("FortX clients", "End-user presentation only. They use FortX Backend APIs and do not call FortVault directly in the normal product flow."),
        ("FortX Backend", "Current foundation includes identity/KYC integration, PostgreSQL, Redis, health, logging, and secret loading. The ledger, swaps, deposits, withdrawals, and FortVault integration remain planned."),
        ("FortVault Backend", "Business-control system of record for partner/workspace, customers, vaults, actions, approvals, and audit history. It is not a cryptographic signer."),
        ("Custody Processing", "Execution owner for address generation, transaction construction, MPC coordination, broadcast, retries, and reconciliation. It owns its own execution state."),
        ("MPC", "Cryptographic boundary. A separate cluster is deployed per partner; key shares remain in MPC node storage. MPC independently validates signing authorization."),
        ("Redis Streams", "Typed asynchronous transport. It is not the durable source of business or financial truth."),
        ("Exchange Processing", "Current scope is read-only exchange-account synchronization. Trading and exchange withdrawals are not part of the implemented scope."),
        ("External suppliers", "Keycloak, Sumsub, blockchain RPC/networks, external exchanges, and notification channels are separate supplier/trust boundaries."),
    ]

    y = height - 49 * mm
    left = 18 * mm
    label_w = 63 * mm
    body_w = width - left * 2 - label_w
    for label, body in rows:
        c.setFillColor(colors.white)
        c.setStrokeColor(LINE)
        c.roundRect(left, y - 28, label_w + body_w, 34, 4, stroke=1, fill=1)
        c.setFillColor(CLIENT)
        c.roundRect(left, y - 28, label_w, 34, 4, stroke=0, fill=1)
        wrapped(c, label, left + 7, y - 5, label_w - 14, 8.2, BOLD)
        wrapped(c, body, left + label_w + 8, y - 5, body_w - 16, 8.2, REGULAR)
        y -= 43

    note_y = 54 * mm
    c.setFillColor(SECURITY)
    c.setStrokeColor(colors.HexColor("#E69AA4"))
    c.roundRect(left, note_y, width - left * 2, 47, 6, stroke=1, fill=1)
    text(c, "ISO evidence note", left + 10, note_y + 33, 9, BOLD)
    wrapped(
        c,
        "The diagram describes application architecture and intended trust boundaries. It does not prove live cloud configuration, TLS termination, network segmentation, backup effectiveness, patch compliance, monitoring, or operational access control. Those controls require separate production evidence.",
        left + 10,
        note_y + 22,
        width - left * 2 - 20,
        8,
        REGULAR,
    )
    footer(c, 2, width)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    width, height = landscape(A3)
    canvas = Canvas(str(OUTPUT), pagesize=(width, height))
    canvas.setTitle("FortVault + FortX Platform Architecture")
    canvas.setAuthor("FortVault")
    canvas.setSubject("Current components and planned FortX-FortVault integration boundary")
    draw_page_one(canvas, width, height)
    canvas.showPage()
    draw_page_two(canvas, width, height)
    canvas.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()
