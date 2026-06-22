# Contributing

This prototype is intentionally small, local-only, deterministic, and
runtime-dependency-free. Contributions should preserve that boundary unless the
operator explicitly approves a scoped change.

## Ground rules

- Use synthetic / placeholder data only. Do not add PHI, real patient records,
  secrets, tokens, private clinical details, screenshots of live records, or
  unsanitized exports.
- Keep the engine a librarian: it may surface, count, group, and cite provenance,
  but must not score, rank, diagnose, triage, recommend, or interpret.
- Keep runtime code Python standard-library only unless a dependency change is
  explicitly approved.
- Do not add network egress to runtime code.
- Add or update hand-written answer keys before changing expected surfacing
  behavior.
- Keep public wording clear that this is a prototype, not a clinical product, not
  a medical device, and not a compliance determination.
- Update user-facing docs when commands, output shape, or public boundaries
  change.
- Update `STATUS.md` last so it remains the current front door for the project.

## Checks

Run the standard check before committing:

```bash
make check
```

For smaller loops:

```bash
make test
make selftest
make lint
make control-audit
```

The sensitive-change scanner is defense-in-depth, not proof that content is safe
to publish. Review all changed public text, examples, screenshots, and generated
artifacts before opening a PR.
