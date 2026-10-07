# Partner API Integration Guide

Status: Implemented interface guide (sections 1-16), with a proposed exchange integration extension (section 17)

API version: `v1`

Last reviewed: 2026-09-18

Exchange integration proposal added: 2026-09-29

## 1. Purpose

The FortVault Partner API allows an approved partner system, such as an exchange,
to read customer custody data and initiate or review supported custody actions.
This guide explains the integration workflow, security model, and operational
behavior. The Partner API Swagger document remains the authoritative reference
for endpoint paths, request fields, response fields, and examples.

Use both resources during implementation:

- Partner API Swagger UI: `<FORTVAULT_API_URL>/partner-api/docs`
- Partner API OpenAPI JSON: `<FORTVAULT_API_URL>/partner-api/openapi.json`
- Partner API base path: `<FORTVAULT_API_URL>/partner-api/v1`

The dashboard Swagger document at `<FORTVAULT_API_URL>/api/docs` contains the
dashboard's internal API and is not the Partner API contract.

[Section 17](#17-planned-exchange-integration) outlines proposed calls for
partner planning. They are not available endpoints or a committed release
contract. Existing endpoint and scope tables describe the implemented interface
only; the exchange extension requires implementation and an agreed OpenAPI
specification before integration begins.

## 2. Integration Model

Every Partner API request is scoped to the workspace that owns the API client.
The caller does not send a partner or workspace ID. FortVault derives the
workspace from the authenticated API client and applies that scope on the
server.

An integration uses two independent identities:

1. **API client identity:** An Ed25519 key pair authenticates each HTTP request.
   FortVault stores the public key. The partner keeps the private key.
2. **Action signer identity:** A FortVault user wallet signs action intent using
   EIP-712. FortVault verifies that the wallet belongs to a user in the same
   workspace and that the user's role permits the requested operation.

An API client's scope does not replace a user's role permission. For a write
operation, both authorization layers must pass.

## 3. Onboarding

### 3.1 Prerequisites

Before calling the Partner API, obtain or configure:

- The FortVault environment base URL.
- An Ed25519 key pair dedicated to the API client.
- The API Client ID shown in **Settings > API Management**.
- The scopes required by the integration.
- A FortVault action-signing user for each required operational role.
- The action signer's EVM wallet and secure signing mechanism.
- The workspace's action and approval policies.

Do not reuse the action signer's EVM key as the API authentication key.

### 3.2 Register an API client

1. Generate an Ed25519 key pair in the partner's secure environment.
2. Keep the private key in a secret manager, HSM, or equivalent protected
   signing boundary.
3. In FortVault API Management, create an API client and provide its public key.
4. Select only the scopes that the client needs.
5. Complete any approval required by the workspace policy.
6. Record the resulting API Client ID.

FortVault does not return or store the API client's private key. The API Client
ID is a public identifier, not a secret. It identifies which registered public
key FortVault must use to verify the request JWT.

### 3.3 Suggested separation of duties

Use separate API clients and action-signing users when initiation and approval
must be operationally separated:

| Identity    | Typical API scopes                              | Typical role permissions                   |
| ----------- | ----------------------------------------------- | ------------------------------------------ |
| Read client | Resource `*:read` scopes only                   | Not applicable to read endpoints           |
| Initiator   | Resource `*:read` and `*:actions:initiate` scopes | Corresponding action `initiate` permissions  |
| Approver    | Resource `*:read` and `*:actions:review` scopes | Corresponding action `approve` permissions |

The exact approval count and mandatory roles come from the workspace's on-chain
policy. Do not hard-code the number of approvals in the integration.

### 3.4 Revoke an API client

An authorized dashboard user can revoke an active API client from **Settings >
API Management** by opening the row overflow menu and selecting **Revoke**.
This operation requires dashboard permission `api_clients:revoke`, is scoped to
the user's workspace, and takes effect immediately. It is not an approval
action and cannot be reversed; register a new API client when replacement is
required.

The dashboard calls `POST /api-clients/{id}/revoke` on the authenticated
internal API. This is not a Partner API endpoint and cannot be called using the
API client's own Partner API JWT. After revocation, requests signed for that
client fail authentication. Integrators should remove the corresponding
private key from their secret store according to their key-retirement policy.

## 4. HTTP Authentication

### 4.1 Bearer JWT

Every request requires a newly signed JWT:

```http
Authorization: Bearer <jwt>
```

The JWT is signed with the API client's Ed25519 private key. Its protected
header must contain:

```json
{
  "alg": "EdDSA",
  "typ": "JWT",
  "kid": "<API_CLIENT_ID>"
}
```

Its claims must contain:

```json
{
  "iss": "<API_CLIENT_ID>",
  "sub": "<API_CLIENT_ID>",
  "aud": "fortvault-partner-api",
  "iat": 1788307200,
  "exp": 1788307260,
  "jti": "f4b49dd0-18ba-4d25-a9e4-7d88cf46ae25"
}
```

Requirements:

- `alg` must be exactly `EdDSA`.
- `typ` must be exactly `JWT`.
- `kid`, `iss`, and `sub` must equal the API Client ID.
- `aud` must match the audience configured by the FortVault environment. Its
  default is `fortvault-partner-api`.
- `iat` and `exp` are Unix timestamps in seconds.
- `exp` must be later than `iat`.
- Token lifetime must not exceed the server maximum. The current default is
  300 seconds; 60 seconds is recommended.
- `jti` must be unique and at least 16 characters long.

The current default clock-skew allowance is 30 seconds. Keep integration hosts
synchronized with a reliable time source.

### 4.2 Replay protection

A JWT is single-use. FortVault consumes its `jti` when authenticating the
request. Reusing the same JWT, including for a retry, is rejected as a replay.

Generate a new JWT with a new `jti` for every HTTP attempt.

### 4.3 Idempotency for write requests

Every Partner API write request requires an idempotency key in addition to a
fresh JWT:

```http
Authorization: Bearer <new-jwt-for-this-attempt>
Idempotency-Key: vault-create-550e8400-e29b-41d4-a716-446655440000
```

This requirement applies to every Partner API `POST`, `PUT`, `PATCH`, and
`DELETE` endpoint. It does not apply to `GET` requests.

An idempotency key must contain 8 through 255 ASCII letters, numbers, periods,
underscores, colons, or hyphens. Generate a new unpredictable key for each
logical write operation. Keep that key when retrying the same operation, but
generate a new JWT and `jti` for every HTTP attempt.

Keys are isolated by workspace and API Client ID and retained for 24 hours:

- Same key and same method, path, query, and body: FortVault returns the stored
  response without executing the operation again.
- Same key with any different request field: FortVault returns
  `IDEMPOTENCY_KEY_REUSED` with HTTP `409`.
- Concurrent request while the first is running: FortVault returns
  `IDEMPOTENCY_REQUEST_IN_PROGRESS` with HTTP `409`, before comparing request
  contents. Completed retries are checked for a matching request hash.
- A replayed response includes `Idempotency-Replayed: true`.
- Every attempt receives a fresh `X-Request-Id` response header, including
  replays. This header is not part of the stored response body.
- Successful responses and deterministic `4xx` responses are replayed.
- New deterministic-error records preserve the complete public envelope, including
  the original `requestId` and `timestamp`; retries are still authenticated and
  audited separately. Legacy partial error records use current request metadata
  because the original complete envelope was not stored.
- Business changes, outgoing durable outbox messages, and the saved response
  now commit in one database transaction. Failure before commit rolls them all
  back; retrying the identical request with the same key is safe. If the commit
  succeeded but its HTTP response was lost, that retry returns the saved result.
- A deterministic `4xx` rolls back business changes before recording the error.
  Authentication/authorization failures before the mutation interceptor and
  idempotency-key conflicts are not recorded as mutation responses.
- A `5xx` or connection loss does not tell the client whether commit succeeded.
  Retry with the same key/body and a fresh JWT, not a new operation key.
- Legacy `processing` records from the earlier non-atomic implementation remain
  uncertain. They return `IDEMPOTENCY_REQUEST_IN_PROGRESS` even after expiry.
  An operator must reconcile the request against its business records/outbox;
  do not delete the reservation or switch keys without confirming the outcome.

After a completed record's 24-hour retention expires, the same key may execute
again and must not be used as a permanent business identifier. This expiry rule
does not reclaim uncertain `processing` records.

Deployment note: drain in-flight mutations and replace all old backend instances
before accepting writes with the new implementation. Mixed old/new writers do
not share the atomic transaction/locking contract. This change requires no new
table or migration; it reuses the existing idempotency and outbox tables. It does
not repair old uncertain requests. Competing approve/reject/cancel operations,
automatic approval and expiration also serialize on a tenant-scoped PostgreSQL
action row lock. The waiting review reloads current state and approvals; it cannot
overwrite a committed terminal decision. A terminal-state conflict returns 409.
A non-final approval leaves the action pending, so a subsequent authorized
cancellation remains possible. The lock lasts through database commit, not Redis
delivery or downstream execution. Outbox delivery remains at-least-once; consumers
must still deduplicate messages. SSE updates and expiration-scheduler hints are
emitted after commit, not stored in the outbox; refresh/startup reconciliation
is still needed if those hints are lost.

### 4.4 Node.js JWT example

This example uses Node.js built-ins and a PEM-encoded Ed25519 private key:

```javascript
import { randomUUID, sign } from "node:crypto";

const base64url = (value) => Buffer.from(value).toString("base64url");

export function createPartnerApiJwt({ clientId, privateKeyPem, audience }) {
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: "EdDSA", typ: "JWT", kid: clientId };
  const claims = {
    iss: clientId,
    sub: clientId,
    aud: audience,
    iat: now,
    exp: now + 60,
    jti: randomUUID(),
  };

  const signingInput = [
    base64url(JSON.stringify(header)),
    base64url(JSON.stringify(claims)),
  ].join(".");
  const signature = sign(null, Buffer.from(signingInput), privateKeyPem);

  return `${signingInput}.${signature.toString("base64url")}`;
}
```

Never log the JWT, private key, action-signing key, or full authorization header.

## 5. Scopes and Endpoints

### 5.1 Read endpoints

| Scope                                 | Method and path       | Purpose                           |
| ------------------------------------- | --------------------- | --------------------------------- |
| `customers:read`                      | `GET /customers`      | List workspace customers          |
| `customers:read`                      | `GET /customers/{id}` | Get one customer                  |
| `vaults:read`                         | `GET /vaults`         | List regular workspace vaults     |
| `vaults:read`                         | `GET /vaults/{id}`    | Get one regular workspace vault   |
| `vaults:read`                         | `GET /vault-types`    | List available vault types        |
| `assets:read`                         | `GET /assets`         | List workspace-enabled assets     |
| `assets:read`                         | `GET /currencies`     | List workspace-enabled currencies |
| `assets:read`                         | `GET /chains`         | List workspace-enabled chains     |
| `addresses:read` plus entity scope    | `GET /addresses`      | List vault addresses              |
| `balances:read` plus entity scope     | `GET /balances`       | List exact vault balances         |
| `transactions:read` plus entity scope | `GET /transactions`   | List vault transaction movements  |
| `whitelist-addresses:read` | `GET /whitelist-addresses` | List persisted WL records |
| `whitelist-addresses:read` | `GET /whitelist-addresses/{id}` | Get one active or archived WL record |
| Resource read scope                   | `GET /actions`        | List authorized action summaries  |
| Resource read scope                   | `GET /actions/{id}`   | Get one authorized action         |
| Resource read plus operation scope    | `POST /actions/{id}/typed-data` | Prepare canonical operation typed data |
| None (results filtered by resource read scopes) | `GET /action-types` | List authorized action types |
| None                                  | `GET /capabilities`   | Get this client's capabilities    |
| None                                  | `GET /version`        | Get the Partner API version       |

`GET /action-types`, `GET /capabilities`, and `GET /version` still require a valid Partner API JWT.
"None" means that no additional business scope is required.

### 5.2 Write endpoints

| Scope                      | Method and path                  | Purpose                              |
| -------------------------- | -------------------------------- | ------------------------------------ |
| `customers:create`         | `POST /customers`                | Create a customer and customer vault |
| `vaults:create`            | `POST /vaults`                   | Create a regular workspace vault     |
| `addresses:actions:initiate` | `POST /generate-address-actions` | Initiate address generation          |
| `transfers:actions:initiate` | `POST /transfer-actions`         | Initiate a transfer                  |
| `transfers:actions:initiate` plus resource read scopes | `POST /transfer-actions/typed-data` | Prepare transfer initiation from IDs; see section 10.0 for required read scopes |
| `whitelist-addresses:read` plus `whitelist-addresses:actions:initiate` | `POST /whitelist-address-actions` | Initiate WL creation |
| `whitelist-addresses:read` plus `whitelist-addresses:actions:initiate` | `PUT /whitelist-addresses/{id}/archive` or `/activate` | Initiate WL status change |
| `vaults:read` plus `vaults:actions:initiate` | `PUT /vaults/{id}/archive` or `/activate` | Initiate regular-vault status change |
| `customers:read` plus `customers:actions:initiate` | `PUT /customers/{id}/archive` or `/activate` | Initiate customer status change |
| `addresses:read` plus `addresses:actions:initiate` | `PUT /vault-address-assets/{id}/archive` or `/activate` | Initiate address-asset status change |
| Resource read plus `*:actions:review` | `POST /actions/{id}/approve` | Approve an action |
| Resource read plus `*:actions:review` | `POST /actions/{id}/reject`  | Reject an action  |
| Resource read plus `*:actions:initiate` | `POST /actions/{id}/cancel`  | Cancel an action as its initiator |

The entity scope is selected from the requested or source vault:

- Customer vault: `customers:read`.
- Regular workspace vault: `vaults:read`.

Vault creation requires `vaults:create`. It creates only standalone regular
vaults; vault types reserved for customers are rejected. Customer vaults are
created through the customer workflow, not `POST /vaults`.

Customer creation requires `customers:create`. `POST /customers` accepts:

| Field         | Type   | Required | Rules                                                |
| ------------- | ------ | -------- | ---------------------------------------------------- |
| `code`        | string | Yes      | Non-empty unique customer code within the workspace  |
| `firstName`   | string | No       | Non-empty when supplied                              |
| `lastName`    | string | No       | Non-empty when supplied                              |
| `email`       | string | No       | Valid email address when supplied                    |
| `phoneNumber` | string | No       | Non-empty when supplied                              |
| `notes`       | string | No       | Non-empty and at most 2,000 characters when supplied |

The operation creates both the customer and its customer vault atomically using
the workspace's configured customer vault type. It returns `id`, `vaultId`,
`code`, `firstName`, `lastName`, `email`, `phoneNumber`, `status`, `createdAt`, and
`updatedAt`. The response does not expose internal partner, vault, balance, or
audit fields.

Action authorization uses resource-specific scope sets:

| Actions | Read | Initiate or cancel | Approve or reject |
| ------- | ---- | ------------------ | ----------------- |
| Generate address; archive/activate a vault or customer address asset | `addresses:read` | `addresses:actions:initiate` | `addresses:actions:review` |
| Transfer | `transfers:read` | `transfers:actions:initiate` | `transfers:actions:review` |
| Create or archive/activate a whitelist address | `whitelist-addresses:read` | `whitelist-addresses:actions:initiate` | `whitelist-addresses:actions:review` |
| Archive/activate a regular vault | `vaults:read` | `vaults:actions:initiate` | `vaults:actions:review` |
| Archive/activate a customer | `customers:read` | `customers:actions:initiate` | `customers:actions:review` |
| Archive/activate an exchange account | `exchange-accounts:read` | `exchange-accounts:actions:initiate` | `exchange-accounts:actions:review` |

Action initiation uses `actions:initiate` in both API scope identifiers and the dashboard. There is no generic `actions:read`, `actions:approve`,
`actions:reject`, or `actions:cancel` scope. The backend resolves the action
resource from the authoritative record. Customer lifecycle and regular-vault
lifecycle actions share the `vault_status_change` action type but use separate
scope sets. The workspace policy and signer permissions remain independently
enforced.

### 5.3 Archive and activate endpoints

Vault, customer, and vault-address-asset archive/activate requests create
actions. They do not change the resource status directly:

```http
PUT /partner-api/v1/vaults/{vaultId}/archive
PUT /partner-api/v1/vaults/{vaultId}/activate
PUT /partner-api/v1/customers/{customerId}/archive
PUT /partner-api/v1/customers/{customerId}/activate
PUT /partner-api/v1/vault-address-assets/{vaultAddressAssetId}/archive
PUT /partner-api/v1/vault-address-assets/{vaultAddressAssetId}/activate
Authorization: Bearer <NEW_JWT>
Idempotency-Key: <UNIQUE_OPERATION_KEY>
Content-Type: application/json
```

All six endpoints accept the same HTTP body:

```json
{
  "signedPayload": "<SERIALIZED_EIP_712_TYPED_DATA>",
  "signature": "<EIP_712_SIGNATURE>",
  "comment": "Optional operational reason"
}
```

The following are builder inputs, not literal EIP-712 message keys. Section
8.3.1 specifies the exact signed field names and order. Inputs must match the route operation:

- Regular vault: `operation`, `scope: "vault"`, authoritative `vaultName`,
  `customerName: null`, and the normalized comment.
- Customer: `operation`, `scope: "customer"`, `vaultName: null`, authoritative
  customer display name, and the normalized comment.
- Vault address asset: `operation`, authoritative vault/customer display name,
  asset symbol, chain name, blockchain address, and normalized comment.

The ID in `/vault-address-assets/{id}` is the `id` returned by
`GET /addresses?vaultId=<VAULT_ID>`. It identifies the vault-address-asset
association; it is not the catalog `assetId` and not the blockchain address.

The EIP-712 signer must be an active user in the same workspace. Vault
requests require signer permission `vaults:actions:initiate`; customer
requests require `customers:actions:initiate`. Address-asset requests require
the initiation permission of their owner: `vaults:actions:initiate` for regular
vault assets or `customers:actions:initiate` for customer assets. The backend
resolves ownership from stored records. `vaults:update` and `customers:update`
alone no longer authorize these requests. Workspace policy then determines whether
the action executes immediately or waits for review.

The response contains `action` and sanitized `statusChange` objects. Save
`action.id` and monitor it through `GET /actions/{id}` using the same resource
read scope. HTTP `409` means the current resource status does not permit the
requested operation. Replays use the idempotency rules in section 4.3.

### 5.3.1 Complete status-change success responses

All six initiation endpoints return **HTTP 200** with the following serialized
shape. Examples use synthetic metadata and show pending actions; a zero-approval
policy can execute immediately and return `action.status: "approved"` instead.
HTTP success with `"pending"` means the request was created, not that the target
has already been archived/activated. Preserve `action.id` for review and tracking.

**Customer archive:**

```json
{
  "action": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "partnerId": "7f4b8a00-2258-4dc5-9ce1-cc125f50d391",
    "typeId": "9a19ef4d-7402-4476-9efe-3668d878c232"
  },
  "statusChange": {
    "operation": "archive",
    "scope": "customer",
    "vaultId": "6c3ac4c9-a562-4913-9060-97e39d471bc7",
    "vaultName": "Customer custody vault",
    "customerName": "Alice Example"
  }
}
```

**Regular-vault activation:**

```json
{
  "action": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "partnerId": "7f4b8a00-2258-4dc5-9ce1-cc125f50d391",
    "typeId": "9a19ef4d-7402-4476-9efe-3668d878c232"
  },
  "statusChange": {
    "operation": "activate",
    "scope": "vault",
    "vaultId": "6c3ac4c9-a562-4913-9060-97e39d471bc7",
    "vaultName": "Treasury",
    "customerName": null
  }
}
```

**Regular-vault asset archive:**

```json
{
  "action": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "partnerId": "7f4b8a00-2258-4dc5-9ce1-cc125f50d391",
    "typeId": "9a19ef4d-7402-4476-9efe-3668d878c232"
  },
  "statusChange": {
    "operation": "archive",
    "vaultId": "6c3ac4c9-a562-4913-9060-97e39d471bc7",
    "vaultAddressAssetId": "34cf32f0-77cd-44d9-89f5-ef96568210d7",
    "vaultName": "Treasury",
    "customerName": null,
    "address": "0x1111111111111111111111111111111111111111",
    "assetSymbol": "USDC"
  }
}
```

**Customer asset activation:**

```json
{
  "action": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "partnerId": "7f4b8a00-2258-4dc5-9ce1-cc125f50d391",
    "typeId": "9a19ef4d-7402-4476-9efe-3668d878c232"
  },
  "statusChange": {
    "operation": "activate",
    "vaultId": "6c3ac4c9-a562-4913-9060-97e39d471bc7",
    "vaultAddressAssetId": "34cf32f0-77cd-44d9-89f5-ef96568210d7",
    "vaultName": "Customer custody vault",
    "customerName": "Alice Example",
    "address": "0x1111111111111111111111111111111111111111",
    "assetSymbol": "USDC"
  }
}
```

For the opposite operation on any target, the same fields are returned with
`operation` set to `archive` or `activate` and newly created action identifiers.
The serialized field-presence rules are:

| `statusChange` field | Customer / regular-vault change | Asset-address change |
| --- | --- | --- |
| `operation` | Present | Present |
| `scope` | `customer` or `vault` | Omitted |
| `vaultId` | Present (underlying vault, also for a customer) | Present |
| `vaultAddressAssetId` | Omitted | Present |
| `whitelistAddressId` | Omitted | Omitted |
| `vaultName` | Stored vault name, including for customer scope | Stored vault name (or `null` if missing) |
| `customerName` | Name, or `null` if no customer/name | Name, or `null` if no customer/name |
| `address` | Omitted | Present |
| `assetSymbol` | Omitted | Present |

Absent metadata becomes `undefined` in the DTO and is **omitted from JSON**;
explicit `null` values remain `null`. Do not require all nullable Swagger fields
to appear. In particular, a customer response's `vaultName` is present even
though that field is omitted from its initiation signature.

The initiation response does not include `customerId`, `fromStatus`,
`toStatus`, `walletType`, `assetId`, `chainName`, `chainRef`, or the
comment inside `statusChange`. Use action detail for the documented historical
status transition fields; do not assume its `details` schema is this response's
`statusChange` schema.

### 5.3.2 Reading current resource status

All resources with Partner API archive/activate endpoints expose a required,
non-null `status` string: `active` or `archived`.

| Resource | Read endpoint | Status source |
| --- | --- | --- |
| Customer | `GET /customers` (`data[]`) and `GET /customers/{id}` | Customer vault's current lifecycle status |
| Regular vault | `GET /vaults` (`data[]`) and `GET /vaults/{id}` | Vault's current lifecycle status |
| Address-asset association | `GET /addresses?vaultId={vaultId}` (`data[]`) | Individual address-asset association's current lifecycle status |

Customer creation (`POST /customers`) returns the same customer DTO, including
`status`. For example, an archived customer detail response is:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "vaultId": "6c3ac4c9-a562-4913-9060-97e39d471bc7",
  "code": "customer-001",
  "firstName": "Alice",
  "lastName": "Example",
  "email": null,
  "phoneNumber": null,
  "status": "archived",
  "createdAt": "2026-09-01T00:00:00.000Z",
  "updatedAt": "2026-09-18T00:00:00.000Z"
}
```

The customer list has no status filter and can include both active and archived
customers with non-deleted associated vaults. Read `status`; presence in the list
or an HTTP 200 does not mean the customer is active. Use `customers:read` for
these customer reads. Do not query `GET /vaults/{customer.vaultId}` instead:
that endpoint excludes customer vaults. Address-asset status is independent of
its owner's lifecycle and must not be used to infer customer or vault status.

A pending archive/activate action does not itself change the resource status.
After execution, reread the resource to obtain its current state. Action
`details.fromStatus` / `details.toStatus` describe a historical transition, not
necessarily the current state after subsequent actions. Do not send mutations
merely to probe status.

### 5.4 Action response details

`GET /actions` returns lightweight action summaries. It does not include the
action-specific `details` object. It supports these optional query filters in
addition to `skip`, `take`, and `order`:

| Query field  | Allowed values                               | Description                          |
| ------------ | -------------------------------------------- | ------------------------------------ |
| `actionType` | Any action type returned by `GET /action-types` | Return only the selected action type |
| `status`     | `pending`, `approved`, `canceled`, `expired` | Return only the selected status      |

The filters can be combined. For example:

```http
GET /partner-api/v1/actions?actionType=generate_address&status=pending&skip=0&take=50
GET /partner-api/v1/actions?actionType=transfer&status=approved&skip=0&take=50
```

The backend applies resource authorization before count and pagination. An
unfiltered request returns only actions visible through the client's resource
read scopes. A filter for an unauthorized action resource is rejected. There
are no separate Partner API list endpoints for individual action types.

`GET /actions/{id}` returns the summary fields, approval count, expiration, and
a sanitized `details` object whose shape depends on `entityType`:

Common action fields:

| Field               | Type               | Description                                                 |
| ------------------- | ------------------ | ----------------------------------------------------------- |
| `id`                | UUID               | Action ID                                                   |
| `entityId`          | UUID or `null`     | ID of the primary entity associated with the action         |
| `entityType`        | string             | Selects the shape of `details`                              |
| `status`            | string             | Action lifecycle status                                     |
| `description`       | string or `null`   | Human-readable action description                           |
| `actionType`        | string             | Requested operation type                                    |
| `createdAt`         | ISO 8601 date-time | Creation time                                               |
| `updatedAt`         | ISO 8601 date-time | Last update time                                            |
| `expirationSeconds` | integer            | Configured action lifetime in seconds; detail endpoint only |
| `approvalCount`     | integer            | Number of recorded approvals; detail endpoint only          |
| `details`           | object or `null`   | Sanitized entity-specific fields; detail endpoint only      |

Entity-specific `details` fields:

| `entityType`                      | Exact fields                                                                                                                                                                             |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `generate_address`                | `vaultId`, `targetType`, `customerId`, `walletType`, `assets`                                                                                                                            |
| `transfer`                        | `fromAddress`, `fromName`, `fromVaultId`, `toAddress`, `toName`, `toVaultId`, `assetId`, `symbol`, `chainRef`, `chainName`, `amount`, `transferStatus`, `txHash`                         |
| `whitelist_address`               | `name`, `address`, `assetId`, `symbol`, `chainRef`, `chainName`, `customerId`, `accessType`, `custodyType`, `ownershipType`                                                              |
| `vault_status_change`             | `vaultId`, `customerId`, `walletType`, `operation`, `fromStatus`, `toStatus`                                                                                                             |
| `vault_asset_status_change`       | `vaultAddressAssetId`, `vaultId`, `customerId`, `address`, `assetId`, `symbol`, `chainRef`, `chainName`, `operation`, `fromStatus`, `toStatus`                                           |
| `whitelist_address_status_change` | `whitelistAddressId`, `name`, `address`, `assetId`, `symbol`, `chainRef`, `chainName`, `customerId`, `accessType`, `custodyType`, `ownershipType`, `operation`, `fromStatus`, `toStatus` |
| `exchange_account_status_change`  | `exchangeAccountId`, `exchangeName`, `accountName`, `operation`, `fromStatus`, `toStatus`                                                                                                |
| `api_client_create`               | `name`, `algorithm`, `publicKeyFingerprint`, `scopes`                                                                                                                                    |

Each item in `generate_address.details.assets` contains:

| Field       | Type             |
| ----------- | ---------------- |
| `assetId`   | UUID or `null`   |
| `symbol`    | string or `null` |
| `chainId`   | UUID or `null`   |
| `chainRef`  | string or `null` |
| `chainName` | string or `null` |
| `address`   | string or `null` |
| `status`    | string or `null` |

Unless a field is an array, all fields inside `details` may be `null` when the
underlying action metadata does not contain that value. `scopes` and `assets`
are arrays and may be empty.

Action details identify vaults and customers by ID. They do not return
`vaultName` or `customerName`. The API also never returns action signatures,
signed payloads, API public keys, private keys, raw MPC responses, or internal
action errors in `details`.

### 5.5 Whitelist address (WL) support

The Partner API supports WL record list/detail, signed creation requests, and
signed archive/activate requests. Paths below are relative to `/partner-api/v1`.

| Operation | Method and path | Required API-client scopes | Success |
| --------- | --------------- | -------------------------- | ------- |
| List persisted records | `GET /whitelist-addresses` | `whitelist-addresses:read` | 200 |
| Read one persisted record | `GET /whitelist-addresses/{id}` | `whitelist-addresses:read` | 200 |
| Request creation | `POST /whitelist-address-actions` | `whitelist-addresses:read` plus `whitelist-addresses:actions:initiate` | 201 |
| Request archival | `PUT /whitelist-addresses/{id}/archive` | `whitelist-addresses:read` plus `whitelist-addresses:actions:initiate` | 200 |
| Request activation | `PUT /whitelist-addresses/{id}/activate` | `whitelist-addresses:read` plus `whitelist-addresses:actions:initiate` | 200 |

List filters are optional `status` (`active` or `archived`), `accessType`
(`all`, `internal`, `customer`), `customerId` (UUID), and `assetId` (UUID), plus
`skip`, `take`, and `order` from section 6. Without filters, both active and
archived records are included. Tenant and filter predicates apply before count
and pagination. The response is `{data, total, skip, take}`. Each record (and the
detail response) has exactly `id`, `name`, `address`, `assetId`, `customerId`
(UUID or null), `accessType`, `custodyType`, `ownershipType`, `status`, `createdAt`,
and `updatedAt`. Timestamps are ISO date-time strings. Missing or foreign-tenant
IDs return 404 without revealing another tenant's records.

Pending creation requests are actions, not persisted WL records. Creation and
status requests remain subject to policy approval/execution; a successful HTTP
response does not itself mean that the address is usable or its status changed.

Both `whitelist_address` (creation) and `whitelist_address_status_change`
(archive/activate) use these generic endpoints. Paths below are relative to
`/partner-api/v1`:

| Operation | Method and path | Required API-client scopes |
| --------- | --------------- | -------------------------- |
| List WL actions | `GET /actions?actionType=whitelist_address` or `GET /actions?actionType=whitelist_address_status_change` | `whitelist-addresses:read` |
| Read one WL action | `GET /actions/{actionId}` | `whitelist-addresses:read` |
| Prepare approve/reject typed data | `POST /actions/{actionId}/typed-data` | `whitelist-addresses:read` plus `whitelist-addresses:actions:review` |
| Approve or reject | `POST /actions/{actionId}/approve` or `/reject` | `whitelist-addresses:read` plus `whitelist-addresses:actions:review` |
| Prepare cancellation typed data or cancel | `POST /actions/{actionId}/typed-data` or `/cancel` | `whitelist-addresses:read` plus `whitelist-addresses:actions:initiate` |

For example, discover pending creation and status-change requests separately:

```http
GET /partner-api/v1/actions?actionType=whitelist_address&status=pending&skip=0&take=50
GET /partner-api/v1/actions?actionType=whitelist_address_status_change&status=pending&skip=0&take=50
```

Authenticate each request with a fresh JWT. These endpoints return action
records, not a whitelist-address directory; use the action `id` for subsequent
review requests. The action-specific `details` fields are listed in section 5.4.

Use the canonical typed-data preparation and signing flow in
[section 9.2](#92-approve-reject-or-cancel), selecting `approve`, `reject`, or
`cancel` as the operation. Mutations require an `Idempotency-Key`; typed-data
preparation does not. The exact initiation contracts follow below.

API-client scopes do not replace signing-user authorization. Initiation requires
`vaults:actions:whitelist:initiate`. Approval/rejection
requires the signing user's `vaults:actions:whitelist:review` permission and the
applicable workspace policy checks. Cancellation must be signed by the original
initiator. Tenant scope and action-state checks apply to every operation.

#### 5.5.1 Exact WL initiation signing contract

All three operations use `primaryType: "Initiate"`. The domain is exactly
`{"name":"FortVault","version":"1","chainId":1}`, including numeric `chainId`
even when the address is on Tron or Bitcoin. Every message field has EIP-712
type `string`, including `TimestampMs` and the customer UUID.

Construct top-level properties in this order: `domain`, `primaryType`, `types`,
`message`. Domain properties must be ordered `name`, `version`, `chainId`.
`types` contains only `Initiate`; do not add `EIP712Domain`. Each type entry is
ordered `name`, `type`. Message properties follow the field order below.
The backend compares parsed payloads with `JSON.stringify`, so property order
matters as well as values. Send `signedPayload = JSON.stringify(typedData)` and
the wallet signature over that same typed data. Use a fresh Ed25519 JWT for HTTP
authentication separately.

`TimestampMs` is always last: current Unix milliseconds as a decimal string of
at least 13 digits, not a JSON number. Omit an absent optional field from **both**
`types.Initiate` and `message`; do not use null, an empty string, or an extra type
entry as a placeholder. No extra fields are accepted in the signed payload.

**Creation: `POST /whitelist-address-actions`**

Body fields: `name`, `address`, `assetId`, `custodyType`, `ownershipType`,
`signedPayload`, `signature`, and optional `customerId` and `accessType`.
There is no creation `comment` field. Name length is 3-30 after normalization.

| Order | Signed field | Exact value |
| ----- | ------------ | ----------- |
| 1 | `Action` | `Whitelist Address` |
| 2 | `Name` | Normalized request `name` |
| 3 | `Address` | Chain-normalized request address, as specified below |
| 4 | `Asset` | Asset `symbol` + ` on ` + chain `name`, e.g. `USDC on Ethereum` |
| 5, optional | `Customer` | The `customerId` UUID, **not** customer name or code; omit for non-customer scope |
| 6 | `Scope` | `all` -> `Global`; `internal` -> `Internal`; `customer` -> `Customer` |
| 7 | `Custody` | `self_custodied` -> `Self-Custodied`; `custodian_managed` -> `Custodian-Managed` |
| 8 | `Ownership` | `owned` -> `Owned`; `external` -> `External` |
| 9 | `TimestampMs` | Decimal milliseconds string |

With `customerId`, scope resolves to `customer`; if `accessType` is supplied it
must be `customer`, and `ownershipType` must be `external`. Without `customerId`,
scope defaults to `all`; `internal` is also allowed, but `customer` is invalid.
Omit optional request properties when unused. `custodyType` and `ownershipType`
are required even though the underlying service has internal defaults.

Creation address normalization uses the selected asset's `chainRef`:

- Trim leading/trailing whitespace.
- For `evm:*`, lowercase the valid 40-hex-character `0x` address. Sign lowercase,
  not a checksum-cased display address.
- For `bitcoin:*`, lowercase Bech32/Bech32m addresses beginning `bc1` or `tb1`.
- Preserve case for Bitcoin Base58 and Tron Base58 addresses. Never lowercase
  all chains indiscriminately. Chain-specific validity checks still apply.

Name normalization is JavaScript `value.trim().replace(/\s\s+/g, " ")`.
This collapses runs of two or more whitespace characters, not every individual
internal whitespace character. Normalize request name before signing it.

Discover asset metadata using `/assets` and `/chains` (`assets:read`). Match the
selected `assetId` and its chain; do not derive display labels from chainRef or
symbol guesses.

**Archive and activate: `PUT /whitelist-addresses/{id}/archive` or `/activate`**

Body fields: `signedPayload`, `signature`, and optional `comment` (maximum 500
characters after HTTP normalization). The target WL ID comes from the URL.

| Order | Signed field | Exact value |
| ----- | ------------ | ----------- |
| 1 | `Action` | Archive: `Archive Whitelist Address`; activate: **`Unarchive Whitelist Address`**, never `Activate Whitelist Address` |
| 2 | `Name` | Persisted WL `name`, unchanged |
| 3 | `Address` | Persisted WL `address`, unchanged |
| 4 | `Asset` | Current asset `symbol` + ` on ` + current chain `name` |
| 5, optional | `Customer` | Current customer name as defined below, **not** the UUID used at creation |
| 6, optional | `Comment` | Normalized nonblank request comment |
| 7 | `TimestampMs` | Decimal milliseconds string |

Fetch the WL record immediately before signing. For status changes, use the
stored address exactly, including any legacy casing; do not run creation-time
address normalization again. Do not include Scope, Custody, Ownership, assetId,
whitelistAddressId, operation, or status in the signed message.

For a customer-scoped record, fetch `/customers/{customerId}` (`customers:read`
required for this discovery request). Compute Customer exactly as
`[firstName, lastName].filter(Boolean).join(" ").trim()`. Omit Customer if the
result is empty or the WL has no customer. There is **no fallback to customer
code or UUID**. Do not collapse internal whitespace in persisted names.
If authoritative metadata changes before submission, fetch it again and re-sign.

Comment normalization is `comment.trim().replace(/\s\s+/g, " ")`, followed by
trimming; omitted, empty, and whitespace-only comments produce no Comment field.
For example, `"  Operational   reason  "` signs `"Operational reason"`.

**Complete payload construction examples**

The following produces the exact complete typed-data object for each operation,
including ordered `types` and `message`. Example addresses and labels are
illustrative: use discovered metadata from the target workspace.

```javascript
function initiate(fields, timestampMs) {
  const entries = fields.filter(([, value]) => value != null);
  entries.push(["TimestampMs", timestampMs]);
  return {
    domain: { name: "FortVault", version: "1", chainId: 1 },
    primaryType: "Initiate",
    types: {
      Initiate: entries.map(([name]) => ({ name, type: "string" })),
    },
    message: Object.fromEntries(entries),
  };
}

const timestampMs = Date.now().toString();
const address = "0x1111111111111111111111111111111111111111";

const creation = initiate([
  ["Action", "Whitelist Address"],
  ["Name", "Treasury"],
  ["Address", address],
  ["Asset", "USDC on Ethereum"],
  ["Customer", null], // Omitted for global scope; customer scope uses UUID here.
  ["Scope", "Global"],
  ["Custody", "Self-Custodied"],
  ["Ownership", "Owned"],
], timestampMs);

const archive = initiate([
  ["Action", "Archive Whitelist Address"],
  ["Name", "Treasury"],
  ["Address", address],
  ["Asset", "USDC on Ethereum"],
  ["Customer", null], // Customer scope uses current nonblank name here, NOT UUID.
  ["Comment", "Operational reason"],
], timestampMs);

const activate = initiate([
  ["Action", "Unarchive Whitelist Address"],
  ["Name", "Treasury"],
  ["Address", address],
  ["Asset", "USDC on Ethereum"],
  ["Customer", null],
  ["Comment", null], // Omitted when no nonblank comment was supplied.
], timestampMs);

// For the chosen operation, sign that typed-data object with the user's wallet.
// Send signedPayload: JSON.stringify(creation), archive, or activate respectively.
// Include signature, the matching request body fields, and Idempotency-Key.
```

Creation returns `{action: {id, status, typeId}, whitelistAddress: {name,
address, assetId, customerId, accessType, custodyType, ownershipType}}`. Its
`whitelistAddress` is requested metadata, not a record with an assigned ID.
After execution, retrieve the persisted record through the WL list.
Status changes return the shared `StatusChangeActionResponseDto`:
`action` contains `id`, `status`, `partnerId`, `typeId`; `statusChange` contains
`operation`, `whitelistAddressId`, `customerName` (string or null), `address`,
and `assetSymbol`. Unrelated `scope`, `vaultId`, `vaultAddressAssetId`, and
`vaultName` are omitted. Use the returned action ID for approval/rejection and
monitoring, not the WL record ID.

## 6. Pagination and Filtering

List endpoints accept:

| Parameter | Default | Rules                         |
| --------- | ------- | ----------------------------- |
| `skip`    | `0`     | Integer, minimum `0`          |
| `take`    | `50`    | Integer from `1` through `50` |
| `order`   | `DESC`  | `ASC` or `DESC`               |

### Sorting contract

The nine paginated lists below default to **DESC**. `order` changes the
direction of **every key in the listed tuple**, including secondary fields and
the final unique tie-breaker; it does not select a field. ASC means oldest to
newest for dates and ascending comparison for text/UUIDs; DESC reverses that
comparison. There is no `orderBy` parameter.

| Endpoint | Primary key | Secondary / unique tie-breaker (same direction) | Null handling | Keys exposed for client verification |
| --- | --- | --- | --- | --- |
| `/customers` | Customer `createdAt` | Customer `id` | Both non-null | Both |
| `/vaults` | Vault `createdAt` | Vault `id` | Both non-null | Both; not sorted by USD amount like the dashboard |
| `/assets` | `symbol` | `chain.name`, then asset `id` | All non-null; records missing required chain metadata are excluded | All; same ordering with or without `vaultId` |
| `/chains` | `name` | Chain `id` | Both non-null | Both |
| `/addresses` | Asset-address link `createdAt` | Link `id` | Both non-null | Both; not the underlying vault-address creation time or ID |
| `/balances` | `symbol` | `assetId` (unique within the required vault) | Both non-null | Both; amount is not a sorting key |
| `/transactions` | `COALESCE(transaction.blockTimestamp, transaction.createdAt)` | `movementId` (transaction-line UUID) | Null block time is replaced by non-null internal creation time, not grouped first/last | `blockTimestamp` and `movementId` exposed; fallback `createdAt` is not |
| `/actions` | Action `createdAt` | Action `id` | Both non-null | Both |
| `/whitelist-addresses` | Whitelist `createdAt` | Whitelist `id` | Both non-null | Both |

Transaction timestamps have different meanings:
- `blockTimestamp`: recorded blockchain block time; used when present.
- `detectedAt`: recorded detection time, nullable; **never used for sorting**.
- Internal transaction `createdAt`: backend row insertion time; used only when
  `blockTimestamp` is null. This is not transaction-line creation time and is not
  exposed in the response. A black-box client cannot fully reconstruct ordering
  for rows with null block time. Do not substitute `detectedAt` or `blockNumber`.

Catalog text (`/assets`, `/chains`, `/currencies`) uses the server JavaScript
`localeCompare` collation. Database text keys (`/balances` symbol and
`/vault-types` name) use PostgreSQL collation. Do not assume ASCII/bytewise text
ordering for mixed case, punctuation or accented names. UUID ties use UUID
ordering (equivalent to lexicographic order of canonical lowercase UUIDs).
Dates are compared at stored database precision; timestamps serialized to
milliseconds can appear equal when stored sub-millisecond values differ.

Tenant/resource authorization and applicable filters are applied before sorting
and pagination. Catalog arrays are filtered/sorted before slicing. Stable keys
make offset pagination deterministic over a **fixed dataset**, not a snapshot
across requests: concurrent inserts, deletes, updates, backfills or permission
changes can cause duplicate or omitted rows between pages. Keep filters,
principal/scopes and direction unchanged when walking a dataset.

The following unpaginated catalogs do not support `order`:

| Endpoint | Fixed order | Verification |
| --- | --- | --- |
| `/vault-types` | Internal `sortOrder ASC`, `name ASC`, `id ASC` | Non-null keys, but `sortOrder` is not exposed; complete black-box verification needs controlled fixtures |
| `/currencies` | `code ASC`, `id ASC` | Both exposed and non-null; the existing code-order claim is correct |
| `/action-types` | `generate_address`, `transfer`, `whitelist_address`, `vault_status_change`, `vault_asset_status_change`, `whitelist_address_status_change`, `exchange_account_status_change` | Exposed unique `actionType`; returns the scope-authorized subsequence in this order |

Test-client validation should use a designated, unchanged development dataset:
compare omitted `order` with explicit DESC; fetch ASC and DESC pages with the
same filters; assert monotonic tuples, unique row identifiers and concatenated
page equality with the known fixture order. Include exact primary-key ties,
multiple movements in one transaction, zero balances, and null block timestamps.
Use fixture-known internal creation times for null-block transactions and
fixture-known `sortOrder` for vault types; otherwise report these primary-order
assertions as unverifiable, not failed. Do not create transfers or mutate
production data merely to test sorting. Existing authorization and tenant
isolation assertions must remain enabled.

Customer list and detail responses include the customer's `vaultId`. Regular
vault IDs are available from `GET /vaults` and `GET /vaults/{id}`.

The `/assets` list accepts an optional `vaultId`:

- Without `vaultId`, it returns every active asset enabled for the workspace.
- With `vaultId`, it returns only assets that are not yet linked to that
  tenant-owned vault and can therefore be selected for address generation.
- An unknown vault or a vault from another workspace returns
  `RESOURCE_NOT_FOUND`.

Examples:

```http
GET /partner-api/v1/assets?skip=0&take=50&order=ASC
GET /partner-api/v1/assets?vaultId=<VAULT_ID>&skip=0&take=50&order=ASC
Authorization: Bearer <NEW_JWT>
```

Both forms require `assets:read`. Supplying `vaultId` does not require an
additional customer or vault read scope because it only narrows the asset
catalogue and does not disclose vault details.

The address, balance, and transaction lists require a `vaultId` UUID.
The selected vault must belong to the authenticated workspace. Customer vaults
require `customers:read`; regular vaults require `vaults:read`, in addition to
the endpoint's resource scope. `customerId` is not accepted as a selector. A
missing or invalid `vaultId` returns `VALIDATION_ERROR`.

Example:

```http
GET /partner-api/v1/transactions?vaultId=<VAULT_ID>&skip=0&take=50&order=DESC
Authorization: Bearer <NEW_JWT>
```

Paginated responses contain `data`, `skip`, and `take`. Some endpoints also
return `total`; consult the endpoint schema rather than assuming it is present.

## 7. Read Data and Amounts

### 7.1 Assets and chains

Each asset represents one asset deployment on exactly one chain. The same
symbol on different chains has a different `assetId`. For example, USDT on
Base Sepolia and USDT on Tron are separate assets.

```json
{
  "id": "5b7a1100-f1d1-4f16-b91d-1b22421ed234",
  "name": "USD Tether",
  "symbol": "USDT",
  "tokenAddress": "0x1111111111111111111111111111111111111111",
  "decimals": 6,
  "dustThresholdAmount": "0",
  "chain": {
    "id": "8c006c7d-c355-45eb-a11d-f221448a0622",
    "name": "Base Sepolia",
    "chainRef": "evm:84532",
    "chainType": {
      "id": "14cdb8be-b9cd-47ed-8195-49f93de6ef5f",
      "name": "evm"
    }
  }
}
```

Use `id` as the `assetId` in Partner API write requests. Chain metadata is
embedded, so address-generation integrations do not need a separate chain
catalogue request. Treat `tokenAddress` as an opaque asset identifier; native
assets may use a non-contract marker.

`GET /partner-api/v1/chains` provides independent chain discovery when an
integration needs the workspace's complete network configuration rather than
the chain attached to a selected asset. It returns only active chains configured
for the authenticated workspace and requires `assets:read`.

```http
GET /partner-api/v1/chains?skip=0&take=50&order=ASC
Authorization: Bearer <NEW_JWT>
```

Each row has this shape:

```json
{
  "id": "8c006c7d-c355-45eb-a11d-f221448a0622",
  "name": "Base Sepolia",
  "chainRef": "evm:84532",
  "chainType": {
    "id": "14cdb8be-b9cd-47ed-8195-49f93de6ef5f",
    "name": "evm"
  }
}
```

Use `chainRef` as the stable machine identifier. `name` is a display label,
while `chainType.name` identifies the protocol family such as `evm`, `bitcoin`,
or `tron`.

### 7.2 General discovery

`GET /vault-types` returns the non-customer vault types currently available for
`POST /vaults` in the workspace. It requires `vaults:read` and returns:

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "hot",
    "name": "Hot",
    "category": "vault"
  }
]
```

Each item contains exactly `id`, `code`, `name`, and `category`. `code` and `name`
are partner-defined; `category` describes behavior and uses the enum `vault`,
`customer`, or `gas`. This endpoint returns only `vault` and `gas` categories.
In `POST /vaults`, set `vaultType` to the discovered **`code`**, not `id`,
`name`, or `category`. The backend resolves that code within the authenticated
workspace. Do not hardcode `hot`: it is only an example of a partner-defined
code. For the discovery response above, submit:

```http
POST /partner-api/v1/vaults
Authorization: Bearer <NEW_JWT>
Idempotency-Key: vault-create-example-001
Content-Type: application/json
```

```json
{
  "name": "Treasury",
  "vaultType": "hot"
}
```

Creation requires `vaults:create`; discovery requires `vaults:read`.
Customer vault types are selected internally by `POST /customers` and are not
returned by this endpoint.

`GET /currencies` requires `assets:read` and returns active currencies
enabled for the workspace, ordered by `code`:

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "code": "USDT",
    "name": "USD Tether",
    "decimals": 6,
    "type": "crypto"
  }
]
```

Currency `type` is `crypto` or `fiat`. Currency IDs describe the accounting
currency; use asset IDs, not currency IDs, for address-generation and transfer
requests.

`GET /action-types` requires a valid Partner API JWT and returns only action
types visible through the client's resource read scopes. No minimum business
scope is required. A client with no business scopes, or only unrelated scopes
such as `assets:read`, receives **HTTP 200 with `[]`**, not HTTP 403. Clients
must validate this as a successful empty array, not as an error response.
This discovery behavior does not grant access to protected action resources
or operations; their resource and operation scope checks still apply.

The values can be used with `GET /actions?actionType=...`. For example, a client with
`addresses:read` and `transfers:read` can receive:

```json
[
  {
    "actionType": "generate_address",
    "supportsApproval": true,
    "supportsRejection": true,
    "expirationSeconds": 3600
  },
  {
    "actionType": "transfer",
    "supportsApproval": true,
    "supportsRejection": true,
    "expirationSeconds": 3600
  },
  {
    "actionType": "vault_asset_status_change",
    "supportsApproval": true,
    "supportsRejection": true,
    "expirationSeconds": 3600
  }
]
```

`expirationSeconds` is `null` only when the corresponding action-type
configuration is missing. Approval requirements are determined by policy for
each concrete action; `supportsApproval` does not mean every action requires an
approval.

`GET /capabilities` requires a valid Partner API JWT but no additional scope.
It returns the authenticated API client's effective scopes and the workspace's
feature flags. It never returns another client's scopes:

```json
{
  "scopes": ["assets:read", "vaults:read"],
  "features": {
    "customers": true,
    "exchanges": false,
    "apiManagement": true
  }
}
```

`GET /version` also requires only a valid Partner API JWT and returns:

```json
{
  "apiVersion": "v1",
  "policyContract": {
    "address": "0x1111111111111111111111111111111111111111",
    "chainRef": "evm:84532",
    "chainName": "Base Sepolia",
    "explorerUrl": "https://sepolia.basescan.org/address/0x1111111111111111111111111111111111111111"
  }
}
```

The policy contract metadata belongs to the authenticated workspace. Its chain
is independent of the custody chains returned by `GET /chains`. The endpoint
uses backend configuration and does not make a blockchain RPC call.

### 7.3 Balances and transaction amounts

Balances and transaction movements return exact integer strings in the asset's
smallest unit. Use the returned `decimals` value to format the amount for display.

Example:

```json
{
  "symbol": "ETH",
  "decimals": 18,
  "baseUnitAmount": "1000000000000000000"
}
```

This represents `1 ETH`. Never parse base-unit amounts with JavaScript `Number`
or another floating-point type. Use an arbitrary-precision integer or decimal
library.

### 7.3 Transaction ownership

Each transaction movement includes `sourceVaultId`, `destinationVaultId`,
`sourceCustomerId`, and `destinationCustomerId`:

- A customer vault address populates both its vault ID and customer ID.
- A non-customer workspace vault address populates its vault ID and leaves its
  customer ID as `null`.
- An external address leaves both its vault ID and customer ID as `null`.

The source fields describe `fromAddress`; the destination fields describe
`toAddress`.

Transfer creation is different: its `amount` field is a positive, non-zero
decimal string, for example `"1.5"`. FortVault validates the asset precision and
converts the value exactly.

### 7.4 Chain identity

Use `chainRef`, not a display name, as the stable chain identifier in returned
data. For example, Base Sepolia can be represented as `evm:84532`.

## 8. Action Signing

### 8.1 Why a second signature is required

The Ed25519 JWT proves which API client sent the HTTP request. The EIP-712 action
signature proves that an authorized FortVault user approved the exact business
intent. Action requests therefore contain both:

- `signedPayload`: serialized EIP-712 typed data.
- `signature`: the EVM wallet signature over that typed data.

FortVault recovers the wallet address, resolves the user inside the API client's
workspace, checks the user's role permission, and verifies the payload against
server-resolved business data.

### 8.2 EIP-712 domain

The current signing domain is:

```json
{
  "name": "FortVault",
  "version": "1",
  "chainId": 1
}
```

The domain's `chainId` is part of FortVault's signing protocol. It does not mean
that the custody action executes on Ethereum mainnet. Do not replace it with the
asset's execution-chain ID.

### 8.3 Canonical payload requirement

Action fields are human-readable but exact. They can include server-resolved
vault or customer names, normalized addresses, wallet type, asset symbol, chain
name, amount, action ID, and timestamp. Generate-address asset labels are sorted
canonically.

The submitted `signedPayload` must match the values FortVault reconstructs from
its authoritative records. A semantically similar payload with different case,
spacing, names, ordering, or address normalization is rejected.

For approval, rejection, and cancellation, call
`POST /actions/{id}/typed-data` and sign the returned `signedPayload` unchanged.
The backend resolves canonical labels and action details from authoritative
records. Clients must not reconstruct review typed data from the sanitized
`GET /actions/{id}` response.

For signed action creation, use the initiation preparation endpoints below.
The backend resolves canonical labels; do not guess labels from IDs. Existing
manual construction according to the documented signing contracts remains supported.

### 8.3.0 Server-prepared initiation typed data

All signed Partner API initiation operations now have read-only preparation.
Paths below are relative to /partner-api/v1. For status paths, operation is
exactly archive or activate; no other value is supported.

| Preparation endpoint (POST) | Body | Required scopes |
| --- | --- | --- |
| /generate-address-actions/typed-data | vaultId, assets:[{assetId}] (1-20 distinct assets) | addresses:actions:initiate, assets:read, and the owner's vaults:read or customers:read |
| /whitelist-address-actions/typed-data | name, address, assetId, custodyType, ownershipType; optional customerId, accessType | whitelist-addresses:actions:initiate, whitelist-addresses:read, assets:read; customers:read when customerId is provided |
| /vaults/{id}/{operation}/typed-data | optional comment | vaults:actions:initiate, vaults:read; also customers:read if it is a customer vault |
| /customers/{id}/{operation}/typed-data | optional comment | customers:actions:initiate, customers:read |
| /vault-address-assets/{id}/{operation}/typed-data | optional comment | addresses:actions:initiate, addresses:read, and the owner's vaults:read or customers:read |
| /whitelist-addresses/{id}/{operation}/typed-data | optional comment | whitelist-addresses:actions:initiate, whitelist-addresses:read; customers:read for a customer-scoped record |
| /transfer-actions/typed-data | source, destination, assetId, amount | See section 10.0 |

Send a fresh API JWT and Content-Type: application/json. No Idempotency-Key or
wallet signature is required for preparation. Use {} for an uncommented status
request. Do not send signature, signedPayload, partnerId, or client-supplied
display labels. Unknown fields are rejected with 400 VALIDATION_ERROR rather
than silently discarded, including nested asset/selector fields. This strict
body validation also applies to /actions/{id}/typed-data review preparation;
existing mutation endpoints retain their validation behavior.

Use vaultId wherever preparation selects an asset owner (generation and both
transfer sides), even for customer vaults. Transfer destinations select exactly
one vaultId or whitelistId; they cannot combine these or supply customerId.
Keep customerId only for assigning WL customer access and the customer ID in
/customers/{id}/{operation}/typed-data. Resolved customerId response metadata
is unchanged. Customer resources require the customers feature. Resource IDs
and joins are tenant-scoped; foreign/deleted resources return 404
RESOURCE_NOT_FOUND. Missing scopes return 403 INSUFFICIENT_SCOPE; disabled
features return 403 FEATURE_DISABLED. DTO/invalid-operation errors return
400 VALIDATION_ERROR. Invalid current status and ambiguous customer-vault resolution
return 409 CONFLICT, matching submission. Disabled generation assets return
400 VALIDATION_ERROR; missing assets return 404 RESOURCE_NOT_FOUND.
JWT/rate-limit/error envelopes are unchanged. Scope guard and DTO checks precede
service resolution; preparation has no idempotency replay response.

Every endpoint in this table except transfer returns HTTP 200 with exactly
timestampMs (string), typedData (object), signedPayload (string), request
(object), all non-null. The transfer response is documented separately in 10.0.
timestampMs is server-generated Unix milliseconds. typedData uses the existing
Initiate signing builder and domain FortVault/1/1; signedPayload is its exact
JSON.stringify serialization. Field order, optional omission and action labels
remain those specified in the operation's signing section. Do not reconstruct
the returned object or sign it as an ordinary text message.

The returned request contains only normalized submission fields:
- Generate address: vaultId and assets:[{assetId}], preserving request asset order.
- Whitelist creation: name, address, assetId, accessType, custodyType,
  ownershipType, and customerId only when present. Default accessType is all
  without a customer and customer with a customer. Customer-scoped entries
  require external ownership. Address validation uses the selected chain type;
  EVM and Bitcoin Bech32 addresses are canonicalized with the existing WL helper.
- All status changes: comment when nonblank; otherwise {}. Comment normalization
  is the same DTO whitespace normalization and trim used during submission.

Example preparation:

```http
POST /partner-api/v1/vaults/11111111-1111-4111-8111-111111111111/archive/typed-data
Authorization: Bearer <FRESH_JWT>
Content-Type: application/json

{"comment":"Maintenance"}
```

After receiving prepared, sign prepared.typedData using EIP-712. Submit this body
with a fresh JWT and an Idempotency-Key:

```javascript
const body = {
  ...prepared.request,
  signedPayload: prepared.signedPayload,
  signature: walletSignature
};
```

Use POST /generate-address-actions or POST /whitelist-address-actions for
creation. For status changes use PUT to the same resource/id/operation path
without /typed-data. Do not submit timestampMs, typedData or a nested request
field. Keep the returned signedPayload string unchanged. Manual payload
construction remains supported; existing initiation/review endpoints are unchanged.

Generation preparation requires an active owner, distinct assets, and active
partner-asset configuration. Status preparation requires active for archive or
archived for activate. It can therefore prepare activation for archived records;
address-asset status preparation does not impose a new parent-active condition.
WL creation rejects archived customers and contradictory scope/ownership fields.
Customer signing labels use first/last name without falling back to customer code,
matching submission. WL creation signs customer UUID; WL status signs customer
name. Address-asset status signs the stored shared-address display value, while
WL status signs the stored whitelist address. Neither status payload lowercases
these stored display addresses. Always use the returned payload, not a label or
address reconstructed from the list DTO.

Preparation does NOT create an action, reserve an address or funds, sign, or
dispatch processing. It does not check signer permissions, initiation policy,
approval requirements, or execution availability. Preparation and submission now
share read-only action-intent resolvers. Generation also checks pending-generation
claims and resolves current address slots; WL activation checks conflicting claims.
These checks are repeated at submission and do not reserve resources. Preparation success is not a dry run or a promise
of acceptance. Names, status and configuration can change: submission reconstructs
and verifies the signed payload and rechecks authorization/current state. Prepare
again after such changes. The existing TimestampMs freshness limitation remains;
preparation does not introduce signature expiry, nonce reservation or single-use
signatures. Auto-approved submission may execute immediately.

Unsigned customer/vault creation does not need typed-data preparation. Exchange
account initiation and API-client management remain unsupported through Partner
API; this change does not add them.

### 8.3.1 Exact status-change initiation payloads

These rules cover the six customer, regular-vault, and vault-address-asset
archive/activate endpoints in section 5.3. Prepare their initiation payloads with
POST to the same resource/id/operation path followed by /typed-data (section 8.3.0).
The existing /actions/{id}/typed-data endpoint remains for review/cancellation
after an action exists.

Use primary type **`Initiate`**, the domain in section 8.2, and EIP-712 type
**`string` for every message field**, including `TimestampMs`. Use the current
Unix time in milliseconds as a decimal string (the parser requires at least 13
digits). The timestamps below are illustrative; do not reuse them.

The backend compares the parsed object with its reconstructed object using
`JSON.stringify`. Preserve object insertion order: top-level `domain`,
`primaryType`, `types`, `message`; domain `name`, `version`, `chainId`;
and each type entry `name`, then `type`. Preserve the ordered fields below
in both `types.Initiate` and `message`. The submitted object contains only
`Initiate` in `types`; do not add `EIP712Domain`, IDs, scope, operation, or
other fields to this serialized object. A signing library may construct the
EIP-712 domain type internally, but submit the original canonical object as
`signedPayload = JSON.stringify(typedData)`.

| Target | Exact ordered message fields (omit optional fields when absent) |
| --- | --- |
| Customer | `Action`, `Customer?`, `Comment?`, `TimestampMs` |
| Regular vault | `Action`, `Vault`, `Comment?`, `TimestampMs` |
| Regular-vault asset address | `Action`, `Vault`, `Asset`, `Address`, `Comment?`, `TimestampMs` |
| Customer asset address with a nonempty customer name | `Action`, `Customer`, `Asset`, `Address`, `Comment?`, `TimestampMs` |
| Customer asset address without a customer name | `Action`, `Vault`, `Asset`, `Address`, `Comment?`, `TimestampMs` |

**Exact action labels:**

| Endpoint suffix | Customer | Regular vault | Either asset-address owner |
| --- | --- | --- | --- |
| `/archive` | `Archive Customer` | `Archive Vault` | `Archive Asset Address` |
| `/activate` | `Unarchive Customer` | `Unarchive Vault` | `Unarchive Asset Address` |

`activate` is the route/operation value, but the signed label is **Unarchive**,
not Activate. IDs belong in the URL, not the initiation message.

**Canonical labels:**

- `Customer` is exactly `[firstName, lastName].filter(Boolean).join(' ').trim()`.
  There is **no customer-code fallback** in this signing builder. If empty, omit
  `Customer` from both the type and message. For a customer-level request, do
  not insert `Vault` in its place.
- `Vault` is the stored vault name. For a customer asset without a customer
  name, the builder instead signs that customer's stored vault name. Customer
  and address DTOs do not expose this name, and the regular-vault endpoint does
  not return customer vaults. Consequently the current Partner API alone cannot
  reliably construct this nameless-customer asset payload. Do not guess a name
  from `code`; obtain authoritative metadata through an approved workflow or
  wait for an API contract extension. Named-customer asset requests do not need it.
- `Asset` is exactly `<symbol> on <chainName>`, including ` on ` for native
  assets (for example `ETH on Ethereum`). Use authoritative symbol and chain
  display name, not chainRef, chain ID, asset name, or a UI-shortened label.
- `Address` is the full stored vault-address value, falling back to the asset
  association's stored address. Do not abbreviate, checksum-convert, or otherwise
  alter the supplied canonical spelling.

**Comment normalization:** the HTTP DTO trims outer whitespace and replaces
runs of **two or more whitespace characters** with one ASCII space. The action
service trims again and treats an empty result as absent:

`const comment = rawComment.trim().replace(/\s\s+/g, ' ').trim()`

This is not `/\s+/g`: a single internal newline or tab is preserved. For example,
`"  Operational  review\n\nrequired  "` becomes
`"Operational review required"`. Send the normalized string in the HTTP body
and sign that same value. For no comment, omit the body property and omit
`Comment` from both the type and message; do not sign `null`, `""`, or a
placeholder. The optional body comment is a string, with a maximum of 500
characters after DTO normalization; JSON `null` is not the omission convention.

**Customer archive, with comment:**

```json
{
  "domain": {
    "name": "FortVault",
    "version": "1",
    "chainId": 1
  },
  "primaryType": "Initiate",
  "types": {
    "Initiate": [
      {
        "name": "Action",
        "type": "string"
      },
      {
        "name": "Customer",
        "type": "string"
      },
      {
        "name": "Comment",
        "type": "string"
      },
      {
        "name": "TimestampMs",
        "type": "string"
      }
    ]
  },
  "message": {
    "Action": "Archive Customer",
    "Customer": "Alice Example",
    "Comment": "Operational review",
    "TimestampMs": "1789732800000"
  }
}
```

**Regular vault activation, without comment:**

```json
{
  "domain": {
    "name": "FortVault",
    "version": "1",
    "chainId": 1
  },
  "primaryType": "Initiate",
  "types": {
    "Initiate": [
      {
        "name": "Action",
        "type": "string"
      },
      {
        "name": "Vault",
        "type": "string"
      },
      {
        "name": "TimestampMs",
        "type": "string"
      }
    ]
  },
  "message": {
    "Action": "Unarchive Vault",
    "Vault": "Treasury",
    "TimestampMs": "1789732800000"
  }
}
```

**Regular-vault asset archive, with comment:**

```json
{
  "domain": {
    "name": "FortVault",
    "version": "1",
    "chainId": 1
  },
  "primaryType": "Initiate",
  "types": {
    "Initiate": [
      {
        "name": "Action",
        "type": "string"
      },
      {
        "name": "Vault",
        "type": "string"
      },
      {
        "name": "Asset",
        "type": "string"
      },
      {
        "name": "Address",
        "type": "string"
      },
      {
        "name": "Comment",
        "type": "string"
      },
      {
        "name": "TimestampMs",
        "type": "string"
      }
    ]
  },
  "message": {
    "Action": "Archive Asset Address",
    "Vault": "Treasury",
    "Asset": "USDC on Ethereum",
    "Address": "0x1111111111111111111111111111111111111111",
    "Comment": "Operational review",
    "TimestampMs": "1789732800000"
  }
}
```

For a named customer's asset, replace the `Vault` type entry and message key
with `Customer` at the same position and use its canonical name. For activation,
change only the `Action` value to `Unarchive Asset Address` (plus a fresh
timestamp and the requested comment). Omitting a comment always removes its
entry from both `types.Initiate` and `message`.

### 8.4 Role permissions

Permissions and scopes follow the same least-privilege principle but authorize
different identities: workspace permissions govern the human user; API scopes
govern the authenticated API client. Dashboard navigation and controls use user
permissions, not API-client scopes. Hiding a control is not authorization: the
backend independently enforces the applicable checks on direct requests.

The action-signing user needs the corresponding workspace permission:

| Operation        | Initiator permission                     | Reviewer permission (approve or reject)   |
| ---------------- | ---------------------------------------- | ----------------------------------------- |
| Generate address | `vaults:actions:generate_address:initiate` | `vaults:actions:generate_address:review` |
| Transfer         | `vaults:actions:transfer:initiate`         | `vaults:actions:transfer:review`         |
| Whitelist creation/status | `vaults:actions:whitelist:initiate` | `vaults:actions:whitelist:review` |
| Vault archive/activation | `vaults:actions:initiate` | `vaults:actions:review` |
| Customer archive/activation | `customers:actions:initiate` | `customers:actions:review` |
| Regular-vault asset archive/activation | `vaults:actions:initiate` | `vaults:actions:review` |
| Customer asset archive/activation | `customers:actions:initiate` | `customers:actions:review` |
| Exchange-account status review | Initiation is dashboard-only (`exchange_accounts:actions:initiate`) | `exchange_accounts:actions:review` |

The signer must belong to the same workspace as the API client.

For these actions, both the signing user's current role review permission and
the current approval policy must allow approval or rejection. The shared backend
service enforces this for dashboard and Partner API submissions. API-client scopes
remain an additional independent requirement; a review scope does not grant the
signing user review permission. Cancellation retains its existing initiator rules.

Exchange-account status reviews require `exchange_accounts:actions:review` plus policy approval. Dashboard archive/activate initiation requires `exchange_accounts:actions:initiate`.
Dashboard API-client creation review requires `api_clients:actions:review` plus
policy; API-client management remains unavailable through Partner API.

Customer/vault API initiation requires the matching `:read` and `:actions:initiate` scopes;
address-asset API initiation uses `addresses:read` and `addresses:actions:initiate`.
API reviews additionally require their resource `:actions:review` scope.

Migration `1789700400000-StandardizeActionInitiationPermissions` renames stored
action `:create` permissions and supported API scopes to `:initiate`. Resource
creation scopes such as `customers:create` and `vaults:create` are unchanged.
Old action `:create` scopes no longer authorize requests. Update API consumers
alongside deployment. Existing API-client IDs, keys and statuses are preserved.
Only partner roles named `admin` automatically receive the new exchange-account
initiation/review permissions; other roles require explicit assignment. Pending,
already-signed API-client creation requests containing old scopes must be
canceled/recreated, not edited in place.

Migration `1789693200000-SeparateStatusActionPermissions` retains existing
`vaults:update`/`customers:update` grants and adds both corresponding initiation
and review permissions to those roles. Approval policy still applies. Roles
without the matching update grant are not automatically granted these permissions.

## 9. Generate an Address

### 9.1 Initiate

```http
POST /partner-api/v1/generate-address-actions
Authorization: Bearer <NEW_JWT>
Idempotency-Key: address-generate-550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json
```

```json
{
  "vaultId": "550e8400-e29b-41d4-a716-446655440000",
  "assets": [
    {
      "assetId": "5b7a1100-f1d1-4f16-b91d-1b22421ed234"
    }
  ],
  "signedPayload": "<SERIALIZED_EIP_712_TYPED_DATA>",
  "signature": "<EIP_712_SIGNATURE>"
}
```

Request fields:

| Field                    | Type   | Required | Rules                                                                                            |
| ------------------------ | ------ | -------- | ------------------------------------------------------------------------------------------------ |
| `vaultId`                | UUID   | Yes      | Existing active vault in the API client's workspace                                              |
| `assets`                 | array  | Yes      | Between 1 and 20 unique asset entries                                                            |
| `assets[].assetId`       | UUID   | Yes      | Partner-enabled asset with no non-terminal generation request already in progress for this vault |
| `signedPayload`          | string | Yes      | Serialized canonical EIP-712 generate-address payload                                            |
| `signature`              | string | Yes      | EIP-712 signature from the initiating FortVault user                                             |

The backend resolves each asset's chain and chain type from the authoritative
asset record. Clients must not send a chain type in this request.

Required authorization:

- API client scope `addresses:actions:initiate`.
- API client scope `customers:read` when `vaultId` is a customer vault, or
  `vaults:read` when it is a regular vault.
- Signer permission `vaults:actions:generate_address:initiate`.
- The API client, vault, asset, and signer must belong to the same workspace.

The response has this shape:

```json
{
  "type": "pending_generation",
  "action": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "partnerId": "7f4b8a00-2258-4dc5-9ce1-cc125f50d391",
    "typeId": "9a19ef4d-7402-4476-9efe-3668d878c232"
  },
  "vaultId": "6c3ac4c9-a562-4913-9060-97e39d471bc7",
  "status": "pending",
  "items": [
    {
      "itemId": "34cf32f0-77cd-44d9-89f5-ef96568210d7",
      "assetId": "5b7a1100-f1d1-4f16-b91d-1b22421ed234",
      "chainTypeName": "evm",
      "assetSymbol": "ETH",
      "status": "pending"
    }
  ]
}
```

`action.status` is the approval lifecycle and can be `pending`, `approved`,
`canceled`, or `expired`. The top-level `status` describes address-generation
execution and can be `pending`, `processing`, `completed`, or `failed`. Each
item `status` can be `pending`, `awaiting_mpc`, `resolved`, or `failed`. When
policy requires no approvals, execution may start during the initial request
and the returned statuses may already have advanced. An existing generated
address does not prevent requesting another address for the same asset.

Save the action ID immediately. It is the correlation identifier for approvals
and status queries.

### 9.2 Approve, reject, or cancel

First prepare the exact typed data for the intended operation:

```http
POST /partner-api/v1/actions/{actionId}/typed-data
Authorization: Bearer <NEW_JWT>
Content-Type: application/json
```

The preparation endpoint is read-only and does not require an
`Idempotency-Key`. It requires the action's resource read scope plus
`*:actions:review` for approve/reject or `*:actions:initiate` for cancellation.
Use one of these request bodies:

```json
{ "operation": "approve" }
```

```json
{ "operation": "reject", "comment": "Operational reason for rejection" }
```

```json
{ "operation": "cancel" }
```

`comment` is required for `reject`, has a maximum length of 500 characters, and
must be omitted for `approve` and `cancel`.

Example response for rejecting a transfer:

```json
{
  "operation": "reject",
  "timestampMs": "1776000000000",
  "typedData": {
    "domain": {
      "name": "FortVault",
      "version": "1",
      "chainId": 1
    },
    "primaryType": "Reject",
    "types": {
      "Reject": [
        { "name": "Action", "type": "string" },
        { "name": "From", "type": "string" },
        { "name": "To", "type": "string" },
        { "name": "Asset", "type": "string" },
        { "name": "Amount", "type": "string" },
        { "name": "RequestId", "type": "string" },
        { "name": "Reason", "type": "string" },
        { "name": "TimestampMs", "type": "string" }
      ]
    },
    "message": {
      "Action": "Transfer",
      "From": "0x1111111111111111111111111111111111111111",
      "To": "0x2222222222222222222222222222222222222222",
      "Asset": "USDC on Base Sepolia",
      "Amount": "25",
      "RequestId": "550e8400-e29b-41d4-a716-446655440000",
      "Reason": "Operational reason for rejection",
      "TimestampMs": "1776000000000"
    }
  },
  "signedPayload": "<EXACT_JSON_SERIALIZATION_OF_TYPED_DATA>"
}
```

The field set varies by action type. `Reject` includes `Reason`; `Approve` and
`Cancel` do not. Always sign the returned `signedPayload`, not a reserialized
copy of `typedData`. Then submit that exact string and its wallet signature to
the corresponding endpoint below.

Approval endpoint:

```http
POST /partner-api/v1/actions/{actionId}/approve
Authorization: Bearer <NEW_JWT>
Idempotency-Key: address-approve-550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json
```

Approval body:

```json
{
  "signedPayload": "<SERIALIZED_APPROVAL_TYPED_DATA>",
  "signature": "<APPROVER_EIP_712_SIGNATURE>"
}
```

Approval returns:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "approved",
  "approvalCount": 1,
  "requiredApprovals": 1
}
```

`status` can remain `pending` until all required approvals and mandatory-role
requirements are satisfied.

Rejection endpoint:

```http
POST /partner-api/v1/actions/{actionId}/reject
Authorization: Bearer <NEW_JWT>
Idempotency-Key: address-reject-550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json
```

Rejection body:

```json
{
  "signedPayload": "<SERIALIZED_REJECTION_TYPED_DATA>",
  "signature": "<APPROVER_EIP_712_SIGNATURE>",
  "comment": "Operational reason for rejection"
}
```

The rejection comment is required and has a maximum length of 500 characters.

Rejection returns:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "canceled"
}
```

Approval and rejection require the resource read scope and corresponding
`*:actions:review` scope from the matrix in section 5.2. Both require an action
in the same workspace and an action signer who satisfies the applicable
on-chain approval policy. The initiator cannot approve or reject their own
action.

Cancellation endpoint:

```http
POST /partner-api/v1/actions/{actionId}/cancel
Authorization: Bearer <NEW_JWT>
Idempotency-Key: action-cancel-550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json
```

Cancellation body:

```json
{
  "signedPayload": "<SERIALIZED_CANCELLATION_TYPED_DATA>",
  "signature": "<INITIATOR_EIP_712_SIGNATURE>"
}
```

Cancellation requires the resource read scope and corresponding
`*:actions:initiate` scope from the matrix in section 5.2. Only the user who
initiated the action may sign its cancellation. A successful cancellation
returns the same `{ "id", "status": "canceled" }` shape as rejection.

For transfer actions, successful rejection or cancellation also changes the
transfer metadata status from `created` to `failed`. A subsequent
`GET /actions/{actionId}` returns `status: "canceled"` and
`details.transferStatus: "failed"`; for an unbroadcast transfer,
`details.txHash` is `null`. These details are not extra fields in the
reject/cancel response. This is termination before execution, not a blockchain
execution failure. The transfer metadata describes the intent; an execution
transfer record need not have been created yet.

Whether approval is required depends on the workspace policy and action scope.

All three endpoints return HTTP `201` on a new successful request or an
identical successful-response replay. In addition to the authentication,
authorization, and idempotency errors described elsewhere in this guide:

- Initiation returns `VALIDATION_ERROR` for malformed signing, asset, or policy
  input, `RESOURCE_NOT_FOUND` when the vault, asset, or chain type is
  unavailable, and `ACTION_SIGNER_NOT_AUTHORIZED` when the recovered signer is
  unavailable, inactive, cross-workspace, or missing the required permission.
- Review or cancellation returns `ACTION_NOT_FOUND` for an unavailable action,
  `ACTION_EXPIRED` after expiration, and `ACTION_ALREADY_PROCESSED` or
  `ACTION_ALREADY_APPROVED` when its current state conflicts with the request.
- An initiator attempting rejection receives `FORBIDDEN` with message `The
  action initiator cannot reject this action; use cancel instead`.
- A user other than the initiator attempting cancellation receives `FORBIDDEN`
  with message `This action can only be canceled by its initiator`.

An action can complete without a separate approver when the policy permits it.

### 9.3 Obtain the generated address

Poll `GET /actions/{id}` with `addresses:read` to observe an address action's
state and sanitized `details.assets`. After processing completes, query
`GET /addresses?vaultId=<VAULT_ID>` with `addresses:read` plus `customers:read`
for a customer vault or `vaults:read` for a regular vault. Treat the address
resource list as authoritative for addresses currently attached to the vault.

## 10. Create a Transfer

### 10.0 Prepare initiation from resource IDs

POST /partner-api/v1/transfer-actions/typed-data returns HTTP 200. It is read-only:
use a fresh API JWT, but no Idempotency-Key or wallet signature. It does not create
an action, reserve funds, authorize a signer, check policy, estimate fees, check
balance, or dispatch execution. Submission revalidates current state.
Preparation does check that the positive amount is exactly representable using
the source asset's decimals, before destination resolution or returning typed data.

Required body fields: source, destination, assetId (UUID), amount (decimal string
with the same normalization/validation as initiation). No field accepts null.
source requires vaultId (including for customer vaults); optional addressAssetId
selects a specific active address-asset link belonging to that owner and asset.
destination accepts the same owner selector OR whitelistId, never both.
whitelistId cannot be combined with vaultId or addressAssetId. customerId is not
a transfer selector. Unknown fields at any depth are rejected with 400 VALIDATION_ERROR.

Example request:

```json
{
  "source": {
    "vaultId": "11111111-1111-4111-8111-111111111111",
    "addressAssetId": "22222222-2222-4222-8222-222222222222"
  },
  "destination": {
    "whitelistId": "33333333-3333-4333-8333-333333333333"
  },
  "assetId": "44444444-4444-4444-8444-444444444444",
  "amount": "1.5"
}
```

For an internal destination, replace destination with {"vaultId":"<UUID>"},
optionally adding addressAssetId. Use vaultId for both regular and customer
vaults; the backend discovers the customer relationship and enforces the owner's
read scope and feature. It never falls back to a whitelist if vault lookup fails.
Obtain addressAssetId from the id field of GET /addresses?vaultId=<UUID>, not
from an underlying shared-address identifier. Obtain whitelistId from
GET /whitelist-addresses. Both source and internal destination use the exact
assetId, which determines the network. No exchange-ID selector is supported.

If an owner has exactly one active link for that asset, addressAssetId may be
omitted. With multiple matching links, preparation returns 409 CONFLICT; select
explicitly. It never picks the latest/highest-balance address. Archived/deleted
owners or links, foreign resources, wrong-asset links and ineligible whitelist
records return 404 RESOURCE_NOT_FOUND. Selected whitelist records use existing
source-customer access rules; another entry at the same address cannot substitute.

Scopes: transfers:actions:initiate and addresses:read are always required.
Each resolved owner additionally requires vaults:read (regular/gas) or
customers:read (customer). Whitelist destinations require whitelist-addresses:read.
Customer resolution requires the customers feature. Missing scopes return 403
INSUFFICIENT_SCOPE; disabled customer features return 403 FEATURE_DISABLED.
Invalid selectors/amounts or identical normalized addresses return 400
VALIDATION_ERROR. Scope guard and DTO checks precede resolution; source resolves
before destination. No signer permission/policy conclusion follows from success.

The response has exactly timestampMs, typedData, signedPayload, transfer, source,
destination. timestampMs is a server-generated milliseconds string. typedData is
the Initiate object in section 10.1; signedPayload is its exact JSON.stringify
serialization. transfer contains exactly fromAddress, toAddress, assetId, amount,
all non-null strings. Both resolved entity objects contain exactly vaultId,
customerId, addressAssetId, whitelistId (nullable UUIDs), and name (non-null string).
Owner results have vaultId/addressAssetId and null whitelistId; customerId is
null for regular/gas vaults. Whitelist results have whitelistId, its nullable
customerId, and null vaultId/addressAssetId. name is the vault or whitelist name.

Sign the returned typedData with EIP-712, then send the following to
POST /transfer-actions with a fresh JWT and an Idempotency-Key:

```javascript
const body = {
  ...prepared.transfer,
  signedPayload: prepared.signedPayload,
  signature: walletSignature
};
```

Do not send source/destination selectors or other preparation response fields to
initiation. The existing signature binds addresses/asset label/amount, NOT the
selector IDs; submission checks address eligibility afresh and may qualify via
another eligible destination path. Preparation is not an immutable entity-ID
authorization or an execution guarantee. Existing manual initiation remains valid.

### 10.1 Request and exact initiation signature

POST /partner-api/v1/transfer-actions returns HTTP 201 on success. Required
headers: Authorization: Bearer <fresh Ed25519 JWT>, Content-Type: application/json,
and Idempotency-Key. Required body fields (none nullable or optional):

| Field | Type | Meaning |
| --- | --- | --- |
| fromAddress | string | A source address linked to the asset in this workspace |
| toAddress | string | An eligible destination address |
| assetId | UUID string | Exact source asset/network catalog record |
| amount | string | Positive, nonzero human-unit decimal amount, NOT base units |
| signedPayload | string | JSON serialization of the complete typed-data object |
| signature | string | Authorized signing user's EIP-712 wallet signature |

Only the six fields above are used as transfer-creation fields. Current creation
validation strips unknown outer-body fields; it does not reject them. For example,
an otherwise valid signed request with "unexpected": true can return HTTP 201
and execute under the normal approval policy. Fields such as comment, vaultId,
customerId, chainId, fee selection, nonce, or approvalCount are ignored, not
supported options. Never use an extra field as a dry-run or safety switch.
Preparation (/transfer-actions/typed-data) differs: it rejects unknown fields
at any depth with 400 VALIDATION_ERROR.

Stripping applies only to the outer request DTO. The JSON inside signedPayload
is not stripped; exact typed-data reconstruction/comparison and signature
verification still apply. Idempotency hashes the raw request before stripping,
so adding, removing, or changing an ignored field under the same unexpired key
returns 409 IDEMPOTENCY_KEY_REUSED. Send only the documented six fields.
Send strings; do not rely on string coercion of numeric JSON values.

Required API scope: transfers:actions:initiate plus vaults:read for a regular/gas
source vault or customers:read for a customer source vault. Initiation does not
require transfers:read, destination read scope, or whitelist-addresses:read.
Discovery and later monitoring require their own read scopes. The recovered
signing user must be active, in the API client's workspace, have
vaults:actions:transfer:initiate, and satisfy the workspace initiation policy.

EIP-712 domain, in property order: name="FortVault", version="1", chainId=1
(JSON number). This signing-domain chain ID stays 1 for every execution network,
including Tron and Bitcoin. primaryType is "Initiate". All fields have EIP-712
type "string". Ordered types.Initiate AND ordered message fields are:

| Order | Field | Exact value |
| --- | --- | --- |
| 1 | Action | Transfer |
| 2 | From | Normalized fromAddress |
| 3 | To | Normalized toAddress |
| 4 | Asset | asset.symbol + " on " + asset.chain.name |
| 5 | Amount | The normalized request decimal string, preserving its zeros |
| 6 | TimestampMs | Decimal Unix milliseconds string, at least 13 digits |

All six fields are required for initiation. None is optional. Do not add assetId,
chainRef, RequestId, fee, or any other signed field. Top-level object order is
domain, primaryType, types, message; domain order is name, version, chainId;
types contains only Initiate (no EIP712Domain); each field descriptor is ordered
name, type. Backend comparison uses JSON.stringify on parsed objects, so key
order matters. Whitespace around JSON tokens is not the binding; the parsed
property order and values are. Serialize the shown object as signedPayload.

Complete signedPayload object example, with no key or signature. Replace the
illustrative addresses, discovered labels, amount, and timestamp before signing:

```json
{
  "domain": {
    "name": "FortVault",
    "version": "1",
    "chainId": 1
  },
  "primaryType": "Initiate",
  "types": {
    "Initiate": [
      {
        "name": "Action",
        "type": "string"
      },
      {
        "name": "From",
        "type": "string"
      },
      {
        "name": "To",
        "type": "string"
      },
      {
        "name": "Asset",
        "type": "string"
      },
      {
        "name": "Amount",
        "type": "string"
      },
      {
        "name": "TimestampMs",
        "type": "string"
      }
    ]
  },
  "message": {
    "Action": "Transfer",
    "From": "0x1111111111111111111111111111111111111111",
    "To": "0x2222222222222222222222222222222222222222",
    "Asset": "USDC on Ethereum",
    "Amount": "01.5000",
    "TimestampMs": "1790000000000"
  }
}
```

**Validity limitation:** the backend verifier checks TimestampMs against
/^\d{13,}$/ but does not compare it with the current clock. There is no enforced
initiation-signature age window or one-use timestamp. Use the current time, but
do not expect an old/future timestamp alone to be rejected. JWT expiry and jti
replay protection are separate: configurable defaults are a maximum 300-second
JWT lifetime and 30-second clock skew. Action expiry is also separate, based on
creation time and the action type's configured expirationSeconds after creation.
A fresh JWT and a different idempotency key can resubmit the same initiation
intent; do not assume signature-level duplicate suppression.

### 10.2 Normalization and discovery

HTTP string fields are trimmed; runs of two or more whitespace characters are
collapsed to one space, except signedPayload which is only outer-trimmed.
For addresses, EVM checksum conversion in HTTP validation is followed by
chain-aware canonicalization for signing and storage:

| Network | Required form and exact signed equivalent |
| --- | --- |
| EVM (evm:*) | Valid 0x hex address, signed lowercase, never checksum/display case. 0x52908400098527886E0F7030069857D2E4169EE7 becomes 0x52908400098527886e0f7030069857d2e4169ee7. |
| Tron | Valid Base58Check T-address; trim and preserve case. TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj stays unchanged. Tron 41... hexadecimal is not a supported alternative and is not converted to Base58. |
| Bitcoin Base58 | Valid Base58Check address; trim and preserve case (1/3/m/n/2 prefixes as accepted by validation). Never lowercase it. |
| Bitcoin Bech32/Bech32m | For bitcoin:* and bc1/tb1 prefix, lowercase for signing; all-uppercase valid addresses normalize to lowercase; mixed-case/checksum-invalid addresses are rejected. |

Source-scope, source-vault, policy-source and execution-source lookups preserve
Bitcoin Base58 case and normalize EVM and Bitcoin bc1/tb1 comparisons. This does
not add Bitcoin testnet execution support. Transaction ownership/history matching
is a separate concern and has not been comprehensively migrated by this change.

Amount regex after string normalization is /^(?!0+(\.0+)?$)\d+(\.\d+)?$/.
" 01.5000 " signs "01.5000", not "1.5" and not "1500000". For a 6-decimal
asset it converts to 1500000 base units. Leading zeros and trailing fractional
zeros are preserved in Amount. Zero, negative values, +1, .5, 1., 1e-6, and
decimal commas are rejected. EVM/Tron/Bitcoin all sign human-unit decimal strings.

**Exact precision validation:** preparation and submission use the same check
before conversion. Digits beyond asset.decimals must all be zero. For decimals=6,
"1.0000001", "1.0000005", and "0.0000001" return HTTP 400 VALIDATION_ERROR
with message "Amount exceeds the asset's supported precision of 6 decimal places".
"01.5000000" is accepted and converts exactly to 1500000 base units, while its
signed Amount remains "01.5000000". Conversion does not round accepted amounts.
Zero is rejected and the converted integer must also be strictly positive.
This does not change amount precision/positivity or balance/fee checks. The stored
transfer amount still has PostgreSQL numeric(36,18) limits; arbitrary-length
values are not guaranteed to persist without rounding/overflow. This change
validates blockchain precision; it does not change database column capacity.

Discover assetId, symbol, decimals, and its network through GET /assets and
GET /chains (assets:read), and source/destination asset-address links through
GET /addresses?vaultId=<id> (addresses:read plus that vault's read scope).
Use the exact current symbol and chain display name, e.g. "USDC on Ethereum";
do not substitute asset name, chainRef, or a hardcoded network label. The signed
Asset label does not separately bind assetId, token address, or numeric execution
chain ID. Do not infer stronger unique-asset binding than the current payload.

### 10.3 Eligibility, balances, and fees

The source must resolve inside the authenticated workspace, have a non-archived
vault and an active link for the exact assetId. Customer flows require the
customers feature. Customer archival is represented by its customer vault status.
The selected assetId determines the execution chain; no cross-chain bridge or
asset conversion is performed. Source and destination normalized addresses must
differ. There is no separate prohibition on different addresses of one vault.

Internal transfers can use regular/gas or customer vaults as source and
destination, including customer-to-customer; there is no same-customer restriction
for the internal-vault destination path. Both sides must have active links for
the same assetId on its chain, and the destination vault must not be archived.
No whitelist entry is required for an eligible internal destination. Workspace
policy can still deny the transfer. Archived resources cannot qualify through
the internal path; destination eligibility is an OR of internal, whitelist, and
exchange paths, not an unconditional ban on the address if another path qualifies.

External destinations require an active matching whitelist entry for the same
assetId, or a recognized active exchange deposit address for the same currency
and chain (exchanges feature required). Customer source vaults may use global
all-scope WL entries or their own customer-scoped entries; regular sources use
non-customer entries (all/internal). Customer sources cannot use internal-only
or another customer's WL entries. An unknown external wallet is not allowed.

GET /balances?vaultId=<id> is NOT sufficient to assess a specific source address.
It sums stored balances across non-deleted links for each asset in the vault,
including archived links. /addresses identifies links/status but has no balance
field. Partner API has no address-level balance endpoint, transfer-options
endpoint, or fee-estimation endpoint. Dashboard-only endpoints are not substitutes.
There is no API spendable-balance/reservation guarantee against pending transfers
or a stale chain snapshot.

Initiation checks the specific source link's stored balance against the converted
amount. The minimum is one asset base unit (`10^-decimals`): for example,
`0.000001` for a 6-decimal asset, `0.00000001` for an 8-decimal asset, and
`0.000000000000000001` for an 18-decimal asset. `dustThresholdAmount` is a
display filter, not an API transfer minimum. Zero and fractional base units
remain invalid. Bitcoin reserves a fixed minimum 218 satoshis for fees.
Network/provider output dust rules may still reject small Bitcoin outputs
during execution even when initiation succeeds.
This is not a dynamic Bitcoin fee quote. Other chains do not have a complete
native-fee sufficiency check in this initiation flow. Token transfers need native
fee funding/resources on the execution chain; native transfers may need balance
beyond their principal. Provider/execution requirements can still cause failure
after acceptance. The API exposes neither a guaranteed fee budget nor Tron
energy/bandwidth availability. Do not submit transfers simply to estimate fees.

If policy requires zero approvals, initiation immediately calls the execution
path, creates the transfer and dispatches processing. An API test can therefore
broadcast a real transfer without a separate approve command. Use only explicitly
authorized test funds/networks; no dry-run parameter exists.

### 10.4 Response, errors, and validation order

Success body has exactly action and transfer. Example (timestamps and IDs are
illustrative; status depends on policy/execution):

```json
{
  "action": {
    "id": "11111111-1111-4111-8111-111111111111",
    "status": "pending",
    "partnerId": "22222222-2222-4222-8222-222222222222",
    "typeId": "33333333-3333-4333-8333-333333333333"
  },
  "transfer": {
    "createdAt": "2026-09-22T00:00:00.000Z",
    "createdBy": "44444444-4444-4444-8444-444444444444",
    "status": "created",
    "fromAddress": "0x1111111111111111111111111111111111111111",
    "toAddress": "0x2222222222222222222222222222222222222222",
    "assetId": "55555555-5555-4555-8555-555555555555",
    "amount": "01.5000"
  }
}
```

All displayed response fields are present. action.partnerId is nullable in the
shared schema (normal authenticated creation populates it); the others are
non-null. Action statuses: pending, approved, canceled, expired. Transfer statuses:
created, processing, completed, failed. transfer is action metadata, NOT a
persisted transfer DTO with an id. Initial status is created, even when action
status has become approved. No txHash, fee, confirmation count, or settlement
promise is returned by initiation.

Errors use the standard envelope with statusCode, errorCode, message, details,
requestId, timestamp, path (no stack). details may be null, string, array, or
object. Do not assert only one validation message when multiple DTO fields fail.

| HTTP | Public errorCode | Examples |
| --- | --- | --- |
| 400 | VALIDATION_ERROR | Malformed DTO, zero/exponent or over-precision amount, bad typed-data/signature, mismatching payload, equal addresses |
| 400 | INSUFFICIENT_BALANCE | Principal exceeds stored source balance; Bitcoin principal plus fixed fee reserve exceeds it |
| 400 | IDEMPOTENCY_KEY_REQUIRED / IDEMPOTENCY_KEY_INVALID | Missing key or not 8-255 characters from A-Z, a-z, 0-9, period, underscore, colon, hyphen |
| 401 | AUTHENTICATION_FAILED | Invalid/revoked client, JWT signature/claims/expiry, reused jti |
| 403 | INSUFFICIENT_SCOPE | Missing endpoint scope or source-vault read scope |
| 403 | ACTION_SIGNER_NOT_AUTHORIZED | Recovered user missing/inactive/foreign or missing initiation permission |
| 403 | FORBIDDEN / FEATURE_DISABLED | Archived source vault, policy denial, unavailable customer/exchange feature |
| 404 | RESOURCE_NOT_FOUND | Missing source/asset metadata or no eligible destination |
| 409 | IDEMPOTENCY_KEY_REUSED | Same key with different request |
| 409 | IDEMPOTENCY_REQUEST_IN_PROGRESS | Same key still reserved/in progress |
| 409 | CONFLICT | Database/business conflict not mapped to a more specific code |
| 429 | RATE_LIMIT_EXCEEDED | Per-client rate limit; Retry-After gives seconds |
| 500 / 503 | INTERNAL_SERVER_ERROR / SERVICE_UNAVAILABLE | Unexpected internal failure or dependency unavailability; outcome may be uncertain |

**Destination error caveat:** although DESTINATION_NOT_ALLOWED exists in the
public enum, the current missing-destination exception wording does not match
that mapping. The usual unknown/ineligible destination path returns HTTP 404
RESOURCE_NOT_FOUND, not DESTINATION_NOT_ALLOWED. Restricted WL entries generally
fail the destination lookup first. Do not change tests to expect a code solely
because it appears in the enum.

Validation precedence for otherwise reachable requests:

1. JWT/client validation, consume jti, rate limit, endpoint initiation scope.
2. Idempotency key validation/reservation (identical completed retry can return
   its saved response without running downstream validation again).
3. DTO transformation/validation.
4. Resolve source asset-address context and require source-vault read scope.
5. Recover signing user; require active same-tenant user and initiation permission.
6. Load user/asset; normalize addresses and reject equality; resolve source,
   customer feature, source vault status, active source asset link and metadata.
7. Reconstruct/compare initiation payload and verify signature.
8. Validate exact amount precision/positivity, convert to positive base units,
   Bitcoin fee reserve check, principal balance check.
9. Resolve destination eligibility/features/WL restrictions.
10. Resolve action type and initiation policy; persist action; calculate approval
    requirements; execute immediately if zero approvals.

Thus an invalid signature can precede insufficient balance; insufficient balance
can precede an invalid destination; a missing source/read scope can precede both.
Policy/provider failures are not a single fixed validation response. An error
after persistence does not prove no action exists.

Idempotency is scoped by tenant and API client, retained for 24 hours. The key
binds method, path, query, and raw request body, including signedPayload/signature.
Identical retries return saved status/body with Idempotency-Replayed: true.
For deterministic 4xx errors stored with the complete-envelope implementation,
all public fields are preserved: statusCode, errorCode, message, details,
requestId, timestamp, and path. requestId and timestamp identify the original
response; the fresh JWT is validated and the retry is audited separately.
Legacy stored errors without a complete envelope cannot recover their original
timestamp and continue to receive current request metadata until those records
expire. Errors before idempotency reservation (including authentication failures)
are not stored replays. Do not submit another transfer to test this behavior;
use an invalid-signature fixture.

For a request under the same key,
changing TimestampMs/signature is a different request. Reuse the original body
and key but always create a fresh JWT/jti. Successful and deterministic client
error responses are recorded atomically as described in section 4.3. A new
pre-commit failure rolls back; a lost post-commit response is replayed. Legacy
uncertain processing records stay blocked even after expiry. Do not switch keys
to retry an uncertain transfer without reconciliation. Completed keys can be
reused after retention, so idempotency is not permanent semantic deduplication.

### 10.5 Review, execution, and ledger verification

Use POST /actions/{actionId}/typed-data with {operation:"approve"},
{operation:"reject",comment:"Reason"}, or {operation:"cancel"}. Requires
transfers:read plus transfers:actions:review for approve/reject, or
transfers:actions:initiate for cancel. Preparation requires no Idempotency-Key.
Rejection comment is required, maximum 500 characters; omit comment for the
other operations. Returned fields are operation, timestampMs, typedData,
signedPayload. Sign returned typedData and submit returned signedPayload
unchanged; do not reorder/normalize/reconstruct the serialized string. Prepare
again if authoritative action details change.

For transfer reviews, primaryType is Approve, Reject, or Cancel respectively.
The domain remains FortVault/1/1. Ordered string fields: Action="Transfer",
From, To, Asset, Amount, RequestId (the action UUID), optional Reason (Reject
only), TimestampMs. From/To are chain-normalized action addresses; Asset uses
stored symbol/network labels; Amount is stored human-unit action amount.
Missing metadata fields are omitted from both types and message; RequestId
binds the review to this action. Do not invent missing fields. The initiation
payload has no RequestId; approval/rejection/cancellation do.

POST /actions/{id}/approve, /reject, /cancel require Idempotency-Key and return
201 on success. Approval returns id, status, approvalCount, requiredApprovals;
reject/cancel return id, status="canceled". Signer review permission is
vaults:actions:transfer:review plus policy for approve/reject. An initiator cannot
approve/reject their own action; only the initiator may cancel. Terminal/expired
actions and duplicate reviews are rejected. Relevant codes include ACTION_NOT_FOUND
(404), ACTION_ALREADY_PROCESSED/ACTION_ALREADY_APPROVED (409), ACTION_EXPIRED
(400), FORBIDDEN (403), and signing/scope/idempotency errors above. Full review
request examples are in section 9.2.

Poll GET /actions/{id} with transfers:read. action.status=approved means the
approval stage completed and execution was initiated, not blockchain settlement.
details.transferStatus is created/processing/completed/failed or null when absent;
details.txHash is a string or null. details also contains fromAddress, fromName,
fromVaultId, toAddress, toName, toVaultId, assetId, symbol, chainRef, chainName,
amount, each nullable if absent. A processing success callback sets completed;
failure sets failed and may provide a hash. Public details do not expose the
internal failure reason. A failed transfer can leave the action approved.

Interpret action status and transfer status together. Rejection or cancellation
before execution produces `action.status="canceled"` with
`details.transferStatus="failed"` and `details.txHash=null`, rather than leaving
the transfer metadata as `created`. Do not classify this as an on-chain failure
or expect a corresponding blockchain transaction. Conversely, a processing
failure may leave `action.status="approved"` with
`details.transferStatus="failed"`; that status alone does not prove the
transaction was broadcast or failed on-chain.

GET /transactions?vaultId=<id> requires transactions:read plus the vault's read
scope. It returns data, skip, take, not total. Available filters are vaultId,
skip, take (1-50), order; there is no actionId/txHash/address filter or transaction
detail endpoint. Page through results and correlate by details.txHash AND
chainRef, then assetId and source/destination address and exact amount. Do not
equate action.entityId (transfer ID after approval) to transactionId or movementId.
Before txHash exists there is no authoritative direct action-to-ledger API link.

Each movement contains exactly transactionId, movementId, sourceVaultId,
destinationVaultId, sourceCustomerId, destinationCustomerId, txHash, chainRef,
blockNumber, blockTimestamp, detectedAt, assetId, symbol, decimals,
baseUnitAmount, fromAddress, toAddress, feeBaseUnitAmount. Ownership IDs, txHash,
blockNumber, blockTimestamp, detectedAt and feeBaseUnitAmount are nullable.
detectedAt is a date-time when present; blockNumber is a string. Principal is an exact integer string in the
movement asset's smallest unit, not the signed decimal text. Ownership fields
identify the source/destination inside this tenant; external ownership is null.
Internal movements can appear in both vault queries; deduplicate by movementId.
Bitcoin change/multiple outputs can produce several lines; do not require one
row per action or add all outputs as outgoing principal.

feeBaseUnitAmount is the transaction-wide stored fee repeated on its movement
rows, in native fee units (e.g. wei, satoshis, sun), not necessarily the movement
asset's units. Null means unavailable, not zero. Do not sum repeated fees across
movements or source/destination queries; deduplicate by transactionId/chainRef.
The response has no fee-asset ID/decimals, fee breakdown, or payer attribution;
movement decimals describe principal only. Use known chain-native metadata and
do not assert that an incoming vault paid the fee.

The ledger query requires a transaction line. Fee-only failed transactions can
be absent even if an on-chain fee was spent. Listener ingestion can lag or miss
events; an empty page is not proof of failure. blockNumber/blockTimestamp provide
observed block information, NOT a confirmation count or finality guarantee.
No confirmations, finalized flag, receipt success, reorg state, settlement
timestamp, or chain-head height is exposed. API-only tests can verify observed
movements, not authoritative chain finality or every failed transaction's fee.

### 10.6 Remaining API-only test limitations

- No per-address spendable balance, fee estimate, funding faucet, or dry run:
  deterministic funding/fee preconditions need externally prepared fixtures.
- No enforced initiation timestamp freshness or signature-level deduplication:
  negative replay/expiry tests must distinguish JWT, idempotency, and action expiry.
- Precision checks now reject nonrepresentable amounts; harmless extra trailing
  zeros remain supported. Database amount capacity remains a separate limit.
- Destination-specific error mapping is incomplete; use actual 404 behavior.
- No finality/receipt endpoint, direct action-ledger link before hash, or guaranteed
  fee-only failed transaction visibility. Do not claim settlement from approval.
- Address case handling is not uniformly chain-specific across all lookup/read
  paths; use canonical discovered addresses and flag collision/casing tests as
  known limitations rather than weakening their assertions.


## 11. Error Contract

### Request correlation on all responses

Every backend response under `/partner-api/v1` includes `X-Request-Id`, a
server-generated UUID identifying the current HTTP attempt. This applies to
successful reads/writes, validation and authentication failures, rate limits,
and application errors. Caller-supplied request IDs are ignored. Responses
generated outside the backend (for example, a gateway outage) may lack it.

Store this header for both successful and failed requests and supply it to
FortVault support. It is exposed through CORS, together with
`Idempotency-Replayed` and `Retry-After`, so browser clients can read it.

The existing error-body `requestId` remains for compatibility. For newly
generated errors it matches the header. A replay of a stored complete error
envelope preserves the original body `requestId` and `timestamp`; the header
identifies the new attempt and its separate audit record.

For example, an invalid-signature request with `Idempotency-Key: transfer-123`
returns HTTP 400 and `X-Request-Id: 11111111-1111-4111-8111-111111111111`.
An identical retry with the same key and a fresh JWT returns HTTP 400,
`Idempotency-Replayed: true`, and
`X-Request-Id: 22222222-2222-4222-8222-222222222222`. The saved error body
still contains `requestId: 11111111-1111-4111-8111-111111111111`.
The idempotency key identifies the operation; the header identifies each attempt.

Partner API errors use a stable public `errorCode` and a human-readable
`message`:

```json
{
  "statusCode": 400,
  "errorCode": "VALIDATION_ERROR",
  "message": "amount must be a positive non-zero decimal string",
  "details": null,
  "requestId": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-09-02T00:00:00.000Z",
  "path": "/partner-api/v1/transfer-actions"
}
```

Store `X-Request-Id` with the partner's request log; retain the body `requestId`
as original-response context when present. FortVault may record a more specific internal
diagnostic code, but internal codes are not part of the public API response.

### 11.1 Public error codes

| Error code                        | Meaning                                                          | Recommended handling                                              |
| --------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------- |
| `VALIDATION_ERROR`                | Request data is invalid                                          | Correct the request; do not retry unchanged                       |
| `AUTHENTICATION_FAILED`           | JWT, client, key, time, or replay validation failed              | Generate a new JWT; verify client configuration                   |
| `INSUFFICIENT_SCOPE`              | API client lacks the endpoint scope                              | Update client scopes through an authorized process                |
| `FORBIDDEN`                       | The authenticated caller cannot perform the operation            | Check workspace access and authorization                          |
| `FEATURE_DISABLED`                | The workspace feature is disabled                                | Stop the workflow or contact the workspace administrator          |
| `RESOURCE_NOT_FOUND`              | A referenced resource is unavailable in this workspace           | Refresh identifiers; do not infer cross-workspace existence       |
| `CUSTOMER_NOT_FOUND`              | Customer is unavailable in this workspace                        | Refresh or correct the customer ID                                |
| `ACTION_NOT_FOUND`                | Action is unavailable in this workspace                          | Correct the action ID                                             |
| `CONFLICT`                        | Current state conflicts with the request                         | Read current state before deciding next steps                     |
| `ACTION_ALREADY_PROCESSED`        | Action is no longer pending                                      | Read the action and treat its current state as authoritative      |
| `ACTION_ALREADY_APPROVED`         | This approval has already been recorded                          | Read the action; do not submit the same approval again            |
| `ACTION_EXPIRED`                  | Approval window elapsed                                          | Create a new action if still required                             |
| `ACTION_SIGNER_NOT_AUTHORIZED`    | Wallet user or role lacks authority                              | Use the correct signer or update role configuration               |
| `INSUFFICIENT_BALANCE`            | Available balance cannot cover the transfer                      | Reduce the amount or wait for funds                               |
| `DESTINATION_NOT_ALLOWED`         | Destination is not eligible for this transfer                    | Select an active, permitted destination                           |
| `IDEMPOTENCY_KEY_REQUIRED`        | A write request omitted `Idempotency-Key`                        | Retry the same operation with a new key and fresh JWT             |
| `IDEMPOTENCY_KEY_INVALID`         | The key has an invalid length or character                       | Correct the key format and retry with a fresh JWT                 |
| `IDEMPOTENCY_KEY_REUSED`          | The key belongs to a different request                           | Do not retry with that key; investigate accidental key reuse      |
| `IDEMPOTENCY_REQUEST_IN_PROGRESS` | The original request is still running or has an uncertain result | Read the affected resource or action before taking further action |
| `RATE_LIMIT_EXCEEDED`             | Client exceeded its request limit                                | Back off and retry with a new JWT                                 |
| `SERVICE_UNAVAILABLE`             | A required service is temporarily unavailable                    | Retry safely with backoff and a new JWT                           |
| `NOT_IMPLEMENTED`                 | The requested behavior is not supported                          | Do not retry; use a supported operation                           |
| `INTERNAL_SERVER_ERROR`           | Unexpected server failure                                        | Record `requestId`; retry only according to safe retry rules      |

Clients must branch on `errorCode`, not exact `message` text. Messages can become
more specific without changing the public error category.

## 12. Rate Limits, Retries, and Uncertain Results

The current default limit is 120 requests per 60 seconds for an API client. An
environment can configure different values. The limit is shared across Partner
API endpoints for the same API client and uses fixed time windows.

When this limit is exceeded, the backend returns HTTP `429` with
`errorCode: "RATE_LIMIT_EXCEEDED"` and a `Retry-After` response header containing
an integer number of seconds (at least 1) until the next window. For example,
`Retry-After: 12` means wait at least 12 seconds before retrying. The error body
is unchanged. The delay reflects the window boundary, not the Redis cleanup TTL.

Honor `Retry-After` when present, optionally adding positive jitter. Concurrent
requests using the same client can consume the next window, so a retry can
still receive another 429. Generate a fresh JWT with a new `jti` for every retry:
the original JWT is consumed before rate-limit enforcement, including on 429.

Use bounded exponential backoff with jitter when the header is missing (for
example, a proxy-generated 429) and for temporary availability failures.
Every retry requires a newly generated JWT and `jti`.

Safe retry rules:

- Read requests can be retried with a fresh JWT.
- Write requests can be retried with the same `Idempotency-Key` and a fresh JWT.
- Never change the method, path, query, or body when reusing a key.
- If a write request times out after reaching FortVault, retry once with the
  same key. If it remains in progress, inspect the action list and relevant
  resources before deciding whether to create a new operation.
- For approval conflicts, read the action and accept its current server state.

Because a network timeout can occur after the server accepted a mutation, the
partner should retain request timestamps, non-secret correlation metadata, and
returned action IDs.

## 13. Security Requirements

- Generate separate Ed25519 credentials for each environment and operational
  purpose.
- Never send a private key to FortVault.
- Store private keys in an HSM or managed secret store where practical.
- Apply least-privilege API scopes.
- Separate initiator and approver identities when policy or governance requires
  separation of duties.
- Never log JWTs, authorization headers, private keys, action signatures, or
  complete signed payloads.
- Validate HTTPS certificates; do not disable TLS verification.
- Synchronize system clocks.
- Treat all identifiers and API responses as workspace-scoped.
- Preserve exact integer amounts in base units.
- Rotate or revoke an API client immediately if its private key may be exposed.

## 14. Integration Checklist

### Before development

- [ ] Confirm the environment base URL and audience.
- [ ] Open the Partner API Swagger UI.
- [ ] Generate and protect an Ed25519 API key pair.
- [ ] Register the public key and record the API Client ID.
- [ ] Select the minimum required scopes.
- [ ] Configure action-signing users and role permissions.
- [ ] Review workspace approval policies.

### Before production use

- [ ] Generate a new JWT for every request and retry.
- [ ] Generate one `Idempotency-Key` per logical write and retain it for retries.
- [ ] Verify replay and expired-token handling.
- [ ] Verify same-key replay, payload mismatch, and in-progress handling.
- [ ] Use arbitrary-precision amount handling.
- [ ] Implement pagination and rate-limit backoff.
- [ ] Store action IDs and `X-Request-Id` from every response, plus error-body `requestId` when present.
- [ ] Handle policy-dependent zero, one, or multiple approvals.
- [ ] Test signer-role failures and scope failures.
- [ ] Test uncertain mutation results without blind retries.
- [ ] Confirm transaction-finality handling for every supported chain.
- [ ] Establish credential rotation and revocation procedures.

## 15. Troubleshooting

### Authentication fails on every endpoint

Check that `kid`, `iss`, and `sub` all contain the API Client ID, the algorithm is
`EdDSA`, the audience matches the environment, the token has not expired, the
host clock is correct, and the client is active.

### Authentication works once and then fails

The same JWT or `jti` is probably being reused. Generate a fresh token for every
HTTP request.

### Read works but an action fails

Check both authorization layers: the API client's action scope and the EIP-712
signer's FortVault role permission. Also verify that the canonical signed payload
matches current server-side names and metadata.

### An action remains pending

Read the action and review the workspace policy. It may still require one or
more approvals, including a mandatory-role approval.

### An action is approved but no transaction is visible

Approval and blockchain settlement are different stages. Query transactions and
apply the chain-specific confirmation policy. If the condition persists, report
the action ID and public error/request correlation IDs without sending secrets.

## 16. Compatibility Rule

Partner API v1 consumers should ignore unknown response fields and branch only
on documented enum and error-code values. A new endpoint, scope, or optional
field can be added without changing the base version. A breaking request or
response change requires a new version or an explicitly coordinated migration.

If this guide and the Partner API Swagger document disagree, stop the affected
integration work and confirm the contract with FortVault. Do not infer behavior
from the dashboard API or undocumented backend routes.

## 17. Planned Exchange Integration

**Status: proposed scope for partner discussion, not an implemented API.**
Endpoint names, schemas, scopes, limits, and delivery dates require agreement.
This section does not add functionality to the current release or supersede its
Swagger specification. The final extension will be documented in Swagger and
this guide when implemented and accepted.

### 17.1 Product boundary

FortX Connect owns customer trading, balances, exposure calculations, risk-based
reconciliation, and decisions to mirror individual trades. FortVault receives
authorized swap requests and returns execution results. Both per-order
mirroring and net reconciliation use the same swap interface; neither requires
a FortX-specific reconciliation endpoint in FortVault.

One asset-pair reconciliation may produce one logical swap. A multi-asset cycle
may require several swaps. Each swap executes on one eligible, sufficiently
funded exchange account. The initial scope excludes cross-exchange splitting
and automatic funding transfers between exchange accounts.

### 17.2 Proposed new calls

All paths below are relative to `/partner-api/v1` and are proposals only.

| Method and proposed path | Purpose |
| --- | --- |
| `GET /exchange-accounts` | Discover authorized connected accounts, status, and trading eligibility without exposing credentials. |
| `GET /exchange-accounts/{id}/balances` | Read available and reserved exchange balances, with observation time and freshness information. |
| `GET /swap-markets` | Discover eligible currency pairs, account availability, amount modes, precision, and minimum trading amounts. |
| `POST /swap-quotes` | Obtain a fee-aware quote and select one eligible account using executable pricing for the requested size. Does not submit an exchange order. |
| `POST /swap-actions/typed-data` | Prepare canonical swap initiation typed data from the server-resolved quote and execution limits. Does not initiate or execute the swap. |
| `POST /swap-actions` | Initiate a signed, idempotent swap action under the applicable business policy and approval requirements. |
| `GET /swaps` | List authorized swap execution records, with proposed filters for account, status, date range, and partner reference. |
| `GET /swaps/{id}` | Read execution status, actual input and output, fees, fills, and any remaining unfilled quantity. |

Exchange-account connection and credential administration may remain in the
backoffice for the initial delivery. An account being connected does not prove
that it has trading permission, current liquidity, or sufficient available funds.
Exchange records and fills must remain distinct from the blockchain movements
returned by the current `GET /transactions` endpoint.

### 17.3 Existing action calls to extend

The following calls already exist for supported actions. **Their support for
swap actions is proposed and is not available merely because the routes exist.**

| Existing call | Proposed extension |
| --- | --- |
| `GET /actions` and `GET /actions/{id}` | Discover and inspect authorized swap actions and their related execution identifiers. |
| `POST /actions/{id}/typed-data` | Prepare canonical approval, rejection, or pending-action cancellation payloads for swaps. |
| `POST /actions/{id}/approve` | Approve a swap action according to its policy; approval is not proof of execution. |
| `POST /actions/{id}/reject` | Reject a swap action that remains eligible for rejection. |
| `POST /actions/{id}/cancel` | Cancel a pending swap action where permitted; this does not cancel an order already submitted to an exchange. |
| `GET /action-types` and `GET /capabilities` | Discover enabled swap support and the authenticated client's effective permissions. |

Provider-order cancellation, if required, needs a separate agreed execution
contract. It must not be inferred from pending-action cancellation.

### 17.4 Contract requirements

- **Amounts:** distinguish exact-input conversions, such as spending 1,000 USDT,
  from target-output requests, such as acquiring 3 BTC within a maximum spend.
  Define net-of-fee quantities, minimum output or maximum input, rounding,
  partial fills, and residual handling. A quantity target is not a guaranteed
  fill. Currency identity and market precision must be explicit; a swap does
  not itself select a blockchain network or move funds between networks.
- **Quotes:** specify the selected account, amounts, fees, expiry, permitted
  price deviation, and whether a quote reserves funds or guarantees any terms.
  An indicative price is not an executable quote. Revalidation must not silently
  change the account or broaden signed execution limits.
- **Authorization:** retain workspace isolation, API-client authentication,
  resource permissions, exact action-payload binding, and applicable signing
  and approval controls. Automation must not bypass them. Credentials remain
  server-side. Final resource-specific scope names will be agreed before release.
- **Execution records:** distinguish action approval from order submission,
  partial fills, completion, failure, and unresolved outcomes. Report exact
  amounts, fee currencies, stable execution/fill identifiers, and timestamps.
  Detailed schemas, status values, ordering, and pagination remain to be agreed.
- **Correlation and retries:** a proposed workspace-scoped `externalReference`
  links a swap to a partner trade or reconciliation cycle. Its uniqueness and
  lookup rules must be defined separately from `Idempotency-Key` behavior.
  Preserve request correlation and safe retry semantics. Reconcile uncertain
  execution on the original account before replacement or rerouting.

### 17.5 Proposed execution updates and recovery

For reliable production synchronization, the recommended extension includes
signed execution-update webhooks and a recoverable event feed:

| Method and proposed path | Purpose |
| --- | --- |
| `GET /events?cursor=...` | Retrieve authorized durable execution updates after an opaque cursor, including updates to previously created swaps. |

This feed and webhook delivery are also proposed, not current capabilities.
Delivery must define event identifiers, signatures and replay protection,
duplicate and out-of-order handling, retention, expired-cursor recovery, and
subscription administration. Cursor semantics must account for committed events;
a raw auto-increment identifier or offset-paginated list is not by itself a
lossless synchronization contract.

### 17.6 Intended integration flow

1. Discover eligible accounts, balances, and markets.
2. Request a quote for the required conversion and execution limits.
3. Prepare typed data, sign the exact payload, and initiate the swap action.
4. Complete any approvals required by policy before execution.
5. Track the swap through its actual execution outcome, including partial or
   unresolved results.
6. Apply confirmed fills and fees to the partner's customer accounting or
   reconciliation cycle without treating action approval as a completed trade.

The [FortX Connect overview](../FORTX_CONNECT_PRODUCT_DESCRIPTION.md) describes
the consuming exchange core. The [FortVault Custody overview](../FORTVAULT_CUSTODY_PRODUCT_DESCRIPTION.md)
describes the custody and proposed single-account swap execution boundary.
