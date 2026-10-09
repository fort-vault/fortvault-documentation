# FortVault Custody

## Product and Technical Overview

**Custody, treasury automation, and connected-exchange execution for digital asset businesses**

| Document Control | Value |
| --- | --- |
| Document version | 1.0 - Partner overview |
| Date | 29 September 2026 |
| Intended audience | Prospective partners and their business, technology, security, and operations teams |
| Distribution | Confidential - prospective partner use |
| Companion document | [Partner API Integration Guide](../integrations/FORTVAULT_PARTNER_API_INTEGRATION_GUIDE.md) |

This overview presents FortVault's custody capabilities, technical architecture, integration approach, and proposed automation and swap services. It supports evaluation of the product alongside the commercial offer. The agreed release, deployment, delivery milestones, and service commitments are defined in the partner's delivery schedule.

**Capability availability:** *Current capabilities* are implemented functionality, subject to the selected release, configuration, and deployment acceptance. *Proposed delivery scope* identifies additional functionality requiring implementation and acceptance under the agreed project. *Roadmap candidates* are possible extensions without committed delivery dates. Proposed capabilities and roadmap items are not represented as currently available services.

## 1. Executive Overview

FortVault provides the custody and asset-operation layer that digital asset businesses need to manage blockchain funds, govern their movement, and integrate custody into their own products. It combines a workspace-based administration model, policy-controlled actions, distributed signing, blockchain monitoring, and operational reporting.

FortVault is an independent product. It can be used through its dashboard, integrated through the Partner API, or operated in both ways. fortX Exchange is a consuming application: it can use FortVault for custody and, under the proposed extension, connected-exchange swaps. Other exchanges, financial platforms, and treasury applications can integrate without using fortX.

The product has three complementary capability areas:

- **Custody operations:** manage customer and treasury vaults, generate addresses, observe deposits, authorize transfers, and maintain transaction and fee history.
- **Treasury automation:** configure independent rules to consolidate deposits and replenish network-fee balances, while retaining the applicable authorization and signing controls.
- **Exchange connectivity and execution:** connect multiple exchange accounts and, under the proposed swap scope, execute a conversion on the single eligible account offering the best executable quote.

The business objective is to provide one controlled operational interface while keeping distinct the authority to request an operation, approve it, sign it, and observe its outcome.

## 2. Operating Model and Product Boundaries

### 2.1 Workspaces and Standalone Use

A workspace is the tenant boundary for a partner's custody configuration, users, API clients, customers, vaults, and exchange-account records. A customer record within a workspace is not itself a separate workspace.

An organization can use one workspace for fortX-connected activity and a separate workspace for standalone custody or another integration. Each integration authenticates to its own workspace; this does not create shared balances, cross-workspace permissions, or automatic transfers between them.

Logical workspace separation and infrastructure isolation are different controls. Backend access is tenant-scoped. The signing deployment model calls for one multi-party computation (MPC) cluster per partner context, with its policy configuration selected at deployment. The partner's deployment design identifies shared or dedicated application infrastructure and maps each workspace to its signing environment.

### 2.2 fortX and Other Integrating Applications

| Responsibility | FortVault | fortX or Other Partner Application |
| --- | --- | --- |
| Customer-facing product | Custody administration and operational views | End-customer experience, product rules, and commercial relationship |
| Blockchain custody | Vaults, addresses, authorized transfers, signing coordination, and custody records | Requests custody operations and consumes their results |
| Customer accounting | Provides custody balances, movement records, fees, and execution evidence | Owns customer liabilities, trading balances, reservations, and credit/debit rules |
| Exchange execution | Connects exchange accounts; proposed quote selection and single-venue swap execution | Requests conversions and decides how results affect its customer ledger |
| Trading venue functions | Does not provide an internal order book or matching engine as part of this scope | Owns any order book, matching, trading product, or execution policy offered to customers |
| Compliance decisions | Provides integration points and operational controls for agreed screening workflows | Owns customer acceptance, compliance decisions, investigations, and applicable obligations |
| Reconciliation | Supplies custody and exchange-operation facts | Reconciles those facts against its business ledger and resolves accounting differences |

A blockchain deposit, a successful sweep, an exchange trade, and a customer account credit are different events. FortVault does not equate them. Moving funds from a customer deposit vault to a treasury vault must not create a second customer deposit credit in the partner application.

### 2.3 Custody and Exchange-Held Funds

Funds at FortVault-controlled blockchain addresses are managed through the custody signing architecture. Funds credited to a connected centralized exchange account are held under that exchange's custody and operating rules.

Using MPC to authenticate an exchange API request protects FortVault's signing credential; it does not place the exchange's wallets under FortVault MPC or remove exchange counterparty, suspension, liquidity, or insolvency risk.

## 3. Custody Capabilities

### 3.1 Vaults, Customers, and Addresses

Current custody capabilities include customer records, regular treasury vaults, configurable vault types, asset-address associations, address generation, and asset and vault lifecycle actions. Address generation is an authorized action rather than an unrestricted key-generation API.

Vault types such as hot and cold express operational classification and policy selection. A type named `cold` does not by itself prove that its signing keys are offline. Actual signing mode, participant availability, and infrastructure determine that property. Offline-device signing remains a separately qualified development capability, not an automatic consequence of the vault label.

An asset is identified by its currency and network, with a token contract where applicable. Shared address formats do not make networks interchangeable. Native assets and tokens on the same supported network may use the same blockchain address while retaining separate asset balances and movement records.

### 3.2 Transfers and Approvals

Transfers pass through business validation, applicable permissions and policy, action signing, required approvals, execution, and subsequent observation. Approval of an action is not proof that a transaction has been broadcast or completed.

Policy can distinguish action types, wallet types, asset types, amount ranges, operational roles, and approval requirements. Depending on the configured policy, an action may require one or more approvals, including role-specific or staged requirements.

Whitelisted destinations are organized into global, internal, and customer-specific scopes. Transfer eligibility is checked server-side against the source context, destination scope, resource state, and asset/network. A visible destination is not an unconditional authorization to send to it.

### 3.3 Monitoring, History, and Reports

Blockchain observations are normalized into transaction and movement records. One blockchain transaction can contain several asset movements, so transaction identity and movement identity are distinct.

Operational views cover actions, transactions, deposits, withdrawals, transaction volume, and network fees. Reporting distinguishes an unsuccessful transfer from any network fee it consumed. A failed execution must not be represented as a successful asset movement simply to account for its fee.

Native network fees and network resources are also distinct. For example, Tron energy or bandwidth consumption is not itself a paid TRX amount. Unknown fee data must remain distinguishable from a verified zero fee. USD equivalents are indicative valuations, not executable exchange quotes.

Controlled recovery procedures can reconstruct supported missing historical transactions from blockchain remote procedure call (RPC) evidence, subject to eligibility checks. Automatic historical backfill, blockchain reorganization compensation, and gap-free provider migration are not included as general guarantees.

## 4. Treasury Automation

**Status: proposed delivery scope.** The main purpose of automation is to consolidate deposited assets and supply the network resources required to move them. Automation is a collection of user-configured rules, not one hard-coded workspace behavior.

### 4.1 Automation Objects

The proposed automation model supports multiple independent rules within a workspace, with the following configuration:

| Configuration | Meaning |
| --- | --- |
| Name, owner, and state | An identifiable rule with controlled draft, enabled, and paused states |
| Source selector | A specific vault, selected vaults, or a supported vault type/category within the workspace |
| Asset and network | The exact assets and networks eligible for evaluation |
| Trigger and condition | An eligible deposit, scheduled evaluation, balance threshold, or insufficient network-fee resources |
| Action and amount | Consolidate transferable funds, move excess above a reserve, or refill a defined native-asset target |
| Destination or funding source | An explicitly configured, authorized vault or approved destination |
| Limits | Minimum useful amount, fee ceiling, per-run limit, aggregate spending limit, and cooldown |
| Authorization | The policy and approval requirements under which the generated action may execute |
| Execution record | Evaluation reason, rule version, related action, transaction identity, outcome, and retry history |

Vault-type selection is intended to evaluate each eligible vault independently, not add all balances into one threshold. A dynamic selector can include newly eligible vaults; its scope and exclusions must be clear when the rule is approved. Archived, disabled, restricted, or otherwise ineligible sources must not enter automation merely because their type matches.

### 4.2 Deposit Consolidation

Deposit sweeping moves funds from deposit vaults to a designated treasury vault. The destination may be a hot vault for operational liquidity or a configured cold vault for storage.

Illustrative rule: evaluate customer deposit vaults holding USDT on Ethereum; when an individual vault has an eligible transferable balance above 1,000 USDT, sweep that balance to the designated treasury vault, subject to fee and authorization limits.

The threshold is not the transfer amount. At 1,250 USDT, a rule configured to retain 1,000 transfers only 250, while a full-sweep rule attempts to move the eligible transferable balance. The chosen behavior must be explicit. The threshold and amount in this example are illustrative, not product defaults.

The proposed workflow is:

1. Observe a deposit and establish eligibility under the configured confirmation, availability, and compliance rules.
2. Re-evaluate the source balance, pending activity, destination, and expected execution cost.
3. If resources are sufficient, create the normal transfer action under the automation's authorized policy context.
4. If resources are insufficient, wait for an eligible gas-refill automation or raise an operational exception.
5. Execute only after the applicable authorization conditions are satisfied.
6. Record the outcome and reconcile the movement without generating a duplicate deposit credit.

Deposit finality and compliance gates form part of automation delivery and acceptance. Blockchain event ingestion alone does not establish eligibility for an automatic sweep.

### 4.3 Gas Refill as a Separate Automation

Gas refill is a separate rule that can be reused by several consolidation rules. For example, a vault holding eligible USDT or USDC may receive native currency from a designated gas vault when its network-fee balance is below the level required for a pending sweep.

Token presence alone is insufficient. A tiny or unsolicited token balance must not cause repeated funding. The rule should consider eligible token value, expected operation, current native balance, pending refill, refill target, fee conditions, and spending limits.

Refill configuration is network-specific: Ethereum token transfers need ETH; Avalanche C-Chain token transfers need AVAX; Tron transfers require appropriate TRX or available network resources. Bitcoin uses fees within its UTXO transaction flow rather than ERC-20-style gas refill.

The destination of a refill is the eligible source vault on that same network. The automation must not turn into an unrestricted payment mechanism. Funding and consolidation rules must coordinate so that multiple evaluations do not fund or spend the same balance twice.

### 4.4 Governance and Failure Handling

Automation initiates work; it does not replace authorization. Unattended execution requires an explicitly approved automation identity or policy mechanism that remains verifiable at the applicable execution and signing boundaries. It must not be implemented by silently bypassing approvals.

The delivery design must address duplicate triggers, concurrent withdrawals, balance reservations, rule changes, funding limits, uncertain broadcasts, and transfer loops. A timeout is not evidence that a transfer failed safely. An unresolved operation must be reconciled before a replacement is permitted.

Receiving funds into an offline-controlled destination does not require that destination to sign. Spending from it may require an offline ceremony and human participation. Automation must not silently switch to online signing to complete such an operation.

## 5. Exchange Connectivity and Unified Swaps

### 5.1 Connected Accounts

Current exchange connectivity supports Binance, Gate.io, and MEXC for account connection checks, balance synchronization, provider-dependent permission information, and supported deposit-address/network discovery. A workspace can manage multiple exchange-account records.

Permission visibility differs by provider. A connection test or balance read does not prove permission to trade or withdraw. Trading eligibility must be evaluated for the intended operation.

Exchange credentials are referenced through controlled secret storage rather than embedded in business messages. Binance supports MPC-backed Ed25519 authentication as well as shared-secret HMAC authentication. Gate.io and MEXC currently use HMAC, not MPC signing.

### 5.2 Single-Exchange Swap Model

**Status: proposed delivery scope.** fortX or another partner will submit a conversion request through one FortVault interface. FortVault will compare quotes across eligible connected accounts and execute on **one exchange account** selected for that request.

For an exact-input conversion, the selection objective is the highest executable net output for the requested amount, considering available market depth, known trading fees, balance, pair availability, and account restrictions. Quote freshness and execution limits must be included. An indicative ticker price is not an executable quote.

The initial scope assumes that the selected exchange account already holds sufficient funds. It does not split an order across exchanges, aggregate account balances, move funds between exchanges to chase a quote, bridge assets between networks, or guarantee the best price outside the eligible connected accounts.

For example, if a workspace has Binance, Gate.io, and MEXC accounts, FortVault may choose Gate.io for one request and Binance for another. Each accepted request executes only on its selected account. Different fills within that exchange do not constitute multi-exchange routing.

### 5.3 Proposed Quote and Execution Lifecycle

1. Validate the request, workspace, eligible accounts, input asset, output asset, and amount.
2. Obtain comparable, sufficiently fresh quotes and exclude accounts without the required funds or permissions.
3. Present or bind the selected quote, account, expected output, fees, expiry, and permitted price deviation.
4. Apply the required business policy and approval flow to the executable operation.
5. Execute through the selected provider using the appropriate credential/signing mechanism.
6. Track acceptance, fills, fees, and final or unresolved outcome; reconcile the provider result before reporting completion.

If a quote expires or the price moves beyond the authorized limit, the operation must require revalidation rather than silently broadening the user's consent. An ambiguous response must be reconciled on the original account before retrying or selecting another venue. Partial execution must be reported as such; it is not automatically a full successful swap.

Quote validity, supported order types, fee treatment, partial-fill behavior, and cancellation rules will be defined in the agreed swap specification and corresponding API documentation before release.

### 5.4 MPC and Policy-Based Exchange Execution

FortVault's design brings exchange connectivity into the same governed operational environment as custody. For compatible exchanges such as Binance, threshold Ed25519 signing can keep the API-signing private key distributed across MPC participants instead of storing a complete private key in the execution service.

**Key protection and operation authorization remain separate.** MPC-backed exchange authentication is an existing capability; independently policy-authorized swap execution is part of the proposed delivery scope. That delivery requires authorization to be bound to the workspace, exchange account, operation, assets, amount, execution limits, expiry, and exact provider request.

For HMAC integrations, the execution service uses a protected exchange secret. The proposed policy-controlled workflow can apply to these integrations, but their credential-protection model remains different from MPC signing.

## 6. Technical Architecture

### 6.1 Component Responsibilities

| Component | Responsibility |
| --- | --- |
| Dashboard and Partner API | Human and application interfaces for authorized operations and read access |
| Backend | Workspace business state, customers, vaults, assets, actions, approvals, exchange-account metadata, and API authorization |
| Custody Processing | Address derivation orchestration, transaction construction, execution state, MPC coordination, and blockchain broadcast |
| Exchange Processing | Exchange credential resolution, provider calls, exchange-operation state, retries, and exchange MPC coordination |
| MPC | Distributed key generation and signing, signing-session state, custody transaction validation, and configured authorization verification |
| Contracts | Registry, policy evaluation, and address-attestation verification |
| Listener | Provider ingestion, chain-specific observation and normalization, tracking state, and supported transaction recovery |
| Messaging | Typed asynchronous service communication through Redis Streams |
| Notifications | Delivery of configured operational notifications; not a business-state authority |
| Proposed automation services | Rule evaluation and coordinated initiation of permitted custody operations |

Backend, Custody Processing, Exchange Processing, Listener, and MPC own their respective durable state. They communicate through defined APIs or messages rather than reading one another's databases. Redis is transport, not the durable business ledger.

### 6.2 Custody Execution Flow

The application creates an action. Backend validates the request against trusted records, verifies the required signatures and policy, and records approval state. Custody Processing receives the authorized work, validates execution context, and constructs the network-specific transaction. MPC performs the relevant transaction and enabled authorization checks before participating in signing. Custody Processing broadcasts the signed transaction; subsequent execution and chain observations update operational records.

These stages are asynchronous. Request acceptance, action approval, broadcast, and confirmed outcome are not interchangeable statuses. Integration logic must track them separately.

### 6.3 Trust Boundaries

The intended signing boundary treats upstream applications, Backend, Processing, messaging, and provider input as potentially compromised. A caller's assertion that an action is approved is not sufficient evidence for a signature. The signing design requires verification against the actual transaction and applicable authorization evidence.

Custody signing includes transaction-fact, signature, and configurable policy verification. The required controls must be enabled and validated for the selected release and deployment. Security assurance, including replay and signing-session controls, is assessed against that configuration and its supporting evidence rather than inferred from a high-level architecture description.

Exchange MPC signing is a separate path from custody ECDSA signing. Its existing key and payload binding must not be confused with the proposed business-policy binding for swaps.

## 7. Smart Contracts and MPC

### 7.1 Registry and Policy Contracts

FortVault's contracts form a policy and verification layer. They are not smart-contract wallets holding all customer funds, and ordinary Bitcoin, Tron, or EVM asset transfers are not all executed by these contracts.

| Contract | Function |
| --- | --- |
| `FortVaultRegistry` | Defines recognized actions, wallet types, asset types, business roles, and role assignments |
| `FortVaultPolicyEngineV2` | Evaluates configured processing and approval policies, including amount segments and role/stage requirements |
| `FortVaultAddressVerifier` | Verifies trusted attestations over a derived public key and wallet context, then checks the supplied blockchain address against that public key |

The deployment specification identifies the policy-engine version and compatible service versions. Upgrades from an earlier policy engine require a separately validated migration plan.

Policy evaluation is consumed by off-chain services. Contract availability, privileged administration, role assignments, and policy configuration are therefore operational security dependencies. Contract administration must be controlled independently of routine application use.

### 7.2 Address Verification

Address attestations bind a public key, wallet type, and issuance timestamp to trusted attestation signers. The verifier supports the implemented EVM, Tron Base58, and Bitcoin mainnet P2WPKH address checks.

The current verifier requires valid signatures from all configured trusted attestation signers. This requirement is separate from the quorum used for MPC transaction signing. Attestation keys are also separate from custody key shares.

A valid proof shows that the configured signer set attested the public key and context and that the address matches. It is not proof of reserves, a statement of customer liabilities, authorization for a future transfer, or a guarantee that all MPC participants are currently available. Proof distribution through a partner interface must be part of the agreed integration scope; the existence of the verifier does not imply that every Partner API response contains a proof.

### 7.3 Distributed Signing

MPC distributes signing material across participants. The online signing model does not require a complete private key to be assembled in Backend or the execution services. The configured participant quorum collaborates to generate signatures.

Custody ECDSA keys, exchange Ed25519 keys, attestation keys, and operator approval keys serve different purposes and must not be treated as interchangeable credentials. Operational security depends on the protection of participant infrastructure, share storage, identity material, and administrative access, as well as the cryptographic protocol.

Offline-device signing and bootstrap workflows remain development prototypes and are excluded from the production offering unless separately qualified and explicitly contracted. Recovery arrangements require controlled procedures and deployment-specific tests; ordinary database backups do not establish signing recovery capability.

### 7.4 Access, Approval, and Audit Controls

Human users, API clients, automation identities, exchange credentials, and MPC participants have different responsibilities. The deployment should apply least privilege to each identity and separate routine initiation, approval, policy administration, and signing-infrastructure administration. API scope alone does not grant the signing user's business permission.

Sensitive actions must be attributable to their initiator and applicable approvers, with the requested operation and resulting execution linked in the operational history. Request IDs, action IDs, movement IDs, and provider operation IDs serve different correlation purposes; they are not interchangeable evidence of completion.

Credential revocation, policy changes, and automation pauses require explicit effects on pending work. The proposed extensions must define these effects before release rather than allowing a previously queued task to bypass changed authorization. Audit records should retain the necessary decisions and identifiers without exposing private keys, shares, secrets, or unnecessary customer data. Tamper-evident or immutable audit storage is a separate deployment requirement, not implied by the existence of application history.

## 8. Partner API and Integration Package

The Partner API exposes workspace-scoped custody operations under `/partner-api/v1`. Current capabilities cover customer and vault creation/read access, supported catalogs, addresses, balances, transaction movements, whitelisted-address operations, and supported action initiation and review.

API-client authentication and business-action authorization are separate. A scoped, signed JWT authenticates the client. Mutating action flows additionally use the required action signature and user authorization. Canonical typed-data preparation allows a client to obtain the server-resolved payload before signing.

The integration model includes request replay protection, documented idempotency for writes, resource-specific scopes, structured errors, and `X-Request-Id` correlation. Applications must preserve the documented signed payload and distinguish an idempotent response replay from a new execution request.

List ordering is endpoint-specific. It must not be assumed to use a common date field. Offset pagination is deterministic for a fixed dataset, not a lossless synchronization feed under concurrent writes. A lossless incremental transaction feed is not part of the current public API contract.

The companion [Partner API Integration Guide](../integrations/FORTVAULT_PARTNER_API_INTEGRATION_GUIDE.md) provides the detailed technical reference for authentication, scopes, endpoints, typed data, approvals, idempotency, pagination, amounts, errors, retries, and integration checks. The integration package comprises this guide and the Partner OpenAPI specification matching the agreed backend release. Automation and unified-swap APIs require an explicit extension to that contract before delivery.

The delivery schedule identifies the applicable guide and OpenAPI versions. Interactive Swagger documentation may be provided alongside them; the agreed versioned specification governs the integration. Dashboard functionality, including operational reports, is available through the Partner API only where explicitly documented.

## 9. Supported Assets and Network Roadmap

### 9.1 Current Asset and Network Coverage

The following matrix describes the currently implemented asset and network combinations. Availability in a partner workspace depends on enablement, network/provider configuration, policy, and release acceptance. The delivery schedule specifies the combinations included for that partner.

| Network | Currency / Asset | Form | Custody Scope |
| --- | --- | --- | --- |
| Bitcoin mainnet | BTC | Native Bitcoin | Supported native-address and UTXO transfer path; specific transaction-shape restrictions apply |
| Ethereum mainnet | ETH | Native asset | Address generation, observation, and native transfers |
| Ethereum mainnet | USDT, USDC | Configured ERC-20 contracts | Token balances, observation, and transfers |
| Avalanche C-Chain mainnet | AVAX | Native asset | Address generation, observation, and native transfers |
| Avalanche C-Chain mainnet | USDT, USDC | Configured ERC-20 contracts | Token balances, observation, and transfers |
| Tron mainnet | TRX | Native asset | Address generation, observation, and native transfers |
| Tron mainnet | USDT | Configured TRC-20 contract | Token balances, observation, and transfers |

Currency symbols alone do not identify a supported asset. Network, token contract, decimals, fee handling, and provider coverage must match. USDC on Tron is not included in current coverage. Development/test networks are separate environments and do not expand production support.

### 9.2 Roadmap Candidates

The following are candidates for prioritization, not committed support or dates:

| Candidate | Scope to Evaluate | Release Conditions |
| --- | --- | --- |
| SOL on Solana | Native SOL custody, followed by specifically approved SPL tokens | Complete address, signing, validation, ingestion, fee, recovery, and operational integration |
| Additional EVM networks | Selected native assets and approved stablecoins; possible priorities include Base, Arbitrum, and Polygon PoS | Chain-specific validation, token mapping, RPC/provider coverage, fee behavior, policy, and acceptance tests |
| Additional tokens on existing networks | Partner-requested ERC-20 or TRC-20 assets | Reviewed token behavior, exact precision, allowlists, pricing coverage, and compliance/provider support |
| Additional network families | Partner-prioritized currencies requiring new execution/signing behavior | Separate feasibility, security, implementation, and commercial approval |

Solana custody is a roadmap candidate, not a current supported network. Similarly, EVM compatibility does not automatically qualify every EVM network or token.

Exchange trading coverage is separate from blockchain custody coverage. A venue listing a currency does not mean FortVault can custody it, and custody support does not guarantee an executable pair on every connected exchange.

## 10. Third-Party Services and Infrastructure

### 10.1 Provider Inventory

| Service | Purpose | Availability | Data and Dependency Considerations |
| --- | --- | --- | --- |
| QuickNode | Blockchain RPC and event ingestion through configured webhooks/streams | Current listener integration | Address subscriptions, chain queries, transaction identifiers, and network observations; provider limits and delivery behavior apply |
| Tatum | Potential additional blockchain RPC/data provider | Optional provider candidate; integration qualification required before inclusion | RPC requests and public chain data; adapter coverage and failover behavior require qualification |
| Sumsub | Transaction-monitoring workflow and configured crypto-risk screening | Optional proposed KYT integration | Required wallet, transaction, and potentially customer-context data; coverage and selected analytics integration must be agreed |
| Chainalysis | Blockchain transaction/address risk intelligence | Optional proposed KYT integration, directly or through an agreed integration | Required addresses, transactions, and risk context; licensed coverage, alert handling, and data responsibilities apply |
| Binance, Gate.io, MEXC | Connected exchange accounts and proposed swap execution | Current account connectivity; swap execution proposed | Account identifiers, authenticated requests, balances, and operation data; venue permissions, liquidity, limits, and availability apply |
| CoinGecko | Indicative USD asset valuations | Current backend price integration | Asset identifiers and price requests; cached valuations are not trade execution prices |
| AWS | Potential hosting and secret-management services | Existing secret-management integrations; hosting configuration is project-specific | Infrastructure metadata and explicitly configured secrets; account ownership, region, and access policies must be agreed |
| Google Cloud | Potential hosting and selected secret-management services | MPC secret-provider support exists; full-platform deployment qualification is separate | Hosting and secret access depend on the chosen topology; not an automatic substitute for all AWS integrations |

QuickNode and Tatum provide blockchain infrastructure services with different integration and operating characteristics. Provider selection does not imply interchangeable adapters or automatic failover. See [QuickNode APIs](https://www.quicknode.com/docs/build-with-ai/quicknode-apis) and [Tatum documentation](https://docs.tatum.io/).

Sumsub can integrate external blockchain analytics providers, including Chainalysis under an appropriate arrangement. The partner may select a direct or combined integration according to coverage, workflow, and licensing needs. See [Sumsub crypto-monitoring providers](https://docs.sumsub.com/docs/providers) and [Chainalysis KYT](https://www.chainalysis.com/product/kyt/).

### 10.2 KYT and Decision Ownership

Know Your Transaction (KYT) screening supplies risk evidence; it does not itself determine the partner's legal obligations or guarantee that a transaction is safe. Before enabling automated movement, the delivery design must specify screening stages, risk thresholds, holds, manual review, rescreening, and behavior when a provider is unavailable or coverage is missing.

Sumsub and Chainalysis enforcement workflows are proposed integrations, not current custody capabilities. Selection of a provider does not constitute compliance certification or regulatory approval.

### 10.3 Account Ownership and Commercial Responsibility

The commercial and deployment schedules define provider account ownership, credential administration, regions, data-processing arrangements, usage monitoring, and payment responsibility. Hosting, blockchain fees, exchange fees, analytics subscriptions, market data, and provider quotas are included only where expressly stated; otherwise their treatment requires agreement.

No API secrets, MPC shares, or private signing keys should be included in the integration guide or business messages. HMAC credentials require protected execution-service access; MPC-backed exchange credentials use a different secret boundary. Public blockchain data can still reveal business activity and warrants data-minimization controls.

## 11. Deployment and Operations

A FortVault-managed deployment or customer-controlled environment may be evaluated according to the partner's requirements. The agreed offer identifies the selected model, its qualification requirements, and the division of operating responsibilities. Production, development, and test environments require separated state, credentials, provider subscriptions, and signing material.

Operational responsibilities must cover:

- Application and database health, queues, execution retries, and unresolved operations.
- MPC participant availability, approved configuration, key/share protection, and access management.
- Policy-contract availability, administration, and compatibility with deployed services.
- Provider quotas, authentication, subscription health, exchange permissions, and credential rotation.
- Ingestion delays, missing evidence, balance reconciliation, and controlled recovery.
- Automation spending limits, gas-vault reserves, failed sweeps, and paused rules once delivered.
- Backup retention, restoration tests, signing recovery procedures, and incident escalation.

Provider acknowledgment is not proof of application completion. An observed transaction is not automatically irreversible finality. Restart, migration, and recovery procedures must distinguish provider delivery, durable ingestion, backend processing, and partner accounting.

Availability targets, support hours, recovery objectives, throughput, latency, and retention periods must be agreed against the selected deployment and tested workload. No unlimited address capacity, fixed execution time, gap-free ingestion guarantee, or unconditional recovery SLA is asserted here.

## 12. Delivery Scope and Acceptance

### 12.1 Scope Summary

| Capability | Classification |
| --- | --- |
| Workspace-scoped custody, action workflows, addresses, supported transfers, and operational history | Current capabilities; deployment qualification required |
| Partner API and detailed integration guide | Current capabilities for documented endpoints |
| Policy contracts, address verifier, and custody MPC verification | Current capabilities; compatible configuration and release-specific security verification required |
| Binance/Gate.io/MEXC account connectivity and synchronization | Current capabilities for the implemented connection and synchronization operations |
| Binance MPC-backed exchange authentication | Current capability; independently policy-authorized swap execution is proposed scope |
| Configurable consolidation and gas-refill automations | Proposed delivery scope |
| Best eligible quote selection and execution on one exchange account | Proposed delivery scope |
| Swap-specific authorization binding and corresponding API extensions | Required part of proposed swap delivery |
| Sumsub/Chainalysis KYT workflows and Tatum integration qualification | Optional proposed scope, subject to provider and commercial decisions |
| Additional networks and currencies | Roadmap candidates |
| Offline-device signing and bootstrap workflows | Development prototypes; excluded from production claims without separate qualification |

The initial swap scope excludes cross-exchange order splitting, automatic cross-exchange funding, bridge execution, derivatives/margin trading, and guaranteed market-wide best execution. Token issuance, a partner accounting ledger, proof of liabilities, and a lossless incremental transaction feed are not implied by this custody-and-swap offer.

### 12.2 Acceptance Principles

Delivery acceptance should demonstrate the selected asset/network flows, tenant and resource authorization, exact action-to-execution binding, relevant MPC verification, duplicate/retry behavior, failure handling, and reconciliation. Signed-payload changes, unauthorized actions, stale/expired requests, and unavailable dependencies must be exercised rather than verified through successful cases alone.

Automation acceptance must include insufficient gas, repeated triggers, conflicting rules, concurrent spending, paused/archived sources, refill caps, and uncertain execution. Swap acceptance must include stale quotes, insufficient account balance, fee-aware selection, permission denial, partial fills, and accepted-but-timed-out provider requests without duplicate orders.

These are delivery acceptance requirements, not a statement that the proposed capabilities already pass those tests. Security assessment, any audit or certification statements, and production readiness require their own dated evidence.

### 12.3 Partner Delivery Agreement

The partner delivery agreement defines:

- Hosting model, workspace-to-MPC mapping, and infrastructure and credential ownership.
- Product release, supported asset/network combinations, and versioned integration documentation.
- Included automation rules, authorization model, confirmation and compliance gates, and operating limits.
- Swap quote and execution contract, fees, expiry, partial-fill behavior, and eligible providers/accounts.
- KYT configuration, data-sharing responsibilities, and third-party subscription costs.
- Delivery milestones, security qualification, support commitments, recovery objectives, and performance acceptance criteria.

This provides a defined operational and commercial foundation for independent custody, controlled treasury automation, and single-exchange swap execution through FortVault.
