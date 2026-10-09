# FortX Component Architecture

| Document field | Value |
| --- | --- |
| Document owner | FortX / FortVault |
| Intended audience | FortVault and its ISO 27001 implementation partner |
| Classification | Confidential |
| Status | Current foundation and planned product integrations |
| Version | 1.0 |
| Date | August 28, 2026 |

## Purpose

This document describes the FortX product boundary, current platform foundation, planned financial-domain components, and intended integration with FortVault custody, exchange providers, and Chainalysis KYT.

The diagram deliberately distinguishes source-verified current components from planned components. A planned connection is not evidence of implementation, deployment, provider onboarding, or operational control effectiveness.

## Components

### User channels

- **FortX Mobile:** Expo/React Native end-user application for iOS and Android.
- **FortX Web:** Vite/React end-user web application.

The clients use FortX Backend APIs and do not call FortVault, exchange providers, or Chainalysis directly.

### Identity and KYC

- **Keycloak:** configured FortX user and administrator identity provider.
- **Sumsub:** current KYC provider using MobileSDK token issuance, status queries, and HMAC-verified status webhooks.

### FortX current foundation

- **FortX Backend:** NestJS API foundation with authentication/KYC integration, configuration, structured logging, health checks, PostgreSQL, Redis, Swagger configuration, and AWS Secrets Manager loading support.
- **FortX PostgreSQL:** current identity and KYC persistence. It is intended to become the durable owner of FortX user-ledger and financial workflow state as those domains are implemented.
- **FortX Redis:** cache, rate-limit, and asynchronous infrastructure. It is not the authoritative financial ledger.

### FortX planned product domain

- **Customer and account domain:** users, currencies/assets, accounts, wallet/address mappings, and ownership relationships.
- **Immutable double-entry ledger:** available, held, pending, and settled user balances with compensating reversals and exact arithmetic.
- **Quotes and swap orchestration:** quote generation, expiry, order acceptance, liquidity decisions, venue execution status, fees, and settlement.
- **Deposits and withdrawals:** deposit-address requests, confirmed-deposit crediting, withdrawal reservation, custody submission, and deterministic settlement/failure handling.
- **Reconciliation:** reconciliation of the FortX ledger against FortVault custody balances and external exchange balances.
- **Risk and compliance orchestration:** server-side KYC policy decisions, KYT requests through FortVault, and workflow gating based on normalized results.

These domains are described in the FortX draft domain design but are not represented as complete current implementation.

### FortVault integration boundary

FortVault is shown as one external platform boundary from the FortX point of view. The intended versioned authenticated integration provides:

- custody deposit addresses and confirmed deposit events;
- approved withdrawal execution and completion/failure callbacks;
- blockchain custody, MPC signing, and transaction broadcast;
- exchange-account credential/key setup and synchronization through FortVault Exchange Processing;
- Chainalysis KYT screening orchestration and normalized risk results; and
- custody and provider reconciliation evidence.

FortX must not read FortVault databases directly or hold blockchain private keys, MPC shares, or raw exchange API secrets.

### Exchange providers

FortVault Exchange Processing currently has source-controlled provider adapters for:

- **Binance:** HMAC and MPC-backed Ed25519 authentication;
- **Gate.io:** HMAC authentication; and
- **MEXC:** HMAC authentication.

The current implemented provider operations are Ed25519 public-key generation, credential testing, balance synchronization, permission synchronization, and deposit-address synchronization. Exchange trading and withdrawals are not in the current implemented FortVault scope.

### Chainalysis KYT

Chainalysis KYT is a requested target provider, but no Chainalysis integration exists in the reviewed FortX or FortVault source. The intended integration is owned by FortVault. FortX accesses KYT only through FortVault's authenticated integration boundary:

- FortX submits the minimum required user, asset, network, address/transaction, workflow, and custody-reference context to FortVault;
- FortVault authenticates Chainalysis requests, verifies callbacks or polling results, and durably correlates provider request IDs, risk results, alerts, and case state;
- FortVault binds each result to the originating tenant, FortX workflow, asset, network, and custody reference, with idempotency and replay protection;
- FortVault returns a normalized KYT decision and status to FortX; and
- FortX applies the approved product policy to crediting, withdrawals, or other configured workflows. Neither Chainalysis nor FortVault writes directly to the FortX ledger.

The exact Chainalysis API product, data fields, callback model, retention, regional processing, and escalation procedure must be agreed before implementation.

## Connection Register

| Source | Destination | Interface | Purpose | Status |
| --- | --- | --- | --- | --- |
| FortX Mobile/Web | Keycloak | OIDC/OAuth over TLS | User authentication and token issuance | Current |
| FortX Mobile/Web | FortX Backend | Authenticated HTTPS API | End-user product operations | Current foundation |
| FortX Mobile | Sumsub MobileSDK | Provider SDK | KYC interaction | Current |
| FortX Backend | Sumsub | Authenticated HTTPS API | SDK token issuance and status queries | Current |
| Sumsub | FortX Backend | HMAC-verified webhook | Normalized KYC status changes | Current |
| FortX Backend | FortX PostgreSQL | PostgreSQL | Current identity/KYC and future financial state | Current foundation |
| FortX Backend | FortX Redis | Redis | Cache, rate limiting, and asynchronous infrastructure | Current foundation |
| FortX Backend | Planned financial domain | Internal application services | Ledger, quotes, swaps, deposits, withdrawals, reconciliation | Planned |
| FortX financial domain | FortVault | Versioned authenticated API | Deposit addresses, approved withdrawals, and KYT screening requests | Planned |
| FortVault | FortX Backend | Signed/validated callbacks, events, or API responses | Custody results and normalized KYT decisions/statuses | Planned |
| FortVault | Chainalysis KYT | Authenticated provider API | Address/transaction screening and case lookup | Planned |
| Chainalysis KYT | FortVault | Verified callback or polling result | Risk score, alert, case, and status updates | Planned |
| FortVault | Blockchain networks/providers | Chain RPC/provider APIs | Address custody, transaction broadcast, and confirmations | Current FortVault capability |
| FortVault | Binance | Authenticated exchange API | Key setup, credential test, balances, permissions, deposit addresses | Current limited scope |
| FortVault | Gate.io | Authenticated exchange API | Credential test, balances, permissions, deposit addresses | Current limited scope |
| FortVault | MEXC | Authenticated exchange API | Credential test, balances, permissions, deposit addresses | Current limited scope |

## Security and Ownership Boundaries

- FortX owns the future end-user financial ledger and product eligibility decisions.
- FortVault owns custody execution, exchange credential execution, blockchain broadcasting, and MPC cryptographic operations.
- FortX and FortVault exchange only authenticated, versioned, tenant-bound, idempotent requests and callbacks/events.
- Chainalysis KYT is a FortVault external compliance dependency. FortX accesses it only through FortVault and applies the approved product decision policy to FortVault's normalized result.
- Sumsub KYC status and Chainalysis KYT risk are separate controls with separate evidence, retention, and escalation requirements.
- Provider failures or delays must not create false user balances, duplicate credits, unreserved withdrawals, or silent risk bypasses.
- Current exchange-provider connectivity does not mean that trading or exchange withdrawals are implemented.

## Source References

- `fortx-backend/AGENTS.md`
- `fortx-backend/README.md`
- `fortx-backend/docs/domain-design.md`
- `fortx-frontend/AGENTS.md`
- `fortx-frontend/apps/mobile/README.md`
- `fortvault-exchange-processing/README.md`
- `fortvault-documentation/iso-27001/FORTVAULT_COMPONENT_ARCHITECTURE.md`
