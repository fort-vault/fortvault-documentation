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
- chain type,
- wallet type,
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
- generated address,
- chain type,
- wallet type,
- issued-at timestamp.

The attestation payload can use chain type instead of full chain reference:

```json
{
  "chainType": "evm",
  "walletType": "customer",
  "address": "0x...",
  "issuedAt": 1770000000
}
```

Expected chain-type values include:

- `evm`
- `tron`
- `utxo`

This reflects the fact that address ownership is tied to address/key family, not necessarily to one specific EVM network. For example, the same ECDSA public key controls the same `0x...` address across Ethereum, Avalanche, Horizon, and other EVM-compatible networks.

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
