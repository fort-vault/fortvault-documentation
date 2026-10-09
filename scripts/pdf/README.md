# PDF Tooling

Run commands from the documentation repository root with Python 3 and ReportLab installed. Font selection and fallback behavior are defined by each builder.

| Command | Input | Staging output |
| --- | --- | --- |
| `python3 scripts/pdf/generate_pdfs.py` | ISO custody/exchange technical overview Markdown | Two technical overview PDFs under `output/pdf/` |
| `python3 scripts/pdf/generate_fortvault_component_architecture_pdf.py` | Diagram/content definitions inside the script | `output/pdf/FortVault_Component_Architecture.pdf` |
| `python3 scripts/pdf/generate_fortx_component_architecture_pdf.py` | Diagram/content definitions inside the script | `output/pdf/FortX_Component_Architecture.pdf` |
| `python3 scripts/pdf/generate_fortx_fortvault_architecture_pdf.py` | Diagram/content definitions inside the script | `output/pdf/FortVault_FortX_Platform_Architecture.pdf` |
| `python3 scripts/pdf/build_air_gapped_mpc_architecture.py` | Diagram/content definitions inside the script | `output/pdf/FortVault_Air_Gapped_MPC_Architecture.pdf` |
| `python3 scripts/pdf/build_evidence_package.py` | Supporting-information Markdown and previously generated overview/component PDFs | August 2026 package directory and ZIP under `output/iso27001-evidence/` |

Generate the technical overviews and three component/platform PDFs before building the evidence package. The offline MPC PDF is a separate output, not an automatically validated component of that package.

Several diagram builders contain their own prose and drawing definitions. They do not automatically follow edits to Markdown. Review both representations when changing their content; a successful build does not establish architecture correctness.

These builders reproduce assessment-oriented material, not a new current-release assurance. Inspect all generated PDF pages before publishing. Reviewed historical exports remain under [exports](../../exports/README.md); builders write only to ignored staging output.
