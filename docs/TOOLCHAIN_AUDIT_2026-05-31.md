# Toolchain Audit — 2026-05-31

_What dev tooling this environment actually has, what it lacks, and what the 2026
landscape says we should reach for. Written so the next (memory-less) session
doesn't re-discover this from scratch. Surface-only: where a tool flags something
about the engine, it is **reported, not auto-fixed** — engine changes are Scott's
call (librarian rule applies to our own code too)._

## TL;DR
- The managed web environment **pre-installs a strong 2026 Python toolchain** in
  every fresh container. We were not actually missing pytest/ruff/mypy/etc. — they
  live in `/root/.local/bin`, which is why `python -m pytest` "failed" (wrong path)
  while the `pytest` CLI runs the suite green.
- The engine stays **pure-stdlib** (operator rule). Everything below is **dev-only**
  tooling — none of it is imported by `recurrence.py` or required to run it.
- Anything genuinely absent (coverage, bandit, ty, pre-commit) is **one `uvx <tool>`
  away** — no install, no env pollution. We effectively have it all.

## Inventory — present in a FRESH container (verified 2026-05-31)
| Tool | Version | Notes |
|---|---|---|
| python3 | 3.11.15 | stdlib runtime; the engine targets this |
| pytest | 9.0.2 | runs the repo's 68 unittest cases green as-is (`pytest -q`) |
| ruff | 0.15.8 | lint (already used in `make lint`); has the 2026 format style |
| black | 26.3.1 | formatter (unused by the project; ruff format preferred) |
| mypy | 1.19.1 | static types (mypy 2.0 exists upstream; 1.19 is fine) |
| pyright | 1.1.408 | static types (1.1.409 upstream; trivial) |
| uv | 0.8.17 | installer/runner — the key to `uvx` on-demand tooling |
| poetry | 2.3.3 | present; project uses neither poetry nor pyproject |
| node / npm | 22.22.2 / 10.9.7 | present (not used here) |
| rust / cargo | 1.94.1 | present (not used here) |

## Absent — but on-demand via `uvx` (no install needed)
| Tool | Purpose | How |
|---|---|---|
| coverage | test coverage | `uvx coverage run -m pytest && uvx coverage report` |
| bandit | security/AST lint | `uvx bandit -r recurrence.py` |
| ty | Astral type checker (the 2026 successor to mypy/pyright) | `uvx ty@latest check` (verified: ty 0.0.40 runs) |
| pre-commit | git hook runner | `uvx pre-commit ...` (no `.pre-commit-config.yaml` yet — workflow change, ask first) |

`pygame` is **not** installed and is **out of scope for this repo** (a stdlib
health-records engine). Not added — Scott confirmed dropping it (2026-05-31).

## 2026 landscape (web-checked 2026-05-31)
- The consolidating default stack is **uv + Ruff + ty**, all from Astral, sharing
  one `pyproject.toml`. We already have uv + Ruff current; **ty is the one genuinely
  new tool we lack** — and it's available via `uvx` today.
- **ty** benchmarks ~10–60× faster than mypy/Pyright on uncached runs.
- **mypy 2.0** shipped (May 2026) with parallel checking (`--num-workers`); we have
  1.19.1, which is stable and sufficient.
- **Ruff** introduced a "2026" formatting style (v0.15.x); we run 0.15.8.

> **Decisions (Scott, 2026-05-31):** both flags below — **leave as-is** (mypy stays
> a noted flag; `ruff format` not applied, keep hand-formatting). **pygame — dropped**
> (out-of-scope; not added).

## Capability flags — SURFACED, not changed (Scott decides)
1. **mypy: 2 errors on `recurrence.py:501`** — `Unsupported left operand type for -
   ("None")`; both operands are unions. Likely a guard mypy can't narrow, possibly
   a latent `None` path. Tests are green and the self-test passes, so this is a
   type-soundness note, not a proven runtime bug. Not touched.
2. **`ruff format` would reformat 10 of 12 files** — the project lints with `ruff
   check` but was never `ruff format`-ted. Applying it is a large, purely-cosmetic
   diff over engine + tests; left for an explicit decision (`make fmt-check` to see
   it, `make fmt` to apply).

## What changed this session (durable, dev-only, additive)
- This audit doc.
- `Makefile`: added optional, non-failing convenience targets — `tools`, `typecheck`,
  `fmt-check`, `fmt`, `cov`, `security` — matching the existing "ruff if installed"
  pattern. None change engine behavior or add a runtime dependency.
- `.claude/hooks/session_start.sh`: one extra line reporting dev-tool availability,
  so a fresh session knows `pytest`/`ruff`/`mypy`/`uv` are here (and the rest are a
  `uvx` away) instead of re-hitting the `python -m pytest` confusion.
