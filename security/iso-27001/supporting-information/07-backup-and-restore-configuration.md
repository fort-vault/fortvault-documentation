# Backup and Restore Configuration

| Document field | Value |
| --- | --- |
| Document owner | FortVault |
| Intended audience | FortVault's ISO 27001 implementation partner |
| Classification | Confidential |
| Evidence basis | Management-provided current-state description |
| Verification status | Not independently verified; restore test not performed |
| Version | 0.1 |
| Date | August 28, 2026 |

## 1. Current Backup Configuration

| Data set | Method | Schedule | Retention / location |
| --- | --- | --- | --- |
| AWS application PostgreSQL databases | Native Amazon RDS automated backup | Daily | 7 days in AWS region `us-east-1` |
| AWS MPC node 1 PostgreSQL database | Native Amazon RDS automated backup | Daily | 7 days in AWS region `us-east-1` |
| GCP MPC node 2 PostgreSQL database | Native Cloud SQL automated backup | Daily | 7 days in a United States multi-region location, as reported |
| Backend, Custody Processing, and Listener databases | Additional scheduled export from an AWS virtual machine | Daily | Password-protected archive uploaded to customer-controlled Azure storage |

The supplied note also referred to a Frontend database. The Frontend is not expected to own durable business data, so FortVault should confirm whether this means the server hosting the backup script rather than a separate Frontend database. Exchange Processing is not listed in the supplied backup scope and must be added if that service is deployed with durable state.

## 2. Backup Administration

The current administrator role can create, modify, delete, restore, and otherwise manage backups. This is operationally convenient but creates a concentration-of-privilege risk. A compromised or mistaken administrator could alter or remove both production data and its recoverable copies.

Recommended improvement: separate backup policy administration, backup deletion, and restore execution; require MFA and approval for destructive changes; restrict routine service identities; and review privileged access periodically.

## 3. Backup Protection Status

| Control | Current status |
| --- | --- |
| Daily managed database backups | Reported as enabled |
| Seven-day retention | Reported as enabled |
| Additional customer-controlled copy | Reported for Backend, Processing, and Listener exports |
| Cross-region copy | Not enabled |
| Cross-account protection | Not enabled |
| Immutable or vault-lock protection | Not enabled |
| Deletion protection for backups | Not enabled |
| Approved recovery point objective (RPO) | Not defined |
| Approved recovery time objective (RTO) | Not defined |
| Recorded successful restore test | Not available |

## 4. Encryption and Transfer Evidence

The additional archive is described as password protected, but the supplied information does not identify the archive encryption algorithm, password storage and rotation process, transfer protocol, Azure storage encryption, retention policy, or access controls. Password protection alone is not sufficient evidence of an approved encryption-at-rest control.

Required evidence:

- RDS and Cloud SQL backup encryption settings and key ownership;
- encryption settings for the customer-controlled Azure storage;
- archive encryption algorithm and approved key/password handling process;
- secure transfer mechanism and service identity used for upload;
- backup-script source revision, execution logs, failure alerting, and ownership; and
- assurance that credentials and backup passwords are never written to source control or logs.

## 5. Recovery Objectives and Restore Testing

RPO and RTO have not been defined, and no successful restore-test result has been supplied. Therefore, daily execution and seven-day retention cannot yet demonstrate that FortVault can recover within an approved business timeframe.

Priority remediation:

- complete a business-impact review and approve RPO/RTO for each data owner;
- perform a controlled restore into an isolated non-production environment;
- verify integrity, application compatibility, access controls, and reconciliation;
- record start/end times, recovered backup age, result, exceptions, and corrective actions; and
- repeat restore testing on an approved schedule and after material backup changes.

## 6. Resilience and Immutability

Recommended improvement: protect at least one backup copy using an isolated account or customer-controlled boundary, immutable retention or vault lock, restricted deletion privileges, and a separate encryption key. Review whether cross-region recovery is required by the approved availability and data-residency objectives.

The customer-controlled Azure copy can contribute to separation, but its current access, immutability, retention, and restore behavior have not been evidenced.

## 7. MPC Recovery Boundary

Database backups are not a substitute for MPC cryptographic recovery. MPC shares and recovery material require a separate controlled process, secure storage boundary, authorization procedure, and tested recovery plan. No MPC share or recovery material should be placed in this evidence package.

## 8. Evidence to Attach

- Sanitized RDS and Cloud SQL backup-policy exports showing schedule, retention, encryption, and status.
- Sanitized Azure storage policy showing encryption, access, retention, and immutability settings.
- Backup job success/failure evidence with identifiers and customer data removed.
- Approved RPO/RTO register.
- Latest restore-test record and corrective actions.
- Privileged backup-role inventory and access-review evidence.
- Backup and restore operating procedure with named control owners.

## 9. Conclusion

FortVault currently has daily managed database backups and an additional off-cloud export for selected application databases. The backup control is only partially evidenced and is not yet operationally validated because recovery objectives, immutable protection, least-privilege administration, and restore testing are missing.
