# FortVault MPC - High-Level Description

## Purpose

FortVault MPC is the threshold-signing component of the FortVault custody platform. It is responsible for distributed key generation, deterministic child-key derivation, and transaction signing without reconstructing a full private key on any single machine.

The MPC service is intentionally separated from the backend and frontend. Backend users can request custody actions, but they cannot directly access private keys or produce blockchain signatures. Final signing is performed only through the processing service and the MPC cluster.

## System Role

FortVault uses a multi-service custody architecture:

- `fortvault-backend` creates business actions and approval records.
- `fortvault-processing` validates executable custody commands, prepares transactions, and calls MPC.
- `fortvault-mpc` performs distributed cryptographic operations.
- Blockchain RPC endpoints are used by processing for transaction construction, broadcast, and confirmation handling.

In the target architecture, `fortvault-processing` is the only service expected to call MPC for key, derivation, and signing operations.

## MPC Cluster Model

The MPC cluster is composed of multiple MPC nodes. The deployment model is configurable. For example, a deployment may use:

- 3 MPC parties.
- A 2-of-3 signing threshold.
- One node configured as the API-facing master node for initiating ceremonies.
- Peer-to-peer communication between MPC nodes for threshold protocol rounds.

The master node coordinates requests but does not independently hold enough key material to sign transactions.

## Key Generation

MPC key generation creates distributed key shares across participating nodes. The private key is never assembled in one place.

High-level flow:

1. Processing or an operator initiates a key generation request through the MPC API.
2. MPC nodes run a distributed key generation protocol.
3. Each node stores its own encrypted key share in its local database.
4. The generated public key/root address can be used by processing as a root for future address derivation.

The MPC design supports ECDSA key generation for EVM, Tron, and Bitcoin signing flows. EDDSA can also be supported by the MPC codebase for chains or assets that require it.

## Address Derivation

FortVault processing uses pregenerated MPC root keys and derives child public keys for generated vault/customer addresses.

High-level flow:

1. Processing receives a `generate_address.process` event.
2. Processing selects/reserves a partner root from its root pool.
3. Processing reserves a deterministic derivation index.
4. Processing calls MPC `/tss/derive` with:
   - root public key,
   - derivation index,
   - wallet type.
5. MPC derives the child public key.
6. MPC can collect public-key attestations from the MPC nodes.
7. Processing stores/publishes the generated address and attestation proof to backend.

Supported address formats include:

- EVM address from secp256k1 public key.
- Tron address from secp256k1 public key.
- Bitcoin mainnet P2WPKH address from secp256k1 public key.

### Address Attestation During Derivation

Address attestation is designed to let a partner or auditor verify that an address shown by FortVault was generated from MPC-controlled key material.

Processing calls only the API-facing master MPC node. Processing does not call each MPC node directly.

During `/tss/derive` with public-key attestation:

1. The master MPC verifies that the required MPC nodes are available.
2. The master MPC derives the child public key locally.
3. The master MPC converts the derived compressed child public key into uncompressed secp256k1 public-key form.
4. The master MPC builds an attestation payload:

```json
{
  "walletType": "customer",
  "publicKey": "0x04...",
  "issuedAt": 1770000000
}
```

5. The master MPC signs the payload with its own address-attestation key.
6. The master MPC sends the same derivation message and attestation context to each remote MPC node over the existing encrypted gRPC transport.
7. Each remote MPC node derives/stores the child key locally, verifies the public key and wallet type, signs the same attestation payload, and returns its signature.
8. The master MPC verifies every returned attestation signature before returning the proof to processing.

The proof returned by MPC has the following shape:

```json
{
  "walletType": "customer",
  "publicKey": "0x04...",
  "issuedAt": 1770000000,
  "signatures": [
    {
      "nodeId": "<mpc-node-id>",
      "signer": "0x...",
      "signature": "0x..."
    }
  ]
}
```

The strict address-attestation mode can be configured so that:

- all required MPC nodes must be available,
- all required MPC nodes must derive/store the child key,
- all required MPC nodes must sign the attestation payload,
- the master must verify all returned signatures,
- otherwise `/tss/derive` fails.

The attestation signer key is separate from the MPC custody key share. It proves that an MPC node attested the derived public key and wallet context; it does not allow custody signing or fund movement.

The visible blockchain address is verified separately by deriving the address from the attested public key according to the selected address format, such as EVM, Tron Base58, or Bitcoin P2WPKH.

## Transaction Signing

Processing builds and validates transaction payloads before asking MPC to sign.

High-level flow:

1. Backend creates and approves a transfer action.
2. Processing consumes the transfer process event.
3. Processing validates chain, asset, wallet type, source address, destination address, amount, EIP-712 signature domain, approval signatures, and policy context.
4. Processing builds an unsigned transaction.
5. Processing calls MPC `/tss/sign` with the raw transaction and the full transfer authorization payload.
6. MPC independently verifies the transfer authorization payload, including signature domain, signed payload freshness, approval signatures, and on-chain policy checks.
7. MPC validates the raw transaction against network-specific validators and checks that the transaction facts match the authorization payload.
8. MPC nodes execute a threshold signing ceremony.
9. Processing receives the signature, builds the final transaction, and broadcasts it.

### Independent Approval Verification

MPC can be configured to independently verify action approvals before participating in transaction signing.

In this model, admin/operator approvals are represented as cryptographic signatures over an immutable action payload. Before signing a transaction, MPC verifies these approvals against the same policy source used by backend and processing, including on-chain smart-contract policy checks where applicable.

This creates an additional defense layer:

- backend validates approvals before publishing executable actions,
- processing validates approvals before transaction construction,
- MPC re-validates approvals and policy before threshold signing.

The intended result is that even if an upstream service is compromised, MPC nodes do not blindly sign a transaction unless the required admin/operator signatures and policy conditions are valid.

For transfer authorization, the signed EIP-712 domain is expected to be:

```json
{
  "name": "FortVault",
  "version": "1",
  "chainId": 1
}
```

Processing validates this domain before transaction construction. MPC validates the same domain before signing. MPC also enforces a signed-payload freshness window so stale approvals cannot be replayed indefinitely.

MPC policy-token hashing follows the smart-contract convention:

- action types and asset types are trimmed/lowercased before hashing, for example `transfer.process` and `usdt`,
- wallet types are normalized to lowercase kebab-case before hashing, for example `Customer Cold` becomes `customer-cold`.

## Network Validators

MPC contains network-specific transaction validation before signing:

- EVM native and ERC-20 transfer validation.
- Tron native and TRC-20 transfer validation.
- Bitcoin native transfer validation.

The validator layer is designed so MPC does not blindly sign arbitrary payloads. It checks transaction structure and applies wallet-type policy restrictions before participating in signing.

## Wallet-Type Guardrails

MPC can enforce wallet-type transfer restrictions. Wallet types are normalized to lowercase.

Example wallet-type behavior:

- `hot`: registered wallet type with no MPC transfer limits.
- `cold`: policy-limited wallet type.
- `warm`: policy-limited wallet type.

Policy windows include:

- 15 minutes.
- 1 hour.
- 24 hours.
- 7 days.
- 30 days.

Policies are enforced per supported network and asset class. Native assets and stablecoins are handled separately where applicable.

## Supported Chains and Assets

MPC support can include:

- Ethereum / EVM:
  - native ETH-like assets,
  - USDT,
  - USDC.
- Avalanche / EVM:
  - native AVAX,
  - USDT,
  - USDC.
- Tron:
  - native TRX,
  - USDT,
  - USDC.
- Bitcoin mainnet:
  - native BTC.

Bitcoin support can target mainnet native BTC and P2WPKH-style addresses.

## Key Storage

Each MPC node stores its own key material locally. Key parts are encrypted before storage using the configured key-parts encryption key.

Important properties:

- No single MPC database should contain enough information to independently sign.
- Key shares are node-local.
- Recovery tooling exists for controlled extraction and offline/manual recovery flows.

## Recovery Tooling

The MPC repository includes:

- `extractor`: extracts and encrypts MPC node key parts from a node database.
- `recovery`: performs a recovery/manual signing ceremony from extracted key parts.

These tools are intended for emergency or controlled operational recovery scenarios and should be access-controlled separately from normal runtime services.

## External Interfaces

Primary MPC API endpoints include:

- `POST /tss/keygen`
- `POST /tss/derive`
- `POST /tss/sign`
- `GET /tss/session`

The OpenAPI/Swagger description is available in:

- `fortvault-mpc/docs/swagger.yaml`

## Security Boundaries

The key security boundary is separation between business authorization and cryptographic signing:

- Backend/frontend can initiate and approve actions.
- Processing decides whether an approved action should be executed.
- MPC performs threshold cryptographic operations only after processing sends a valid request.
- MPC validators reduce the risk that a compromised caller can make MPC sign arbitrary transactions.

## Operational Assumptions

The MPC security model assumes:

- MPC nodes are deployed on separate infrastructure or isolated trust domains where possible.
- MPC node databases are not co-located in a way that collapses the threshold-security model.
- Node identity keys and key-parts encryption keys are protected.
- Address-attestation private keys are protected separately from custody key shares.
- Public attestation signer addresses in MPC node configuration match the signer set configured in the on-chain address verifier.
- Processing is the only production component allowed to call MPC signing endpoints.
- Network and database access to MPC nodes is restricted.

## Known Limitations and Audit Notes

- Bitcoin support may be limited to native BTC depending on deployment scope.
- Bitcoin transfer validation supports a constrained transaction shape and should be reviewed carefully against expected production BTC flows.
- The policy layer is partly enforced in MPC code and partly represented in smart contracts/off-chain services. Auditors should review both layers together.
- Transfer authorization is intentionally checked in multiple layers. Backend, processing, and MPC must keep EIP-712 field construction, domain rules, token normalization, and policy-token hashing aligned.
- MPC-side transfer authorization returns generic API errors to callers while detailed rejection reasons are logged by the MPC node. Operational monitoring should include MPC logs for audit and incident analysis.
- Address attestation proves that an MPC node set attested a derived public key and wallet context. It is not a replacement for transaction authorization, transaction validation, or threshold transaction signing.
- Runtime security depends on deployment isolation, secret management, and network ACLs in addition to source-code controls.

## Relevant Source Areas

- `fortvault-mpc/controller/keygen.go`
- `fortvault-mpc/service/masternode.go`
- `fortvault-mpc/keygen/`
- `fortvault-mpc/networks/`
- `fortvault-mpc/attestation/`
- `fortvault-mpc/repository/db/`
- `fortvault-processing/src/modules/processing/services/generate-address-process.service.ts`
- `fortvault-processing/src/modules/processing/services/transfer-process.service.ts`
- `fortvault-processing/src/modules/processing/services/transfer-sign.service.ts`
