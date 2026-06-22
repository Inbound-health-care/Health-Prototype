# Publish Checklist

Before pushing a branch, opening a PR, or sharing output from this repository:

## Data and sensitivity

- [ ] No PHI or real patient records are included.
- [ ] No secrets, tokens, keys, private `.env` values, or credentials are included.
- [ ] Placeholder / synthetic data only.
- [ ] Generated exports, screenshots, HTML demos, logs, and raw evidence are
      excluded unless intentionally sanitized.
- [ ] Public examples do not contain private clinical details copied from a real
      person, workflow, message, chart, or support request.

## Product and regulatory boundary

- [ ] Public wording says this is a prototype, not a clinical product and not a
      medical device.
- [ ] No claim is made that the repo is HIPAA de-identified, FDA-cleared,
      clinically validated, medication-safe, or production-ready.
- [ ] Output language preserves the librarian boundary: surface, count, group,
      and cite only; no scoring, ranking, diagnosis, triage, recommendations, or
      interpretation.
- [ ] Any legal / regulatory language is framed as design context unless counsel
      verification is explicitly documented.

## Code and behavior

- [ ] No new runtime dependencies were added.
- [ ] No runtime network egress was added.
- [ ] New or changed surfacing behavior has a hand-written answer key and tests.
- [ ] User-facing docs are updated when CLI behavior, output shape, or public
      boundaries change.

## Verification

- [ ] `make check` passes, or any unavailable local command is listed honestly
      with the component commands or CI checks used instead.
- [ ] Sensitive-change findings, if any, are reviewed without copying sensitive
      values into public text.
- [ ] `STATUS.md` is updated last when the branch changes project state.
