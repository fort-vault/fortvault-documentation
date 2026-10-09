# FortVault Component Architecture

| Document field | Value |
| --- | --- |
| Document owner | FortVault |
| Intended audience | FortVault and its ISO 27001 implementation partner |
| Classification | Confidential |
| Status | Current implementation architecture |
| Version | 1.0 |
| Date | August 28, 2026 |

## Purpose

This document identifies the FortVault runtime components, their owned data stores, their principal connections, and the main security boundaries between business control, custody execution, cryptographic signing, and external suppliers.

The architecture describes source-controlled application behavior. Live cloud topology, network segmentation, firewall rules, TLS termination, backup effectiveness, and production access controls require separate operational evidence.

## Components

### User and business-control plane

- **Authorized partner users:** administrators and approvers operating through the FortVault Frontend.
- **FortVault Frontend:** React/Vite partner and administrator dashboard. It is not an authorization or business source of truth.
- **External API clients:** authenticated partner integrations using Backend APIs where enabled.
- **Backend:** business system of record for partner/workspace scope, users, roles, customers, vaults, assets, chains, actions, approvals, exchange accounts, and audit history.
- **Backend PostgreSQL:** durable Backend-owned business, audit, inbox, and outbox state.

### Messaging and execution plane

- **Messaging:** shared typed message contracts and Redis Streams transport behavior. It is a library, not an independent runtime service.
- **Redis Streams:** asynchronous command and event transport. It is not durable business or custody state.
- **Custody Processing:** owns address generation, derivation, transaction construction, custody execution state, MPC coordination, retries, and blockchain broadcast.
- **Processing PostgreSQL:** durable execution state, address/root metadata, MPC request lifecycle, transfer requests, retries, inbox, and outbox.
- **Listener:** ingests blockchain/provider events, tracks monitored addresses, normalizes events, and publishes idempotent chain events.
- **Listener PostgreSQL:** tracked addresses and Listener-owned idempotency/event state.
- **Notification:** consumes notification commands and routes them to configured channels. Telegram delivery is implemented; the email adapter remains a placeholder until a production email provider is integrated.
- **Exchange Processing:** durable exchange execution service for MPC-backed Ed25519 key generation, credential testing, balance, permission, and deposit-address synchronization. Trading and exchange withdrawals are not in the current implemented scope.
- **Exchange Processing PostgreSQL:** exchange request state, leases, MPC sessions, provider attempts, inbox, and outbox.

### Cryptographic and on-chain plane

- **Partner-specific MPC cluster:** one cluster per partner. Processing calls the API-facing master node; MPC peers communicate over encrypted gRPC and perform threshold key generation, derivation, signing, attestation, and independent authorization validation.
- **MPC node storage:** each MPC node owns separate encrypted key-share and MPC session state. No single node database should independently contain enough material to sign.
- **Policy and verification contracts:** on-chain registry, policy, and address-verification boundaries read by Backend, Processing, and MPC as applicable.
- **Blockchain RPC, data providers, and networks:** transaction construction/broadcast, confirmations, chain data, and provider callbacks used by Processing and Listener.

### External and operational components

- **Approved secret store:** supplies runtime credentials and configuration references to authorized services. Secret values must not enter Redis messages, logs, source control, or client applications.
- **Exchange APIs:** Binance, Gate, MEXC, and configured providers used by Exchange Processing. Private credential material is resolved inside Exchange Processing; MPC-backed private key material remains in MPC.
- **Notification channels:** Telegram Bot API is implemented. A production email supplier must be connected before email delivery can be claimed.
- **Health Audit:** read-only operational tool that queries liveness, readiness, sanitized configuration, partner/policy, MPC cluster, and Redis stream/consumer-group health.

### Development prototypes

- **Bootstrap Station:** development macOS prototype for offline MPC bootstrap transport.
- **Cold Signer:** development iOS participant for offline ECDSA MPC ceremonies and protected local share storage.

These prototypes are not part of the production runtime architecture and are not production-ready or independently security-audited. Their intended flow is documented separately in `architecture/offline-mpc.md`.

## Connection Register

| Source | Destination | Interface | Purpose |
| --- | --- | --- | --- |
| Authorized user | Frontend | HTTPS | Custody administration, action review, and approval interaction |
| Frontend | Backend | Authenticated HTTPS API | Read and mutate partner-scoped business resources |
| External API client | Backend | Authenticated HTTPS API | Partner integration where API access is enabled |
| Backend | Backend PostgreSQL | PostgreSQL protocol | Durable business, audit, inbox, and outbox state |
| Backend | Redis Streams | Typed Messaging envelopes | Publish custody, exchange, and notification commands; consume completion events |
| Redis Streams | Custody Processing | Consumer group | Deliver address and transfer execution commands |
| Custody Processing | Redis Streams | Durable outbox publication | Publish address and transfer completion events |
| Custody Processing | Processing PostgreSQL | PostgreSQL protocol | Durable execution, retry, root/address, MPC, inbox, and outbox state |
| Custody Processing | MPC master node | Authenticated HTTP API | Key generation during bootstrap, derivation, and exact-payload signing requests |
| MPC nodes | MPC peers | Encrypted gRPC | Interactive threshold cryptographic protocol |
| MPC node | MPC node storage | PostgreSQL/local storage boundary | Encrypted key shares and MPC session state owned by that node |
| Backend | Policy and verification contracts | Blockchain read calls | Read partner policy and verification configuration |
| Custody Processing | Policy and verification contracts | Blockchain read calls | Validate wallet types, policy, and execution context |
| MPC cluster | Policy and verification contracts | Blockchain read calls | Independently validate authorization and policy before signing |
| Custody Processing | Blockchain RPC/networks | Chain-specific RPC | Build and broadcast signed transactions; query transaction state |
| Blockchain data providers | Listener | Provider webhook/polling APIs | Deliver chain activity and confirmation data |
| Listener | Listener PostgreSQL | PostgreSQL protocol | Persist tracked addresses and idempotent event state |
| Listener | Redis Streams | Typed normalized events | Publish deposits, confirmations, and transaction status events |
| Redis Streams | Notification | Consumer group | Deliver notification commands |
| Notification | Telegram Bot API | HTTPS provider API | Deliver configured Telegram notifications |
| Notification | Email adapter | Internal adapter | Placeholder/log-only until a production email provider is integrated |
| Redis Streams | Exchange Processing | Consumer group | Deliver exchange operation commands |
| Exchange Processing | Exchange Processing PostgreSQL | PostgreSQL protocol | Persist requests, leases, MPC sessions, attempts, inbox, and outbox |
| Exchange Processing | MPC master node | Authenticated HTTP API | Generate Ed25519 public keys and sign exact exchange request payloads |
| Exchange Processing | Exchange APIs | Authenticated HTTPS APIs | Test credentials and synchronize balances, permissions, and deposit addresses |
| Exchange Processing | Redis Streams | Durable outbox publication | Publish sanitized exchange completion events |
| Approved secret store | Authorized services | Cloud secret-management API | Supply runtime configuration and opaque credential material |
| Health Audit | Service and MPC health endpoints | Read-only HTTPS | Check liveness, readiness, and sanitized configuration |
| Health Audit | Redis Streams metadata | Read-only Redis commands | Validate expected streams and consumer groups |

## Security Boundaries

- Frontend input and presentation are not authorization boundaries.
- Backend approval is necessary but does not replace independent MPC validation.
- Custody Processing is the only production component that should request custody signatures and broadcast blockchain transactions.
- Exchange Processing may request exchange-specific MPC key generation/signing but must not broadcast blockchain custody transactions.
- Redis Streams is transport only; each owning service persists its durable state before exposing completion.
- Each partner uses a separately configured MPC cluster. MPC key shares and exchange private-key material remain inside the MPC boundary.
- Services do not read another service's PostgreSQL database directly.
- Offline MPC prototypes remain outside the production runtime boundary until their documented security and operational gaps are closed.

## Source References

- `AGENTS.md`
- `ARCHITECTURE.md`
- `iso-27001/FORTVAULT_CUSTODY_TECHNICAL_OVERVIEW.md`
- `iso-27001/FORTVAULT_EXCHANGE_TECHNICAL_OVERVIEW.md`
- `architecture/offline-mpc.md`
- `fortvault-processing/README.md`
- `fortvault-exchange-processing/README.md`
- `fortvault-mpc/README.md`
- Listener, Notification, Backend, and Health Audit source-controlled health and message handlers
