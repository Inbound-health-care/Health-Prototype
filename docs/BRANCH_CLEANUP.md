# Branch Cleanup

Low-risk branch cleanup is intentionally boring: inspect first, delete only merged
local branches, and never delete protected branch names.

## Quick audit

```bash
make branch-audit
```

The audit is read-only. It reports:

- the current branch,
- local branches,
- remote-tracking branches,
- merged local branches that are eligible for deletion,
- local branches whose upstream is gone.

## Safe local cleanup

Only after reviewing the audit output:

```bash
python scripts/branch_audit.py --delete-merged --yes
```

The helper refuses to delete the current branch and skips protected names:
`main`, `master`, `develop`, `development`, `dev`, and `trunk`.

## Remote cleanup rule

Do not delete remote branches from automation unless the branch is already merged
and the pull request is closed or merged. Prefer GitHub's UI or `gh pr view`
before any remote deletion.
