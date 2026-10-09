# FortVault Offline MPC Architecture

## Status

This document records the intended offline ECDSA MPC architecture and the security invariants that changes must preserve. It does not claim that every transport and recovery step is fully implemented.

Current repository status:

- `fortvault-cold-signer` documents and implements development mobile participation in interactive secp256k1 ECDSA TSS key generation and signing, protected local share storage, request validation, and QR/wired transport components.
- `fortvault-bootstrap-station` is a development macOS prototype. Its current README states that it can discover a wired iPhone and redeem a development authorization, but does not yet run MPC rounds or transfer a generated share to the phone.
- Neither application is production-ready or independently security-audited.

When implementation and this intended architecture differ, report the gap. Do not rewrite the security invariant to match incomplete or insecure behavior.

## Trust Model

- Backend, Processing, Redis, frontend, Bootstrap Station, transport envelopes, and online MPC participants are not sufficient individually to authorize an offline signature.
- Cold Signer must independently validate the coordinator identity, purpose, action, signing session, root, participants, payload hash, round number, expiry, and round ordering before participating.
- Processing coordinates ceremonies but is not an independent authorization authority.
- MPC must independently validate the signing request and available authorization evidence before producing a signature.
- A transport or device-identity signature authenticates an envelope; it is not the threshold MPC signature over the transaction.
- Private MPC shares remain inside their intended participant boundary and must never be serialized into QR, wired, Redis, backend, or log payloads.

## Intended Root Bootstrap Flow

1. An administrator with the required bootstrap permission requests a short-lived, bootstrap-only authorization from Backend.
2. Bootstrap Station creates an ephemeral device identity and redeems the one-time authorization with proof bound to that identity.
3. Processing enters explicit bootstrap mode and requests the configured online and offline root pool.
4. For an offline root, Processing coordinates the online MPC participants and the temporary offline participant.
5. Bootstrap Station transports signed ceremony requests and responses between the coordinator and Cold Signer over the authorized wired channel.
6. Cold Signer validates the request context and participates as a real ECDSA TSS party.
7. MPC persists completed root public/session metadata. Cold Signer stores only its completed private share under device-local protection.
8. An authorized recovery workflow exports encrypted recovery material and verifies that it corresponds to the completed public root before durable storage.

Bootstrap and ceremony payload state in Backend and Processing is intentionally transient in the current design. MPC owns protocol-session and root metadata. Restart or resume behavior must be designed explicitly across Backend, Processing, MPC, Bootstrap Station, and Cold Signer; do not add partial persistence in one service and claim the ceremony is resumable.

## Intended Offline Transaction Signing Flow

1. Backend completes the normal action, reconstructed-payload verification, policy, and approval flow.
2. Backend submits the approved transfer to Processing using the shared durable command contract.
3. Processing constructs the exact chain transaction and requests signing from the partner's MPC cluster.
4. Online participants continue through MPC transport while the offline participant's rounds are exposed as signed, bounded envelopes.
5. Backend exposes pending offline rounds to the authenticated frontend without changing their signed context.
6. The frontend displays request frames and transports scanned Cold Signer response frames back through Backend and Messaging to Processing.
7. Cold Signer verifies the transaction context, loads the share matching the requested root public key, and participates in interactive ECDSA TSS signing.
8. Processing forwards each validated response to MPC. MPC validates session and authorization binding before accepting it.
9. After MPC returns a valid threshold signature, Processing broadcasts the exact approved transaction and reports the durable result to Backend.

## Binding Requirements

Each request and response must be cryptographically or durably bound, as applicable, to:

- protocol and envelope version;
- operation purpose;
- partner and action identity;
- MPC signing session and root/key identity;
- participant set and threshold;
- approved coordinator identity;
- exact transaction or payload hash;
- chain, asset, source, destination, amount, and nonce;
- policy and approval evidence available to the protocol;
- round number and expected previous round;
- issue time and expiry;
- replay-protection identifier.

If a field is unavailable in the current protocol, treat it as an implementation gap rather than silently omitting the invariant.

## Derivation

Non-hardened child public metadata may be derived and persisted without exposing the offline private share when the MPC protocol supports it. Offline transaction signing still requires the share belonging to the requested root. Never silently substitute another root, an online-only root, or a single-party signature.

## Failure and Recovery Rules

- Reject expired, replayed, out-of-order, wrong-purpose, wrong-participant, wrong-root, or payload-mismatched envelopes.
- Do not acknowledge a transport round before the receiving component has durably reached a safe state.
- A disconnect, application restart, or partial round must not result in signing a different payload under the same session.
- Recovery packages must be encrypted, authenticated, explicitly authorized, and verified against the expected public root.
- Failure handling must not downgrade `air_gapped_mpc` to another signing mode.

## Production Readiness

Before production use, complete and document:

- end-to-end threat modeling and independent cryptographic review;
- secure device and coordinator enrollment, rotation, and revocation;
- hardware-backed storage and device-compromise analysis;
- authenticated backup and recovery ceremonies;
- durable/restart-safe session design or explicit non-resumability;
- transport-size, corruption, replay, timeout, and failure-injection tests;
- physical-device validation for wired transport, camera scanning, protected storage, installation detection, and disconnect/reconnect behavior;
- operational monitoring, incident response, and audit evidence.
