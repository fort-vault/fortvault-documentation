# FortVault Smart Contracts - High-Level Description

## Purpose

FortVault smart contracts provide an on-chain policy and registry layer for the custody platform. They define action types, wallet types, asset types, business roles, role assignments, and policy rules used by backend, processing, and MPC-related services.

The contracts are not themselves a token custody vault. They do not hold customer funds and do not directly execute asset transfers. Instead, they act as a policy registry and verification layer for off-chain custody services.

## Contract Set

The smart-contract package can include:

- `FortVaultRegistry`
- `FortVaultPolicyEngine`
- `FortVaultAddressVerifier`

Together, these contracts model:

- Which action types are recognized.
- Which wallet and asset types are recognized.
- Which operational roles exist.
- Which blockchain addresses hold those roles.
- Which roles can process or approve actions under configured amount ranges.
- Whether an MPC-generated address proof is valid.

## FortVaultRegistry

`FortVaultRegistry` is the base registry and access-control contract.

It stores:

- Action type definitions.
- Wallet type definitions.
- Asset type definitions.
- Business role definitions.
- Address-to-role assignments.
- Action metadata flags.

Action metadata flags define whether an action requires:

- wallet type,
- asset type,
- amount,
- approve-action semantics.

Examples of configured action types include:

- `transfer.process`
- `transfer.approve`
- `whitelist_address.process`
- `whitelist_address.approve`
- `generate_address.process`
- `generate_address.approve`

### Registry Roles

The registry uses OpenZeppelin `AccessControl`.

Important roles:

- `DEFAULT_ADMIN_ROLE`: contract administration.
- `MODERATOR_ROLE`: registry/policy configuration authority.

Only accounts with the moderator role can configure action specs, wallet types, asset types, business roles, and address role assignments.

### Registry Versioning

`FortVaultRegistry` maintains `registryVersion`.

The version is incremented when registry state changes. Off-chain services can use this as a signal that cached policy/registry data may need refresh.

## FortVaultPolicyEngine

`FortVaultPolicyEngine` stores and evaluates process/approval policies.

It references `FortVaultRegistry` as the source of truth for:

- known action types,
- known wallet types,
- known asset types,
- known roles,
- role assignments.

The policy engine uses tuple keys:

```text
actionType + walletType + assetType
```

These tuple keys are used to configure policies for specific combinations, for example:

```text
transfer.process + cold + usdt
transfer.approve + cold + eth
generate_address.approve + customer + none
```

Off-chain services must hash policy tokens using the same convention as the contracts:

- action types are string names such as `transfer.process` and `transfer.approve`,
- asset types are normalized string symbols such as `eth`, `usdt`, or `usdc`,
- wallet types are normalized to lowercase kebab-case before hashing, such as `customer`, `hot`, or `customer-cold`.

Backend, processing, and MPC must keep this normalization aligned because policy checks are executed by off-chain services before custody actions are completed.

## Process Policies

Process policies define whether a role is allowed to initiate/process an action for a given tuple and amount segment.

For amount-based actions, policy ranges are represented as ordered upper-bound segments.

Example concept:

```text
0 - 1,000 USDT: payment role may process
1,000 - 50,000 USDT: senior/payment-head role may be required
```

The exact values are configured through bootstrap policy JSON and contract write calls.

## Approval Policies

Approval policies define how many approvals are required and which roles can satisfy those approvals.

Approval policies can include:

- required total approval count,
- role-specific approval requirements,
- ordered/staged approval rules.

This allows FortVault to express workflows such as:

- one approval from a specific role,
- multiple approvals from different roles,
- staged approvals where some roles must approve before others.

## Amount Segmentation

The policy engine supports half-open amount ranges represented by upper bounds.

For an amount-based tuple, the configured bounds divide amounts into segments. Each segment can have different process and approval rules.

This allows policy to become stricter as transaction amount increases.

## FortVaultAddressVerifier

`FortVaultAddressVerifier` verifies address attestation proofs.

It is designed to validate that an address was generated/attested by a trusted signer set for a specific:

- address,
- address format,
- wallet type,
- public key,
- issuance timestamp.

The verifier stores:

- trusted signer list,
- active signer count,
- required signature threshold.

Verification succeeds only if enough unique trusted signers signed the expected attestation digest.

This contract can be used by external systems or partners to verify that a generated address belongs to the expected FortVault MPC-controlled context.

## Address Attestation Digest

Address attestation binds the proof to:

- FortVault attestation domain,
- wallet type,
- derived public key,
- issued-at timestamp.

The MPC attestation payload signs the derived public key and wallet context, not the final visible blockchain address:

```json
{
  "walletType": "customer",
  "publicKey": "0x04...",
  "issuedAt": 1770000000
}
```

The verifier receives the visible address and address format separately, then derives/checks the address from the attested public key.

Expected address-format values can include:

- `evm`
- `tron-base58`
- `btc-p2wpkh`

This keeps MPC focused on key ownership while the verifier contract handles address-format validation. For example, the same ECDSA public key can be represented as an EVM address, a Tron address, or a Bitcoin P2WPKH address, depending on the selected format.

The verifier validates that enough unique trusted MPC attestation signers signed the expected digest. The threshold and signer set are configured in the verifier contract.

The proof can be kept intentionally compact and does not need to include salt, verifier contract address, or verifier chain ID when verification is based on possession of the signed proof and the verifier contract's trusted signer set.

## Bootstrap Policy

Policy and registry state are configured from JSON bootstrap files.

Example bootstrap files:

- `bootstrap-policy-metax.json`
- `bootstrap-policy-fv-custody.json`

Bootstrap config includes:

- action specs,
- wallet types,
- asset types,
- roles,
- address-role mappings,
- process bounds,
- process allowed roles,
- approve bounds,
- approve policies.

Bootstrap scripts are intended to be idempotent, applying only missing or changed policy state.

## Administrative API and Scripts

The contract repository includes:

- deployment scripts,
- policy bootstrap scripts,
- a local admin API for read/write operations,
- tests for registry and policy behavior.

Key scripts:

- `scripts/deploy-fortvault.ts`
- `scripts/bootstrap-policy.ts`
- `scripts/admin-api/server.js`

## Security Boundaries

The smart contracts are a policy/control plane, not the custody execution plane.

They do not directly:

- hold funds,
- broadcast transactions,
- sign transactions,
- replace MPC signing controls.

They do:

- define recognized policy vocabulary,
- assign roles to addresses,
- expose policy checks/configuration for off-chain enforcement,
- provide an on-chain source of truth for policy state.

Transfer execution services use the policy contracts as a read-only authorization source before signing/broadcasting. Processing checks policy before constructing executable transactions, and MPC can independently re-check policy before participating in threshold signing.

## Operational Assumptions

The smart-contract security model assumes:

- moderator/admin private keys are protected.
- policy bootstrap is reviewed before execution.
- off-chain services correctly query and enforce policy results.
- policy changes are treated as privileged operational changes.
- address-role assignments correspond to real authorized human/operator wallets.

## Audit Notes

Auditors should review:

- access-control boundaries in `FortVaultRegistry`.
- policy tuple validation in `FortVaultPolicyEngine`.
- amount-bound insertion/replacement behavior.
- approval rule replacement and validation.
- role assignment and revocation behavior.
- version counters and event emissions.
- address-attestation digest construction in `FortVaultAddressVerifier`, including exact field order and string normalization rules.
- trusted signer uniqueness and threshold enforcement in `FortVaultAddressVerifier`.
- whether the verifier digest matches the MPC attestation digest implementation.
- whether processing and MPC policy-token normalization exactly matches contract bootstrap data.
- bootstrap scripts and policy JSON used in production.
- whether off-chain services correctly enforce contract policy outputs.

## Relevant Source Areas

- `fortvault-contracts/contracts/FortVaultRegistry.sol`
- `fortvault-contracts/contracts/FortVaultPolicyEngine.sol`
- `fortvault-contracts/contracts/FortVaultAddressVerifier.sol`
- `fortvault-contracts/scripts/deploy-fortvault.ts`
- `fortvault-contracts/scripts/bootstrap-policy.ts`
- `fortvault-contracts/scripts/admin-api/server.js`
- `fortvault-contracts/test/FortVaultRegistry.ts`
- `fortvault-contracts/test/FortVaultPolicyEngine.ts`
- `fortvault-contracts/test/FortVaultAddressVerifier.ts`
- `bootstrap-policy-metax.json`
- `bootstrap-policy-fv-custody.json`
