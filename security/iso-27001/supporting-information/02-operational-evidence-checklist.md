# Operational Evidence Checklist

| Document field | Value |
| --- | --- |
| Document owner | FortVault |
| Classification | Confidential |
| Status | Collection checklist |
| Date | August 28, 2026 |

This checklist covers evidence that source code cannot establish. Do not include credentials, raw secrets, private keys, MPC shares, or customer data in the evidence package.

## 1. Cloud Hosting and Configuration

Collect a sanitized record for every production and non-production environment in scope:

- cloud provider and account/project identifier;
- region(s) and data-location decision;
- deployed services, databases, caches, object storage, secret store, monitoring, and networking services;
- a deployment/network diagram showing public ingress, private subnets, security groups/firewalls, and service-to-service access;
- identity and access management roles for deployment, operations, and application workloads;
- production change/deployment process and source of infrastructure configuration;
- cloud audit-log service and retention setting; and
- security monitoring, vulnerability scanning, and alerting configuration.

## 2. Backup and Restore

For Backend PostgreSQL, Custody Processing PostgreSQL, Listener PostgreSQL, Exchange Processing PostgreSQL where deployed, MPC node storage, and any critical object storage:

- backup method and service;
- schedule, retention, and immutable/cross-account or cross-region protection where used;
- encryption setting and key ownership;
- access control for backup creation, modification, deletion, and restore;
- RPO and RTO approved for the service;
- most recent successful restore-test evidence, scope, result, and corrective actions; and
- owner of the backup and restore procedure.

MPC recovery material requires a separate procedure. Do not include key shares or recovery material in this package.

## 3. Central Logging and Monitoring

Collect:

- central log platform and log sources;
- log retention, archival, and deletion policy;
- access-control roles and access-review evidence;
- time-synchronization source and timezone handling;
- alert rules for availability, authorization failures, provider failures, and security-relevant events;
- incident-ticket or alert examples with sensitive data redacted; and
- confirmation of the log-scrubbing/redaction standard for tokens, passwords, private keys, MPC shares, and customer data.

## 4. TLS and Encryption at Rest

Collect:

- public ingress/load-balancer or reverse-proxy configuration showing the enforced TLS versions and certificate management;
- evidence of HTTP-to-HTTPS redirect and secure-cookie settings where applicable;
- database, disk/volume, object-storage, cache, and backup encryption-at-rest settings;
- cloud KMS or equivalent key-management configuration, rotation policy, and access control; and
- exception register for any internal or legacy connection not using the standard TLS policy.

Do not state a TLS version until it is verified from the production ingress or equivalent configuration.

## 5. Endpoint Operating Systems and Updates

Clarify whether this request covers workforce/admin endpoints, production servers, or both. For each included endpoint class, collect:

- supported operating systems and minimum versions;
- device/endpoint inventory;
- automatic update and patch-deadline policy;
- device-management and compliance reporting;
- full-disk encryption and screen-lock policy;
- endpoint-protection/EDR configuration where used;
- administrator privilege policy; and
- sample compliance report or patch-status export, sanitized of personal details.

## 6. Release-Specific Test and Health Evidence

For the release/environment presented to the ISO partner, collect:

- CI or local test results for Backend, Custody Processing, MPC, and the health-audit tool;
- build/version identifiers and release approval record;
- a sanitized health-audit output showing live, ready, configuration, dependency, partner/policy, and stream checks; and
- any known degraded checks, remediation owner, and target completion date.

## Evidence Register Fields

Track every collected artifact with these fields:

| Field | Required value |
| --- | --- |
| Control area | Cloud, backup, logging, TLS/encryption, endpoint, testing, or health |
| Environment | Production, staging, development, or another approved label |
| Evidence title | Clear description of the screenshot, export, record, or document |
| Source system | AWS, Google Cloud, device-management tool, CI, monitoring platform, or controlled repository |
| Collected by | Named FortVault control owner |
| Date collected | Date and timezone |
| Review status | Draft, reviewed, approved, or superseded |
| Redaction check | Confirmed before external sharing |
