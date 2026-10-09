from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output" / "pdf" / "FortVault_Air_Gapped_MPC_Architecture.pdf"

NAVY = colors.HexColor("#07133D")
BLUE = colors.HexColor("#0A43A6")
AZURE = colors.HexColor("#1677FF")
PALE_BLUE = colors.HexColor("#EAF2FF")
LIGHT = colors.HexColor("#F5F7FB")
MID = colors.HexColor("#67708A")
LINE = colors.HexColor("#DDE4F0")
GREEN = colors.HexColor("#1E9D67")


class FortVaultDocTemplate(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=21 * mm,
            rightMargin=21 * mm,
            topMargin=22 * mm,
            bottomMargin=19 * mm,
            title="FortVault Air-Gapped MPC Architecture",
            author="FortVault",
            subject="Air-gapped MPC architecture and operating model",
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="normal",
        )
        self.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=self._draw_page))

    def _draw_page(self, canvas, doc):
        canvas.saveState()
        width, height = A4
        if doc.page > 1:
            canvas.setStrokeColor(LINE)
            canvas.setLineWidth(0.6)
            canvas.line(21 * mm, height - 14 * mm, width - 21 * mm, height - 14 * mm)
            canvas.setFont("Helvetica-Bold", 8)
            canvas.setFillColor(BLUE)
            canvas.drawString(21 * mm, height - 10.5 * mm, "FORTVAULT")
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(MID)
            canvas.drawRightString(
                width - 21 * mm,
                height - 10.5 * mm,
                "AIR-GAPPED MPC ARCHITECTURE",
            )
        canvas.setStrokeColor(LINE)
        canvas.line(21 * mm, 13 * mm, width - 21 * mm, 13 * mm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MID)
        canvas.drawString(21 * mm, 8.5 * mm, "FortVault technical architecture")
        canvas.drawRightString(width - 21 * mm, 8.5 * mm, f"Page {doc.page}")
        canvas.restoreState()


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="CoverBrand",
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=BLUE,
        spaceAfter=24,
    )
)
styles.add(
    ParagraphStyle(
        name="CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=29,
        leading=34,
        textColor=NAVY,
        spaceAfter=14,
    )
)
styles.add(
    ParagraphStyle(
        name="CoverSubtitle",
        fontName="Helvetica",
        fontSize=13,
        leading=19,
        textColor=MID,
        spaceAfter=26,
    )
)
styles.add(
    ParagraphStyle(
        name="Section",
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=21,
        textColor=NAVY,
        spaceBefore=6,
        spaceAfter=9,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="BodyFV",
        fontName="Helvetica",
        fontSize=9.8,
        leading=15,
        textColor=colors.HexColor("#202A44"),
        alignment=TA_LEFT,
        spaceAfter=7,
    )
)
styles.add(
    ParagraphStyle(
        name="BulletFV",
        parent=styles["BodyFV"],
        leftIndent=14,
        firstLineIndent=-8,
        bulletIndent=0,
        spaceAfter=4,
    )
)
styles.add(
    ParagraphStyle(
        name="Callout",
        fontName="Helvetica-Bold",
        fontSize=10.3,
        leading=15,
        textColor=NAVY,
        spaceAfter=0,
    )
)
styles.add(
    ParagraphStyle(
        name="StepTitle",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=NAVY,
        spaceAfter=2,
    )
)
styles.add(
    ParagraphStyle(
        name="StepBody",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=MID,
    )
)


def p(text, style="BodyFV"):
    return Paragraph(text, styles[style])


def bullets(items):
    result = []
    for item in items:
        result.append(Paragraph(f"<bullet>&bull;</bullet>{item}", styles["BulletFV"]))
    return result


def section(number, title):
    return KeepTogether(
        [
            Table(
                [[p(str(number), "Callout"), p(title, "Section")]],
                colWidths=[13 * mm, 151 * mm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, 0), PALE_BLUE),
                        ("BOX", (0, 0), (0, 0), 0.6, colors.HexColor("#C6D8F8")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (0, 0), 4),
                        ("RIGHTPADDING", (0, 0), (0, 0), 4),
                        ("TOPPADDING", (0, 0), (0, 0), 5),
                        ("BOTTOMPADDING", (0, 0), (0, 0), 5),
                        ("LEFTPADDING", (1, 0), (1, 0), 7),
                        ("RIGHTPADDING", (1, 0), (1, 0), 0),
                        ("TOPPADDING", (1, 0), (1, 0), 0),
                        ("BOTTOMPADDING", (1, 0), (1, 0), 0),
                    ]
                ),
            ),
            Spacer(1, 4),
        ]
    )


def callout(text):
    table = Table([[p(text, "Callout")]], colWidths=[164 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#B9D0F5")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return table


def flow_steps(steps):
    cells = []
    for number, title, body in steps:
        cells.append(
            [
                p(number, "Callout"),
                Paragraph(title, styles["StepTitle"]),
                Paragraph(body, styles["StepBody"]),
            ]
        )
    table = Table(cells, colWidths=[11 * mm, 42 * mm, 111 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


story = []

# Cover
story.append(Spacer(1, 18 * mm))
story.append(p("FORTVAULT", "CoverBrand"))
story.append(p("Air-Gapped MPC<br/>Architecture", "CoverTitle"))
story.append(
    p(
        "Technical description of the partner-controlled offline MPC participant, "
        "bootstrap and recovery applications, optical transport, and online orchestration model.",
        "CoverSubtitle",
    )
)
story.append(Spacer(1, 6 * mm))
story.append(
    Table(
        [
            [p("DOCUMENT PURPOSE", "StepTitle"), p("Architecture and operating model", "StepBody")],
            [p("AUDIENCE", "StepTitle"), p("Partner institutions and regulatory reviewers", "StepBody")],
            [p("DOCUMENT DATE", "StepTitle"), p("7 September 2026", "StepBody")],
        ],
        colWidths=[47 * mm, 100 * mm],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.45, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        ),
    )
)
story.append(Spacer(1, 23 * mm))
story.append(
    callout(
        "The complete private key is never created or stored. Signing is performed through "
        "a configurable threshold protocol using independent MPC shares."
    )
)
story.append(PageBreak())

# 1
story.append(section(1, "Overview"))
story.append(
    p(
        "FortVault's air-gapped signing architecture adds a partner-controlled offline "
        "multiparty computation (MPC) participant to the threshold-signature cluster."
    )
)
story.append(
    p(
        "The private key is never created or stored as a complete key. Each MPC participant "
        "holds an independent cryptographic share. A valid signature can be produced only "
        "through the configured threshold protocol involving the required MPC participants, "
        "including the partner's offline device."
    )
)
story.append(
    p(
        "The offline device has no application-level connection to FortVault Backend, Custody "
        "Processing, Redis, blockchain RPC endpoints or the public internet. Normal signing "
        "data is exchanged optically using QR codes. A controlled local cable connection is "
        "used only for bootstrap and recovery operations."
    )
)
story.append(Spacer(1, 3 * mm))
story.append(callout("The offline device is an MPC participant, not a holder of a complete private key."))
story.append(Spacer(1, 8 * mm))

# 2
story.append(section(2, "macOS Bootstrap Station"))
story.append(
    p(
        "The FortVault Bootstrap Station is a dedicated macOS application used to initialize "
        "and recover the partner's offline MPC participant."
    )
)
story.extend(
    bullets(
        [
            "Detects and communicates with the partner's authorized iPhone.",
            "Registers and authorizes the Bootstrap Station for the partner.",
            "Coordinates offline MPC root generation with the online MPC cluster.",
            "Relays interactive MPC protocol messages between the iPhone and online services.",
            "Receives and stores the encrypted recovery package generated for the offline participant.",
            "Imports a recovery package into an authorized replacement iPhone when recovery is required.",
        ]
    )
)
story.append(
    p(
        "The Bootstrap Station does not perform the threshold cryptographic calculations. It "
        "provides controlled transport, ceremony coordination and recovery management. It has "
        "its own device identity and cryptographic keys, and recovery packages are not stored "
        "in plaintext."
    )
)
story.append(PageBreak())

# 3
story.append(section(3, "iOS Cold Signer Application"))
story.append(
    p(
        "The FortVault Cold Signer is installed on a dedicated, partner-controlled iPhone. "
        "The device stores the partner's offline MPC share and participates directly in MPC "
        "root-generation and signing ceremonies."
    )
)
story.extend(
    bullets(
        [
            "Runs the threshold ECDSA MPC protocol locally.",
            "Generates and stores an independent MPC share.",
            "Participates in interactive distributed root generation.",
            "Validates coordinator identity and signing-session metadata.",
            "Displays transaction details before the initial approval.",
            "Produces the offline participant's MPC protocol messages.",
            "Encrypts its MPC share using a device-protected encryption key.",
            "Supports controlled recovery-package import.",
            "Rejects expired, invalid, replayed or out-of-order protocol messages.",
        ]
    )
)
story.append(
    p(
        "The share-encryption key is stored using the iOS Keychain with device-only and "
        "unlocked-device protection. Encrypted MPC share files use iOS file protection."
    )
)
story.append(Spacer(1, 7 * mm))

# 4
story.append(section(4, "QR Code Communication"))
story.append(
    p(
        "QR codes provide the air-gapped transport used for routine signing communication "
        "between the online FortVault interface and the offline iPhone. Large MPC protocol "
        "messages are divided into multiple animated QR frames."
    )
)
story.append(
    Table(
        [
            [p("Sequential animated QR", "StepTitle"), p("Frames are displayed and reconstructed in a defined order.", "StepBody")],
            [p("Fountain-coded animated QR", "StepTitle"), p("Redundant coded frames allow reconstruction without reading every frame in order.", "StepBody")],
            [p("Interactive optical exchange", "StepTitle"), p("Both devices alternate between display and camera roles to exchange MPC round data.", "StepBody")],
        ],
        colWidths=[57 * mm, 107 * mm],
        style=TableStyle(
            [
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT, colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        ),
    )
)
story.append(Spacer(1, 4 * mm))
story.append(
    p(
        "The selected mode changes only the transport method. It does not change the MPC "
        "algorithm, signing threshold or transaction-authorization rules."
    )
)
story.extend(
    bullets(
        [
            "Partner and MPC root.",
            "Signing action, session and participant set.",
            "Coordinator identity and transaction payload hash.",
            "Protocol round, message direction and expiration time.",
            "Unique replay-protection identifier.",
        ]
    )
)
story.append(
    p(
        "QR codes contain authenticated protocol messages, public metadata and MPC round data. "
        "They do not contain the complete private key or the stored MPC share. Cryptographic "
        "signatures, hashes and session binding protect authenticity and integrity."
    )
)
story.append(PageBreak())

# 5
story.append(section(5, "Air-Gapped Device as a Full MPC Participant"))
story.append(
    p(
        "The iPhone contains one full MPC protocol participant. This means that the device "
        "runs the cryptographic MPC state machine locally, holds its own share and calculates "
        "its own protocol-round messages. It is not merely an approval application or remote "
        "control for an online MPC node."
    )
)
story.append(
    p(
        "The iPhone does not contain the complete private key and cannot sign independently. "
        "It also does not run FortVault Backend or an online MPC server."
    )
)
story.append(
    callout(
        "Distributed key generation creates a common public root and a separate private share "
        "for each participant. It does not reconstruct a complete private key."
    )
)
story.append(Spacer(1, 5 * mm))
story.append(
    p(
        "Public child addresses can be derived from public root information without connecting "
        "the iPhone. Spending funds requires a threshold signature and therefore requires the "
        "offline participant whenever it is part of the configured signing threshold. There is "
        "no automatic fallback to an online root or single-party signer."
    )
)
story.append(Spacer(1, 8 * mm))

# 6
story.append(section(6, "Master MPC Orchestration Role"))
story.append(
    p(
        "The Master MPC is the online coordinator for the MPC ceremony. The term 'Master' "
        "describes its orchestration role; it does not mean that the node possesses a master "
        "private key or can sign independently."
    )
)
story.extend(
    bullets(
        [
            "Creates unique root-generation and signing sessions.",
            "Verifies the approved transaction and its authorization evidence.",
            "Selects and coordinates the configured MPC participants.",
            "Verifies online participant availability.",
            "Creates authenticated messages for the offline device.",
            "Routes MPC messages between online participants and the iPhone.",
            "Enforces round ordering, expiration and replay protection.",
            "Verifies responses produced by the enrolled offline device.",
            "Persists public root information and online MPC state.",
            "Returns the completed threshold signature to Custody Processing.",
        ]
    )
)
story.append(
    p(
        "The Master MPC never receives or stores the iPhone's private share. The coordinator "
        "alone does not possess sufficient key material to produce a valid threshold signature."
    )
)
story.append(PageBreak())

# 7
story.append(section(7, "Root Generation and Recovery"))
story.append(
    p(
        "Initial provisioning establishes the partner-controlled offline participant and binds "
        "it to the corresponding MPC root."
    )
)
story.append(
    flow_steps(
        [
            ("1", "Provision", "The partner provisions a dedicated iPhone and macOS Bootstrap Station."),
            ("2", "Authorize", "The Bootstrap Station is authorized for the relevant partner environment."),
            ("3", "Generate", "Online MPC participants and the iPhone perform interactive distributed root generation."),
            ("4", "Store", "Each participant stores only its own private share; the public root is registered."),
            ("5", "Export", "The iPhone prepares encrypted recovery material for its offline participant share."),
            ("6", "Retain", "The Bootstrap Station stores the encrypted recovery package under partner control."),
        ]
    )
)
story.append(Spacer(1, 5 * mm))
story.append(
    p(
        "The recovery package contains the air-gapped participant's encrypted share and the "
        "associated root metadata. It is not a complete private key and cannot independently "
        "authorize transactions. Online MPC node shares have separate backup procedures."
    )
)
story.append(
    p(
        "If the iPhone is lost, damaged or replaced, the partner can use the Bootstrap Station "
        "to import the encrypted recovery material into an authorized replacement device. The "
        "recovered share is validated against the expected public root before acceptance."
    )
)
story.append(Spacer(1, 8 * mm))

# 8
story.append(section(8, "Partner Ownership and Responsibilities"))
story.append(
    p(
        "The partner establishes and controls the air-gapped operating environment. FortVault "
        "does not require custody of the partner's offline MPC share or recovery package."
    )
)
story.extend(
    bullets(
        [
            "Procure and provision the dedicated iPhone.",
            "Install and control the Cold Signer application.",
            "Keep the device offline during normal operation.",
            "Control physical access, device passcode and operational custody.",
            "Operate the Bootstrap Station in a controlled environment.",
            "Receive and retain encrypted recovery packages directly.",
            "Maintain protected recovery copies under the partner's custody procedures.",
            "Maintain an inventory of authorized devices and recovery packages.",
            "Use the partner's internal authorization process for recovery and device replacement.",
            "Manage device loss, replacement and decommissioning procedures.",
        ]
    )
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
doc = FortVaultDocTemplate(str(OUTPUT))
doc.build(story)
print(OUTPUT)
