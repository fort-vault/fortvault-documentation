# Architecture Overview

**Status:** architecture reference and intended security boundaries. This overview replaces the March 2026 regulatory draft as the navigation entry point. It is not an audit, deployment attestation, or verification that every intended invariant is enforced by a particular release.

## Component Ownership

| Component | Responsibility | Boundary |
| --- | --- | --- |
| Backend | Tenants, customers, vaults, assets, actions, approvals, policies, and APIs | Business source of truth; reconstructs authorized action payloads from trusted records |
| Frontend | Dashboard and user interaction | No independent authorization or policy authority |
| Custody Processing | Address derivation, custody execution state, MPC coordination, and blockchain broadcast | Execution orchestrator, not an independent authorization authority |
| Exchange Processing | Exchange provider calls, credential resolution, retries, and operation state | Own database; does not read Backend PostgreSQL or broadcast custody transactions |
| MPC | Threshold cryptography, derivation, signing, attestation, and authorization validation | Cryptographic boundary; independently validates the signing request and its authorization evidence |
| Messaging | Shared Redis Streams contracts and transport | Transport, not durable business state |
| Listener | Chain/provider ingestion and normalized transaction events | Observation, not business authorization |
| Notification | User-facing message rendering and delivery | Not a source of truth |
| Contracts | On-chain registry, policy, and address-verification contracts | Role and verification mechanisms must be checked against the deployed contract version |

Backend, Custody Processing, Exchange Processing, and MPC own their respective durable state. Inter-service contracts carry identifiers and sanitized results, not private keys, shares, or raw credentials.

## Custody Execution

1. A dashboard user or partner requests an action through Backend.
2. Backend applies tenant/resource authorization and the required policy, signature, and approval checks for that action.
3. Custody Processing coordinates the approved execution and persists its execution state.
4. MPC validates authorization evidence and exact payload bindings before participating in signing.
5. Custody Processing broadcasts the authorized signed transaction through the appropriate chain implementation.
6. Listener ingests chain results and emits normalized events. Consumers durably process them, tolerate duplicates, and update their own state before exposing completion.

This is a responsibility-level flow, not a specification of one endpoint's response timing or a guarantee that every observed transaction has finality. Confirmation thresholds, recovery, reorg handling, and API status fields require chain- and release-specific verification.

## Exchange Execution

Backend owns exchange accounts and approved business operations. Exchange Processing owns provider execution and its own operation state. Exchange-authentication signing follows its dedicated MPC authorization path; it must not become an alternative route for authorizing custody broadcasts.

FortX can use FortVault for custody and exchange connectivity. FortVault can also serve other partners independently. Product descriptions and proposed API extensions define the intended swap and automation scope; existing exchange connectivity alone does not establish that unified best-quote execution is delivered.

## Signing Trust Boundary

Backend, Processing, Redis, Listener, Notifications, frontend input, and other online services must be treated as potentially compromised when assessing signing authorization. Backend approval is necessary but not the only boundary.

The intended MPC checks bind the action and actual transaction to the chain, asset, source, destination, amount, nonce, approvals, signer authorization, expiry, policy decision, and replay protection wherever applicable. A missing binding is an implementation gap to report, not an architectural guarantee to assume.

Deploy one MPC cluster per partner. Partner context and `POLICY_ENGINE_ADDRESS` belong to deployment configuration, not runtime tenant routing inside a shared cluster. Private keys and MPC shares remain within their designated secure boundaries.

## Chain and Data Boundaries

- Keep EVM, Tron, Bitcoin/UTXO, and exchange behavior behind their own chain/provider abstractions.
- Store financial amounts as exact base-unit integers, never floating-point values.
- Persist ordering-sensitive state before publishing it. Redis delivery is not proof of durable business completion.
- Duplicate events must not cause duplicate financial effects; mismatched payloads must be rejected.
- Frontend filtering cannot replace server-side tenant isolation or authorization.

## Further Reading

| Topic | Reference |
| --- | --- |
| Product scope and status distinctions | [FortVault Custody](../products/fortvault-custody.md) |
| MPC design background | [MPC](mpc.md) |
| Registry, policy, and verification contracts | [Smart contracts](smart-contracts.md) |
| Offline MPC and device boundaries | [Offline MPC](offline-mpc.md) |
| Custody integration contract | [Partner API guide](../integrations/FORTVAULT_PARTNER_API_INTEGRATION_GUIDE.md) |
| Historical regulatory draft | [March 2026 architecture](../archive/2026-03/architecture-draft.md) |

Cold Signer and Bootstrap Station remain development prototypes pending security, recovery, physical-device, and independent cryptographic review. Neither should be presented as production-ready on the basis of this overview.
