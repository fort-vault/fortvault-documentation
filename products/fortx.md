# FortX

## Full Exchange Product

**FortX Connect plus end-user iOS, Android, and web applications**

Version 1.0 | 29 September 2026 | Confidential - prospective partner use

This document extends the [FortX Connect product description](fortx-connect.md). All Connect scope, operating boundaries, integration dependencies, and delivery qualifications apply unchanged. The additions below describe the customer-facing application scope, subject to the agreed release and acceptance criteria.

## 1. Overview

FortX combines the exchange backend and backoffice of FortX Connect with applications through which end users access the exchange on iOS, Android, and the web.

**FortX = FortX Connect + end-user iOS app + end-user Android app + end-user web app.**

| Component | FortX Connect | FortX |
| --- | --- | --- |
| Exchange backend and integration interfaces | Included | Included through Connect |
| Operator backoffice | Always included | Included through Connect |
| Keycloak authentication and Sumsub KYC backend integration | Part of the Connect scope | Same Connect scope, with end-user application integration |
| Risk-based reconciliation and optional per-order mirroring | Part of the Connect scope | Same Connect scope |
| End-user iOS application | Not included | Included |
| End-user Android application | Not included | Included |
| End-user web application | Not included | Included |

In this product distinction, **frontend means only the end-user iOS, Android, and web applications**. Although the backoffice has a user interface, it belongs to FortX Connect and is not an additional frontend component.

## 2. End-User Applications

The application scope provides customer access to the agreed exchange functions:

- Keycloak-backed account access and registration, profile workflows, and Sumsub identity verification under the configured onboarding process.
- Portfolio and balance views, distinguishing available, reserved, and pending amounts where applicable.
- Supported asset and conversion views with quotes, disclosed fees, validity, and confirmation before submission.
- Deposit instructions and withdrawal requests for enabled assets and networks.
- Customer order, transaction, and operation history with pending, completed, and unsuccessful outcomes.

The three channels use the same FortX Connect backend and customer records. They do not introduce a separate trading ledger, reconciliation engine, or custody implementation. Branding, languages, supported operating systems and browsers, accessibility requirements, and any channel-specific differences are agreed during delivery.

### Sign-In and Identity Verification

The mobile implementation uses Keycloak's browser-based authorization-code flow with PKCE for sign-in and registration, with token refresh, logout, and device-secure session storage. For KYC, the app requests a short-lived token from FortX Connect and opens the Sumsub MobileSDK verification flow. It then reads the backend's verification status; closing or completing the SDK does not mark the customer as approved.

These authentication and verification flows are present in the mobile client code. Equivalent end-user web flows remain delivery work, not completed functionality. Production readiness requires provider configuration and acceptance on supported physical iOS and Android devices and web browsers.

Keycloak authentication and Sumsub verification remain Connect integrations shared by the customer channels. The applications provide the customer experience, not a separate identity authority or compliance decision engine. KYC-dependent trading and withdrawal restrictions must be enforced server-side under the agreed policy, not inferred from screen navigation.

## 3. Consistent Trading and Custody Behavior

FortX retains Connect's quote-based exchange model without an internal matching engine. Adding customer applications does not change risk-based reconciliation, optional per-order mirroring, or the FortVault execution boundary.

Customer applications submit requests to FortX Connect and display its authorized results. Financial calculations, permissions, limits, and operation state remain backend responsibilities. Platform credentials, exchange secrets, and custody signing material must not be distributed to end-user devices or browsers.

A request being accepted is not proof of a completed withdrawal or external swap. The application experience must reflect the backend's actual states and distinguish the customer trade from any related hedge or custody movement.

## 4. Backoffice and Delivery

Operators use the same backoffice included in FortX Connect to manage the exchange across all customer channels. There is no separate backoffice purchase or functional tier implied by adding the end-user applications.

The FortX delivery scope adds application design and branding, integration with Connect, iOS and Android release preparation, and deployment of the end-user web application. App-store account ownership, submission responsibilities, hosting, maintenance, and release acceptance are defined in the partner agreement. App-store approval is subject to the relevant platform's review.

The release scope must be verified on supported physical devices and browsers, including authentication, quote expiry, interrupted requests, duplicate submission protection, and operation-status recovery. These are acceptance requirements, not a claim that testing or publication has already been completed.

All backend capabilities, custody and swap dependencies, supported markets, exclusions, and service commitments remain as described in the [FortX Connect overview](fortx-connect.md). FortX adds the end-user channels, not a different exchange core.
