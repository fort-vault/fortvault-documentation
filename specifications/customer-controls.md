# FortX Connect Customer Eligibility and Controls

Status: Proposed functionality. Not a statement of current implementation.

Document version: `0.1`

Last reviewed: 2026-09-29

## 1. Purpose

This document describes customer account states, verification, policies,
permissions, limits, and holds for FortX Connect. It supplements the proposed
[Frontend API Integration Guide](../integrations/FORTX_CONNECT_API_INTEGRATION_GUIDE.md)
and the [FortX Connect product description](../products/fortx-connect.md).

The initial scope is individual customers and crypto operations. Corporate
verification, fiat payment controls, and administrative API schemas are outside
this document. States and workflows below require implementation and acceptance
before they can be represented as available functionality.

## 2. Functionality Overview

| Functionality | Examples | Ownership and configuration |
| --- | --- | --- |
| Account status | `active`, `restricted`, `disabled` | Predefined lifecycle states with authorized transitions |
| KYC status | `not_started`, `in_progress`, `pending_review`, `action_required`, `approved`, `rejected` | Verification results and authorized review |
| Verification validity | Expired documents; reverification required | Configured requirements evaluated by the backend |
| Customer risk classification | `unknown`, `low`, `medium`, `high` | Screening and authorized review |
| Assigned policy | Standard, Higher Limits, Trading Only | Reusable workspace profiles configured by authorized administrators |
| Operation permissions | Trade, withdraw, obtain deposit instructions, automatically credit deposits | Policy rules combined with individual restrictions |
| Amount limits | Per-withdrawal, rolling-24-hour, asset-specific limits | System ceilings, policy limits, and stricter individual limits |
| Individual holds | Withdrawal hold, trading hold, financial-operation hold | Authorized operators or automated controls |
| Asset/network restrictions | An asset or network cannot be used for a particular operation | Customer controls combined with workspace/system availability |
| Destination restrictions | Blocked destination; required address verification | Backend policy and screening |
| Additional verification | Stronger authentication for a withdrawal | Security requirements bound to the exact operation |
| Balance restrictions | Available, reserved, restricted amounts | Backend accounting and authorized holds |
| Review and approval | Manual review before releasing a withdrawal | Configured operational workflow |
| Audit and notifications | Policy changed, verification required, hold applied | Audited backend events and customer-safe notifications |

These are different types of controls, not fields in a single status enum.
Account status, KYC status, policy assignment, risk classification, and active
holds must remain separately identifiable.

## 3. Account Status

| Status | Meaning |
| --- | --- |
| `active` | Account is operational, subject to all other controls |
| `restricted` | Functionality is limited; effective permissions identify which operations remain available |
| `disabled` | Financial operations are suspended; read/support access follows the agreed account-access policy |

Do not introduce compound states such as
`active_kyc_approved_withdrawal_blocked`. Record the underlying restrictions and
reasons separately. An account marked active must not bypass a hold or an unmet
verification requirement.

Lifecycle transitions are predefined system behavior, not arbitrary statuses
created by workspace administrators. Transition authorization, the relationship
between `restricted` and active holds, and read access for disabled customers
must be finalized in the implementation contract. Manually changing a display
status must never erase its underlying restrictions.

## 4. KYC, KYT, and Risk Classification

### 4.1 Customer verification: KYC

Know Your Customer (KYC) describes the customer's identity verification outcome.
Proposed public states are:

- `not_started`: verification has not started.
- `in_progress`: the customer is completing verification.
- `pending_review`: verification is awaiting a provider or authorized review.
- `action_required`: additional customer action is needed.
- `approved`: the verification workflow has approved the customer.
- `rejected`: verification has been rejected under the applicable process.

Completion of a verification SDK flow is not approval. The backend derives the
effective result from validated provider updates and authorized decisions.
Duplicate and stale updates must not overwrite a newer valid result.

Approval is not necessarily permanent: document expiry or changed requirements
may require reverification. The public status mapping and validity metadata
must be defined before release. No administrator may bypass mandatory checks
merely by setting a profile field to `approved`.

### 4.2 Address and transaction screening: KYT

Know Your Transaction (KYT) concerns a particular address or transaction,
separately from the customer's KYC result. Proposed normalized screening states:

| State | Meaning |
| --- | --- |
| `not_checked` | Required screening has not been performed |
| `pending` | Screening is underway |
| `passed` | The configured screening stage passed; other controls still apply |
| `review_required` | An authorized review is required |
| `blocked` | The applicable screening decision blocks the operation |
| `unavailable` | Screening could not produce a usable result |

These are proposed FortX workflow states, not a promise that every provider
uses these exact values. KYC approval does not approve every transaction.
An unavailable or missing required screening result must not be treated as a
successful check. Review and outage handling need explicit policy.

### 4.3 Customer risk classification

Proposed customer classifications are `unknown`, `low`, `medium`, and `high`.
Record their source, reason, evaluation time, and authorized changes. A risk
classification is an input to policy evaluation, not an account lifecycle state
or an automatic assertion of wrongdoing.

The effects of each classification must be explicitly configured. For example,
a classification may require additional review without disabling every customer
operation. Sensitive assessments remain in the backoffice; the customer API
returns only appropriate restriction information.

## 5. Policies and Effective Permissions

### 5.1 Control levels

| Level | Managed by | Purpose |
| --- | --- | --- |
| System controls | FortX | Supported permission types and mandatory security rules/ceilings |
| Workspace policy | Authorized workspace administrators | Reusable permissions and limits for customers |
| Individual restrictions | Authorized administrators/operators | Stricter restrictions for a particular customer |
| Operational holds | Authorized operators or automated controls | Block an operation while a condition or review remains unresolved |

The initial proposal assigns one policy to each customer. Administrators may
create policy profiles from supported controls; they cannot invent permission
names that the backend does not enforce or override mandatory system controls.
Operator administrative roles are separate from customer operation permissions.

Example: a Trading Only profile can allow conversions while blocking withdrawals.
Its allowance does not override a disabled account, mandatory KYC requirement,
screening block, or individual trading hold.

### 5.2 Permission evaluation

```text
Effective permission =
    system rules allow
    AND account and verification requirements allow
    AND assigned policy allows
    AND individual restrictions allow
    AND no applicable hold blocks
    AND operation-specific conditions are satisfied
```

A denial takes precedence over an allowance. A missing individual restriction
means inheritance, not an independent grant. An individual allowance cannot
override a policy denial. Policy and hold evaluation must be tenant-scoped and
performed by the backend on every financial command.

## 6. Amount Limits

Initial scope includes per-withdrawal and rolling-24-hour amount limits, with
optional asset-specific restrictions. Trading limits, request-count limits and
longer-period limits are possible extensions, not additional confirmed v1 scope.

For limits with the same operation, asset/valuation denomination, counting basis,
and period:

```text
Effective limit =
    minimum(system ceiling, assigned policy limit, individual limit)
```

An unset individual limit inherits the policy. It does not mean unlimited access.
A configured zero amount means no positive amount is permitted under that limit.

| Policy limit | Individual limit | Effective limit |
| --- | --- | --- |
| 1,000 USDT | Not set | 1,000 USDT |
| 1,000 USDT | 100 USDT | 100 USDT |
| 100 USDT | 1,000 USDT | 100 USDT |
| 1,000 USDT | 1,000 USDT | 1,000 USDT |

These are illustrative per-withdrawal limits, assuming no lower system ceiling
or blocking hold. They are not recommended regulatory thresholds.

Increasing an individual field above the policy value never increases the
effective allowance. An authorized administrator must change the assigned policy
or assign a higher-limit profile, while remaining within system controls.

Evaluate per-operation, rolling-period, asset-specific, and aggregate limits
independently. A request must satisfy all applicable constraints; do not compare
unrelated periods or different denominations directly in one minimum calculation.

### 6.1 Usage and reservation rules

- Use exact amount arithmetic and explicit asset precision.
- Reserve applicable allowance atomically when accepting a withdrawal so that
  simultaneous requests cannot bypass limits.
- Outstanding operations consume reserved allowance, including unresolved ones;
  do not free them solely because they have waited a long time.
- Transfer reserved usage into settled usage without double-counting completion.
- Idempotent retries do not consume allowance again.
- Release unused allowance only after a definitive cancellation, failure, or
  settlement. Account for any charged fee under the configured counting basis.
- Explicitly define principal versus total-debit counting, the rolling window's
  timestamp basis, and treatment of long-running operations before release.
- Equivalent-value limits require a trusted source, freshness requirements,
  valuation time, and stored valuation evidence. Missing required prices must
  not bypass a limit.
- Policy editing or reassignment must not reset history or outstanding reservations.

Policy changes apply to new requests. Pending operations need explicit
revalidation and transition rules. Lowering a limit does not erase reservations
or mean that a broadcast transaction can be canceled.

## 7. Holds, Balances, and Deposits

### 7.1 Individual holds

A hold identifies the affected operation or funds, reason, source, creation time,
and applicable review/expiry rules. A customer can have multiple active holds.
Removing one does not remove another or automatically reactivate the account.

Automated controls may impose holds. Release must follow the hold's authorized
review process; ordinary customer policy editing cannot bypass it. Sensitive
releases should support maker-checker approval and a complete audit trail.

### 7.2 Balance categories

```text
Total credited balance = available + reserved + restricted
```

Categories must not overlap. Reserved funds back accepted operations; restricted
funds are credited but unavailable due to a hold or another applicable restriction.
Uncredited deposits are visible in deposit history, not in credited balances.

A positive available amount is not itself permission to trade or withdraw.

### 7.3 Deposit controls

Disabling deposits cannot prevent someone from sending funds to an existing
blockchain address. Control these stages separately:

- Obtaining deposit instructions.
- Observing and recording incoming transactions.
- Automatically crediting a deposit versus requiring review.
- Making credited funds available versus restricting them.

Customer restrictions must not cause incoming transfers to be silently ignored.
Deposits, duplicate observations, and corrections need durable, auditable handling.

## 8. Operation and Review States

Customer controls are separate from the status of each operation:

| Resource | Proposed states |
| --- | --- |
| Order | `pending`, `processing`, `completed`, `failed` |
| Deposit | `confirming`, `under_review`, `credited`, `rejected` |
| Withdrawal | `pending`, `under_review`, `processing`, `confirming`, `completed`, `failed` |
| Review case | `open`, `awaiting_information`, `resolved` |

A resolved review requires an explicit outcome; `resolved` does not itself mean
approved or that all holds were released. A failed operation can still have a
charged network fee. An uncertain execution result must not be marked failed
only because a request timed out.

## 9. Example Customer

```text
Account status:           restricted
KYC status:               approved
Risk classification:      medium
Assigned policy:          Standard
Policy withdrawal limit:  1,000 USDT per withdrawal
Individual limit:         100 USDT per withdrawal
Active hold:              withdrawals blocked pending review
```

Effective behavior:

- Trading may remain allowed if the policy and all other applicable checks pass.
- Withdrawals are blocked despite the calculated 100 USDT per-withdrawal limit.
- Removing the withdrawal hold through its authorized process permits at most
  100 USDT per withdrawal, subject to remaining period allowance, available funds,
  destination eligibility, and any other restrictions.
- Deposit crediting follows its separate verification and screening rules.
- Removing one hold does not erase risk classification, change KYC, or remove
  other account restrictions.

## 10. Frontend and Backoffice

### 10.1 Customer frontend

Return effective permissions, applicable limits, remaining allowance, and safe
restriction reasons. Do not make the frontend combine raw policy records or
reimplement authorization logic. Responses are snapshots; recheck the exact
operation, amount, asset, network, and destination during backend acceptance.

Do not expose confidential screening data, internal investigations, credentials,
or operator-only notes. The existing proposed `/me` permission shape remains the
starting point; limits and verification metadata need an agreed API schema before
adding fields or endpoints to the integration guide.

### 10.2 Backoffice

Organize customer controls into Account, Verification, Risk, Policy, Limits,
Holds, and Audit views. Administrative authorization must distinguish viewing
sensitive information, assigning policies, editing limits, imposing holds,
reviewing cases, and releasing holds.

Every change records its actor, reason, timestamp, previous value, and new value.
Support maker-checker approval for sensitive changes, especially increased limits
and removal of restrictions. Audit decisions and notification content must not
leak provider secrets or confidential investigation details.

## 11. Decisions Required Before Implementation

- Account transition rules and how `restricted` relates to individual holds.
- KYC validity/reverification mapping and permitted provider/manual decisions.
- KYT provider mappings, screening freshness, outages, and review outcomes.
- Risk classification criteria and their explicit effects on eligibility.
- Initial policy templates, administrator roles, and maker-checker requirements.
- Limit counting basis, timestamps, valuation rules, and long-running reservations.
- Effects of policy/hold changes on accepted but not yet executed operations.
- Public limits schema, safe reason codes, and review/notification visibility.

This document defines proposed behavior only. It introduces no API implementation,
database schema, migration, regulatory certification, or verified security guarantee.
