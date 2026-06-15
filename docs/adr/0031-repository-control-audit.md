# 0031 — Repository control audit: required controls become checkable

## Context

This repository already had the cross-repo governance layer: `LOAD.md`,
`AGENTS.md`, `CLAUDE.md`, `SECURITY.md`, `SECURITY_AND_TOOL_POLICY.md`, the
sensitive-change scanner, pinned workflow actions, and branch/PR discipline.
Those controls were documented, but there was no single committed policy file or
mechanical gate that checked whether the controls stayed present.

The related `testing-kits` and `DEP-TEST-KIT` repositories now use explicit
repository-control checks and stronger anti-regression posture. This health repo
needs the same pattern, adapted to its stricter local-only, synthetic-data,
stdlib-runtime boundary.

## Decision

Add a repository-control policy and stdlib-only audit tool:

- `.github/control-policy.json` pins required control files, instruction sources,
  workflow names, and workflow-hardening rules.
- `tools/control_audit.py` checks the policy without adding a runtime dependency.
- `.github/workflows/repository-controls.yml` runs the audit on pull requests,
  pushes to `main`, and manual dispatch.
- `make control-audit` exposes the same check locally.
- `make check` now includes `make control-audit` so the default local gate covers
  repository controls as well as behavior.
- Existing workflows get explicit `timeout-minutes` so the audit can enforce the
  timeout rule without waivers.

The audit is deliberately structural. It does not claim to prove HIPAA
compliance, de-identification, clinical safety, or branch-protection settings.
It checks files and workflow text that live in the repository.

## Consequences

Positive:

- Required governance files cannot silently disappear without CI failing.
- Workflow hardening rules become machine-checkable: explicit read permissions,
  concurrency, timeouts, full-SHA action pins, checkout credential disabling, no
  `pull_request_target`, and no fork-scan skip pattern.
- The repo keeps its pure-stdlib runtime. The audit itself is stdlib-only.
- The pattern maps to the other governance-heavy repos without copying their
  dependency assumptions.

Trade-offs:

- The audit is a conservative text-structure checker, not a complete YAML parser.
- A future workflow shape outside the current style may need the auditor updated.
- Required branch-protection settings still need GitHub settings review; they are
  not fully represented in repository files.

## Confirmation

Required confirmation for this PR:

```bash
python tools/control_audit.py
make control-audit
make check
```

CI confirmation:

- `Repository controls` workflow passes.
- Existing `CI`, `Sensitive change scan`, and `Dependency review` workflows still pass.

## Evidence level

IMPLEMENTED_UNVERIFIED until the PR checks pass and Scott or CI confirms the new
control gate on the branch.
