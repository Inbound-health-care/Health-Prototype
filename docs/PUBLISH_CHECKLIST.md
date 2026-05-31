# Publish Checklist

Before pushing a branch, opening a PR, or sharing output from this repository:

- [ ] No PHI or real patient records are included.
- [ ] No secrets, tokens, keys, or private `.env` values are included.
- [ ] Placeholder data only.
- [ ] Generated exports, screenshots, and raw evidence are excluded unless intentionally sanitized.
- [ ] New or changed surfacing behavior has a hand-written answer key and tests.
- [ ] `make check` passes.
- [ ] User-facing docs are updated when CLI behavior changes.
- [ ] `STATUS.md` is updated last.
