# Partner API Integration Guide

Status: Implemented interface guide

API version: `v1`

Last reviewed: 2026-09-18

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
  `IDEMPOTENCY_REQUEST_IN_PROGRESS` with HTTP `409`.
- A replayed response includes `Idempotency-Replayed: true`.
- Successful responses and deterministic `4xx` responses are replayed.
- An unexpected `5xx` leaves the request in an uncertain processing state to
  prevent automatic duplicate execution. Read the affected resource or action
  before deciding whether a new operation is necessary.

After 24 hours, the same key may execute again and must not be used as a
permanent business identifier.

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

## 6. Pagination and Filtering

List endpoints accept:

| Parameter | Default | Rules                         |
| --------- | ------- | ----------------------------- |
| `skip`    | `0`     | Integer, minimum `0`          |
| `take`    | `50`    | Integer from `1` through `50` |
| `order`   | `DESC`  | `ASC` or `DESC`               |

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
Use the vault type `id` in `POST /vaults`. Customer vault types are selected
internally by `POST /customers` and are not returned by this endpoint.

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

For action creation, use the maintained FortVault integration helper or
reference client. Do not independently guess canonical labels from IDs. If no
helper is available for the target language, confirm the exact typed-data
contract with FortVault before implementing action creation.

### 8.3.1 Exact status-change initiation payloads

These rules cover the six customer, regular-vault, and vault-address-asset
archive/activate endpoints in section 5.3. There is no initiation typed-data
preparation endpoint for these requests. The existing action typed-data endpoint
prepares review/cancellation only, after an action exists.

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
| Whitelist creation/status review | Initiation is not exposed through Partner API | `vaults:actions:whitelist:review` |
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

### 10.1 Initiate

```http
POST /partner-api/v1/transfer-actions
Authorization: Bearer <NEW_JWT>
Content-Type: application/json
```

```json
{
  "fromAddress": "0x1111111111111111111111111111111111111111",
  "toAddress": "0x2222222222222222222222222222222222222222",
  "assetId": "5b7a1100-f1d1-4f16-b91d-1b22421ed234",
  "amount": "1.5",
  "signedPayload": "<SERIALIZED_EIP_712_TYPED_DATA>",
  "signature": "<EIP_712_SIGNATURE>"
}
```

Rules include:

- Source and destination must be valid for the asset's chain.
- Source address, asset, signer, and destination must belong to or be eligible
  for the authenticated workspace.
- The source must have sufficient available balance.
- The decimal string must not exceed the asset's supported precision.
- A whitelist destination must be active and eligible for the source vault.
- Archived whitelist addresses cannot be used for new transfers.
- Internal whitelist addresses are not eligible for customer vault transfers.

FortVault can also recognize eligible partner vault or exchange deposit
destinations. Destination rules are enforced by the backend; do not rely on
client-side filtering as authorization.

### 10.2 Approve, reject, and monitor

Use the shared action approve, reject, or cancel endpoint with a fresh JWT and
the corresponding EIP-712 payload. Poll `GET /actions/{id}` for the action
lifecycle and use `GET /transactions` for observed transaction movements.

The action status values currently exposed by Partner API v1 are:

- `pending`
- `approved`
- `canceled`
- `expired`

`approved` means the action passed its required approval state. It does not by
itself prove that a blockchain transaction is finalized. Use transaction data
and the applicable operational confirmation rules for settlement decisions.

## 11. Error Contract

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

Store `requestId` with the partner's request log. Supply it to FortVault support
when investigating a failure. FortVault may record a more specific internal
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
- [ ] Store action IDs and public error `requestId` values.
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
