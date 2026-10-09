# FortX and FortVault Platform Architecture

| Document field | Value |
| --- | --- |
| Document owner | FortVault |
| Intended audience | FortVault and its ISO 27001 implementation partner |
| Classification | Confidential |
| Status | Current implementation and planned integration boundary |
| Version | 1.0 |
| Date | August 28, 2026 |

## Purpose

This architecture describes the relationship between FortX, the end-user product, and FortVault, the custody and execution platform. It identifies current components and marks future FortX financial-domain and FortVault integration components separately.

The diagram must not be read as confirmation that every planned component is deployed or production-ready.

## System Boundary

### FortX - current foundation

- FortX web and mobile clients provide the end-user interface.
- FortX Backend currently provides the NestJS application foundation, separate user/admin identity integration, KYC integration with Sumsub, PostgreSQL, Redis, health checks, logging, and AWS Secrets Manager loading support.
- Keycloak provides the configured identity realm(s); Sumsub provides the external KYC service and authenticated webhook events.

### FortX - planned financial domain

The user ledger, deposits, withdrawals, quotes, swaps, liquidity decisions, and the versioned FortVault integration are product-boundary requirements. They are intentionally shown as planned until their APIs, authorization, persistence, reconciliation, and tests are implemented and approved.

### FortVault - custody platform

- FortVault Frontend is the partner/admin dashboard.
- Backend owns partner/workspace scope, users and roles, customers, vaults, actions, approvals, business records, and audit history.
- Messaging carries typed Redis Streams messages; it is not durable business state.
- Custody Processing owns address generation, custody execution state, transaction construction, MPC coordination, broadcast, retries, and reconciliation.
- MPC is deployed as an independent cluster per partner and owns threshold key shares, key generation, derivation, signing, and independent authorization validation.
- Listener ingests normalized blockchain events; Notification delivers user-facing messages.
- Exchange Processing is the separate provider-execution service for the current read-only exchange-account integration. Trading and exchange withdrawals are outside the current implemented scope.
- Policy/verification smart contracts and external blockchain/RPC providers form the external execution boundary.

## Integration Principle

FortX owns end-user product decisions and, when implemented, its financial ledger. FortVault owns physical custody and cryptographic execution. FortX must use versioned authenticated FortVault APIs and validated callbacks/events; it must not access FortVault databases directly or hold blockchain private keys, MPC shares, or exchange API secrets.

## Security Notes

- Backend approval does not replace MPC authorization. MPC must independently validate the exact signing request and authorization evidence.
- FortVault services own their own durable state. Redis Streams is transport only.
- Secrets are supplied through the approved deployment/secret-management boundary; they must not be placed in client applications, logs, source code, or Redis messages.
- Cloud deployment, network controls, TLS termination, backup configuration, monitoring, and endpoint management are operational controls that require separate live-environment evidence.

## Source References

- `fortx-backend/AGENTS.md` and `fortx-backend/README.md`
- `fortx-backend/docs/domain-design.md`
- `fortx-frontend/AGENTS.md` and `fortx-frontend/apps/mobile/README.md`
- `fortvault-documentation/iso-27001/FORTVAULT_CUSTODY_TECHNICAL_OVERVIEW.md`
- `fortvault-documentation/iso-27001/FORTVAULT_EXCHANGE_TECHNICAL_OVERVIEW.md`
- `fortvault-documentation/ARCHITECTURE.md`
