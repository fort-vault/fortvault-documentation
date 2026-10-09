# FortX Connect

## Exchange Backend and Backoffice

**Product overview for prospective partners**

Version 1.0 | 29 September 2026 | Confidential - prospective partner use

This document describes the agreed product scope. The partner delivery agreement identifies the available release, included integrations, implementation milestones, and acceptance criteria; this overview is not a certification of implementation or production readiness.

## 1. Overview

FortX Connect provides the backend services and operator backoffice for a digital asset exchange. It enables a partner to offer trading through its own customer channels while using a shared exchange core for customer balances, conversions, risk-based reconciliation, and operational management.

The current product model is quote-based and does not include an internal matching engine. Customer trades are handled through configured pricing and execution rules, with external execution initiated through FortVault when required.

**The backoffice is always part of FortX Connect.** Connect does not include end-user iOS, Android, or web applications. Those applications are added by the full [FortX product](fortx.md).

## 2. Exchange Core

The product scope covers:

| Area | Purpose |
| --- | --- |
| Identity and access | Keycloak-based authentication for customers and administrators, with backend-controlled account access and operator permissions |
| Customer verification | Sumsub individual KYC sessions, verification status, and status history |
| Customer accounts and balances | Maintain the exchange's customer trading balances, liabilities, reservations, and operation history |
| Quotes and conversions | Offer supported asset conversions under configured prices, spreads, fees, limits, and quote validity |
| Deposits and withdrawals | Coordinate customer funding and withdrawal workflows with FortVault custody, keeping customer accounting separate from blockchain execution |
| Risk-based reconciliation | Measure accumulated exposure from customer trades and initiate offsetting swaps when configured conditions are met |
| Per-order mirroring | Request a corresponding external execution for an individual customer trade where that execution mode is selected |
| Integration interfaces | Connect partner systems and customer channels to the exchange backend through the agreed API contract |
| Operational records | Link customer activity, reconciliation cycles, execution requests, fills, fees, and unresolved outcomes |

Supported assets, pairs, networks, limits, and provider integrations are defined for the selected deployment. Exchange trading support and blockchain custody support are different capabilities.

## 3. Trading and Reconciliation

### Risk-Based Reconciliation

Customer trades are not necessarily mirrored individually at an external venue. FortX Connect can accumulate and net opposite customer flows, monitor the remaining exposure, and request an offsetting swap based on configured risk, price-movement, notional, time, or manual triggers.

For example, if customers buy 10 BTC and sell 7 BTC, the residual is 3 BTC. FortX Connect determines whether and when to cover that residual, then requests the corresponding swap through FortVault. FortVault receives an execution request; it does not calculate FortX's customer exposure or decide its risk threshold.

One asset-pair reconciliation can map to one logical swap. A cycle involving several assets may require several swaps. Actual fills and fees determine the remaining position; submitting an order does not eliminate exposure.

Risk thresholds trigger intervention, not a guaranteed cap on losses. Execution depends on prices, liquidity, funding, authorization, and provider availability. The operating policy must define restrictions and escalation when exposure cannot be reduced.

### Per-Order Mirroring

Where selected, a customer trade produces a corresponding swap request through FortVault instead of waiting for a net reconciliation cycle. FortX Connect retains responsibility for the relationship between the customer trade and the external result, including pending, partial, rejected, and uncertain execution.

The same exposure must not be covered twice: mirroring and deferred reconciliation must account consistently for completed and outstanding executions. Customer trade commitment and failure treatment are defined in the agreed execution specification.

### Accounting Reconciliation

Comparing customer accounting records with custody movements and exchange results is separate from risk-based trading. Deposit consolidation is also distinct: moving funds between custody vaults must not create a second customer deposit credit.

## 4. Identity and Customer Verification

### Keycloak Authentication

FortX Connect integrates Keycloak for OpenID Connect (OIDC) authentication. The backend verifies access tokens against configured signing keys, issuer settings, and allowed clients, and associates authenticated identities with FortX records. Customer and administrator access use separately configured authentication contexts.

Administrator access additionally requires an active, provisioned FortX administrator account and the permissions required by the requested operation. A valid identity-provider token does not itself grant administrative or financial authority. Authentication policies, account recovery, identity-provider operation, and deployment configuration are agreed with the partner.

### Sumsub KYC

FortX Connect integrates Sumsub for individual Know Your Customer (KYC) verification. The backend issues short-lived SDK access tokens bound to the authenticated customer and a configured verification level. Document and liveness checks depend on that level and the provider configuration. Provider API credentials remain server-side.

The authentication and KYC interfaces belong to FortX Connect; they are not endpoints of the FortVault Partner API.

FortX records normalized verification status and status history, including pending, action-required, approved, and rejected outcomes. Status updates are received through signature-verified Sumsub webhooks, with duplicate and stale-event handling. An application completing an SDK session is not itself evidence of approval.

**Implementation scope:** backend authentication, administrator permission checks, authenticated KYC session/status APIs, and Sumsub webhook processing are present in the code. Production enablement requires the agreed Keycloak configuration, Sumsub account and verification level, data-processing arrangements, and deployment acceptance. Backoffice KYC review screens and end-user channel coverage must be included explicitly in delivery acceptance; these backend integrations do not establish that every screen is complete.

KYC establishes an identity-verification result, not permission to trade or withdraw. The partner's acceptance policy and server-side financial restrictions require their own implementation and acceptance. This customer KYC integration is separate from the proposed blockchain transaction-screening (KYT) integrations described in the FortVault Custody overview and does not imply regulatory certification.

## 5. Included Backoffice

The backoffice is the operator interface for administering FortX Connect, whether the partner supplies its own customer applications or uses the full FortX product.

Its functional scope covers customer and account review; balance and operation history; supported market and commercial configuration; reconciliation monitoring; execution exceptions; and authorized operational actions. Access is role-controlled and subject to backend authorization. Exact screens, reports, permissions, and configurable controls are identified in the delivery scope.

Backoffice is not an optional end-user frontend package. It remains included when no FortX customer application is supplied. FortVault's separate custody dashboard does not replace the FortX Connect backoffice.

## 6. FortVault Integration

| Responsibility | FortX Connect | FortVault |
| --- | --- | --- |
| Customer trading | Quotes, customer orders, trading balances, and commercial rules | Executes authorized custody or swap requests |
| Risk-based reconciliation | Exposure calculation, triggers, cycle management, and trading P&L | Returns execution outcomes, fills, and fees |
| Per-order mirroring | Decides when to mirror and links the customer trade to its execution | Processes the corresponding authorized swap |
| Blockchain custody | Requests operations and applies customer accounting rules | Vaults, addresses, policy-controlled transfers, signing, and chain observations |
| External swaps | Specifies the required conversion and permitted execution limits | Selects an eligible quote and executes on one sufficiently funded exchange account under the agreed swap scope |

Requests must distinguish the quantity to buy or sell from the amount to spend, including fee treatment and permitted execution limits. Target-quantity support is part of the agreed swap contract, not an assumption about an existing endpoint.

The initial FortVault swap model does not split a request across exchanges or automatically move funds between exchange accounts. Partial fills and uncertain responses require reconciliation before replacement execution. Automation does not bypass the applicable policy or approval requirements.

The [FortVault Custody overview](fortvault-custody.md) describes its separate capabilities and dependencies. That document currently classifies unified swaps, swap-specific authorization, and their API extensions as proposed delivery scope. These dependencies must be implemented and accepted for the integrated trading workflows; this document does not represent them as existing public API endpoints.

## 7. Delivery Boundary

FortX Connect comprises the exchange backend, integration interfaces, and operator backoffice. A partner provides its own end-user channels or selects the full FortX product for the iOS, Android, and web applications.

The delivery agreement defines supported assets and markets, pricing and execution modes, reconciliation controls, custody and exchange integrations, API versions, backoffice permissions, hosting, and service commitments. It also identifies Keycloak operating responsibilities, Sumsub licensing and verification levels, data retention and processing arrangements, and KYC-dependent operation restrictions. Fiat payment rails, additional identity providers, transaction screening, and additional trading features require explicit scope agreement. An internal matching engine is not included in the current product model.

FortX Connect and FortVault remain distinct products with distinct responsibilities. Their deployment and commercial inclusion are specified in the partner offer.
