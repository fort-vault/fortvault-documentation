# FortVault Weekly Release Notes

**Partner Update**  
**Week ending:** May 15, 2026

## Overview

This release focused on custody operations, archive workflows, stronger address verification, improved reporting controls, and Bitcoin transaction reliability. The changes improve day-to-day back-office usability and add an independent verification path for generated custody addresses.

## Key Updates

### 1. Customer Whitelist Scope Cleanup

Customer whitelist records were removed from the global whitelist list. Customer-specific whitelist records are now handled in the correct customer/vault context, reducing confusion between global whitelist entries and customer-owned address records.

### 2. Whitelist Archive

Archive support was added for whitelist records. This allows operators to hide retired or inactive whitelist entries without permanently deleting historical records.

### 3. Customer Archive

Archive support was added for customers. Operators can now archive customers that should no longer appear in active operational views while preserving their historical data.

### 4. Vault Archive

Archive support was added for vaults. This helps separate active vaults from closed or inactive vaults while keeping the audit trail available.

### 5. Vault and Customer Address Archive

Archive support was added for vault/customer addresses. Old deposit or custody addresses can now be removed from active views while remaining available for history, audit, and reconciliation.

### 6. Wallet Type Visibility

The vault list now shows the wallet type directly in the table. Operators can identify whether a vault is Hot, Cold, Gas, or another configured partner wallet type without opening the vault details page.

### 7. Reports Archive and Type Filters

Reports now support archived data more consistently. Report pages include archive status filtering, and whitelist reports can distinguish between Global and Customer whitelist records. This makes operational reporting clearer while preserving access to historical archived records.

### 8. Application Footer and Version Display

A footer was added to the authenticated application layout with the FortVault copyright notice and application version 1.0.0. This gives operators and support teams a consistent way to identify the running application version.

### 9. MPC Address Attestation and Smart Contract Verification

Generated custody addresses now include MPC-based attestation proof. This proof can be stored and shown to users or operators so they can independently verify that an address was generated from FortVault-controlled MPC key material.

A smart contract verification flow was added so the proof can be checked independently outside the FortVault backend and frontend. This is important for trust minimization: even if the UI or backend is unavailable or suspected to be compromised, an operator can verify the address proof against the smart contract.

### 10. MPC Bootstrap Mode for Secure Root Generation

MPC nodes now support a dedicated `BOOTSTRAP_MODE` for initial root generation. During bootstrap mode, key generation is enabled so root keys can be generated for partner setup and recovery preparation, while normal signing and derivation APIs are blocked.

After bootstrap is completed, MPC nodes are restarted in normal mode. In normal mode, key generation is disabled, reducing the risk of accidental or unauthorized new root generation during daily operations.

### 11. Bitcoin Multi-UTXO Transaction Fix

Bitcoin transaction handling was fixed for cases where the requested transfer amount must be assembled from multiple UTXO addresses. This improves reliability for BTC withdrawals when funds are fragmented across several smaller unspent outputs.

## Security and Processing Improvements

Processing and MPC transfer authorization checks were strengthened. Transfer payload validation now has stricter consistency checks before signing and broadcasting.

EIP-712 signature domain validation was added to reduce the risk of accepting signatures produced for the wrong signing domain.

MPC bootstrap mode was added to separate setup-time key generation from normal transaction execution. This gives partners a clearer operational flow for root generation, backup/export preparation, and safe production runtime.

## Notes

These changes are part of the continuing FortVault custody service hardening effort. The main focus is to make operational flows clearer, make generated addresses independently verifiable, improve reporting visibility, and reduce edge-case failures in transaction processing.
