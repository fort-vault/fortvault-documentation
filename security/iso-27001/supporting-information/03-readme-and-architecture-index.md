# README and Architecture Index

| Document field | Value |
| --- | --- |
| Document owner | FortVault |
| Classification | Confidential |
| Status | Proposed controlled sharing set |
| Date | August 28, 2026 |

The following documents are suitable starting examples for the ISO implementation partner. Share them through the approved controlled channel or provide a reviewed export. Do not provide repository-wide access by default.

| Document | Purpose | Sharing notes |
| --- | --- | --- |
| `fortvault-backend/README.md` | Backend setup and development overview | Review for environment-specific values before sharing. |
| `fortvault-processing/README.md` | Custody Processing setup and execution overview | Review for environment-specific values before sharing. |
| `fortvault-mpc/README.md` | MPC component overview and development setup | Do not share node configuration, generated `node.env` files, keys, or recovery material. |
| `fortvault-health-audit/README.md` | Read-only health-audit procedure | Share only example/sanitized manifests; never include the audit key. |
| `iso-27001/FORTVAULT_CUSTODY_TECHNICAL_OVERVIEW.md` | Custody architecture, data flows, trust boundaries, and ISO control considerations | Current implementation overview; not evidence of operational control effectiveness. |
| `iso-27001/FORTVAULT_EXCHANGE_TECHNICAL_OVERVIEW.md` | Read-only exchange-integration architecture and scope | Confirm the recipient understands that trading and withdrawals are outside the current implemented scope. |
| `iso-27001/FORTVAULT_COMPONENT_ARCHITECTURE.md` | FortVault component, connection, and ownership architecture | Distinguishes durable state, transport, external providers, and MPC trust boundaries. |
| `iso-27001/FORTX_COMPONENT_ARCHITECTURE.md` | FortX product architecture and FortVault integration boundary | Distinguishes current foundation from planned financial-domain and KYT integrations. |
| `iso-27001/FORTX_FORTVAULT_PLATFORM_ARCHITECTURE.md` | Combined FortX and FortVault component architecture | Distinguishes current components from planned financial-domain integration. |
| `architecture/offline-mpc.md` | Development-prototype offline MPC architecture | Share only when relevant; explicitly retain its prototype and non-production status. |

## Pre-Sharing Review

Before sending any README or architecture document externally:

1. Review for credentials, tokens, private URLs, customer names, addresses, or internal operational identifiers.
2. Confirm the document describes the intended environment and has not been superseded.
3. Share the smallest relevant set rather than a full repository export.
4. Record what was shared, with whom, and on what date in the evidence register.
