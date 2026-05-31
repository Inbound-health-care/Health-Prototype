# Contributing

This prototype is intentionally small, local-only, and dependency-light.

## Ground rules

- Use placeholder data only; do not add PHI, real patient records, secrets, or private clinical details.
- Keep the engine a librarian: it may surface, count, and cite, but must not score, rank, diagnose, or interpret.
- Add or update hand-written answer keys before changing expected surfacing behavior.
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
```
