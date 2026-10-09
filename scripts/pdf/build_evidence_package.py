#!/usr/bin/env python3
"""Build the review-ready ISO 27001 evidence directory.

The package intentionally excludes secrets and operational claims that cannot be
verified from source. Cloud, backup, production TLS, endpoint, and runtime
evidence can be added later without changing the package layout.
"""

from __future__ import annotations

import csv
import hashlib
import shutil
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate

DOCS_DIR = Path(__file__).resolve().parents[2]
ISO_DIR = DOCS_DIR / "security" / "iso-27001"
SOURCE_DIR = ISO_DIR / "supporting-information"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_pdfs import DARK, FONT_BOLD, FONT_REGULAR, FORTVAULT_BLUE, LINE, MUTED, markdown_to_story, page_decorator


PACKAGE = (
    DOCS_DIR
    / "output"
    / "iso27001-evidence"
    / "FortVault_ISO27001_Evidence_2026-08"
)


def generate_pdf(source: Path, output: Path, subject: str) -> None:
    if output.exists() and output.stat().st_mtime >= source.stat().st_mtime:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=27 * mm,
        bottomMargin=20 * mm,
        title=source.stem.replace("-", " ").replace("_", " "),
        author="FortVault",
        subject=subject,
    )
    story = markdown_to_story(
        source,
        "Evidence",
        A4[0] - doc.leftMargin - doc.rightMargin,
    )
    decorator = page_decorator("ISO 27001 Evidence")
    doc.build(story, onFirstPage=decorator, onLaterPages=decorator)


def copy_pdf(source: Path, relative_output: str) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Required PDF is missing: {source}")
    destination = PACKAGE / relative_output
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and file_digest(destination) == file_digest(source):
        return
    shutil.copy2(source, destination)


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def draw_box(pdf: canvas.Canvas, x: float, y: float, w: float, h: float, title: str, detail: str, fill: colors.Color, stroke: colors.Color) -> None:
    pdf.setFillColor(fill)
    pdf.setStrokeColor(stroke)
    pdf.setLineWidth(1)
    pdf.roundRect(x, y, w, h, 7, fill=1, stroke=1)
    pdf.setFillColor(DARK)
    pdf.setFont(FONT_BOLD, 8.6)
    pdf.drawCentredString(x + w / 2, y + h - 14, title)
    pdf.setFillColor(MUTED)
    pdf.setFont(FONT_REGULAR, 6.4)
    for index, line in enumerate(detail.split("\n")):
        pdf.drawCentredString(x + w / 2, y + h - 27 - index * 9, line)


def draw_arrow(pdf: canvas.Canvas, x1: float, y1: float, x2: float, y2: float, label: str = "") -> None:
    pdf.setStrokeColor(colors.HexColor("#70809D"))
    pdf.setFillColor(colors.HexColor("#70809D"))
    pdf.setLineWidth(1)
    pdf.line(x1, y1, x2, y2)
    direction = 1 if x2 >= x1 else -1
    pdf.line(x2, y2, x2 - 5 * direction, y2 + 3)
    pdf.line(x2, y2, x2 - 5 * direction, y2 - 3)
    if label:
        pdf.setFont(FONT_REGULAR, 5.8)
        pdf.drawCentredString((x1 + x2) / 2, (y1 + y2) / 2 + 5, label)


def draw_routed_arrow(pdf: canvas.Canvas, points: list[tuple[float, float]], label: str = "") -> None:
    pdf.setStrokeColor(colors.HexColor("#70809D"))
    pdf.setFillColor(colors.HexColor("#70809D"))
    pdf.setLineWidth(1)
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        pdf.line(x1, y1, x2, y2)
    (x1, y1), (x2, y2) = points[-2], points[-1]
    direction = 1 if x2 >= x1 else -1
    pdf.line(x2, y2, x2 - 5 * direction, y2 + 3)
    pdf.line(x2, y2, x2 - 5 * direction, y2 - 3)
    if label:
        pdf.setFont(FONT_REGULAR, 5.8)
        pdf.drawCentredString((points[-2][0] + points[-1][0]) / 2, points[-1][1] + 6, label)


def generate_cloud_diagram(output: Path) -> None:
    source = Path(__file__)
    if output.exists() and output.stat().st_mtime >= source.stat().st_mtime:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    width, height = landscape(A4)
    pdf = canvas.Canvas(
        str(output),
        pagesize=(width, height),
        pageCompression=1,
        title="FortVault Production Cloud Deployment and Trust Boundaries",
        author="FortVault",
        subject="Sanitized management-provided cloud deployment architecture",
    )
    pdf.setTitle("FortVault Production Cloud Deployment and Trust Boundaries")
    pdf.setAuthor("FortVault")
    pdf.setSubject("Sanitized management-provided cloud deployment architecture")

    pdf.setFillColor(colors.white)
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setFillColor(DARK)
    pdf.setFont(FONT_BOLD, 20)
    pdf.drawString(30, height - 43, "FortVault Production Cloud Deployment")
    pdf.setFillColor(MUTED)
    pdf.setFont(FONT_REGULAR, 8)
    pdf.drawString(30, height - 59, "Sanitized management-provided topology | Confidential | August 28, 2026")

    aws_x, aws_y, aws_w, aws_h = 28, 110, 485, 395
    gcp_x, gcp_y, gcp_w, gcp_h = 530, 286, 282, 219
    customer_x, customer_y, customer_w, customer_h = 530, 110, 282, 145

    for x, y, w, h, title, subtitle, fill, stroke in [
        (aws_x, aws_y, aws_w, aws_h, "AWS production boundary", "Region us-east-1 | One VPC | Security groups per service", colors.HexColor("#FFF8EB"), colors.HexColor("#C77D12")),
        (gcp_x, gcp_y, gcp_w, gcp_h, "GCP production boundary", "Region us-east1 | MPC node 2", colors.HexColor("#EEF5FF"), colors.HexColor("#2D6FC3")),
        (customer_x, customer_y, customer_w, customer_h, "Customer-managed boundary", "Partner-operated MPC node and storage", colors.HexColor("#F1F8F4"), colors.HexColor("#27865D")),
    ]:
        pdf.setFillColor(fill)
        pdf.setStrokeColor(stroke)
        pdf.setLineWidth(1.2)
        pdf.roundRect(x, y, w, h, 10, fill=1, stroke=1)
        pdf.setFillColor(DARK)
        pdf.setFont(FONT_BOLD, 10)
        pdf.drawString(x + 14, y + h - 20, title)
        pdf.setFillColor(MUTED)
        pdf.setFont(FONT_REGULAR, 6.5)
        pdf.drawString(x + 14, y + h - 35, subtitle)

    blue_fill = colors.HexColor("#EEF4FF")
    green_fill = colors.HexColor("#EDF8F3")
    amber_fill = colors.HexColor("#FFF3DA")
    red_fill = colors.HexColor("#FFF0F0")

    draw_box(pdf, 48, 405, 105, 55, "Public access", "HTTPS ingress\nconfiguration to evidence", blue_fill, FORTVAULT_BLUE)
    draw_box(pdf, 175, 405, 105, 55, "Frontend VM", "User interface\nAWS compute", green_fill, colors.HexColor("#27865D"))
    draw_box(pdf, 302, 405, 115, 55, "Backend VM", "Backend and application\nworkloads", green_fill, colors.HexColor("#27865D"))
    draw_box(pdf, 48, 310, 105, 55, "VPN VM", "Administrative access\nseparate subnet", blue_fill, FORTVAULT_BLUE)
    draw_box(pdf, 175, 310, 105, 55, "MPC node 1", "Threshold signing node\nAWS compute", red_fill, colors.HexColor("#B83232"))
    draw_box(pdf, 302, 310, 115, 55, "RDS PostgreSQL", "Application and MPC\ndatabases", amber_fill, colors.HexColor("#B7791F"))
    draw_box(pdf, 48, 205, 105, 55, "ElastiCache", "Redis transport and\nservice cache", amber_fill, colors.HexColor("#B7791F"))
    draw_box(pdf, 175, 205, 105, 55, "Secrets Manager", "Runtime secret\nreferences", red_fill, colors.HexColor("#B83232"))
    draw_box(pdf, 302, 205, 115, 55, "AWS IAM roles", "Deployment and runtime\nservice access", blue_fill, FORTVAULT_BLUE)

    draw_box(pdf, 550, 393, 110, 55, "MPC node 2", "Compute Engine VM\nzone us-east1-d", red_fill, colors.HexColor("#B83232"))
    draw_box(pdf, 681, 393, 110, 55, "Cloud SQL", "PostgreSQL\nmanaged database", amber_fill, colors.HexColor("#B7791F"))
    draw_box(pdf, 550, 315, 110, 55, "Secret Manager", "Runtime secret\nreferences", red_fill, colors.HexColor("#B83232"))
    draw_box(pdf, 681, 315, 110, 55, "Service accounts", "Deployment and runtime\naccess", blue_fill, FORTVAULT_BLUE)

    draw_box(pdf, 550, 147, 110, 55, "Customer MPC", "Partner-operated\nthreshold node", red_fill, colors.HexColor("#B83232"))
    draw_box(pdf, 681, 147, 110, 55, "Customer database", "Partner-operated\nPostgreSQL", amber_fill, colors.HexColor("#B7791F"))

    draw_arrow(pdf, 153, 432, 175, 432, "HTTPS")
    draw_arrow(pdf, 280, 432, 302, 432, "API")
    draw_arrow(pdf, 153, 337, 175, 337, "admin")
    draw_arrow(pdf, 280, 337, 302, 337, "storage")
    draw_arrow(pdf, 280, 365, 550, 420, "cross-cloud authenticated MPC transport")
    draw_arrow(pdf, 660, 420, 681, 420, "storage")
    draw_arrow(pdf, 660, 342, 681, 342, "identity")
    draw_routed_arrow(pdf, [(280, 320), (290, 320), (290, 174), (550, 174)], "customer MPC transport")
    draw_arrow(pdf, 660, 174, 681, 174, "storage")

    pdf.setFillColor(colors.HexColor("#FFF4E5"))
    pdf.setStrokeColor(colors.HexColor("#C77D12"))
    pdf.roundRect(28, 28, 784, 58, 8, fill=1, stroke=1)
    pdf.setFillColor(DARK)
    pdf.setFont(FONT_BOLD, 7.5)
    pdf.drawString(42, 64, "Current-state limitations")
    pdf.setFont(FONT_REGULAR, 6.4)
    pdf.drawString(42, 49, "Cloud audit logging, centralized monitoring, and infrastructure-as-code are not configured. Public/private ingress, firewall rules, encryption settings, and backup controls require sanitized console evidence.")
    pdf.drawString(42, 36, "The full AWS account identifier, private addresses, endpoint names, credentials, secret values, and customer identifiers are intentionally omitted.")

    pdf.setStrokeColor(LINE)
    pdf.line(28, 98, width - 28, 98)
    pdf.setFillColor(MUTED)
    pdf.setFont(FONT_REGULAR, 6)
    pdf.drawString(30, 13, "Supporting document for ISO/IEC 27001 implementation")
    pdf.drawRightString(width - 30, 13, "Page 1")
    pdf.showPage()
    pdf.save()


def write_register() -> None:
    rows = [
        ("Package index", "00_README.pdf", "Source-controlled", "Included"),
        ("FortVault component architecture", "01_Architecture/FortVault_Component_Architecture.pdf", "Source-reviewed architecture", "Included"),
        ("FortX component architecture", "01_Architecture/FortX_Component_Architecture.pdf", "Source-reviewed current/planned architecture", "Included"),
        ("Combined platform architecture", "01_Architecture/FortVault_FortX_Platform_Architecture.pdf", "Source-reviewed architecture", "Included"),
        ("Custody technical overview", "01_Architecture/FortVault_Custody_Technical_Overview.pdf", "Source-reviewed technical overview", "Included"),
        ("Exchange technical overview", "01_Architecture/FortVault_Exchange_Technical_Overview.pdf", "Source-reviewed limited scope", "Included"),
        ("Testing, health, logging and encryption", "02_Source_Controlled_Evidence/Testing_Health_Logging_and_Encryption.pdf", "Source-controlled implementation evidence", "Included"),
        ("README and architecture index", "02_Source_Controlled_Evidence/README_and_Architecture_Index.pdf", "Controlled sharing index", "Included"),
        ("GitHub component README examples", "02_Source_Controlled_Evidence/GitHub_Component_README_Examples.pdf", "Sanitized revision-bound README excerpts", "Included"),
        ("Cloud deployment diagram", "03_Operational_Evidence/Cloud_Deployment_and_Trust_Boundaries.pdf", "Management-provided current-state topology", "Included - management review required"),
        ("Cloud configuration", "03_Operational_Evidence/Cloud_Infrastructure_and_Configuration.pdf", "Management-provided current-state description", "Included - console evidence pending"),
        ("Backup and restore", "03_Operational_Evidence/Backup_and_Restore_Configuration.pdf", "Management-provided current-state description", "Included - restore evidence pending"),
        ("Operational evidence checklist", "03_Operational_Evidence/Operational_Evidence_Checklist.pdf", "Collection checklist", "Included"),
        ("Centralized production logging", "03_Operational_Evidence/PENDING_INFORMATION.txt", "Operational evidence", "Known gap - not configured"),
        ("Production TLS and encryption", "03_Operational_Evidence/PENDING_INFORMATION.txt", "Operational evidence", "Pending"),
        ("Endpoint OS and updates", "03_Operational_Evidence/PENDING_INFORMATION.txt", "Operational evidence", "Pending"),
        ("Release-specific test results", "03_Operational_Evidence/PENDING_INFORMATION.txt", "Runtime/release evidence", "Pending"),
    ]
    target = PACKAGE / "Evidence_Register.csv"
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "Control / evidence area",
                "Package artifact",
                "Evidence basis",
                "Status",
                "Owner",
                "Package date",
                "Classification",
            ]
        )
        for title, artifact, basis, status in rows:
            writer.writerow(
                [
                    title,
                    artifact,
                    basis,
                    status,
                    "FortVault",
                    "2026-08-28",
                    "Confidential",
                ]
            )


def write_pending_information() -> None:
    target = PACKAGE / "03_Operational_Evidence" / "PENDING_INFORMATION.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        """FortVault ISO 27001 evidence still required from operational owners

1. Cloud configuration evidence
   Sanitized AWS and GCP exports for network boundaries, IAM/service accounts,
   databases, caches, secret stores, encryption, backup settings, and workload inventory.
   Cloud audit logging and centralized monitoring are currently not configured.

2. Backup and restore completion evidence
   Encryption settings, least-privilege access review, approved RPO/RTO, immutable or
   isolated copy controls, job evidence, and the latest successful restore-test record.
   Do not include MPC shares or recovery material.

3. Centralized production logging
   Platform, sources, access control, retention, alerting, time synchronization,
   redaction standard, and representative sanitized evidence.

4. Production TLS and encryption at rest
   Ingress TLS policy, certificate management, redirect behavior, storage/database/
   cache/backup encryption, KMS configuration, key rotation, and exceptions.

5. Endpoint operating systems and updates
   In-scope endpoint classes, inventory, supported versions, patch policy, device
   management, disk encryption, endpoint protection, and sanitized compliance output.

6. Release-specific verification
   CI/test output, release identifier, approval record, sanitized health-audit output,
   known degraded checks, owners, and remediation dates.

Never place credentials, tokens, private keys, MPC shares, customer data, or raw
secret-manager values in this package.
""",
        encoding="utf-8",
    )


def main() -> None:
    PACKAGE.mkdir(parents=True, exist_ok=True)

    generate_pdf(
        SOURCE_DIR / "README.md",
        PACKAGE / "00_README.pdf",
        "Index for the FortVault ISO 27001 supporting-information package",
    )
    generate_pdf(
        SOURCE_DIR / "01-source-controlled-testing-health-and-security.md",
        PACKAGE
        / "02_Source_Controlled_Evidence"
        / "Testing_Health_Logging_and_Encryption.pdf",
        "Source-controlled testing, health, logging, and encryption evidence",
    )
    generate_pdf(
        SOURCE_DIR / "02-operational-evidence-checklist.md",
        PACKAGE
        / "03_Operational_Evidence"
        / "Operational_Evidence_Checklist.pdf",
        "Operational evidence checklist for ISO 27001 implementation",
    )
    generate_pdf(
        SOURCE_DIR / "06-cloud-infrastructure-and-configuration.md",
        PACKAGE
        / "03_Operational_Evidence"
        / "Cloud_Infrastructure_and_Configuration.pdf",
        "Management-provided cloud infrastructure configuration and control gaps",
    )
    generate_pdf(
        SOURCE_DIR / "07-backup-and-restore-configuration.md",
        PACKAGE
        / "03_Operational_Evidence"
        / "Backup_and_Restore_Configuration.pdf",
        "Management-provided backup configuration and recovery-control gaps",
    )
    generate_cloud_diagram(
        PACKAGE
        / "03_Operational_Evidence"
        / "Cloud_Deployment_and_Trust_Boundaries.pdf"
    )
    generate_pdf(
        SOURCE_DIR / "03-readme-and-architecture-index.md",
        PACKAGE
        / "02_Source_Controlled_Evidence"
        / "README_and_Architecture_Index.pdf",
        "Controlled README and architecture sharing index",
    )
    generate_pdf(
        SOURCE_DIR / "05-component-readme-examples.md",
        PACKAGE
        / "02_Source_Controlled_Evidence"
        / "GitHub_Component_README_Examples.pdf",
        "Sanitized examples from selected FortVault component READMEs",
    )

    copy_pdf(
        DOCS_DIR / "output" / "pdf" / "FortVault_Component_Architecture.pdf",
        "01_Architecture/FortVault_Component_Architecture.pdf",
    )
    copy_pdf(
        DOCS_DIR / "output" / "pdf" / "FortX_Component_Architecture.pdf",
        "01_Architecture/FortX_Component_Architecture.pdf",
    )
    copy_pdf(
        DOCS_DIR
        / "output"
        / "pdf"
        / "FortVault_FortX_Platform_Architecture.pdf",
        "01_Architecture/FortVault_FortX_Platform_Architecture.pdf",
    )
    copy_pdf(
        DOCS_DIR / "output" / "pdf" / "FORTVAULT_CUSTODY_TECHNICAL_OVERVIEW.pdf",
        "01_Architecture/FortVault_Custody_Technical_Overview.pdf",
    )
    copy_pdf(
        DOCS_DIR / "output" / "pdf" / "FORTVAULT_EXCHANGE_TECHNICAL_OVERVIEW.pdf",
        "01_Architecture/FortVault_Exchange_Technical_Overview.pdf",
    )

    shutil.copy2(
        SOURCE_DIR / "04-cover-email-draft.md",
        PACKAGE / "04_Email_Draft.md",
    )
    write_register()
    write_pending_information()
    print(PACKAGE)


if __name__ == "__main__":
    main()
