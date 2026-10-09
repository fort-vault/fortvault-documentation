# FortVault and FortX Response to Bank Platform Requirements

**Document status:** Internal review draft  
**Solution scope:** FortVault multi-tenant digital-asset custody and FortX multi-tenant exchange integration  
**Delivery model:** Subscription technology platform. Alternative deployment and source-code arrangements are subject to separate commercial and technical agreement.

## 1. Response basis

FortVault and FortX are primarily digital-asset custody, wallet, transaction-processing, exchange-connectivity, and compliance-integration platforms. This response assesses all 211 coded requirements in the source specification. Requirements specific to card issuing, fiat payment-channel operations, yield products, customer tax accounting, internal matching, or bank-internal processes are identified transparently when they are outside the current product scope.

The platform uses tenant isolation for each connected bank. FortVault provides custody and policy-controlled MPC signing; FortX provides exchange connectivity, balances, trading, conversion, and reconciliation capabilities. The platform has undergone independent source-code audit and penetration testing by GT. FortVault is also progressing through its ISO 27001 implementation programme.

The status **Compliant** identifies a supported platform capability. It does not replace deployment evidence or contractual agreement. SLA, performance, disaster-recovery, retention, support, audit-right, and similar operational commitments become binding only when defined in the final agreement and supported by the agreed production evidence.

## 2. Scope assumptions requiring bank confirmation

This internal draft uses the following working assumptions. They should be confirmed with the bank before the response is finalized:

1. **Core product scope.** The primary scope is multi-tenant digital-asset custody, wallet management, blockchain transaction processing, exchange connectivity, conversion, and related compliance controls.
2. **Delivery model.** The standard model is a managed subscription service. Source-code delivery, source-code escrow, bank-hosted deployment, or transfer of platform-specific intellectual-property rights requires a separate commercial, legal, and technical agreement.
3. **MPC deployment.** Standard partner onboarding is configuration-driven. A bank that elects to operate an MPC node requires a coordinated infrastructure and security deployment.
4. **Ledger interpretation.** Blockchain state is authoritative for controlled on-chain assets. The bank should confirm whether its ledger requirements also require FortVault/FortX to act as the authoritative accounting ledger for internal customer liabilities.
5. **Fiat scope.** A simple integration with fiat payment processing is available. Full fiat reconciliation, payer verification, settlement accounting, recalls, and chargeback case management depend on the bank and payment provider and are not complete native platform capabilities.
6. **Excluded banking products.** Card issuing/authorization, yield products, and customer tax calculation are not part of the standard platform scope unless separately agreed.
7. **Compliance providers.** Chainalysis KYT provides blockchain transaction and address-risk screening. Travel Rule compliance requires a separately enabled Travel Rule service or compatible VASP messaging network.
8. **Bank-channel architecture.** Bank mobile and web applications access FortVault/FortX through the bank backend; platform credentials are not distributed to end-user devices.
9. **Operational commitments.** Final availability, support, data residency, recovery, retention, audit, and performance commitments depend on the agreed production topology and contract.
10. **Exchange execution model.** The standard FortX model routes orders to configured external exchanges. A shared internal order book or matching engine is a separate capability that can be discussed and implemented if required.
11. **Custody treasury automation.** Customer addressing, MPC signing, recovery, and network fee handling are core capabilities. Fully automatic consolidation, demand forecasting, and storage-allocation governance require additional treasury automation.
12. **Proof of reserves.** MPC address-control attestations prove control of custody addresses. Merkle proof of liabilities, periodic third-party proof of reserves, and bank-specific liability inclusion proofs are not currently provided.
13. **Automated decisions.** FortVault/FortX does not train a proprietary customer-risk model. Third-party screening outputs support controlled decisions, while provider model evidence and quality metrics depend on the provider.
14. **RPC resilience.** Multi-RPC operation with provider health and stale or divergent-state detection is included in the proposed custody capability.

## 3. Overall summary

| Status | Count | Percentage |
|---|---:|---:|
| Compliant | 105 | 49.8% |
| Partially compliant | 66 | 31.3% |
| Not compliant | 40 | 19.0% |
| **Total** | **211** | **100%** |

## 4. Summary by section

| Section | Compliant | Partially compliant | Not compliant | Total |
|---|---:|---:|---:|---:|
| BUS - Business and tenancy | 7 | 2 | 0 | 9 |
| API - Integration interfaces | 13 | 6 | 2 | 21 |
| LGR - Ledger and financial control | 3 | 6 | 3 | 12 |
| NFR - Non-functional requirements | 2 | 8 | 1 | 11 |
| OPS - Operations and commercial controls | 5 | 6 | 5 | 16 |
| SEC - Security | 8 | 5 | 2 | 15 |
| CMP - Compliance | 11 | 4 | 1 | 16 |
| FUN - Functional capabilities | 23 | 5 | 18 | 46 |
| TEC - Technical architecture | 8 | 8 | 2 | 18 |
| CUS - Custody engineering | 17 | 7 | 3 | 27 |
| MTC - Internal matching and trading | 6 | 7 | 2 | 15 |
| ADJ - Automated decision governance | 2 | 2 | 1 | 5 |
| **Total** | **105** | **66** | **40** | **211** |

## 5. Detailed responses

### BUS - Business and tenancy

| ID | Requirement | Status | FortVault/FortX response |
|---|---|---|---|
| BUS-01 | Every stored entity and interface must be isolated by connected bank. | Compliant | Tenant scope is enforced server-side across customers, vaults, exchange accounts, actions, reports, and APIs. Cross-bank operator access is privileged and audited. |
| BUS-02 | Bank onboarding must be configuration and credential issuance without code changes. | Compliant | Standard tenant onboarding is automated and configuration-driven. A bank-operated MPC node requires a separately coordinated infrastructure deployment. |
| BUS-03 | The platform must be purpose-built, with third-party components declared and platform-specific source rights and escrow addressed. | Partially compliant | FortVault/FortX are purpose-built platforms and dependencies are documented. The standard model is subscription-based; source rights and escrow require a separate agreement. |
| BUS-04 | Per-bank configuration must cover assets, currencies, fees, limits, features, retention, reports, and reliance policy. | Compliant | Partner configuration is tenant-specific and controls enabled assets, services, policies, limits, reporting, and related operational settings. |
| BUS-05 | A capability can be enabled or disabled for one bank without redeploying or affecting others. | Compliant | Tenant-level service and policy configuration isolates capability availability without changing other banks. |
| BUS-06 | A bank may require data storage and processing in a specified jurisdiction. | Compliant | Deployment topology and tenant placement can be selected to meet agreed residency requirements, subject to provider and service availability. |
| BUS-07 | One bank's load must not reduce another bank below its agreed service level. | Compliant | Tenant rate limits, isolated operation state, worker scaling, and infrastructure controls prevent one tenant from consuming uncontrolled shared capacity. |
| BUS-08 | An exiting bank receives a complete documented export of customers, positions, operations, and evidence. | Partially compliant | Tenant-scoped reports and exports cover key customer, balance, transaction, and audit data, but a single complete exit export package is not currently provided. |
| BUS-09 | Revenue allocation must be calculated and reported by bank and capability. | Compliant | Tenant and operation attribution supports separate calculation and reporting of platform, bank, fee, and exchange-related revenue. |

### API - Integration interfaces

| ID | Requirement | Status | FortVault/FortX response |
|---|---|---|---|
| API-01 | Every catalogue capability must be available through public APIs rather than console-only action. | Compliant | Bank-facing business capabilities are exposed through authenticated, tenant-scoped APIs; administrative operations remain appropriately privileged. |
| API-02 | APIs require a machine-readable, versioned contract used for documentation, SDK generation, and contract tests. | Compliant | OpenAPI contracts are generated and versioned from the authoritative API surface and support documentation and generated clients. |
| API-03 | Monetary values must be strings with explicit asset and scale; floating point is prohibited. | Compliant | Digital-asset and financial amounts are exchanged as exact strings/base units with explicit asset and network context. |
| API-04 | Every mutating endpoint requires a bank-provided idempotency key and status lookup. | Compliant | Mutating operations use durable identifiers and idempotent processing; operation status is retrievable by identifier. |
| API-05 | Breaking changes require a new major version, 12-month parallel support, and individual notice. | Partially compliant | APIs are versioned, but a universal contractual 12-month parallel-support and notification commitment has not yet been established. |
| API-06 | Rate limits must be published, returned in headers, configurable by bank, and produce retryable errors. | Compliant | Tenant-aware rate controls and explicit retryable errors protect platform capacity; limits can be agreed per API class. |
| API-07 | Bulk exports of balances, operations, postings, and cases must support independent bank reconciliation. | Partially compliant | Reports and exports cover key custody and exchange data, but the complete requested bulk dataset is not available through one unified export domain. |
| API-08 | A test environment must reproduce production semantics and deterministically simulate defined failures. | Partially compliant | Test environments and mocks exist, but the full catalogue of deterministic blockchain, custody, exchange, screening, and card failure scenarios is not provided. |
| API-09 | Generated and co-versioned SDKs must exist for Java, Kotlin, Swift, Python, and TypeScript. | Not compliant | The complete required multi-language SDK set is not currently distributed. |
| API-10 | A developer portal must provide documentation, changelog, contracts, sandbox credentials, request inspection, and integration status. | Partially compliant | API documentation and contracts exist, but a complete tenant-specific developer portal with all requested capabilities is not currently provided. |
| API-11 | Every request and response must propagate a bank-provided correlation identifier into support tools. | Partially compliant | Service and operation identifiers exist, but universal end-to-end propagation of a bank-supplied correlation ID is not yet demonstrated. |
| API-12 | Customer-context calls require a short-lived signed bank assertion identifying the customer and authentication context. | Compliant | Partner authentication and signed authorization evidence bind customer context and authentication information to protected operations. |
| API-13 | Value-moving operations require operation-specific strong customer authentication evidence. | Compliant | Approval and authorization evidence is bound to the exact action rather than accepted as a generic session authorization. |
| API-14 | Authentication evidence must be retained with the operation for the required period. | Compliant | Action, approval, actor, policy, and related authorization evidence are retained in audit and operation history. |
| API-15 | The platform must enforce minimum limits, cooling periods, and holds independently of bank assertions. | Partially compliant | FortVault policy and MPC validation independently enforce custody limits and restrictions, but the complete formal accounting hold and expiry lifecycle is not provided. |
| API-16 | Bank-employee actions on behalf of customers must be distinguishable, privileged, and justified. | Compliant | RBAC, actor identity, action reason, approvals, and audit records distinguish administrative actions from customer actions. |
| API-17 | Events must be signed, at-least-once, retried, and monotonically sequenced per bank. | Compliant | Durable events are retried and tenant-scoped; identifiers and ordering metadata support duplicate and gap detection. |
| API-18 | Any event range must be replayable and subscriptions resumable from a specified position. | Not compliant | Arbitrary historical replay and position-based resubscription are not currently exposed as a complete bank-facing service. |
| API-19 | Events must carry identifiers and state, not presentation content. | Compliant | Event contracts communicate typed state and identifiers; the bank controls customer-facing presentation. |
| API-20 | Delivery failure for one bank must not block another bank or the business operation. | Compliant | Tenant delivery state and asynchronous processing isolate failures from other banks and from durable business completion. |
| API-21 | Event types must be versioned; existing semantics cannot change within a major version. | Compliant | Typed event contracts follow compatibility rules and preserve existing meaning within a supported contract version. |

### LGR - Ledger and financial control

| ID | Requirement | Status | FortVault/FortX response |
|---|---|---|---|
| LGR-01 | Balances must be derived from authoritative activity and never arbitrarily set. | Partially compliant | Blockchain state is authoritative for controlled on-chain assets. The bank must confirm whether FortX must also be the authoritative internal customer-liability ledger. |
| LGR-02 | Ledger history must be append-only, with corrections by reversal rather than deletion or modification. | Partially compliant | Blockchain history is immutable, but append-only enforcement for every local accounting and metadata record is not guaranteed. |
| LGR-03 | Amounts require exact base units/fixed point and deterministic documented rounding. | Compliant | Amounts use exact base units or fixed-point strings, with asset-specific precision and deterministic calculation rules. |
| LGR-04 | Posting must be idempotent by business key. | Compliant | Unique operation, transaction, and movement identifiers prevent duplicate balance effects under retries or duplicate events. |
| LGR-05 | The ledger must provide the specified bank accounting classifications. | Partially compliant | Custody, available/locked exchange balances, transactions, and fees are classified, but no complete bank chart of accounts is claimed. |
| LGR-06 | Holds must expire and release through ledger postings. | Not compliant | A formal accounting-ledger hold and expiry-posting subsystem is not currently provided. |
| LGR-07 | Historical balances must be reconstructable without replaying application logic. | Partially compliant | Historical custody positions can be reconstructed from retained records and blockchain history, subject to confirmation of the bank's internal-ledger interpretation. |
| LGR-08 | Maintain customer and asset cost basis for realized profit/loss and tax reporting. | Not compliant | Customer tax cost-basis calculation is outside the current product scope. Transaction data can be exported to the bank's accounting systems. |
| LGR-09 | Perform daily and on-demand solvency checks with automatic shortfall alerts. | Partially compliant | Controlled assets and balances are available for reconciliation, but a complete automatic liability-versus-assets solvency control is not claimed. |
| LGR-10 | Protect the internal ledger against undetected retrospective modification. | Not compliant | Blockchain history is tamper-resistant, but the internal database ledger does not currently provide independently verifiable cryptographic tamper evidence. |
| LGR-11 | Declare and test ledger throughput. | Partially compliant | Application services scale horizontally and settlement throughput is constrained by the selected blockchain or exchange, but the requested ledger benchmark evidence is not currently available. |
| LGR-12 | Define valuation sources, cutoffs, stale-price rules, and illiquid-asset treatment. | Compliant | FortX defines configured price sources, freshness limits, unavailable-price behavior, and asset-specific valuation handling. |

### NFR - Non-functional requirements

| ID | Requirement | Status | FortVault/FortX response |
|---|---|---|---|
| NFR-01 | Platform availability must be 99.95% monthly and card authorization 99.99%. | Partially compliant | FortVault/FortX supports redundant deployment and health monitoring for custody and exchange services, but no card authorization service is currently provided. Exact production availability commitments are contractual. |
| NFR-02 | P99 authorization, sub-300 ms quotation, and sub-200 ms P95 balance latency are required. | Partially compliant | The architecture supports low-latency operations, but these percentile thresholds have not been established as measured production commitments. |
| NFR-03 | Sustained and peak throughput, including 5x volatility spikes, must be load-tested. | Partially compliant | Services are horizontally scalable; settlement throughput depends on the selected blockchain. The complete requested benchmark evidence is not currently available. |
| NFR-04 | Support 10x launch volume without architecture replacement and declare the ceiling. | Partially compliant | The service architecture scales horizontally, but a measured 10x capacity ceiling has not been formally demonstrated. |
| NFR-05 | Zero ledger/authorization data loss, reads within one hour, and full recovery within four hours. | Partially compliant | Durable stores and backups exist, but zero-loss recovery and the requested RTO require an agreed production topology and completed recovery testing. |
| NFR-06 | Any unexplained reconciliation difference must alert within one reconciliation cycle. | Compliant | Reconciliation status and discrepancy controls identify unexpected differences and support immediate operational escalation. |
| NFR-07 | End-to-end tracing must propagate a bank identifier with metrics and structured logs. | Partially compliant | Operation, action, tenant, and transaction identifiers support investigation, but universal bank-provided correlation-ID propagation and complete distributed tracing are not yet demonstrated. |
| NFR-08 | Define SLIs/SLOs per path, error budgets, and an exhaustion policy. | Not compliant | A complete formal SLI, SLO, and error-budget governance framework is not currently established. |
| NFR-09 | Provide a status page and machine-readable service state. | Partially compliant | Machine-readable liveness, readiness, configuration, and dependency health checks exist, but a complete external service-status page is not currently provided. |
| NFR-10 | Externalize and localize error and status messages. | Compliant | Stable error semantics are separated from client presentation, allowing the bank to localize customer-facing messages. |
| NFR-11 | CI must enforce coverage thresholds and architecture decisions must be maintained. | Partially compliant | Automated tests and architecture documentation exist, but uniform CI-enforced coverage thresholds across all components are not currently demonstrated. |

### OPS - Operations and commercial controls

| ID | Requirement | Status | FortVault/FortX response |
|---|---|---|---|
| OPS-01 | The platform provides second-line support with contractual channels, severity, response targets, and escalation. | Partially compliant | FortVault can provide technical second-line support, but no bank-specific support agreement or SLA exists at this first-contact stage. |
| OPS-02 | Bank support agents can trace operations without accessing credentials or key material. | Compliant | RBAC-protected dashboards, activity history, audit records, and APIs provide operational visibility without exposing secrets or MPC material. |
| OPS-03 | Card disputes and chargebacks must follow scheme deadlines and evidence procedures. | Not compliant | Card dispute and chargeback processing is outside the current platform scope. |
| OPS-04 | Reconciliation must produce dated reports retained per bank and overall. | Compliant | Tenant-scoped and consolidated reconciliation reports retain balances, movements, timestamps, and supporting operational evidence. |
| OPS-05 | Accounting corrections require two-person approval and documented justification. | Partially compliant | Maker-checker controls and audit records support controlled changes, but a complete append-only accounting correction and reversal workflow is not currently provided. |
| OPS-06 | Treasury requires liquidity by asset and location, thresholds, forecasts, and rebalancing. | Partially compliant | FortX consolidates custody and exchange positions and supports monitoring, thresholds, and controlled rebalancing, but complete demand forecasting is not currently provided. |
| OPS-07 | Low operational balances must alert before customer operations fail. | Compliant | Balance monitoring and configured thresholds support proactive treasury and operational notification. |
| OPS-08 | Venue and counterparty exposure must be measured, limited, reported, and automatically constrained. | Compliant | FortX associates balances and operations with each exchange, applies tenant limits, and prevents unauthorized exposure-increasing actions. |
| OPS-09 | The bank must receive data for independent reconciliation and discrepancy resolution. | Compliant | Reports and APIs expose transactions, balances, fees, identifiers, and timestamps needed for independent reconciliation. |
| OPS-10 | Support tiers require severity-based response/resolution targets and a continuous critical-incident channel. | Partially compliant | Technical support can be provided, but no bank-specific contractual support tiers or response commitments exist yet. |
| OPS-11 | The commercial proposal must quantify remedies for SLA breach. | Not compliant | No commercial agreement or quantified SLA-remedy schedule exists at this first-contact stage. |
| OPS-12 | Platform-specific source code must be held in escrow under defined release conditions. | Not compliant | No source-code escrow agreement currently exists. Source-code deployment or escrow can be discussed under a separate arrangement. |
| OPS-13 | A transition plan must define transfer of knowledge, data, and operations. | Not compliant | No bank-specific exit or transition plan has yet been agreed. |
| OPS-14 | Intellectual-property and post-termination rights must be allocated explicitly. | Not compliant | No bank-specific intellectual-property agreement currently exists. Subscription rights and any alternative source-code rights require negotiation. |
| OPS-15 | Maintain a subprocessor register and a process for objections to additions. | Partially compliant | Infrastructure and external providers are identifiable, but no bank-specific contractual notification and objection process exists yet. |
| OPS-16 | The bank and regulators require contractual audit rights over security and production changes. | Partially compliant | Security and audit evidence can be provided under confidentiality controls, but formal bank and regulator audit rights have not yet been agreed. |

### SEC - Security

| ID | Requirement | Status | FortVault/FortX response |
|---|---|---|---|
| SEC-01 | Signing material must remain inside custody and signing must require hardware or quorum policy. | Compliant | Private keys are not reconstructed. MPC key shares remain in separate MPC nodes, and signing requires the configured threshold and authorization evidence. |
| SEC-02 | Custody requires operational, intermediate, and deep-storage tiers with controlled replenishment. | Compliant | FortVault supports configurable custody structures and controlled movement between operational and protected storage according to partner policy. |
| SEC-03 | Withdrawal limits must be enforced outside the application. | Compliant | Policy contracts and MPC-side authorization checks prevent the application alone from bypassing custody limits and approval policy. |
| SEC-04 | Secrets require managed storage or hardware modules and automatic rotation. | Partially compliant | Production secrets use approved cloud secret managers and are not embedded in build artifacts, but automatic rotation is not demonstrated for every secret type. |
| SEC-05 | Trust must use short-lived workload identities rather than network location. | Partially compliant | Cloud roles, service accounts, and scoped credentials supplement private networking, but short-lived automatically renewed identity is not universal across all workloads. |
| SEC-06 | Privileged actions require multiple approvals and an auditable initiator/approver record. | Compliant | RBAC and approval policies record the initiator, approver, reason, action, tenant, and resulting state. |
| SEC-07 | CI/CD requires dependency, static, dynamic, and image scanning, artifact signing, and provenance. | Partially compliant | Source review and automated testing exist, but the complete requested SAST, DAST, image scanning, artifact signing, and provenance chain is not yet demonstrated. |
| SEC-08 | Independent penetration testing is required before launch and annually, with remediation validation. | Compliant | GT performed independent source-code audit and penetration testing. Reports and remediation evidence can support the review process. |
| SEC-09 | Abuse controls must cover takeover, coercion, and social engineering across value-moving operations. | Partially compliant | Authentication, approvals, limits, KYT screening, and operational intervention protect supported custody and exchange workflows, but card-spending abuse controls are unavailable. |
| SEC-10 | Incident response must define severity, responsibility, and bank/regulator notification. | Compliant | Incident procedures define classification, escalation, containment, evidence, communication, and notification responsibilities. Specific deadlines are contractual. |
| SEC-11 | Custody insurance limits and exclusions must be disclosed, or absence stated. | Not compliant | No custody insurance coverage is currently claimed. |
| SEC-12 | Compromised bank credentials must be revoked independently within minutes. | Compliant | Credentials and tenant access are isolated and can be disabled for one bank without interrupting other tenants. |
| SEC-13 | Penetration testing must explicitly test and report attempted cross-bank access. | Not compliant | Existing independent testing does not currently provide explicit evidence of the required cross-bank isolation penetration scenario. |
| SEC-14 | Mobile applications must not hold platform credentials or bypass the bank backend. | Compliant | FortX provides bank-facing APIs through the bank backend. Platform credentials remain server-side and are not distributed to the bank's mobile application. |
| SEC-15 | Card data must remain in a certified perimeter and use hosted or tokenized display. | Partially compliant | FortVault/FortX does not currently provide card services or process card credentials. Any future card integration must keep sensitive data within a certified issuer/provider using hosted or tokenized interfaces. |

### CMP - Compliance

| ID | Requirement | Status | FortVault/FortX response |
|---|---|---|---|
| CMP-01 | Reliance on bank verification must be recorded, reasoned, dated, policy-bound, and revocable. | Compliant | Customer verification source, policy, decision, date, and scope are retained and can be revoked by tenant policy. |
| CMP-02 | Sanctions and PEP screening is required at onboarding and continuously, at least daily. | Compliant | The configured identity/compliance provider supports onboarding and ongoing sanctions and PEP screening. |
| CMP-03 | Customer risk rating must include jurisdiction, products, behavior, and screening and drive controls. | Compliant | Tenant-configurable risk classification determines applicable limits, approvals, screening, and monitoring intensity. |
| CMP-04 | Risk tiers, thresholds, and permissions must be configurable per bank. | Compliant | Roles, limits, assets, policies, and risk controls are tenant-scoped and configuration-driven. |
| CMP-05 | Periodic review must follow risk and document expiry, with advance bank notice. | Compliant | Verification status and review schedules support risk-based renewal and bank-facing status notification. |
| CMP-06 | Verification artifacts require a separate encryption hierarchy and retention policy. | Compliant | Sensitive source documents remain with approved verification providers where possible; retained evidence is protected under dedicated access and retention controls. |
| CMP-07 | Complete verification, decision, actor, and rationale history must be exportable. | Compliant | Verification and decision events are retained with actor, status, reason, and tenant context and are available for evidence reporting. |
| CMP-08 | Travel Rule data must be exchanged before or with transfers and recorded with the withdrawal. | Partially compliant | Chainalysis integration provides KYT screening. Travel Rule compliance additionally requires the Chainalysis Travel Rule service or another compatible VASP messaging network. |
| CMP-09 | Transfers to custodial wallets require proof of control above configurable thresholds. | Partially compliant | FortVault can attest control of its own MPC addresses, but universal destination-wallet proof by signature or micro-transfer is not currently provided. |
| CMP-10 | Unsupported Travel Rule counterparties require explicit bank/jurisdiction policy. | Compliant | Transfer policy is tenant and jurisdiction specific; unsupported counterparties can be blocked or escalated rather than silently permitted. |
| CMP-11 | A unified rule and case model must cover every supported movement of value. | Partially compliant | Tenant-scoped controls cover supported custody and exchange activity, but the required unified model does not cover unsupported card and yield products. |
| CMP-12 | Compliance users must manage versioned rules without code releases, with testing and dual approval. | Compliant | Configurable tenant policies and maker-checker administration separate controlled rule changes from ordinary application releases. |
| CMP-13 | Monitoring must cover structuring, rapid movement, dormant accounts, risky counterparties, mixers, bridges, and layering. | Partially compliant | Chainalysis KYT and platform transaction controls cover blockchain and account risks, but card cash-out monitoring is unavailable. |
| CMP-14 | Cases require ownership, timers, evidence, reasoning, escalation, immutable history, and API access. | Compliant | Compliance decisions and evidence are tenant-scoped, auditable, assignable, and available through controlled platform interfaces. |
| CMP-15 | Jurisdiction-specific regulatory exports require destination controls. | Not compliant | Complete jurisdiction-specific regulatory filing packages are not currently generated. Transaction and evidence exports remain available to the bank. |
| CMP-16 | Historical counterparties must be rescreened when lists change and cases created for new matches. | Compliant | Ongoing Chainalysis monitoring supports updated counterparty risk detection and operational escalation of changed classifications. |

### FUN - Functional capabilities

| ID | Requirement | Status | FortVault/FortX response |
|---|---|---|---|
| FUN-01 | Customers can have multiple digital-asset and fiat accounts opened through API. | Compliant | Customer account and asset capabilities are exposed through tenant-scoped APIs for supported digital assets and configured currencies. |
| FUN-02 | Internal transfers within a bank must be atomic and independent of external settlement. | Compliant | FortX records supported internal transfers atomically without waiting for blockchain or exchange settlement. |
| FUN-03 | Available and reserved balances must be separate, with reservation reasons retrievable. | Compliant | Account and exchange balance models distinguish available and locked amounts and associate operation context with restrictions. |
| FUN-04 | Closing an account with a residual amount requires a defined settlement procedure. | Compliant | Tenant policy determines consolidation, transfer, conversion, or documented treatment of residual digital-asset balances. |
| FUN-05 | Accounts can be blocked by the bank, operator, or automatic control, with distinct records. | Compliant | Restriction source, actor, reason, time, and affected capability are retained in tenant-scoped state and audit records. |
| FUN-06 | Deposit crediting must be idempotent and resilient to rescans and chain reorganizations. | Compliant | Network transaction and movement identifiers prevent duplicate ingestion; confirmation policy and listener processing handle network finality. |
| FUN-07 | Confirmation depth must be configurable by asset/network and readable through API. | Compliant | Network and asset configuration defines required confirmation depth and exposes applicable reference information. |
| FUN-08 | Unsupported, below-minimum, or missing-memo deposits must be recorded and handled. | Compliant | Exceptional deposits are retained for operator review rather than discarded, with audited resolution and return handling. |
| FUN-09 | Held deposits require deadlines, defined outcomes, and bank notification at each transition. | Compliant | Deposit state transitions, review outcomes, reasons, and notifications are represented as durable tenant-scoped operations. |
| FUN-10 | Returns require compliance approval and a sanctions-policy check. | Compliant | Return actions require authorization and renewed policy/risk validation before custody execution. |
| FUN-11 | Support destination whitelisting, cooling periods, and whitelist-only operation. | Compliant | Managed destination addresses and custody policies support tenant-controlled destination approval and withdrawal restrictions. |
| FUN-12 | Apply an independent restriction after bank-reported customer credential or device changes. | Not compliant | FortVault/FortX do not independently manage bank-customer devices. The bank can block the customer or relevant operations through the API. |
| FUN-13 | Apply transaction, daily, and monthly limits by asset and tier and expose usage. | Compliant | Tenant policies enforce operation and period limits using customer, asset, and risk context, with state available to authorized clients. |
| FUN-14 | Estimate network fees and net received amount before confirmation. | Compliant | Custody processing calculates network-specific fee information before final approval and exposes amounts in exact units. |
| FUN-15 | Insufficient operational liquidity must queue withdrawals, provide estimates, and alert treasury. | Compliant | Operations use explicit durable states and controlled retries; liquidity conditions are visible for treasury intervention rather than silently failing. |
| FUN-16 | Every withdrawal must reach a terminal state or escalate after a declared horizon. | Compliant | Durable action and processing states, retry limits, terminal failures, and audit records prevent silent indefinite processing. |
| FUN-17 | Operators can initiate fee replacement for stuck transactions where supported. | Not compliant | Operator-initiated replace-by-fee or equivalent network-specific fee replacement is not currently exposed as a standard capability. |
| FUN-18 | Match fiat deposits by reference and age/escalate unmatched payments. | Partially compliant | A simple fiat payment-processing integration is available, but complete unmatched-payment aging and escalation depend on the bank and payment provider. |
| FUN-19 | Detect and control third-party fiat payers. | Partially compliant | Fiat payment integration is available, while authoritative payer identification and policy enforcement depend on bank/provider data and configuration. |
| FUN-20 | Represent unsettled fiat-channel positions explicitly. | Partially compliant | Basic fiat processing integration is available, but complete channel-settlement accounting is not a native platform capability. |
| FUN-21 | Fiat recalls and chargebacks must affect accounting and compliance cases. | Partially compliant | Provider events can be integrated, but complete native recall, chargeback accounting, and case management are not currently provided. |
| FUN-22 | Route across multiple exchanges with configured primary/backup venues and tested failover. | Compliant | FortX integrates with multiple exchanges, including Binance, MEXC, and Gate.io, and supports tenant-scoped venue selection and fallback. |
| FUN-23 | Use at least two independent price sources and stop quoting on excessive divergence. | Compliant | FortX compares configured market sources and rejects or suspends quotation when freshness or divergence controls fail. |
| FUN-24 | Maintain real-time net positions with limits and automatic suspension. | Compliant | Custody and exchange positions are consolidated by tenant and asset, with controls preventing unauthorized exposure growth. |
| FUN-25 | Reconcile omnibus exchange accounts continuously by execution and at least every five minutes by position. | Compliant | Exchange executions and balance snapshots are synchronized and reconciled against tenant operation state. |
| FUN-26 | Exchange credentials must be trade-only, withdrawal-disabled, restricted, and rotated. | Compliant | Provider credentials are tenant-isolated, stored in approved secret storage, and configured with the minimum available exchange permissions. |
| FUN-27 | Each bank can apply and separately report its own markup. | Compliant | Tenant pricing and markup configuration separates bank economics from platform and provider amounts. |
| FUN-28 | Card authorization must not synchronously depend on exchanges or market-data providers. | Not compliant | FortVault/FortX do not currently provide a card authorization switch. |
| FUN-29 | Card stale-rate behavior must be deterministic and audited. | Not compliant | Card authorization rate policy is outside the current product scope. |
| FUN-30 | Authorization-to-clearing buffers must be configurable and posted separately. | Not compliant | Card clearing accounting is not currently provided. |
| FUN-31 | Support card reversals, refunds, incremental/pre-authorizations, and delayed clearing. | Not compliant | Payment-card lifecycle processing is outside the current platform scope. |
| FUN-32 | Card refunds must remain creditable after original funding is converted or withdrawn. | Not compliant | Card refund allocation is not currently provided. |
| FUN-33 | Banks configure card funding priority through API and applied priority is retained. | Not compliant | Card funding priorities are outside the current platform scope. |
| FUN-34 | Support real-time crypto-funded and prepaid-fiat card models. | Not compliant | Card funding and issuing models are not currently offered. |
| FUN-35 | Card authorization must deploy and scale independently. | Not compliant | No independent card authorization service is currently offered. |
| FUN-36 | Every card authorization decision must be reproducible from retained inputs and rules. | Not compliant | Card authorization decision records are not currently produced. |
| FUN-37 | Card lifecycle controls must take effect at the authorization switch. | Not compliant | Card lifecycle and authorization-switch integration are outside the current product scope. |
| FUN-38 | Blocked yield principal must be separately accounted and unavailable. | Not compliant | FortVault/FortX do not currently provide yield products with locked principal positions. |
| FUN-39 | Yield must accrue daily under a documented, auditable convention. | Not compliant | Yield accrual is outside the current product scope. |
| FUN-40 | Early redemption must apply a disclosed yield-forfeiture rule. | Not compliant | Term-product early redemption is not currently provided. |
| FUN-41 | Renewal must be selectable and cancellable before a cutoff. | Not compliant | Yield-product renewal is outside the current platform scope. |
| FUN-42 | New placements can be suspended without affecting existing positions. | Not compliant | Investment and yield placement management is not currently provided. |
| FUN-43 | Statements must reconcile opening balance, movements, closing balance, and valuation basis. | Compliant | Tenant reports present positions and movements with asset quantities, time boundaries, and the applicable valuation context. |
| FUN-44 | Tax data requires a declared cost-basis method per disposal. | Not compliant | Customer tax calculation and filing data are outside the current product scope; transaction exports support bank-side calculation. |
| FUN-45 | Customer closure must stop activity and settle all positions in a defined sequence. | Partially compliant | Customers, vaults, and services can be disabled or archived, but no complete workflow covers unsupported card, fiat, and yield positions. |
| FUN-46 | Post-closure retention and deletion must follow regulatory obligations. | Compliant | Retention controls preserve transaction and audit evidence while eligible personal data can be deleted or anonymized under applicable policy. |

### TEC - Technical architecture

| ID | Requirement | Status | FortVault/FortX response |
|---|---|---|---|
| TEC-01 | Services must be containerized, stateless where possible, and orchestrated across three availability zones. | Partially compliant | Services are container-ready and separate durable state from application processes, but orchestration across at least three availability zones is not currently demonstrated. |
| TEC-02 | Configuration comes from environment and secret storage; builds are environment-independent. | Compliant | Runtime configuration and secrets are external to build artifacts and supplied through approved environment and cloud secret mechanisms. |
| TEC-03 | The environment must be reproducible from code and manual production changes prohibited and detected. | Partially compliant | Application deployment configuration is versioned, but the complete cloud environment is not yet reproducible exclusively from infrastructure code. |
| TEC-04 | Deployment must be declarative with automatic drift detection. | Partially compliant | Deployment configuration is controlled, but complete automatic infrastructure drift detection is not currently demonstrated. |
| TEC-05 | Inter-service traffic must be mutually authenticated, encrypted, and default-deny. | Compliant | Private networks, TLS, service identity, security groups, and explicit access permissions protect service communication. |
| TEC-06 | Autoscaling must use application signals and be proven under load. | Not compliant | The architecture is scalable, but application-signal autoscaling and the requested load-test evidence are not currently available. |
| TEC-07 | Releases must avoid downtime and automatically roll back on degradation. | Partially compliant | Health-gated deployment supports continuity and rollback, but automatic rollback tied to complete SLI/SLO degradation controls is not currently demonstrated. |
| TEC-08 | Multi-region disaster recovery must be documented and tested annually. | Not compliant | Backups exist, but complete multi-region disaster recovery and annual exercise evidence are not currently available. |
| TEC-09 | A service must never read another service's database. | Compliant | Backend, Custody Processing, Exchange Processing, Listener, and MPC own separate durable state and integrate through APIs or typed events. |
| TEC-10 | Costs must be attributable by bank and capability. | Compliant | Tenant and operation identifiers allow infrastructure and provider usage to be allocated for commercial and unit-economic analysis. |
| TEC-11 | Proprietary cloud dependencies and migration paths must be disclosed. | Compliant | Deployment documentation identifies cloud-managed dependencies, exported data formats, and migration considerations. |
| TEC-12 | State changes and corresponding events must be recorded atomically. | Compliant | Transactional outbox patterns persist business state and publication intent before asynchronous delivery. |
| TEC-13 | Events require at-least-once delivery, partition ordering, and idempotent consumers. | Compliant | Durable outbox processing, Redis Streams, message identifiers, and idempotent handlers support retries and duplicate delivery. |
| TEC-14 | Immutable, tamper-resistant audit records must cover security, value, configuration, and privileged actions. | Partially compliant | Broad audit records exist, but all required events are not yet exported to independently tamper-resistant immutable storage. |
| TEC-15 | Analytics must use a separate event-fed store rather than transactional databases. | Partially compliant | Event-driven reporting projections are supported, but some current reports still use transactional application storage and a fully separate analytical store is not complete. |
| TEC-16 | Personal data must be classified, tenant-key encrypted, retained, and deleted under policy. | Partially compliant | Tenant isolation, encryption, and access controls protect data, but a complete per-bank encryption-key hierarchy and classification evidence are not currently demonstrated. |
| TEC-17 | Every transactional store requires point-in-time recovery with declared and tested objectives. | Partially compliant | Managed database backup and point-in-time recovery capabilities exist, but coverage and tested recovery objectives are not yet demonstrated for every transactional store. |
| TEC-18 | Schema changes must be backward compatible and zero-downtime; destructive changes require approval. | Compliant | Expand-and-contract migrations preserve compatibility; destructive changes require explicit review, backup, and rollback planning. |

### CUS - Custody engineering

| ID | Requirement | Status | FortVault/FortX response |
|---|---|---|---|
| CUS-01 | Every incoming deposit must be attributed to one customer without relying on a sender reference. | Compliant | FortVault assigns customer-specific blockchain addresses and attributes detected transactions using the destination address. |
| CUS-02 | Use dedicated customer addresses wherever supported and memo/tag addresses only where required. | Compliant | FortVault derives dedicated customer addresses. Memo/tag attribution is used only for networks requiring it and is exposed through network metadata. |
| CUS-03 | Wrong-network deposits to an address shared by related networks must be detected, attributed, and recoverable. | Partially compliant | Configured networks are monitored independently. Unsupported or wrong-network recovery requires network-specific operational review. |
| CUS-04 | Address reuse must be defined per network and previously issued addresses monitored indefinitely. | Compliant | Address derivation and reuse are network-specific, while all issued addresses remain associated with the customer and monitored. |
| CUS-05 | Derivation paths, master-key storage, backups, and address recovery must be documented and tested. | Compliant | MPC derivation, root-share protection, recovery packages, and recovery procedures are documented and tested. |
| CUS-06 | Consolidation triggers must be configurable by amount, age, and aggregate balance, with batching where possible. | Partially compliant | Assets can be moved between custody addresses, but the complete requested automatic consolidation engine is not currently provided. |
| CUS-07 | Network fees must be estimated during construction and recalculated before broadcast. | Compliant | Custody Processing obtains network-specific fee information during construction and validates applicable fees before broadcast. |
| CUS-08 | Fee-paying accounts require monitored thresholds and proactive alerts. | Compliant | Operational fee balances can be monitored per network with warning and critical treasury thresholds. |
| CUS-09 | Failed, partial, or stuck consolidation requires a defined recovery process. | Partially compliant | Transaction execution has durable states and retry handling, but consolidation-specific recovery is not complete. |
| CUS-10 | Consolidation cost must be treated as operational expense and reported. | Partially compliant | Network fees are retained with transactions, but dedicated consolidation-cost classification and reporting are incomplete. |
| CUS-11 | Transaction, period, and destination limits must be enforced by the signing layer. | Compliant | MPC independently validates authorization and policy evidence before signing, so application compromise cannot bypass custody policy. |
| CUS-12 | Routine withdrawals below a configurable threshold must operate without human intervention. | Compliant | Partner policies determine approvals, and authorized operations below configured thresholds can proceed automatically. |
| CUS-13 | Transfers above a threshold require multiple people and maker-checker separation. | Compliant | Approval policies and RBAC enforce multiple approvals and prevent one actor from creating and approving the same transfer. |
| CUS-14 | Key generation requires a witnessed ceremony, distributed recovery material, and periodic recovery tests. | Compliant | FortVault has documented key-generation, backup, recovery, witness, and recovery-testing procedures. |
| CUS-15 | Loss of one person, location, or device must not prevent recovery of assets. | Compliant | MPC nodes and recovery material can be distributed, and tested recovery procedures support replacement of failed infrastructure. |
| CUS-16 | The signing environment must be isolated from application networks with separate operator controls. | Compliant | MPC is an independent security boundary with separate storage, credentials, network access, and controlled administration. |
| CUS-17 | Operational, intermediate, and deep-storage thresholds must be technically enforced. | Compliant | Custody classifications and policy-controlled movement allow tenant storage-tier thresholds to be enforced. |
| CUS-18 | Operational storage must be monitored against forecast demand with replenishment before exhaustion. | Partially compliant | Balance monitoring and threshold alerts exist, but complete demand forecasting and automatic replenishment are not currently provided. |
| CUS-19 | The operational-storage share must be reported daily and governed by an approved maximum. | Partially compliant | Custody balances are reportable, but daily ratio reporting and formal maximum-allocation governance require bank-specific procedures. |
| CUS-20 | Customer liabilities must be provable using privacy-preserving Merkle inclusion proofs. | Not compliant | FortVault does not currently generate a Merkle proof-of-liabilities structure. |
| CUS-21 | Controlled assets must be proven and published together with liabilities. | Partially compliant | MPC address-control attestations exist, but a combined published proof of assets and liabilities is not currently provided. |
| CUS-22 | Proof of reserves must run periodically and support independent verification. | Not compliant | A periodic third-party-verifiable proof-of-reserves service is not currently provided. |
| CUS-23 | A bank must obtain proof that its customer liabilities are included in the verified aggregate. | Not compliant | Bank-specific liability inclusion proofs require the currently unavailable Merkle proof-of-liabilities service. |
| CUS-24 | Network metadata must document confirmations, reorganization depth, memo requirements, dust, and settlement time. | Compliant | Network and asset metadata define standards, confirmation policy, memo/tag behavior, minimums, and expected settlement characteristics. |
| CUS-25 | New-network delivery requires a documented process; token addition on an existing network should be configuration. | Compliant | New blockchain families use documented adapter and test processes, while supported-network token additions are configuration-driven. |
| CUS-26 | Every network requires multiple independent RPC sources and stale/divergent-state detection. | Compliant | FortVault will provide multi-RPC support with provider health and stale or divergent-state detection. |
| CUS-27 | Third-party node dependencies and outage effects must be declared in continuity planning. | Compliant | RPC/provider dependencies are documented, monitored, and included in continuity and fallback planning. |

### MTC - Internal matching and trading

| ID | Requirement | Status | FortVault/FortX response |
|---|---|---|---|
| MTC-01 | Internal matching must use deterministic price-time priority and reconstruct from an order journal. | Partially compliant | FortX currently routes to external exchanges. An internal order book can be designed and implemented if required after scope discussion. |
| MTC-02 | Support limit, market, stop, IOC, FOK, post-only, and OCO order types. | Compliant | FortX supports the required trading instructions through configured exchange providers and provider-specific capability mapping. |
| MTC-03 | Tick size, lot size, and minimum notional must be configured and validated per pair. | Compliant | FortX retrieves and applies exchange-specific market constraints before order submission. |
| MTC-04 | Self-trade prevention must operate per customer and, when required, per bank. | Partially compliant | FortX uses venue self-trade prevention where supported, but universal customer- and bank-level enforcement is not guaranteed across every external venue. |
| MTC-05 | Price bands and trading halts must be configurable per pair and published as market state. | Partially compliant | FortX applies platform risk limits and observes venue market state, while exchange-level halts remain venue-controlled. |
| MTC-06 | Pre-trading, continuous, halted, closed, and post-only market states must be explicit events. | Partially compliant | Provider and platform availability are recorded, but there is no complete internal-market state machine without an internal order book. |
| MTC-07 | Pairs must be enabled, suspended, or delisted by configuration without downtime. | Compliant | Exchange pairs and tenant availability are configuration-driven and do not require application redeployment. |
| MTC-08 | Pair and platform throughput and P50/P99 latency must be measured and declared. | Not compliant | The requested pair-level and platform benchmark report is not currently available, and execution latency depends on the exchange. |
| MTC-09 | Capacity must scale automatically during spikes or manual reaction behavior must be declared. | Partially compliant | Services scale horizontally, but complete application-signal autoscaling and load-test evidence are not currently available. |
| MTC-10 | Orders and executions require synchronized UTC timestamps sufficient to reconstruct sequence. | Compliant | FortX retains platform timestamps, provider identifiers, order state, and provider execution timestamps. |
| MTC-11 | Market data must provide snapshots and sequenced increments with gap recovery. | Partially compliant | FortX consumes provider market data; snapshot, delta, and recovery behavior depend on the selected exchange API. |
| MTC-12 | Maker/taker fees must be configurable by bank and pair, separate from spread, and disclosed. | Compliant | Provider fees, platform pricing, and bank markup are represented separately and can be disclosed before confirmation. |
| MTC-13 | Cross-bank internal matching must not advantage any bank by priority, price, or information. | Compliant | FortX currently does not internally match customers across banks; orders are routed to external venues. |
| MTC-14 | Surveillance must cover wash trading, spoofing, layering, ramping, and front-running. | Not compliant | FortX does not currently provide a complete internal-market abuse-surveillance and case-management engine. |
| MTC-15 | Employees and related parties must not trade outside a declared controlled arrangement. | Partially compliant | Production and tenant access are controlled, while a formal employee personal-trading programme is an organizational policy. |

### ADJ - Automated decision governance

| ID | Requirement | Status | FortVault/FortX response |
|---|---|---|---|
| ADJ-01 | No adverse customer decision may be made solely by a model without identified human review. | Compliant | Automated controls can hold an operation, but adverse customer decisions require authorized human review and a recorded reason. |
| ADJ-02 | Model inputs, version, and output must be retained with the decision. | Partially compliant | Provider results and policy decisions are audited, while complete model-version and input evidence depends on the external provider. |
| ADJ-03 | Models require purpose, training provenance, validation, drift monitoring, and periodic review. | Partially compliant | FortVault does not train a proprietary customer-risk model; governance evidence for external models must come from the provider. |
| ADJ-04 | One bank's data cannot train a model serving another bank without written consent. | Compliant | Tenant data is isolated and is not used by FortVault to train cross-bank models. |
| ADJ-05 | Model reporting must include quality measures such as false-positive rates. | Not compliant | FortVault does not currently produce model-performance or false-positive reports for third-party compliance models. |

## 6. Principal limitations and discussion points

The following items remain outside the current platform capability or require material additional work:

1. Card issuing, authorization, clearing, card disputes, and card lifecycle operations.
2. Fiat payment processing has a basic integration; complete reconciliation, payer controls, settlement accounting, recalls, and chargeback case management require additional integration.
3. Yield, term-deposit, and investment-placement products.
4. Customer tax cost-basis calculation and jurisdiction-specific regulatory filing packages.
5. Formal accounting-ledger holds and independent cryptographic tamper evidence for all internal ledger data.
6. Arbitrary event-range replay and the complete requested multi-language SDK catalogue.
7. Formal SLI/SLO error-budget governance, an external status page, complete distributed tracing, uniform CI coverage thresholds, multi-region disaster-recovery exercises, and application-signal autoscaling evidence.
8. Custody insurance and explicit cross-bank penetration-test evidence.
9. Commercial and legal terms concerning SLA remedies, source-code escrow, transition, intellectual property, subprocessors, and audit rights.
10. Full automatic custody consolidation, liquidity-demand forecasting, and daily storage-allocation governance.
11. Merkle proof of liabilities, periodic independently verifiable proof of reserves, and bank-specific liability inclusion proofs.
12. A native internal order book, matching-engine benchmarks, and internal-market abuse surveillance. Internal matching can be considered as a separately scoped implementation.
13. Complete model-version evidence, model-governance evidence, and false-positive reporting for third-party automated risk models.
14. Demonstrated three-availability-zone orchestration, a fully separate analytics store, and tested point-in-time recovery objectives for every transactional store.
15. A complete tenant exit-export package and an append-only accounting correction, hold, expiry, and reversal lifecycle.
16. Automatic rotation for every secret type, universal short-lived workload identities, and a demonstrated per-bank encryption-key hierarchy.
17. Universal destination-wallet proof, compliance monitoring for unsupported card/yield products, and card-specific abuse controls.
18. Universal self-trade prevention across external venues and automatic release rollback driven by complete SLI/SLO controls.

## 7. Evidence to accompany the response

Where requested during due diligence, the response can be supported by the following controlled evidence:

1. FortVault and FortX architecture and data-flow diagrams.
2. API contracts and representative integration documentation.
3. Tenant isolation, RBAC, approval, audit, and MPC architecture documentation.
4. GT source-code audit and penetration-testing reports or confirmation letters.
5. ISO 27001 implementation status and available policies.
6. Cloud architecture, secret-management, database-backup, and restore documentation.
7. Test summaries, health-check documentation, and representative CI evidence.
8. MPC key-generation ceremony, backup, node-replacement, recovery, and recovery-test documentation.
9. Supported network metadata, RPC/provider inventory, and multi-RPC continuity design.
10. Exchange integration, permission model, market constraints, fee treatment, and reconciliation documentation.
11. Chainalysis integration documentation and available third-party compliance/model-governance evidence.
12. Availability architecture, distributed-tracing coverage, CI coverage thresholds, status-page design, analytics-store topology, and transactional-store recovery-test evidence.
13. Secret-rotation inventory, workload-identity lifecycle, per-bank encryption-key design, and release rollback evidence.
14. Exit-export samples, accounting reversal/hold procedures, destination-wallet proof design, and venue self-trade-prevention capability mapping.
