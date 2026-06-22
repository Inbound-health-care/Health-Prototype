# Security policy

This public repository contains a local-only, synthetic-data healthcare
prototype. Do not submit real patient data, credentials, private keys, access
tokens, private clinical details, screenshots of live records, or other sensitive
personal information in an issue, pull request, commit, log, sample file, or demo
artifact.

## Reporting a vulnerability

Report vulnerabilities privately through GitHub's security-advisory form:

https://github.com/Inbound-health-care/Health-Prototype/security/advisories/new

Include the affected revision, a minimal reproduction using synthetic data, and
the expected impact. Do not open a public issue for an unpatched vulnerability,
and do not include live secrets or real health information in the report.

## Scope and handling

- Runtime code is Python standard-library only and is designed for no network
  access.
- Repository examples, fixtures, demos, and screenshots must be synthetic or
  intentionally sanitized.
- The prototype surfaces and cites evidence only. It must not score, rank,
  diagnose, triage, recommend, or state what a pattern means.
- The commit-time sensitive-change scanner is a narrow defense-in-depth gate. It
  is not a HIPAA de-identification determination and cannot prove that content is
  safe to publish.
- Legal / regulatory notes in this repository are design context, not legal
  advice and not counsel verification.
- The detailed agent/tool/PHI policy remains canonical in
  `SECURITY_AND_TOOL_POLICY.md`.

Maintainers will acknowledge a valid private report in the advisory thread,
investigate it without moving sensitive details into public channels, and
coordinate disclosure after a fix is available.
