# FortX Connect API Integration Guide

Status: FortX Connect API integration guide

Document version: `0.1`

API version: `v1`

Last reviewed: 2026-09-29

## 1. Purpose

This guide defines the FortX Connect API for end-user web, iOS, and Android
applications. It follows the HTTP conventions of the
[FortVault Partner API Integration Guide](../../fortvault-documentation/integrations/PARTNER_API_INTEGRATION_GUIDE.md)
for errors, idempotency keys, and pagination, while describing a separate
customer interface and trust boundary.

Version 1 covers Keycloak authentication, customer eligibility, Sumsub KYC,
crypto balances, indicative rates, amount-to-spend crypto conversions,
deposits, withdrawals, and customer activity. It excludes fiat balances and
payment rails, an order book or matching engine, amount-to-receive orders,
and saved withdrawal addresses.

- FortX Connect API base URL: `<FORTX_API_URL>/api/v1`
- Paths in the endpoint tables are relative to that base URL.
- Release-matched OpenAPI is the authoritative schema when it differs from this guide.
- Example IDs, prices, amounts, addresses, and timestamps are synthetic.

### 1.1 Versioning

The FortX Connect API is versioned in the path.


| Surface           | Base path                      | Role                                                                |
| ----------------- | ------------------------------ | ------------------------------------------------------------------- |
| FortX Connect API | `/api/v1`                      | This guide. Web, iOS, and Android call only this prefix.            |
| Health            | `/health`                      | Process probe for PostgreSQL and Redis. Not a client contract.      |
| Sumsub webhook    | `POST /api/v1/webhooks/sumsub` | Provider callback. Versioned so a later contract can keep this URL. |


A breaking change ships as a new prefix (`/api/v2`). Version `v1` keeps its paths, amount units, and the meaning of terminal statuses. Adding a response field is allowed. Removing or renaming one is not.

Integrate only against `/api/v1`. Local-only sandbox helpers are outside this contract.

## 2. Integration Model

```text
FortX web / iOS / Android
    -> FortX Connect API (/api/v1)
```

FortX Connect owns customer trading accounts, balances, reservations, quotes,
orders, deposits, withdrawals, and customer operation history. On-chain
settlement and custody are server-side. A customer balance is the spendable
and reserved amount FortX reports, not a wallet balance the client reads
directly from a chain or custody API.

Every request is scoped to the authenticated customer and workspace through
trusted server-side identity mapping. A caller cannot select another customer
or workspace by changing a body, query parameter, or resource ID. Resources
outside the authorized scope return `RESOURCE_NOT_FOUND` without revealing
their existence. All list filters and pagination operate inside that scope.

The client never holds custody signing material, exchange credentials, or
provider secrets. Customer authentication does not replace server-side
authorization on each financial command.

## 3. Onboarding

### 3.1 Prerequisites

Before implementation, obtain the sandbox API URL, approved Keycloak issuer
and client configuration for each channel, redirect/logout URIs, allowed web
origins, and test customer accounts. Agree supported assets, networks, markets,
KYC requirements, and withdrawal fee rates per network route.

Use separate sandbox and production configurations. Do not put a confidential
OAuth client secret or a provider API secret in a browser or mobile app.

### 3.2 Suggested integration order

1. Sign in and retrieve `/me`.
2. Implement KYC and operation eligibility states.
3. Load assets, networks, markets, rates, and balances.
4. Implement quote confirmation, order creation, and result recovery.
5. Implement deposit instructions and deposit tracking.
6. Implement withdrawal amount and fee confirmation, then submission.
7. Implement activity, pagination, error handling, and sandbox acceptance cases.

### 3.3 Session and operation identifiers

Keep authentication sessions separate from financial operations. A new login,
token refresh, screen remount, or app restart is not permission to submit an
uncertain order or withdrawal again with a new key. Retain non-secret operation
IDs and retry metadata within the appropriate customer account context.

## 4. HTTP Authentication

### 4.1 Bearer access token

Use Keycloak's OpenID Connect authorization-code flow with PKCE for public
clients under the approved channel configuration. Use approved libraries and
discovery metadata rather than constructing a password-login API in FortX.
Registration, authentication challenges, account recovery, refresh, and logout
follow the configured identity-provider flows.

```http
GET /api/v1/me
Authorization: Bearer <KEYCLOAK_ACCESS_TOKEN>
Accept: application/json
```

Send an access token, not an ID token. FortX must validate the trusted issuer,
signature, expiry, intended audience/client configuration, and the associated
customer/workspace access. Account status and financial permissions are checked
server-side in addition to identity authentication.

A valid Keycloak access token may authenticate multiple requests according to
its lifetime and session policy. Refresh when required.

### 4.2 Session expiry and logout

On HTTP `401`, use the approved refresh flow or require sign-in. Bound automatic
refresh/retry attempts. After authentication is restored, recover pending
operations before permitting a replacement submission. Logout clears local
authentication material, but does not cancel accepted financial operations.

Native apps require platform-secure token storage. The web token/session storage
and any backend-for-frontend arrangement require a separate security decision;
this guide does not prescribe persistent browser storage for bearer tokens.

### 4.3 Idempotency for write requests

Mandatory idempotency coverage:


| Endpoint                  | Key required | Reason                                                                |
| ------------------------- | ------------ | --------------------------------------------------------------------- |
| `POST /orders`            | Yes          | Prevent duplicate customer conversions                                |
| `POST /withdrawals`       | Yes          | Prevent duplicate withdrawals                                         |
| `POST /deposit-addresses` | Yes          | Deduplicate address preparation requests                              |
| `POST /quotes`            | No           | Creates an expiring preview; does not reserve or move funds           |
| `POST /me/kyc/sessions`   | No           | Issues short-lived SDK credentials; do not replay expired credentials |


Preview and SDK endpoints do not require idempotency keys but still require rate limiting.

```http
POST /api/v1/orders
Authorization: Bearer <KEYCLOAK_ACCESS_TOKEN>
Content-Type: application/json
Idempotency-Key: order-550e8400-e29b-41d4-a716-446655440000
```

Key format: 8 through 255 ASCII letters, numbers, periods, underscores, colons,
or hyphens. Generate a new unpredictable key per logical command and retain it
across retries.

Behavior:

- Keys are isolated by workspace and authenticated customer, not by session.
Method, path, query, and body are included in the request comparison.
- Same key and same request: replay the saved HTTP status and response body.
- Same key with a different completed request: HTTP `409`,
`IDEMPOTENCY_KEY_REUSED`.
- An original command still running or unresolved: HTTP `409`,
`IDEMPOTENCY_REQUEST_IN_PROGRESS`; do not start another command.
- A replay includes `Idempotency-Replayed: true` and a fresh `X-Request-Id`.
- Authentication, tenant/customer scope, and authorization are checked again
before replay; a saved response does not grant access after revocation.
- Business changes, reservations, quote consumption, the command response, and
any required durable outbound intent must commit consistently. A lost HTTP
response after commit must not allow duplicate work.
- Save successful command responses and deterministic business/validation `4xx`
responses after the command's authenticated idempotency boundary. Do not cache
authentication/authorization failures, key errors, rate-limit responses, or
transient `5xx` as completed command outcomes.
- Preserve a stored error's complete envelope, including its original
`requestId` and `timestamp`. Do not regenerate that body on replay.

Completed-response retention is 24 hours. Uncertain
in-progress commands must not be made executable again merely because time has
elapsed. After retention, do not blindly retry: establish the business outcome
from the resource first.

Consuming a quote must also be unique within its customer/workspace scope.
Submitting the same consumed quote with a different key must return
`QUOTE_ALREADY_USED`, not create another operation. A quote must not be reused
to create a replacement operation even after idempotency-response retention.

### 4.4 Request correlation

Every application response under `/api/v1` must include a server-generated
`X-Request-Id`, including errors and idempotency replays. Ignore caller-supplied
request IDs for this identifier. Gateway-generated failures may lack it.

Expose `X-Request-Id`, `Idempotency-Replayed`, and `Retry-After` through CORS for
approved browser origins. Allow the required request headers, including
`Authorization`, `Content-Type`, and `Idempotency-Key`.


| Identifier            | Lifetime                                          |
| --------------------- | ------------------------------------------------- |
| Idempotency key       | One logical command, retained across retries      |
| Request ID            | One HTTP attempt; always changes on a new attempt |
| Order / withdrawal ID | One business operation and its lifecycle          |


## 5. Permissions and Endpoints

### 5.1 Read endpoints

All endpoints require customer authentication, including catalog and rates.
Public pre-login pricing is not part of this version.


| Method | Endpoint                      | Purpose                                                    |
| ------ | ----------------------------- | ---------------------------------------------------------- |
| `GET`  | `/me`                         | Current profile, account status, and operation eligibility |
| `GET`  | `/me/kyc`                     | Backend verification status and required customer action   |
| `GET`  | `/assets`                     | Supported trading assets and amount precision              |
| `GET`  | `/assets/{assetId}/networks`  | Supported funding routes and limits                        |
| `GET`  | `/markets`                    | Supported directed spend/receive pairs and limits          |
| `GET`  | `/market-rates`               | Indicative prices, timestamps, and availability            |
| `GET`  | `/balances`                   | Customer balances and indicative USDT valuation            |
| `GET`  | `/orders`                     | Customer conversion history                                |
| `GET`  | `/orders/{orderId}`           | Current conversion result                                  |
| `GET`  | `/deposit-addresses`          | Assigned or preparing deposit instructions                 |
| `GET`  | `/deposits`                   | Customer deposit history                                   |
| `GET`  | `/deposits/{depositId}`       | Deposit details and crediting state                        |
| `GET`  | `/withdrawals`                | Customer withdrawal history                                |
| `GET`  | `/withdrawals/{withdrawalId}` | Withdrawal execution and accounting result                 |
| `GET`  | `/activity`                   | Unified customer operation history                         |


### 5.2 Write endpoints


| Method | Endpoint             | Purpose                                         | Success |
| ------ | -------------------- | ----------------------------------------------- | ------- |
| `POST` | `/me/kyc/sessions`   | Obtain a short-lived Sumsub SDK session         | `201`   |
| `POST` | `/quotes`            | Create an amount-to-spend conversion quote      | `201`   |
| `POST` | `/orders`            | Accept a conversion quote                       | `201`   |
| `POST` | `/deposit-addresses` | Obtain or request assigned deposit instructions | `201`   |
| `POST` | `/withdrawals`       | Submit a withdrawal                             | `201`   |


`201` acknowledges the returned resource or accepted command, not financial
completion. Address requests may return existing instructions or a preparing
resource; they do not imply address rotation. A replay preserves the original
status/body. All reads return `200` on success.

### 5.3 Customer eligibility

`GET /me` returns a single object with `id`, `displayName`, `status`, and
`permissions`. Account status is one control. It is not a compound of KYC,
risk, policy, or holds. Do not invent states such as
`active_kyc_approved_withdrawal_blocked`.


| Status       | Meaning                                                                                                                      |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| `active`     | The account is operational. Every other control still applies.                                                               |
| `restricted` | Functionality is limited. `permissions` says which operations remain available.                                              |
| `disabled`   | Financial operations are suspended. Read access for disabled accounts follows the account-access policy in your environment. |


```json
{
  "id": "80000000-0000-4000-8000-000000000001",
  "displayName": "Sandbox Customer",
  "status": "restricted",
  "permissions": {
    "trade": { "allowed": true, "reasonCode": null },
    "deposit": { "allowed": true, "reasonCode": null },
    "withdraw": { "allowed": false, "reasonCode": "KYC_REQUIRED" }
  }
}
```

`trade` is placing a conversion. `deposit` is obtaining deposit instructions. `withdraw` is submitting a withdrawal. Automatic crediting of an incoming transfer is a separate backend control. It is not a fourth permission the client combines.

The backend evaluates every financial command. A denial wins over an allowance:

```text
Effective permission =
    system rules allow
    AND account status and verification allow
    AND the assigned policy allows
    AND individual restrictions allow
    AND no applicable hold blocks
    AND the operation's own checks pass
```

A missing individual restriction inherits the policy. It is not an extra grant. An individual allowance cannot override a policy denial, a disabled account, a mandatory KYC requirement, a screening block, or a hold. One customer has one assigned policy.

`permissions` is the snapshot the UI may display. It is not authorization. The backend checks the same operation again at acceptance, including amount, asset, network, and destination. A positive Available balance, or an approved KYC result, does not by itself allow a trade or a withdrawal.

Holds, risk classification, address and transaction screening, and amount limits are enforced on the server. This response does not include policy records, risk labels, screening results, or remaining allowance. A customer-safe `reasonCode` is the only explanation of a denial. Several holds can be active at once. Removing one does not remove the others and does not by itself change `status`.

## 6. Pagination and Filtering

Query parameters:


| Parameter | Default | Rules                                            |
| --------- | ------- | ------------------------------------------------ |
| `skip`    | `0`     | Integer, minimum `0`                             |
| `take`    | `50`    | Integer from `1` through `50`                    |
| `order`   | `DESC`  | `ASC` or `DESC`; no separate `orderBy` parameter |


List envelope for every collection in Section 5.1:

```json
{
  "items": [],
  "total": 0,
  "skip": 0,
  "take": 50
}
```

`total` counts the authorized filtered dataset before paging.
Resource details and command responses are single objects, not list envelopes.

### 6.1 Sorting contract


| Collection                                                   | Ordered fields, in priority order                               |
| ------------------------------------------------------------ | --------------------------------------------------------------- |
| `/assets`                                                    | `symbol`, `id`                                                  |
| `/assets/{assetId}/networks`                                 | `name`, `id`                                                    |
| `/markets`                                                   | `spendAssetId`, `receiveAssetId`, `id`                          |
| `/market-rates`                                              | `baseAssetId`, `quoteAssetId` (unique pair)                     |
| `/balances`                                                  | `symbol`, `assetId` (unique customer balance per trading asset) |
| `/orders`, `/deposit-addresses`, `/deposits`, `/withdrawals` | `createdAt`, `id`                                               |
| `/activity`                                                  | `createdAt`, `id` (unique activity ID)                          |


`order` applies to every field in the tuple, including the unique tie-breaker.
All sorting fields are non-null and exposed in the response. ASC is oldest
first for timestamps and ascending for text/IDs; DESC reverses the comparison.
UUID tie-breakers use UUID order; text uses a fixed, documented collation rather
than locale-dependent frontend comparison. Ordering precedes pagination.

History uses the FortX record's `createdAt`, not a chain's block time, a
provider's detection time, or the latest update time. Expose `blockTimestamp`
separately where available; it may be null and is not a sorting key.

Offset pagination does not prevent duplicates or omissions during concurrent
inserts/updates. It is not a lossless synchronization feed or a commit-order
cursor. Clients may refresh and deduplicate by ID; exports/snapshot feeds are
outside this version.

### 6.2 Filters


| Collection                  | Optional filters                                |
| --------------------------- | ----------------------------------------------- |
| `/assets`                   | `symbol` (exact)                                |
| `/markets`                  | `spendAssetId`, `receiveAssetId`                |
| `/market-rates`             | `baseAssetId`, `quoteAssetId`                   |
| `/balances`                 | `assetId`                                       |
| `/orders`                   | `assetId` (either side), `status`, `from`, `to` |
| `/deposit-addresses`        | `assetId`, `networkId`                          |
| `/deposits`, `/withdrawals` | `assetId`, `networkId`, `status`, `from`, `to`  |
| `/activity`                 | `type`, `assetId`, `status`, `from`, `to`       |


`from` is inclusive and `to` exclusive, both ISO 8601 UTC timestamps, filtering
`createdAt`. Reject an invalid range or unsupported filter with
`VALIDATION_ERROR`. Filters combine with AND; an order matches `assetId` if
either its spend or receive asset matches. No customer/workspace override is
accepted. `status` is a resource-specific value; activity requires `type` when
filtering by status to avoid mixing different status vocabularies.

## 7. Read Data and Amounts

### 7.1 Assets, markets, and networks

An `assetId` identifies a FortX trading and accounting asset. Symbols are
display labels, not unique identifiers. Use only FortX asset and network ids
from this API.

```json
{
  "id": "10000000-0000-4000-8000-000000000001",
  "name": "Tether",
  "symbol": "USDT",
  "decimals": 6
}
```

Network rows contain `id`, `name`, `chainRef`, `depositEnabled`,
`withdrawalEnabled`, `memoRequired`, `minDepositAmountBaseUnits`,
`minWithdrawalAmountBaseUnits`, `withdrawalAmountStepBaseUnits`, and
`withdrawalFeeRate`. `withdrawalFeeRate` is the fixed fraction of the recipient
amount, in the same asset. Limits
use the parent trading asset's units; network precision conversion must be
exact and validated server-side. Display `name`, not the internal `chainRef`.
Network rows do not include a confirmation count. FortX does not expose
blockchain confirmation counts for deposits. A network route does not promise
cross-network liquidity or automatic bridging.

Market rows contain `id`, `spendAssetId`, `receiveAssetId`, `enabled`,
`minSpendAmountBaseUnits`, `maxSpendAmountBaseUnits`, and
`spendAmountStepBaseUnits`. A market is directed: support for A -> B does not
imply support for B -> A. An enabled pair does not guarantee a quote at every
amount or at every moment.

### 7.2 Exact amounts

- Amounts, balances, fees, and limits are base-unit integer strings.
- Use asset metadata to convert display units: `100000000` with six decimals
is 100 USDT. Do not use JavaScript floating-point arithmetic for money.
- Canonical unsigned amount strings match `0|[1-9][0-9]*`. A command amount must
be positive; balances and fees may be zero. No exponents, signs, or separators.
- Reject excess precision and route-step violations rather than silently
rounding a customer submission. Apply network minimums and execution limits
independently of display precision.
- The backend calculates final quote amounts. Rates are decimal strings for
display; their rounded presentation must not be used to reconstruct settlement.
- All timestamps use ISO 8601 UTC. IDs are opaque; examples use UUIDs.
- Unknown request fields are rejected with `400 VALIDATION_ERROR`, not silently
stripped. Clients tolerate additional response fields but not unknown statuses
as evidence of completion.

### 7.3 Indicative market rates

```http
GET /api/v1/market-rates?baseAssetId=10000000-0000-4000-8000-000000000002&quoteAssetId=10000000-0000-4000-8000-000000000001
Authorization: Bearer <KEYCLOAK_ACCESS_TOKEN>
```

One row in `items`:

```json
{
  "baseAssetId": "10000000-0000-4000-8000-000000000002",
  "quoteAssetId": "10000000-0000-4000-8000-000000000001",
  "rate": "70000",
  "asOf": "2026-09-29T10:00:00.000Z",
  "validUntil": "2026-09-29T10:00:15.000Z",
  "status": "available"
}
```

The rate means quote-asset units per one base-asset unit, here 70,000 USDT per
BTC. `status` is `available`, `stale`, or `unavailable`. For unavailable prices,
`rate`, `asOf`, and `validUntil` may be null; never substitute zero. A stale row
may retain its last rate/timestamp, visibly marked stale. Reaching `validUntil`
does not make the last cached price current merely because no new poll succeeded.

The backend owns price sources, freshness, and normalization. Exact sources and
refresh intervals are release decisions. Use `baseAssetId`/`quoteAssetId` rather
than the earlier discussion's ambiguous symbol-based currency filters. This API
does not provide a guaranteed customer rate or place any trade.

### 7.4 Balances and portfolio value

One row from `GET /balances`:

```json
{
  "assetId": "10000000-0000-4000-8000-000000000001",
  "symbol": "USDT",
  "decimals": 6,
  "availableAmountBaseUnits": "400000000",
  "lockedAmountBaseUnits": "100000000",
  "unconfirmedAmountBaseUnits": "50000000",
  "frozenAmountBaseUnits": "25000000",
  "totalAmountBaseUnits": "525000000",
  "valuation": {
    "quoteAssetId": "10000000-0000-4000-8000-000000000001",
    "amountBaseUnits": "525000000",
    "asOf": "2026-09-29T10:00:00.000Z",
    "validUntil": "2026-09-29T10:00:15.000Z",
    "status": "available"
  }
}
```

Each customer asset has four balance amounts. They do not overlap. None of them may be negative.


| Amount                       | Name        | Meaning                                                                                                        |
| ---------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------- |
| `availableAmountBaseUnits`   | Available   | Spendable credited balance. Trades and withdrawals draw from this amount only.                                 |
| `lockedAmountBaseUnits`      | Locked      | Reserved balance. Held for an accepted withdrawal or another command that outlives the request. Not spendable. |
| `unconfirmedAmountBaseUnits` | Unconfirmed | Pending incoming. Observed funds that are not yet credited to Available. Not spendable.                        |
| `frozenAmountBaseUnits`      | Frozen      | Compliance hold on funds already attributed to the customer. Not spendable.                                    |


`totalAmountBaseUnits` is the credited balance: Available + Locked + Frozen. Unconfirmed is returned beside it and is not part of that credited total. A market order that completes in one transaction does not leave a Locked balance after the response. A withdrawal moves the reserved amount from Available to Locked until it settles. When FortX observes an inbound transfer to the issued deposit address, it
credits Available unless a review holds the credit first. While that review holds the credit, the amount is Unconfirmed. Crediting moves it from Unconfirmed to Available. A compliance hold of funds already credited moves them from Available to Frozen. Releasing that hold moves them back. A positive Available balance is not permission to trade or withdraw.

The portfolio denomination is USDT, not fiat USD. Backend-calculated valuation uses the quote asset's decimals, carries its own freshness state, and is informational. It covers Available, Locked, and Frozen. It excludes Unconfirmed, because that amount is still pending incoming. Unavailable valuation has null amount and timestamps rather than a zero amount. The frontend must not present Available as if it included the other three, must not show an incomplete sum as a complete portfolio total, must not sum only one page, and must not combine different quote denominations.

### 7.5 Unified activity

`GET /activity` combines customer conversions, deposits, and withdrawals. Each
row contains `id`, `type` (`conversion`, `deposit`, `withdrawal`), `resourceId`,
`createdAt`, `updatedAt`, the underlying resource `status`, and `amounts`.
Each amount entry has `role` (`spend`, `receive`, `fee`), `assetId`, and
`amountBaseUnits`; a fee breakdown is not an additional principal movement.

Open details through the corresponding `/orders`, `/deposits`, or `/withdrawals`
resource. Activity uses one row per customer operation, not one per webhook,
confirmation, or custody movement. Status updates preserve the activity ID.
Treasury or internal operations are excluded from activity. Any post-credit
correction must have an auditable reference and must not silently rewrite the
original receipt.

## 8. Customer Verification

### 8.1 Read verification status

`GET /me/kyc` returns `status`, `updatedAt`, and nullable `requiredAction`.
Public statuses are `not_started`, `in_progress`, `pending_review`,
`action_required`, `approved`, and `rejected`. `requiredAction` contains a stable
`code` and customer-safe `message`, not provider-internal investigation data.


| Status            | Meaning                                                        |
| ----------------- | -------------------------------------------------------------- |
| `not_started`     | Verification has not started.                                  |
| `in_progress`     | The customer is completing verification.                       |
| `pending_review`  | Verification is awaiting the provider or an authorized review. |
| `action_required` | The customer must take a further step.                         |
| `approved`        | The verification workflow has approved the customer.           |
| `rejected`        | Verification has been rejected under the applicable process.   |


Provider-internal states map onto this public list before they are returned.
Completing the SDK is not approval. A newer valid provider result must not be overwritten by a duplicate or older event. Setting a profile field to `approved` does not bypass the required checks. Approval can expire. KYC approval does not approve every transaction, and it does not grant trading or withdrawal permission. Read `/me` for effective operation eligibility.

Address and transaction screening is separate from this KYC status. The FortX Connect API does not return screening states or risk classification (`unknown`, `low`, `medium`, `high`). A missing or unusable screening result is not a pass. The customer sees only the resulting permission denial.

### 8.2 Start or resume verification

```http
POST /api/v1/me/kyc/sessions
Authorization: Bearer <KEYCLOAK_ACCESS_TOKEN>
Content-Type: application/json

{}
```

```json
{
  "provider": "sumsub",
  "sdkToken": "<SHORT_LIVED_SDK_TOKEN>",
  "expiresAt": "2026-09-29T10:10:00.000Z"
}
```

The backend binds the SDK session to the authenticated customer and configured
verification level. Do not accept a caller-selected customer or arbitrary
provider level. Do not log/cache SDK tokens in analytics or idempotency records.
After the SDK returns, poll `/me/kyc`; SDK completion is not approval. Validated
provider events determine the backend result, with duplicate/stale-event safety.

## 9. Create a Conversion

### 9.1 Request an amount-to-spend quote

```http
POST /api/v1/quotes
Authorization: Bearer <KEYCLOAK_ACCESS_TOKEN>
Content-Type: application/json

{
  "spendAssetId": "10000000-0000-4000-8000-000000000001",
  "receiveAssetId": "10000000-0000-4000-8000-000000000002",
  "spendAmountBaseUnits": "100000000"
}
```

Example response for USDT (six decimals) -> BTC (eight decimals):

```json
{
  "id": "30000000-0000-4000-8000-000000000001",
  "spendAssetId": "10000000-0000-4000-8000-000000000001",
  "receiveAssetId": "10000000-0000-4000-8000-000000000002",
  "spendAmountBaseUnits": "100000000",
  "totalDebitAmountBaseUnits": "100000000",
  "receiveAmountBaseUnits": "141858",
  "fees": [
    {
      "type": "conversion",
      "assetId": "10000000-0000-4000-8000-000000000002",
      "amountBaseUnits": "142"
    }
  ],
  "spreadIncluded": true,
  "effectiveRate": {
    "baseAssetId": "10000000-0000-4000-8000-000000000002",
    "quoteAssetId": "10000000-0000-4000-8000-000000000001",
    "rate": "70494.02980445"
  },
  "createdAt": "2026-09-29T10:00:00.000Z",
  "expiresAt": "2026-09-29T10:00:10.000Z"
}
```

The customer spends exactly 100 USDT. Before the fee, the receive amount is
0.00142 BTC (`142000` base units). The conversion fee is 10 basis points of that
amount, `142` base units of BTC, and is taken from the amount received. The
customer is credited the net, 0.00141858 BTC (`141858`). The displayed effective
rate is rounded from those binding net amounts.

`receiveAmountBaseUnits` is the net customer credit. Fee rows contain `type`,
`assetId`, and `amountBaseUnits`, and the fee asset is the receive asset. Their
sum is already excluded from `receiveAmountBaseUnits` and must not be charged
again. Do not also deduct the fee from the spend amount, and do not introduce a
third-asset debit.

Quotes are customer/workspace-bound, immutable, expiring, and single-use for
order creation. They do not reserve funds. `expiresAt` is 10 seconds after
`createdAt`. The server clock determines expiry. There is no expiry job.
Reject unsupported markets, invalid amounts, or unavailable executable pricing.

### 9.2 Confirm and accept

Display the spend amount, net receive amount, effective rate, fee breakdown,
and expiry. Request quotes after input settles rather than on every keystroke.
If a quote expires or the customer changes input, obtain and display a new
quote before confirmation. Do not silently replace an accepted customer price.

```http
POST /api/v1/orders
Authorization: Bearer <KEYCLOAK_ACCESS_TOKEN>
Content-Type: application/json
Idempotency-Key: order-550e8400-e29b-41d4-a716-446655440000

{
  "quoteId": "30000000-0000-4000-8000-000000000001"
}
```

Example accepted response:

```json
{
  "id": "40000000-0000-4000-8000-000000000001",
  "quoteId": "30000000-0000-4000-8000-000000000001",
  "status": "completed",
  "spendAssetId": "10000000-0000-4000-8000-000000000001",
  "receiveAssetId": "10000000-0000-4000-8000-000000000002",
  "totalDebitAmountBaseUnits": "100000000",
  "receiveAmountBaseUnits": "141858",
  "fees": [
    {
      "type": "conversion",
      "assetId": "10000000-0000-4000-8000-000000000002",
      "amountBaseUnits": "142"
    }
  ],
  "createdAt": "2026-09-29T10:00:05.000Z",
  "updatedAt": "2026-09-29T10:00:05.000Z",
  "completedAt": "2026-09-29T10:00:05.000Z",
  "failureReason": null
}
```

The receive amount on a `completed` order is the amount credited to the customer.
Acceptance checks quote ownership, unused state and expiry, account/KYC/policy
eligibility, limits, and available funds. FortX then creates the order, processes
it, and succeeds or fails it in one database transaction: consume the quote, debit
the spend amount, and credit the net receive amount, or release the lock and mark
the order failed. Concurrent commands cannot spend the same available money.

Once accepted, the customer amounts are fixed. Later price changes do not
justify silently repricing the order. Before acceptance, reject an invalid or
expired quote and require new confirmation. Replaying an already accepted
command must still return its saved response after that quote has expired.

### 9.3 Read the result

```http
GET /api/v1/orders/40000000-0000-4000-8000-000000000001
Authorization: Bearer <KEYCLOAK_ACCESS_TOKEN>
```

Details and list rows use the order object above, with current status and
timestamps. `failureReason`, when present, is a stable `code` and safe `message`.


| Status       | Meaning                                                                     |
| ------------ | --------------------------------------------------------------------------- |
| `pending`    | Created inside the customer-order transaction, before processing            |
| `processing` | Customer ledger processing inside that same transaction                     |
| `completed`  | Spend debit and net receive credit committed                                |
| `failed`     | Customer lock released and the order recorded as failed in that transaction |


A successful `POST /orders` returns `completed`. A definitive customer-side failure returns `failed`. The client does not poll for a separate settlement step before showing the credited balance. `pending` and `processing` are steps inside the transaction. A creation replay returns that committed outcome. There is no partial customer fill in this version.

### 9.4 Balance example


| Stage                                            | Available | Locked | Unconfirmed | Frozen |
| ------------------------------------------------ | --------- | ------ | ----------- | ------ |
| Before accepting a 100 USDT order                | 500       | 0      | 0           | 0      |
| Same request, completed                          | 400       | 0      | 0           | 0      |
| Alternatively, same request, failed and released | 500       | 0      | 0           | 0      |


The completed order also credits the agreed net BTC amount to Available in that same transaction. The failure row is an alternative outcome, not a reversal after completion. Any lock taken inside the order transaction is released before the response, so the client does not observe it as Locked. Balance updates in the response are authoritative. The client does not need to
poll for a second completion step after `completed`.

## 10. Deposits and Withdrawals

### 10.1 Obtain deposit instructions

Select a returned asset/network route. Read its enabled state, minimum, and
memo/tag requirement before requesting instructions. Do not wait for a confirmation count. FortX does not expose one.

```http
POST /api/v1/deposit-addresses
Authorization: Bearer <KEYCLOAK_ACCESS_TOKEN>
Content-Type: application/json
Idempotency-Key: deposit-address-550e8400-e29b-41d4-a716-446655440000

{
  "assetId": "10000000-0000-4000-8000-000000000001",
  "networkId": "20000000-0000-4000-8000-000000000001"
}
```

```json
{
  "id": "50000000-0000-4000-8000-000000000001",
  "assetId": "10000000-0000-4000-8000-000000000001",
  "networkId": "20000000-0000-4000-8000-000000000001",
  "status": "preparing",
  "address": null,
  "memo": null,
  "createdAt": "2026-09-29T10:00:00.000Z",
  "updatedAt": "2026-09-29T10:00:00.000Z",
  "failureReason": null
}
```

Read `GET /deposit-addresses?assetId=...&networkId=...` to find the current
instructions. Status is `preparing`, `ready`, or `failed`. Only `ready` includes
a usable address and, where required, memo/tag. Display/copy the exact returned
values; do not apply EVM formatting assumptions to other networks.

Reuse an existing assigned instruction by default, even for a new logical
request. Concurrent requests must converge on the same assignment. This API
does not request fresh address rotation. A failed preparation must be resolved
through the defined backend retry process, not repeated client key changes.

### 10.2 Track deposits

`GET /deposits` and `GET /deposits/{depositId}` return `id`, `assetId`,
`networkId`, `amountBaseUnits`, `creditedAmountBaseUnits`, `status`, `address`,
nullable `memo`, nullable `transactionHash`, nullable `blockTimestamp`,
`createdAt`, `updatedAt`, nullable `creditedAt`, and nullable `reviewReason`.
The deposit resource does not include `confirmations` or `requiredConfirmations`.

FortX does not expose a confirmation count or a finalized flag. An observed
inbound transfer to the issued deposit address is treated as confirmed for
crediting. FortX correlates deposits by stable identifiers such as `txHash`,
`chainRef`, asset, address, and exact amount. The same inbound transfer credits
the customer once.


| Status         | Meaning                                                                      |
| -------------- | ---------------------------------------------------------------------------- |
| `under_review` | The movement is confirmed, and crediting is waiting on a compliance decision |
| `credited`     | The confirmed movement has been credited to Available                        |
| `rejected`     | The confirmed movement was not credited; customer-safe next step provided    |


There is no `confirming` status. `creditedAmountBaseUnits` is zero until `credited`. A movement that is credited immediately does not pass through Unconfirmed. A movement held in `under_review` stays Unconfirmed until it is credited or rejected. A compliance hold of funds already credited is Frozen, not Unconfirmed. A rejected deposit does not mean the funds were automatically returned. A provider notification, transaction hash, or frontend SDK result does not by
itself credit the customer. A credited deposit appears through this API when
FortX accepts the inbound transfer.

Deposit controls are separate from whether an address already exists. Stopping new deposit instructions does not stop a transfer to an address that was already issued. FortX still records the incoming movement. It does not drop it because the customer is restricted. The controlled steps are: issuing instructions, recording the movement, crediting it or holding it for review, and then leaving the credited amount Available or moving it to Frozen.

Duplicate delivery of the same inbound transfer must not credit twice. An empty
deposit list is not proof that a transfer failed. A later chain reorganization
after credit is handled as an operational correction with an auditable reference.
Do not silently remove a credited deposit from history.

### 10.3 Submit a withdrawal

There is no withdrawal quote. The fee is a fixed percentage of the amount the recipient will receive, published as `withdrawalFeeRate` on the network route. The client shows that recipient amount and the fee before the customer confirms, then sends both amounts. FortX sends the recipient amount exactly. It does not add or remove a network fee from that amount after the customer has seen it.

Customers may enter an external destination, but the backend must validate the network, address, memo, route, account eligibility, destination policy, and custody controls. Free-form input is not a policy bypass. Saved-address management is excluded from v1.

```http
POST /api/v1/withdrawals
Authorization: Bearer <KEYCLOAK_ACCESS_TOKEN>
Content-Type: application/json
Idempotency-Key: withdrawal-550e8400-e29b-41d4-a716-446655440000

{
  "assetId": "10000000-0000-4000-8000-000000000001",
  "networkId": "20000000-0000-4000-8000-000000000001",
  "destination": {
    "address": "<VALID_SANDBOX_ADDRESS_FOR_SELECTED_NETWORK>",
    "memo": null
  },
  "recipientAmountBaseUnits": "100000000",
  "feeAmountBaseUnits": "1000000"
}
```

`recipientAmountBaseUnits` is the amount shown on the confirmation screen and
the amount sent on-chain to the destination. `feeAmountBaseUnits` is the fee shown on that same screen. Both are in the same asset. If `withdrawalFeeRate` is `0.01`, the fee on 100 USDT is 1 USDT. FortX locks 101 USDT: 100 to send and 1 as the fee. The rate in this paragraph is an illustration.

FortX recalculates the fee from the current `withdrawalFeeRate` and compares it with `feeAmountBaseUnits`. The withdrawal is accepted only when they match. If the platform fee changed after the customer saw the screen, the request fails with `409 FEE_CHANGED` and the message `The withdrawal fee has changed. Please retry.` Nothing is locked. The client refreshes the route, shows the new fee, and submits again with a new idempotency key.

The response includes `id`, `assetId`, `networkId`, `destination`, `recipientAmountBaseUnits`, `feeAmountBaseUnits`, `lockedAmountBaseUnits`, `status`, nullable `transactionHash`, `createdAt`, `updatedAt`, nullable `completedAt`, and nullable `failureReason`. `lockedAmountBaseUnits` is the recipient amount plus the fee the customer sent.

Server-side custody policy can require destination approval before broadcast.
That step does not change the recipient amount the customer confirmed.

### 10.4 Track a withdrawal

Read `/withdrawals/{withdrawalId}` for the current result. List rows use the same fields.


| Status         | Meaning                                                                             |
| -------------- | ----------------------------------------------------------------------------------- |
| `pending`      | Accepted. Available has been moved to Locked for the recipient amount plus the fee. |
| `under_review` | Waiting on a compliance or custody policy decision. The lock stays.                 |
| `processing`   | The transfer has been submitted or the result is not yet known.                     |
| `completed`    | The recipient amount was sent. The fee stays debited. The lock is cleared.          |
| `failed`       | The send did not complete. The full lock, including the fee, returns to Available.  |


A failed withdrawal does not charge the customer. FortX does not keep the fee, and it does not pass on a chain cost from the failed attempt. Unknown broadcast results stay `pending` or `processing` until FortX resolves the outcome. Do not mark the withdrawal failed only because the customer request timed out. Cancellation and address-book endpoints are not in this version.

## 11. Error Contract

Use the Partner API public envelope and `errorCode` naming style:

```json
{
  "statusCode": 409,
  "errorCode": "QUOTE_EXPIRED",
  "message": "The quote has expired. Request a new quote and confirm again.",
  "details": null,
  "requestId": "a0000000-0000-4000-8000-000000000001",
  "timestamp": "2026-09-29T10:00:21.000Z",
  "path": "/api/v1/orders"
}
```

For a newly generated error, body `requestId` matches `X-Request-Id`. A stored
error replay preserves the original body ID and timestamp; the response header
identifies the new HTTP attempt. Successful responses have the header without
requiring an extra request ID field in every resource.

### 11.1 Public error codes


| HTTP  | Error code                        | Recommended handling                                                |
| ----- | --------------------------------- | ------------------------------------------------------------------- |
| `400` | `VALIDATION_ERROR`                | Correct invalid/unknown fields or precision                         |
| `401` | `AUTHENTICATION_FAILED`           | Refresh/sign in through Keycloak; bound retries                     |
| `403` | `FORBIDDEN`                       | Do not bypass server-side authorization                             |
| `403` | `ACCOUNT_RESTRICTED`              | Show safe restriction information                                   |
| `403` | `KYC_REQUIRED`                    | Read verification status and required action                        |
| `403` | `VERIFICATION_REQUIRED`           | Complete the approved, operation-bound verification flow            |
| `403` | `DESTINATION_NOT_ALLOWED`         | Select an eligible destination; do not retry unchanged              |
| `404` | `RESOURCE_NOT_FOUND`              | Resource unavailable in the authenticated scope                     |
| `409` | `QUOTE_EXPIRED`                   | Obtain a new quote and fresh confirmation                           |
| `409` | `FEE_CHANGED`                     | Refresh the route, show the new fee, and submit again               |
| `409` | `QUOTE_ALREADY_USED`              | Recover the existing operation; do not submit another quote blindly |
| `409` | `INSUFFICIENT_BALANCE`            | Refresh available balances                                          |
| `409` | `MARKET_UNAVAILABLE`              | Refresh market state; no automatic price substitution               |
| `409` | `NETWORK_UNAVAILABLE`             | Refresh route availability                                          |
| `409` | `CONFLICT`                        | Read current resource state before further action                   |
| `400` | `IDEMPOTENCY_KEY_REQUIRED`        | Missing key rejected before execution                               |
| `400` | `IDEMPOTENCY_KEY_INVALID`         | Correct invalid key format before submission                        |
| `409` | `IDEMPOTENCY_KEY_REUSED`          | Investigate different request content using the same key            |
| `409` | `IDEMPOTENCY_REQUEST_IN_PROGRESS` | Wait/recover the original operation                                 |
| `429` | `RATE_LIMIT_EXCEEDED`             | Honor `Retry-After` and back off                                    |
| `503` | `SERVICE_UNAVAILABLE`             | Retry reads or the identical keyed command safely                   |
| `500` | `INTERNAL_SERVER_ERROR`           | Retain request ID; treat write outcome as potentially uncertain     |


Branch on `errorCode`, not exact message text. Field-level `details` must contain
only safe validation information, never token contents or private provider data.

### 11.2 Replay example


| Attempt                          | Idempotency key     | `X-Request-Id` | Response                                                 |
| -------------------------------- | ------------------- | -------------- | -------------------------------------------------------- |
| Initial expired-quote submission | `order-example-001` | `request-A`    | Stored `409`, body `requestId=request-A`                 |
| Identical retry                  | `order-example-001` | `request-B`    | Same stored `409` and body; `Idempotency-Replayed: true` |


The symbolic request IDs in this table stand for server UUIDs. The body retains
the original timestamp. A fresh quote and deliberate new submission require a
new key; changing a timed-out request's key is not a recovery strategy.

## 12. Rate Limits, Retries, and Uncertain Results

Rate limits and recommended polling intervals are environment-specific. FortX
returns `Retry-After` in integer seconds on HTTP `429`. Use bounded backoff
with jitter where appropriate and stop automatic retry loops on deterministic
errors.

Safe recovery sequence:

1. Keep the exact command request, customer context, and idempotency key locally
  in appropriately protected pending-operation state; exclude auth/proof secrets.
2. On timeout, do not infer whether execution occurred.
3. If an operation ID is known, read its detail. Otherwise retry the identical
  command with the same key while within the retention/recovery contract.
4. An in-progress response means wait/recover, not create another operation.
5. Use a valid Keycloak session.
6. Beyond safe replay retention or when uncertainty persists, require authoritative
  recovery. Similar amount/time history entries alone cannot prove identity.

Start with polling rather than requiring SSE/WebSockets. Poll indicative rates
according to freshness, pending operations while relevant screens are active,
and KYC while awaiting an outcome. Refresh `/me` and balances when operation
state changes and when the app resumes/reconnects. Stop terminal-operation polling.
Background/mobile limitations mean backend work must never depend on polling.

Keep the last known state visibly stale during connectivity loss. Do not show
a completed operation as failed because a follow-up GET failed. Debounce quote
requests and discard late responses for inputs that the customer has changed.

## 13. Security Requirements

- Enforce workspace/customer isolation on every resource, filter, replay, and
event, including UUID guessing and cross-session retries.
- Validate authorization and eligibility server-side; the UI is not a policy engine.
- Bind quotes to the customer and immutable business values. A quote ID alone
is not authorization, and financial commands must not trust client prices.
- Preserve custody approval, exact payload binding, signing authorization, expiry,
and replay protection in downstream integration; do not bypass them for UX speed.
- Use TLS, approved origins/redirects, safe token storage, and server-side session
validation. Define CSRF protections if cookie-based web sessions are introduced.
- Never send credentials, access/refresh tokens, SDK tokens, verification proofs,
signing material, or unredacted provider payloads to logs, Redis, or analytics.
- Deduplicate provider observations and execution results against durable business
state. Redis delivery or provider acknowledgment is not customer completion.
- Use exact arithmetic and transactional reservations. Preserve an auditable ledger
for credits, debits, fees, releases, and any correction.
- Do not expose internal risk investigations or provider credentials in errors.
- Do not assume EVM address, fee, finality, or token behavior for Tron or Bitcoin.

## 14. Integration Checklist

### 14.1 Before development

- Confirm endpoint and field names against the release OpenAPI contract.
- Configure supported assets, networks, markets, and withdrawal fee rates.
- Configure Keycloak clients, origins, redirect URIs, and sandbox customer accounts.
- Obtain enabled catalogs, amount precision, and route limits. Do not require a deposit confirmation count.
- Define which KYC/account states permit each operation.

### 14.2 Required sandbox acceptance cases


| Area           | Required cases                                                                                                                                                 |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Authentication | Valid/expired tokens, refresh/logout, wrong issuer/audience, disabled customer                                                                                 |
| Isolation      | Other customer/workspace IDs and idempotency keys cannot reveal or mutate resources                                                                            |
| KYC            | SDK exit is not approval; stale/duplicate provider events; action-required and rejected states                                                                 |
| Catalog/rates  | Disabled pair/route, null/stale price, same symbol on distinct assets                                                                                          |
| Amounts        | Zero/negative/exponent/overprecision rejection; exact large amounts and step limits                                                                            |
| Quotes         | Expiry, changed input, late quote responses, cross-customer quote, unknown fields                                                                              |
| Orders         | Fixed accepted amounts, exact reservation, one-time quote consumption, concurrent spending                                                                     |
| Idempotency    | Same request replay, different-body conflict, concurrent retry, refresh across attempts                                                                        |
| Error replay   | Original body ID/timestamp preserved; new header ID; deterministic versus transient errors                                                                     |
| Recovery       | Lost response before/after commit, app restart, unknown provider result, retention boundary                                                                    |
| Deposits       | Repeated address requests, memo/network validation, duplicate observation, review, reorganization                                                              |
| Withdrawals    | Recipient amount equals the amount sent; submitted fee must match the current rate or the request fails with `FEE_CHANGED`; failed send releases the full lock |
| Accounting     | Available, Locked, Unconfirmed, and Frozen do not overlap and are never negative; no duplicate credit or treasury-sweep customer deposit                       |
| History        | Every filter; ASC/DESC ties; fixed-dataset paging; scoped totals; no treasury-only rows                                                                        |
| Frontend       | Offline/resume, accessible errors, expired confirmation, no duplicate submit on remount                                                                        |


Run these cases in sandbox before production. Use synthetic operations only;
do not validate retries by sending real customer funds.

## 15. Troubleshooting

### Authentication works in Keycloak but the API returns 401

Check the access-token audience, issuer, expiry, and approved client configuration.
Do not substitute an ID token for the access token.

### KYC is approved but a financial command is forbidden

Read `/me` and the safe error code. Verification is one eligibility input; account
restrictions, policy, route availability, and limits are independent.

### The displayed market rate differs from the conversion quote

Indicative pricing is not a customer offer. Quotes include applicable spread,
fee treatment, size, and validity. Display the quote amounts on confirmation.

### A retry returns an old order status

A creation replay returns the original response. For a customer order that
response is already `completed` or `failed`. GET the order if the replay body is
unavailable, then refresh balances. Treat `completed` as credited when the
response or a GET shows that status.

### The order request timed out

Retry the same order with the same idempotency key. If the transaction
committed, the replay is `completed` or `failed` and the customer balances are
final. Do not submit a second order, and do not treat a missing response as a
failure. A withdrawal can still be reserved after acceptance; recover that
withdrawal the same way, without changing its key.

### A failed withdrawal still shows a fee

A failed withdrawal returns the recipient amount and the fee to Available. If the screen still shows a fee, it is showing the lock from before the failure. Refresh the withdrawal. `failed` means the customer was not charged.

## 16. Versioning and compatibility

Use additive response evolution inside `v1`. Renaming paths, changing amount
units, altering fee semantics, changing quote commitment, or changing the meaning
of terminal statuses requires a new path prefix, as in Section 1.1. Do not map
unknown states to success. Web, iOS, and Android must follow the same server
contract.

When OpenAPI and this guide differ, OpenAPI for your release environment wins.
Report discrepancies to FortX before production integration.