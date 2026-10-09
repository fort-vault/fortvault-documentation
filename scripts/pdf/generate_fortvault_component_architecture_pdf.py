#!/usr/bin/env python3
"""Generate the FortVault component and connection architecture PDF."""

from math import atan2, cos, sin
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


DOCS_DIR = Path(__file__).resolve().parents[2]
OUTPUT = DOCS_DIR / "output" / "pdf" / "FortVault_Component_Architecture.pdf"

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
OPERATIONS = colors.HexColor("#EEF8FB")
PROTOTYPE = colors.HexColor("#F5F5F7")
GREEN = colors.HexColor("#157A55")
AMBER = colors.HexColor("#A65A00")


def register_fonts() -> tuple[str, str]:
    regular = Path("/System/Library/Fonts/Supplemental/Verdana.ttf")
    bold = Path("/System/Library/Fonts/Supplemental/Verdana Bold.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("FortVaultSans", str(regular)))
        pdfmetrics.registerFont(TTFont("FortVaultSans-Bold", str(bold)))
        return "FortVaultSans", "FortVaultSans-Bold"
    return "Helvetica", "Helvetica-Bold"


REGULAR, BOLD = register_fonts()


def draw_text(c: Canvas, value: str, x: float, y: float, size: float, font=REGULAR, color=INK) -> None:
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawString(x, y, value)


def draw_centered(c: Canvas, value: str, x: float, y: float, size: float, font=REGULAR, color=INK) -> None:
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawCentredString(x, y, value)


def wrapped_lines(c: Canvas, value: str, font: str, size: float, width: float) -> list[str]:
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


def draw_wrapped(
    c: Canvas,
    value: str,
    x: float,
    y: float,
    width: float,
    size: float,
    font=REGULAR,
    color=INK,
    leading: float | None = None,
) -> float:
    leading = leading or size * 1.3
    lines = wrapped_lines(c, value, font, size, width)
    for index, line in enumerate(lines):
        draw_text(c, line, x, y - index * leading, size, font, color)
    return y - len(lines) * leading


def footer(c: Canvas, page: int, width: float) -> None:
    c.setStrokeColor(LINE)
    c.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)
    draw_text(c, "FortVault Component Architecture | Confidential", 18 * mm, 8 * mm, 6.8, REGULAR, MUTED)
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
    draw_text(c, title, x + 12, y + h - 22, 9.2, BOLD)


def card(
    c: Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: list[str],
    fill,
    title_size: float = 8.6,
    body_size: float = 6.6,
    dashed: bool = False,
) -> None:
    c.saveState()
    c.setFillColor(fill)
    c.setStrokeColor(MUTED if dashed else BLUE)
    c.setLineWidth(1.05)
    if dashed:
        c.setDash(4, 3)
    c.roundRect(x, y, w, h, 7, stroke=1, fill=1)
    c.restoreState()
    draw_centered(c, title, x + w / 2, y + h - 19, title_size, BOLD)
    body_y = y + h - 35
    for index, line in enumerate(body):
        draw_centered(c, line, x + w / 2, body_y - index * 10, body_size, REGULAR, MUTED)


def db_card(c: Canvas, x: float, y: float, w: float, title: str, body: str) -> None:
    card(c, x, y, w, 43, title, [body], STORE, 7.7, 5.9)


def connector(
    c: Canvas,
    points: list[tuple[float, float]],
    label: str = "",
    label_at: tuple[float, float] | None = None,
    dashed: bool = False,
    bidirectional: bool = False,
) -> None:
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
        arrow_path = c.beginPath()
        arrow_path.moveTo(*end)
        arrow_path.lineTo(end[0] - size * cos(angle - 0.46), end[1] - size * sin(angle - 0.46))
        arrow_path.lineTo(end[0] - size * cos(angle + 0.46), end[1] - size * sin(angle + 0.46))
        arrow_path.close()
        c.drawPath(arrow_path, stroke=0, fill=1)

    head(points[-2], points[-1])
    if bidirectional:
        head(points[1], points[0])
    c.restoreState()
    if label and label_at:
        draw_centered(c, label, label_at[0], label_at[1], 5.8, REGULAR, MUTED)


def mpc_card(c: Canvas, x: float, y: float, w: float, h: float) -> None:
    c.setFillColor(SECURITY)
    c.setStrokeColor(BLUE)
    c.setLineWidth(1.1)
    c.roundRect(x, y, w, h, 7, stroke=1, fill=1)
    draw_centered(c, "Partner-specific MPC Cluster", x + w / 2, y + h - 18, 8.6, BOLD)
    node_y = y + 28
    node_x = [x + w * 0.28, x + w * 0.5, x + w * 0.72]
    c.setStrokeColor(MUTED)
    c.setLineWidth(0.8)
    c.line(node_x[0], node_y, node_x[1], node_y)
    c.line(node_x[1], node_y, node_x[2], node_y)
    c.line(node_x[0], node_y, node_x[2], node_y)
    for index, current_x in enumerate(node_x, 1):
        c.setFillColor(colors.white)
        c.setStrokeColor(BLUE)
        c.circle(current_x, node_y, 10, stroke=1, fill=1)
        draw_centered(c, str(index), current_x, node_y - 3, 6.5, BOLD, BLUE)
    draw_centered(c, "encrypted peer protocol", x + w / 2, y + 8, 5.8, REGULAR, MUTED)


def draw_page_one(c: Canvas, width: float, height: float) -> None:
    margin = 18 * mm
    draw_text(c, "FortVault Runtime Architecture", margin, height - 21 * mm, 22, BOLD)
    draw_text(c, "Components, owned state, runtime connections, and trust boundaries", margin, height - 29 * mm, 10, REGULAR, BLUE)

    legend_y = height - 43 * mm
    legend = [
        (CLIENT, "User/client"),
        (SERVICE, "Service"),
        (STORE, "Owned durable state"),
        (SECURITY, "Cryptographic/secret boundary"),
        (EXTERNAL, "External/on-chain"),
        (OPERATIONS, "Operational control"),
    ]
    legend_x = margin
    for fill, label in legend:
        c.setFillColor(fill)
        c.setStrokeColor(LINE)
        c.roundRect(legend_x, legend_y, 14, 9, 3, stroke=1, fill=1)
        draw_text(c, label, legend_x + 19, legend_y + 2.2, 6.7, REGULAR, MUTED)
        legend_x += 110

    bottom = 24 * mm
    top = height - 56 * mm
    zone_h = top - bottom
    control_x, control_w = margin, 390
    transport_x, transport_w = control_x + control_w + 16, 150
    execution_x, execution_w = transport_x + transport_w + 16, 240
    external_x = execution_x + execution_w + 16
    external_w = width - margin - external_x

    zone(c, control_x, bottom, control_w, zone_h, "1. User and Business Control", CLIENT)
    zone(c, transport_x, bottom, transport_w, zone_h, "2. Messaging", STORE)
    zone(c, execution_x, bottom, execution_w, zone_h, "3. Execution Services", SERVICE)
    zone(c, external_x, bottom, external_w, zone_h, "4. Cryptographic and External", SECURITY)

    # User and business control.
    card(c, control_x + 18, 565, 110, 58, "Authorized Users", ["administrators", "and approvers"], CLIENT)
    card(c, control_x + 145, 565, 110, 58, "Frontend", ["partner/admin", "dashboard"], CLIENT)
    card(c, control_x + 272, 565, 100, 58, "Backend", ["business control", "and approvals"], SERVICE)
    connector(c, [(control_x + 128, 594), (control_x + 145, 594)], "HTTPS", (control_x + 136, 601))
    connector(c, [(control_x + 255, 594), (control_x + 272, 594)], "API", (control_x + 263, 601))

    card(c, control_x + 18, 470, 125, 50, "External API Clients", ["authenticated partner API"], CLIENT, 8.0, 6.1)
    db_card(c, control_x + 235, 470, 137, "Backend PostgreSQL", "business, audit, inbox/outbox")
    connector(c, [(control_x + 143, 495), (control_x + 200, 495), (control_x + 200, 565), (control_x + 322, 565)], "authenticated API", (control_x + 197, 504))
    connector(c, [(control_x + 322, 565), (control_x + 322, 520), (control_x + 303, 520), (control_x + 303, 513)], "SQL", (control_x + 337, 532))

    card(c, control_x + 18, 325, 160, 68, "Approved Secret Store", ["runtime credentials and", "configuration references"], SECURITY)
    card(c, control_x + 212, 325, 160, 68, "Health Audit", ["read-only liveness, readiness,", "config and stream checks"], OPERATIONS)
    draw_wrapped(c, "Cross-cutting controls: the secret store supplies only authorized runtimes; Health Audit reads protected sanitized endpoints and broker metadata.", control_x + 18, 286, control_w - 36, 6.7, REGULAR, MUTED, 9)

    # Messaging spine.
    card(c, transport_x + 20, 250, transport_w - 40, 340, "Redis Streams", ["typed commands", "and events", "", "consumer groups", "and acknowledgements", "", "transport only", "not business state"], STORE, 9.2, 6.5)
    draw_centered(c, "FortVault Messaging", transport_x + transport_w / 2, 225, 7.4, BOLD)
    draw_centered(c, "shared envelope and payload contracts", transport_x + transport_w / 2, 211, 5.8, REGULAR, MUTED)

    # Execution services and owned state.
    card(c, execution_x + 18, 545, execution_w - 36, 70, "Custody Processing", ["address generation, transaction construction,", "MPC coordination, broadcast and retries"], SERVICE, 9.2, 6.3)
    db_card(c, execution_x + 45, 487, execution_w - 90, "Processing PostgreSQL", "execution, roots, addresses, MPC, inbox/outbox")
    card(c, execution_x + 18, 390, execution_w - 36, 62, "Listener", ["tracked addresses, provider events,", "normalized chain activity"], SERVICE, 9.0, 6.3)
    db_card(c, execution_x + 45, 337, execution_w - 90, "Listener PostgreSQL", "tracked addresses and idempotent event state")
    card(c, execution_x + 18, 245, execution_w - 36, 62, "Notification", ["Telegram delivery", "email adapter currently placeholder"], SERVICE, 9.0, 6.3)
    card(c, execution_x + 18, 132, execution_w - 36, 70, "Exchange Processing", ["Ed25519 keygen/signing, credential tests,", "balance, permission and deposit-address sync"], SERVICE, 8.8, 6.1)
    db_card(c, execution_x + 45, 78, execution_w - 90, "Exchange PostgreSQL", "requests, leases, sessions, attempts, inbox/outbox")

    # Cryptographic and external boundaries.
    mpc_card(c, external_x + 18, 545, external_w - 36, 76)
    db_card(c, external_x + 45, 487, external_w - 90, "MPC Node Storage", "separate encrypted shares and session state per node")
    card(c, external_x + 18, 382, external_w - 36, 72, "Blockchain RPC, Data Providers and Networks", ["transaction broadcast and confirmations", "provider callbacks and chain data"], EXTERNAL, 8.1, 6.1)
    card(c, external_x + 18, 298, external_w - 36, 58, "Policy and Verification Contracts", ["registry, policy and address verification"], EXTERNAL, 8.1, 6.2)
    card(c, external_x + 18, 228, external_w - 36, 48, "Telegram Bot API", ["implemented notification channel"], EXTERNAL, 8.3, 6.2)
    card(c, external_x + 18, 142, external_w - 36, 64, "External Exchange APIs", ["Binance, Gate, MEXC", "no trading or withdrawals in current scope"], EXTERNAL, 8.4, 6.0)

    # Core runtime connections. Labels are intentionally brief; page two is authoritative.
    connector(c, [(control_x + 372, 594), (transport_x + 20, 594)], "commands / events", ((control_x + 372 + transport_x + 20) / 2, 603), bidirectional=True)
    connector(c, [(transport_x + transport_w - 20, 580), (execution_x + 18, 580)], "custody commands", ((transport_x + transport_w - 20 + execution_x + 18) / 2, 589))
    connector(c, [(transport_x + transport_w - 20, 421), (execution_x + 18, 421)], "chain events", ((transport_x + transport_w - 20 + execution_x + 18) / 2, 430), bidirectional=True)
    connector(c, [(transport_x + transport_w - 20, 276), (execution_x + 18, 276)], "notify", ((transport_x + transport_w - 20 + execution_x + 18) / 2, 285))
    connector(c, [(transport_x + transport_w - 20, 167), (execution_x + 18, 167)], "exchange ops", ((transport_x + transport_w - 20 + execution_x + 18) / 2, 176), bidirectional=True)

    connector(c, [(execution_x + execution_w - 18, 580), (external_x + 18, 580)], "HTTPS derive / sign", ((execution_x + execution_w - 18 + external_x + 18) / 2, 589))
    connector(c, [(external_x + external_w / 2, 545), (external_x + external_w / 2, 530)], "encrypted storage", (external_x + external_w / 2 + 49, 535))
    connector(c, [(execution_x + execution_w - 18, 558), (external_x - 8, 558), (external_x - 8, 430), (external_x + 18, 430)], "broadcast", (external_x - 25, 469))
    connector(c, [(external_x + 18, 410), (execution_x + execution_w - 18, 410)], "provider events", ((execution_x + execution_w - 18 + external_x + 18) / 2, 419))
    connector(c, [(execution_x + execution_w - 18, 276), (external_x + 18, 252)], "Telegram", ((execution_x + execution_w + external_x) / 2, 274))
    connector(c, [(execution_x + execution_w - 18, 167), (external_x + 18, 174)], "authenticated provider API", ((execution_x + execution_w - 18 + external_x + 18) / 2, 180), bidirectional=True)

    # Local persistence connections.
    connector(c, [(execution_x + execution_w / 2, 545), (execution_x + execution_w / 2, 530)], "SQL", (execution_x + execution_w / 2 + 20, 534))
    connector(c, [(execution_x + execution_w / 2, 390), (execution_x + execution_w / 2, 380)], "SQL", (execution_x + execution_w / 2 + 20, 382))
    connector(c, [(execution_x + execution_w / 2, 132), (execution_x + execution_w / 2, 121)], "SQL", (execution_x + execution_w / 2 + 20, 123))

    draw_text(c, "Policy reads", external_x + 24, 286, 6.2, BOLD, MUTED)
    draw_wrapped(c, "Backend, Custody Processing, and MPC read policy/verification contracts. These cross-cutting reads are listed explicitly on page 2.", external_x + 84, 286, external_w - 100, 5.8, REGULAR, MUTED, 8)
    footer(c, 1, width)


CONNECTIONS = [
    ("Authorized user", "Frontend", "HTTPS", "Custody administration, review and approval", "Current"),
    ("Frontend", "Backend", "Authenticated HTTPS API", "Partner-scoped business operations", "Current"),
    ("External API client", "Backend", "Authenticated HTTPS API", "Partner API integration where enabled", "Current"),
    ("Backend", "Backend PostgreSQL", "PostgreSQL", "Business, audit, inbox and outbox state", "Current"),
    ("Backend", "Redis Streams", "Typed Messaging envelopes", "Publish commands and consume completion events", "Current"),
    ("Redis Streams", "Custody Processing", "Consumer group", "Address and transfer execution commands", "Current"),
    ("Custody Processing", "Redis Streams", "Durable outbox", "Address and transfer completion events", "Current"),
    ("Custody Processing", "Processing PostgreSQL", "PostgreSQL", "Execution, retries, roots, addresses and MPC state", "Current"),
    ("Custody Processing", "MPC master node", "Authenticated HTTP API", "Bootstrap keygen, derivation and exact-payload signing", "Current"),
    ("MPC node", "MPC peers", "Encrypted gRPC", "Interactive threshold cryptographic protocol", "Current"),
    ("MPC node", "Own node storage", "PostgreSQL/local boundary", "Encrypted key share and MPC session state", "Current"),
    ("Backend", "Policy contracts", "Blockchain read calls", "Read partner policy and verification configuration", "Current"),
    ("Custody Processing", "Policy contracts", "Blockchain read calls", "Validate wallet types, policy and execution context", "Current"),
    ("MPC cluster", "Policy contracts", "Blockchain read calls", "Independent authorization and policy validation", "Current"),
    ("Custody Processing", "RPC / blockchain", "Chain-specific RPC", "Build, broadcast and query custody transactions", "Current"),
    ("Chain data provider", "Listener", "Webhook / polling API", "Chain activity and confirmation data", "Current"),
    ("Listener", "Listener PostgreSQL", "PostgreSQL", "Tracked addresses and idempotent event state", "Current"),
    ("Listener", "Redis Streams", "Typed normalized events", "Deposits, confirmations and transaction status", "Current"),
    ("Redis Streams", "Notification", "Consumer group", "Notification commands", "Current"),
    ("Notification", "Telegram Bot API", "HTTPS provider API", "Configured Telegram delivery", "Current"),
    ("Notification", "Email adapter", "Internal adapter", "Logs intended email; provider not yet integrated", "Placeholder"),
    ("Redis Streams", "Exchange Processing", "Consumer group", "Exchange operation commands", "Current"),
    ("Exchange Processing", "Exchange PostgreSQL", "PostgreSQL", "Requests, leases, sessions, attempts and outbox", "Current"),
    ("Exchange Processing", "MPC master node", "Authenticated HTTP API", "Ed25519 key generation and exact query signing", "Current"),
    ("Exchange Processing", "Exchange APIs", "Authenticated HTTPS API", "Credential test, balance, permission and deposit sync", "Current"),
    ("Exchange Processing", "Redis Streams", "Durable outbox", "Sanitized exchange completion events", "Current"),
    ("Approved secret store", "Authorized services", "Secret-management API", "Runtime configuration and credential material", "Current"),
    ("Health Audit", "Service / MPC health", "Read-only HTTPS", "Liveness, readiness and sanitized configuration", "Current"),
    ("Health Audit", "Redis metadata", "Read-only Redis commands", "Expected streams and consumer groups", "Current"),
]


def status_badge(c: Canvas, value: str, x: float, y: float, w: float) -> None:
    fill = SERVICE if value == "Current" else STORE
    color = GREEN if value == "Current" else AMBER
    c.setFillColor(fill)
    c.setStrokeColor(fill)
    c.roundRect(x, y, w, 14, 7, stroke=0, fill=1)
    draw_centered(c, value, x + w / 2, y + 3.7, 5.7, BOLD, color)


def draw_page_two(c: Canvas, width: float, height: float) -> None:
    margin = 18 * mm
    draw_text(c, "FortVault Connection Register", margin, height - 21 * mm, 22, BOLD)
    draw_text(c, "Authoritative summary of the runtime connections shown on page 1", margin, height - 29 * mm, 10, REGULAR, BLUE)

    table_x = margin
    table_top = height - 43 * mm
    table_w = width - 2 * margin
    columns = [150, 165, 175, table_w - 150 - 165 - 175 - 82, 82]
    headers = ["Source", "Destination", "Interface", "Purpose", "Status"]
    header_h = 25
    c.setFillColor(BLUE)
    c.roundRect(table_x, table_top - header_h, table_w, header_h, 5, stroke=0, fill=1)
    current_x = table_x
    for label, col_w in zip(headers, columns):
        draw_text(c, label, current_x + 7, table_top - 16, 7.2, BOLD, colors.white)
        current_x += col_w

    row_h = 17.0
    y = table_top - header_h
    for index, row in enumerate(CONNECTIONS):
        y -= row_h
        c.setFillColor(colors.white if index % 2 == 0 else colors.HexColor("#F8FAFD"))
        c.setStrokeColor(LINE)
        c.rect(table_x, y, table_w, row_h, stroke=1, fill=1)
        current_x = table_x
        for col_index, (value, col_w) in enumerate(zip(row, columns)):
            if col_index == 4:
                status_badge(c, value, current_x + 7, y + 1.5, col_w - 14)
            else:
                font = BOLD if col_index < 2 else REGULAR
                color = INK if col_index < 2 else MUTED
                line = value
                max_width = col_w - 14
                if c.stringWidth(line, font, 6.2) > max_width:
                    while line and c.stringWidth(f"{line}...", font, 6.2) > max_width:
                        line = line[:-1]
                    line = f"{line.rstrip()}..."
                draw_text(c, line, current_x + 7, y + 5.2, 6.2, font, color)
            current_x += col_w

    note_y = 50 * mm
    c.setFillColor(PROTOTYPE)
    c.setStrokeColor(LINE)
    c.roundRect(margin, note_y, table_w, 48, 6, stroke=1, fill=1)
    draw_text(c, "Development prototypes outside the production runtime boundary", margin + 10, note_y + 32, 8.1, BOLD)
    draw_wrapped(c, "Bootstrap Station and Cold Signer implement development work toward offline ECDSA MPC bootstrap/signing. They remain non-production prototypes; the intended architecture, security invariants, and remaining readiness work are documented in architecture/offline-mpc.md.", margin + 10, note_y + 20, table_w - 20, 6.8, REGULAR, MUTED, 9)
    footer(c, 2, width)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    width, height = landscape(A3)
    canvas = Canvas(str(OUTPUT), pagesize=(width, height))
    canvas.setTitle("FortVault Component Architecture")
    canvas.setAuthor("FortVault")
    canvas.setSubject("FortVault runtime components, connections, owned state and trust boundaries")
    draw_page_one(canvas, width, height)
    canvas.showPage()
    draw_page_two(canvas, width, height)
    canvas.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()
