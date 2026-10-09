# FortVault Documentation

Product descriptions, integration contracts, architecture references, and dated evidence for FortVault and FortX. Start here rather than with an exported PDF or an old architecture draft.

## Start Here

| Reader | Document | Purpose |
| --- | --- | --- |
| Custody partner | [FortVault Custody](products/fortvault-custody.md) | Product scope, custody controls, integrations, and roadmap distinctions |
| Backend exchange partner | [FortX Connect](products/fortx-connect.md) | Exchange backend and backoffice product scope |
| Full exchange partner | [FortX](products/fortx.md) | FortX Connect plus end-user web, iOS, and Android applications |
| Custody API integrator | [Partner API guide](integrations/FORTVAULT_PARTNER_API_INTEGRATION_GUIDE.md) | API contract, signing, idempotency, examples, and explicitly proposed extensions |
| FortX frontend integrator | [FortX Connect API guide](integrations/FORTX_CONNECT_API_INTEGRATION_GUIDE.md) | Frontend-facing API design; confirm endpoint availability against the target release |
| Engineer or technical reviewer | [Architecture overview](architecture/overview.md) | Component ownership, boundaries, execution paths, and further reading |

Product descriptions are not release certification. Features marked proposed, planned, optional, or prototype must not be presented as delivered without release-specific evidence. API behavior is ultimately owned by the implementation and its published release contract.

## Documentation Map

| Folder | Contents | Status and use |
| --- | --- | --- |
| [products](products/fortvault-custody.md) | FortVault, FortX Connect, and FortX descriptions | Partner-facing product documents with implementation and roadmap distinctions |
| [architecture](architecture/overview.md) | Overview, MPC, smart contracts, and offline MPC | Technical references; offline components retain prototype status |
| [integrations](integrations/FORTVAULT_PARTNER_API_INTEGRATION_GUIDE.md) | Custody and frontend API guides | Original guide content preserved; proposed sections are not implementation guarantees |
| [specifications](specifications/customer-controls.md) | Customer statuses, restrictions, permissions, and limits | Functional design; not proof that every control is implemented |
| [security](security/iso-27001/README.md) | ISO preparation and supporting evidence | Dated assessment material, not certification or a current security assurance |
| [partners](partners/README.md) | Oroex architecture | Partner-specific context, not the general product contract |
| [release-notes](release-notes/weekly-release-notes-2026-06-08.md) | Weekly Markdown/PDF release records | Historical release snapshots |
| [assets](assets/README.md) | Brand SVGs and diagram images | Reusable assets; diagrams require review before reuse as current architecture |
| [scripts](scripts/pdf/README.md) | PDF builders and documentation checks | Maintained tooling; generated staging output is not the source of truth |
| [exports](exports/README.md) | Preserved evidence packages | Dated distributable snapshots |
| [archive](archive/README.md) | Superseded architecture and retired drafts | Historical context only |

## Maintenance

- Give each topic one primary source. Link to it instead of copying its explanation into multiple overview files.
- Separate product scope, API contracts, functional designs, partner commitments, and audit evidence.
- Check technical claims against their owning repositories before updating them. Never infer a security guarantee from a diagram or a successful build.
- Keep dated evidence intact. Create a new version for a new assessment rather than silently updating an old package.
- Generate PDFs into `output/`; use `tmp/` for local renders. Both are ignored by Git. Publish reviewed, dated packages under `exports/`.
- Run `node scripts/check-docs.mjs` and `git diff --check` before sharing changes.

Three compatibility symlinks retain filenames referenced by the unchanged integration guides: `FORTVAULT_CUSTODY_PRODUCT_DESCRIPTION.md`, `FORTX_CONNECT_PRODUCT_DESCRIPTION.md`, and `integrations/PARTNER_API_INTEGRATION_GUIDE.md`. They point to the primary documents; do not maintain separate copies.

This repository contains confidential product, architecture, and assessment material. Select the appropriate partner-facing documents for delivery; do not distribute the whole repository as an offer attachment.
