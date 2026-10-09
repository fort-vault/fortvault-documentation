#!/usr/bin/env python3
"""Generate the FortX component and integration architecture PDF."""

from math import atan2, cos, sin
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


DOCS_DIR = Path(__file__).resolve().parents[2]
OUTPUT = DOCS_DIR / "output" / "pdf" / "FortX_Component_Architecture.pdf"

BLUE = colors.HexColor("#003087")
INK = colors.HexColor("#0B1739")
MUTED = colors.HexColor("#667085")
LINE = colors.HexColor("#D8E0EC")
ZONE = colors.HexColor("#F8FAFD")
CLIENT = colors.HexColor("#EDF4FF")
SERVICE = colors.HexColor("#EDF8F2")
STORE = colors.HexColor("#FFF6E6")
SECURITY = colors.HexColor("#FFF0F0")
EXTERNAL = colors.HexColor("#F3F0FF")
PLANNED = colors.HexColor("#F5F5F7")
COMPLIANCE = colors.HexColor("#EEF8FB")
GREEN = colors.HexColor("#157A55")
AMBER = colors.HexColor("#A65A00")
GREY = colors.HexColor("#6B7280")


def register_fonts() -> tuple[str, str]:
    regular = Path("/System/Library/Fonts/Supplemental/Verdana.ttf")
    bold = Path("/System/Library/Fonts/Supplemental/Verdana Bold.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("FortXSans", str(regular)))
        pdfmetrics.registerFont(TTFont("FortXSans-Bold", str(bold)))
        return "FortXSans", "FortXSans-Bold"
    return "Helvetica", "Helvetica-Bold"


REGULAR, BOLD = register_fonts()


def text(c: Canvas, value: str, x: float, y: float, size: float, font=REGULAR, color=INK) -> None:
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawString(x, y, value)


def centered(c: Canvas, value: str, x: float, y: float, size: float, font=REGULAR, color=INK) -> None:
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawCentredString(x, y, value)


def wrap_lines(c: Canvas, value: str, font: str, size: float, width: float) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if c.stringWidth(candidate, font, size) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def wrapped(c: Canvas, value: str, x: float, y: float, width: float, size: float, font=REGULAR, color=INK, leading: float | None = None) -> float:
    leading = leading or size * 1.3
    lines = wrap_lines(c, value, font, size, width)
    for index, line in enumerate(lines):
        text(c, line, x, y - index * leading, size, font, color)
    return y - len(lines) * leading


def footer(c: Canvas, page: int, width: float) -> None:
    c.setStrokeColor(LINE)
    c.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)
    text(c, "FortX Component Architecture | Confidential", 18 * mm, 8 * mm, 6.8, REGULAR, MUTED)
    c.setFont(REGULAR, 6.8)
    c.setFillColor(MUTED)
    c.drawRightString(width - 18 * mm, 8 * mm, f"Page {page}")


def zone(c: Canvas, x: float, y: float, w: float, h: float, title: str, accent) -> None:
    c.setFillColor(ZONE)
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 8, stroke=1, fill=1)
    c.setFillColor(accent)
    c.roundRect(x, y + h - 34, w, 34, 8, stroke=0, fill=1)
    c.rect(x, y + h - 34, w, 8, stroke=0, fill=1)
    text(c, title, x + 11, y + h - 22, 8.8, BOLD)


def card(c: Canvas, x: float, y: float, w: float, h: float, title: str, body: list[str], fill, dashed: bool = False, title_size: float = 8.6, body_size: float = 6.4) -> None:
    c.saveState()
    c.setFillColor(fill)
    c.setStrokeColor(GREY if dashed else BLUE)
    c.setLineWidth(1.05)
    if dashed:
        c.setDash(4, 3)
    c.roundRect(x, y, w, h, 7, stroke=1, fill=1)
    c.restoreState()
    centered(c, title, x + w / 2, y + h - 19, title_size, BOLD)
    body_y = y + h - 35
    for index, line in enumerate(body):
        centered(c, line, x + w / 2, body_y - index * 10, body_size, REGULAR, MUTED)


def connector(c: Canvas, points: list[tuple[float, float]], label: str = "", label_at: tuple[float, float] | None = None, dashed: bool = False, bidirectional: bool = False) -> None:
    c.saveState()
    c.setStrokeColor(colors.HexColor("#6D7890"))
    c.setFillColor(colors.HexColor("#6D7890"))
    c.setLineWidth(1.05)
    if dashed:
        c.setDash(4, 3)
    path = c.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    c.drawPath(path, stroke=1, fill=0)

    def head(start: tuple[float, float], end: tuple[float, float]) -> None:
        angle = atan2(end[1] - start[1], end[0] - start[0])
        size = 5
        arrow = c.beginPath()
        arrow.moveTo(*end)
        arrow.lineTo(end[0] - size * cos(angle - 0.46), end[1] - size * sin(angle - 0.46))
        arrow.lineTo(end[0] - size * cos(angle + 0.46), end[1] - size * sin(angle + 0.46))
        arrow.close()
        c.drawPath(arrow, stroke=0, fill=1)

    head(points[-2], points[-1])
    if bidirectional:
        head(points[1], points[0])
    c.restoreState()
    if label and label_at:
        centered(c, label, label_at[0], label_at[1], 5.8, REGULAR, MUTED)


def status_pill(c: Canvas, x: float, y: float, label: str, fill, color) -> None:
    width = max(48, c.stringWidth(label, BOLD, 6.1) + 18)
    c.setFillColor(fill)
    c.roundRect(x, y, width, 16, 8, stroke=0, fill=1)
    centered(c, label, x + width / 2, y + 4.4, 6.1, BOLD, color)


def product_domain(c: Canvas, x: float, y: float, w: float, h: float) -> None:
    c.saveState()
    c.setFillColor(PLANNED)
    c.setStrokeColor(GREY)
    c.setLineWidth(1.1)
    c.setDash(5, 4)
    c.roundRect(x, y, w, h, 9, stroke=1, fill=1)
    c.restoreState()
    text(c, "Planned FortX Financial Domain", x + 14, y + h - 25, 10.4, BOLD)
    status_pill(c, x + w - 75, y + h - 30, "PLANNED", STORE, AMBER)
    modules = [
        ("Customer Accounts", "users, assets, ownership"),
        ("Double-entry Ledger", "available, held, settled"),
        ("Quotes and Swaps", "pricing, orders, fees"),
        ("Deposits / Withdrawals", "custody requests and results"),
        ("Reconciliation", "ledger, custody, venues"),
        ("Risk and Compliance", "KYC policy; KYT via FortVault"),
    ]
    chip_w = (w - 42) / 2
    chip_h = 50
    for index, (title, subtitle) in enumerate(modules):
        col = index % 2
        row = index // 2
        chip_x = x + 14 + col * (chip_w + 14)
        chip_y = y + h - 95 - row * 62
        card(c, chip_x, chip_y, chip_w, chip_h, title, [subtitle], colors.white, dashed=True, title_size=7.4, body_size=5.6)


def fortvault_boundary(c: Canvas, x: float, y: float, w: float, h: float) -> None:
    c.setFillColor(SERVICE)
    c.setStrokeColor(BLUE)
    c.setLineWidth(1.3)
    c.roundRect(x, y, w, h, 10, stroke=1, fill=1)
    text(c, "FortVault", x + 16, y + h - 31, 15, BOLD)
    status_pill(c, x + w - 88, y + h - 34, "ONE BOUNDARY", CLIENT, BLUE)
    centered(c, "Custody and Exchange", x + w / 2, y + h - 58, 8.0, BOLD, BLUE)
    centered(c, "Execution Platform", x + w / 2, y + h - 72, 8.0, BOLD, BLUE)
    bullets = [
        "versioned API and callbacks",
        "custody addresses and transfers",
        "MPC key generation and signing",
        "blockchain broadcast and confirmations",
        "exchange account setup and synchronization",
        "Chainalysis KYT screening",
        "normalized KYT results to FortX",
        "provider credentials stay in FortVault",
    ]
    for index, line in enumerate(bullets):
        bullet_y = y + h - 104 - index * 22
        c.setFillColor(BLUE)
        c.circle(x + 24, bullet_y + 3, 2.2, stroke=0, fill=1)
        text(c, line, x + 34, bullet_y, 6.0, REGULAR, MUTED)
    c.setFillColor(STORE)
    c.setStrokeColor(STORE)
    c.roundRect(x + 16, y + 16, w - 32, 52, 7, stroke=0, fill=1)
    centered(c, "Current exchange scope", x + w / 2, y + 51, 6.4, BOLD, AMBER)
    centered(c, "key setup, credential test, balances, permissions", x + w / 2, y + 37, 5.5, REGULAR, MUTED)
    centered(c, "and deposit addresses - no trading or withdrawals", x + w / 2, y + 25, 5.5, REGULAR, MUTED)


def draw_page_one(c: Canvas, width: float, height: float) -> None:
    margin = 18 * mm
    text(c, "FortX Product Architecture", margin, height - 21 * mm, 22, BOLD)
    text(c, "Current foundation, planned financial domain, FortVault boundary, exchange providers, and Chainalysis KYT", margin, height - 29 * mm, 9.7, REGULAR, BLUE)

    legend_y = height - 43 * mm
    legend = [
        (CLIENT, "Client"),
        (SERVICE, "Current platform"),
        (STORE, "Owned state"),
        (EXTERNAL, "External provider"),
        (PLANNED, "Planned component / connection"),
    ]
    legend_x = margin
    for fill, label in legend:
        c.setFillColor(fill)
        c.setStrokeColor(LINE)
        c.roundRect(legend_x, legend_y, 14, 9, 3, stroke=1, fill=1)
        text(c, label, legend_x + 19, legend_y + 2.2, 6.7, REGULAR, MUTED)
        legend_x += 130

    bottom = 24 * mm
    top = height - 56 * mm
    zone_h = top - bottom
    user_x, user_w = margin, 145
    identity_x, identity_w = user_x + user_w + 14, 165
    fortx_x, fortx_w = identity_x + identity_w + 14, 350
    fortvault_x, fortvault_w = fortx_x + fortx_w + 16, 220
    providers_x = fortvault_x + fortvault_w + 16
    providers_w = width - margin - providers_x

    zone(c, user_x, bottom, user_w, zone_h, "1. User Channels", CLIENT)
    zone(c, identity_x, bottom, identity_w, zone_h, "2. Identity and KYC", EXTERNAL)
    zone(c, fortx_x, bottom, fortx_w, zone_h, "3. FortX", SERVICE)
    zone(c, fortvault_x, bottom, fortvault_w, zone_h, "4. FortVault", SERVICE)
    zone(c, providers_x, bottom, providers_w, zone_h, "5. Providers", EXTERNAL)

    card(c, user_x + 17, 555, user_w - 34, 70, "FortX Mobile", ["Expo / React Native", "iOS and Android"], CLIENT)
    card(c, user_x + 17, 435, user_w - 34, 70, "FortX Web", ["Vite / React", "end-user browser"], CLIENT)
    wrapped(c, "Clients call FortX APIs only. They never call FortVault, exchanges, or KYT providers directly.", user_x + 17, 380, user_w - 34, 6.3, REGULAR, MUTED, 8.5)

    card(c, identity_x + 18, 555, identity_w - 36, 70, "Keycloak", ["OIDC identity", "users and administrators"], EXTERNAL)
    card(c, identity_x + 18, 435, identity_w - 36, 70, "Sumsub", ["KYC MobileSDK", "verified status webhooks"], EXTERNAL)
    wrapped(c, "Authentication and KYC are separate provider boundaries. FortX remains responsible for product access decisions.", identity_x + 18, 380, identity_w - 36, 6.3, REGULAR, MUTED, 8.5)

    card(c, fortx_x + 20, 555, fortx_w - 40, 78, "FortX Backend", ["current NestJS application foundation", "identity, KYC, API, health, logging"], SERVICE, title_size=10.0, body_size=6.8)
    card(c, fortx_x + 28, 488, (fortx_w - 70) / 2, 48, "FortX PostgreSQL", ["current identity/KYC state"], STORE, title_size=7.8, body_size=5.8)
    card(c, fortx_x + 42 + (fortx_w - 70) / 2, 488, (fortx_w - 70) / 2, 48, "FortX Redis", ["cache, rate limit, async infra"], STORE, title_size=7.8, body_size=5.8)
    product_domain(c, fortx_x + 20, 150, fortx_w - 40, 305)

    fortvault_boundary(c, fortvault_x + 15, 245, fortvault_w - 30, 385)
    wrapped(c, "FortX integrates through authenticated versioned APIs and validated callbacks/events. There is no direct FortVault database access.", fortvault_x + 18, 205, fortvault_w - 36, 6.2, REGULAR, MUTED, 8.5)

    provider_card_w = providers_w - 34
    provider_x = providers_x + 17
    card(c, provider_x, 575, provider_card_w, 48, "Binance", ["HMAC and MPC Ed25519"], EXTERNAL, title_size=8.2, body_size=5.9)
    card(c, provider_x, 510, provider_card_w, 48, "Gate.io", ["HMAC provider adapter"], EXTERNAL, title_size=8.2, body_size=5.9)
    card(c, provider_x, 445, provider_card_w, 48, "MEXC", ["HMAC provider adapter"], EXTERNAL, title_size=8.2, body_size=5.9)
    card(c, provider_x, 350, provider_card_w, 62, "Blockchain Networks", ["RPC, broadcast, confirmations", "and chain data providers"], EXTERNAL, title_size=8.0, body_size=5.8)
    card(c, provider_x, 190, provider_card_w, 95, "Chainalysis KYT", ["FortVault-owned provider boundary", "address and transaction risk", "alerts, cases and status"], COMPLIANCE, dashed=True, title_size=8.6, body_size=5.8)
    status_pill(c, provider_x + 9, 198, "PLANNED", STORE, AMBER)

    # Current authentication and KYC connections.
    connector(c, [(user_x + user_w - 17, 590), (identity_x + 18, 590)], "OIDC", ((user_x + user_w + identity_x) / 2, 599), bidirectional=True)
    connector(c, [(user_x + user_w - 17, 570), (identity_x + 8, 570), (identity_x + 8, 470), (identity_x + 18, 470)], "MobileSDK", (identity_x - 8, 516), bidirectional=True)
    connector(c, [(identity_x + identity_w - 18, 590), (fortx_x + 20, 590)], "token validation", ((identity_x + identity_w + fortx_x) / 2, 599))
    connector(c, [(identity_x + identity_w - 18, 470), (fortx_x + 8, 470), (fortx_x + 8, 572), (fortx_x + 20, 572)], "KYC API / webhook", (fortx_x - 12, 500), bidirectional=True)

    # Internal FortX and planned product integration.
    connector(c, [(fortx_x + fortx_w / 2, 555), (fortx_x + fortx_w / 2, 536)], "SQL / Redis", (fortx_x + fortx_w / 2 + 32, 540))
    connector(c, [(fortx_x + fortx_w / 2, 488), (fortx_x + fortx_w / 2, 455)], "planned services", (fortx_x + fortx_w / 2 + 42, 468), dashed=True)
    connector(c, [(fortx_x + fortx_w - 20, 342), (fortvault_x + 15, 342)], "custody / KYT API", ((fortx_x + fortx_w + fortvault_x) / 2, 351), dashed=True, bidirectional=True)

    # FortVault provider connections.
    connector(c, [(fortvault_x + fortvault_w - 15, 586), (providers_x + 17, 599)], "setup / sync", ((fortvault_x + fortvault_w + providers_x) / 2, 608), bidirectional=True)
    connector(c, [(fortvault_x + fortvault_w - 15, 555), (providers_x + 8, 555), (providers_x + 8, 534), (providers_x + 17, 534)], bidirectional=True)
    connector(c, [(fortvault_x + fortvault_w - 15, 520), (providers_x + 4, 520), (providers_x + 4, 469), (providers_x + 17, 469)], bidirectional=True)
    connector(c, [(fortvault_x + fortvault_w - 15, 400), (providers_x + 17, 381)], "custody chain flow", ((fortvault_x + fortvault_w + providers_x) / 2, 400), bidirectional=True)

    # Chainalysis is a FortVault provider; FortX reaches it through FortVault.
    connector(c, [(fortvault_x + fortvault_w - 15, 260), (providers_x + 17, 238)], "KYT request / result", ((fortvault_x + fortvault_w + providers_x) / 2, 268), dashed=True, bidirectional=True)

    footer(c, 1, width)


CONNECTIONS = [
    ("FortX Mobile/Web", "Keycloak", "OIDC/OAuth over TLS", "Authentication and token issuance", "Current"),
    ("FortX Mobile/Web", "FortX Backend", "Authenticated HTTPS API", "End-user product operations", "Current foundation"),
    ("FortX Mobile", "Sumsub MobileSDK", "Provider SDK", "User KYC interaction", "Current"),
    ("FortX Backend", "Sumsub", "Authenticated HTTPS API", "SDK token issuance and KYC status", "Current"),
    ("Sumsub", "FortX Backend", "HMAC-verified webhook", "Normalized KYC status changes", "Current"),
    ("FortX Backend", "FortX PostgreSQL", "PostgreSQL", "Identity/KYC and future financial state", "Current foundation"),
    ("FortX Backend", "FortX Redis", "Redis", "Cache, rate limiting and async infrastructure", "Current foundation"),
    ("FortX Backend", "Financial domain", "Internal services", "Ledger, quotes, swaps, deposits and withdrawals", "Planned"),
    ("FortX financial domain", "FortVault", "Versioned authenticated API", "Custody operations and KYT screening requests", "Planned"),
    ("FortVault", "FortX Backend", "Validated callback/event/API result", "Custody results and normalized KYT decisions", "Planned"),
    ("FortVault", "Chainalysis KYT", "Authenticated provider API", "Address/transaction screening and case queries", "Planned"),
    ("Chainalysis KYT", "FortVault", "Verified callback/polling", "Risk, alert, case and status updates", "Planned"),
    ("FortVault", "Blockchain networks", "Chain RPC/provider APIs", "Custody broadcast, confirmations and chain data", "Current FortVault"),
    ("FortVault", "Binance", "Authenticated exchange API", "Key setup, test, balance, permission, deposit sync", "Current limited"),
    ("FortVault", "Gate.io", "Authenticated exchange API", "Credential test, balance, permission, deposit sync", "Current limited"),
    ("FortVault", "MEXC", "Authenticated exchange API", "Credential test, balance, permission, deposit sync", "Current limited"),
]


def table_status(c: Canvas, value: str, x: float, y: float, w: float) -> None:
    if value == "Planned":
        fill, color = STORE, AMBER
    elif "limited" in value.lower():
        fill, color = CLIENT, BLUE
    elif "foundation" in value.lower():
        fill, color = COMPLIANCE, BLUE
    else:
        fill, color = SERVICE, GREEN
    c.setFillColor(fill)
    c.roundRect(x, y, w, 15, 7, stroke=0, fill=1)
    centered(c, value, x + w / 2, y + 4.2, 5.7, BOLD, color)


def draw_page_two(c: Canvas, width: float, height: float) -> None:
    margin = 18 * mm
    text(c, "FortX Connection and Status Register", margin, height - 21 * mm, 22, BOLD)
    text(c, "Current foundation and provider capabilities are separated from planned product integrations", margin, height - 29 * mm, 10, REGULAR, BLUE)

    table_x = margin
    table_top = height - 44 * mm
    table_w = width - 2 * margin
    columns = [175, 175, 190, table_w - 175 - 175 - 190 - 105, 105]
    headers = ["Source", "Destination", "Interface", "Purpose", "Status"]
    header_h = 27
    c.setFillColor(BLUE)
    c.roundRect(table_x, table_top - header_h, table_w, header_h, 5, stroke=0, fill=1)
    current_x = table_x
    for label, col_w in zip(headers, columns):
        text(c, label, current_x + 8, table_top - 17, 7.3, BOLD, colors.white)
        current_x += col_w

    row_h = 26
    y = table_top - header_h
    for index, row in enumerate(CONNECTIONS):
        y -= row_h
        c.setFillColor(colors.white if index % 2 == 0 else colors.HexColor("#F8FAFD"))
        c.setStrokeColor(LINE)
        c.rect(table_x, y, table_w, row_h, stroke=1, fill=1)
        current_x = table_x
        for col_index, (value, col_w) in enumerate(zip(row, columns)):
            if col_index == 4:
                table_status(c, value, current_x + 7, y + 5.3, col_w - 14)
            else:
                font = BOLD if col_index < 2 else REGULAR
                color = INK if col_index < 2 else MUTED
                line = value
                max_width = col_w - 16
                if c.stringWidth(line, font, 6.4) > max_width:
                    while line and c.stringWidth(f"{line}...", font, 6.4) > max_width:
                        line = line[:-1]
                    line = f"{line.rstrip()}..."
                text(c, line, current_x + 8, y + 9, 6.4, font, color)
            current_x += col_w

    notes_y = 43 * mm
    note_w = (table_w - 16) / 2
    c.setFillColor(STORE)
    c.setStrokeColor(colors.HexColor("#E7C78A"))
    c.roundRect(margin, notes_y, note_w, 74, 7, stroke=1, fill=1)
    text(c, "Exchange scope limitation", margin + 12, notes_y + 53, 8.8, BOLD, AMBER)
    wrapped(c, "Binance, Gate.io, and MEXC adapters currently support key setup and account synchronization operations. The diagram does not claim exchange trading or withdrawals.", margin + 12, notes_y + 38, note_w - 24, 6.7, REGULAR, MUTED, 9)

    note2_x = margin + note_w + 16
    c.setFillColor(COMPLIANCE)
    c.setStrokeColor(colors.HexColor("#A5CBD8"))
    c.roundRect(note2_x, notes_y, note_w, 74, 7, stroke=1, fill=1)
    text(c, "Chainalysis KYT target integration", note2_x + 12, notes_y + 53, 8.8, BOLD, BLUE)
    wrapped(c, "No Chainalysis integration was found in the reviewed source. FortVault will own the provider integration; FortX will submit KYT requests and receive normalized results only through FortVault.", note2_x + 12, notes_y + 38, note_w - 24, 6.7, REGULAR, MUTED, 9)
    footer(c, 2, width)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    width, height = landscape(A3)
    canvas = Canvas(str(OUTPUT), pagesize=(width, height))
    canvas.setTitle("FortX Component Architecture")
    canvas.setAuthor("FortX / FortVault")
    canvas.setSubject("FortX foundation, planned financial domain, FortVault boundary, exchange providers and Chainalysis KYT")
    draw_page_one(canvas, width, height)
    canvas.showPage()
    draw_page_two(canvas, width, height)
    canvas.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()
