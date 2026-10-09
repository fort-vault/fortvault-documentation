# Cover Email Draft

Subject: FortVault ISO 27001 Supporting Information

Dear Nare,

Thank you again for the meeting and for the clear list of requested information.

We have organized the supporting information into a controlled evidence package. The package includes source-controlled documentation for testing, health checks, logging design, application-level secret handling, selected technical README and architecture documents, and management-provided current-state summaries for cloud infrastructure and backups.

The cloud and backup documents describe both the controls currently in place and the outstanding gaps. Daily managed database backups and an additional off-cloud export are reported as enabled. Cloud audit logging, centralized monitoring, infrastructure-as-code, immutable/cross-region backup protection, approved RPO/RTO, and recorded restore testing are not yet implemented or evidenced. We have included these as remediation items rather than presenting them as completed controls.

We will provide:

- testing and health-check documentation, together with release/environment-specific test and health evidence;
- cloud hosting and configuration overview with a sanitized deployment diagram;
- backup scope, schedules, retention, access, and recovery-control status;
- logging, monitoring, retention, and access-control information;
- TLS and encryption-at-rest evidence;
- endpoint operating-system and update-management evidence; and
- selected FortVault README and architecture documents.

We are continuing to collect sanitized cloud-console exports, production TLS/encryption evidence, endpoint-management evidence, release-specific test output, and the future restore-test record. We will also keep application/database backup information separate from MPC recovery material, as these are distinct control areas.

Best regards,

Armen and Karen
