# SESSION HANDOFF — 2026-06-05

_Engine-agnostic. For any future AI session (or Scott) resuming this work. Read
`AGENTS.md` (source of truth) + `STATUS.md` first, then this. Logs the session so
the chat does not need re-reading._

## ORIENT IN 60 SECONDS
- **Repo:** `Inbound-health-care/Health-Prototype`. Pure stdlib, local-only, zero real PHI.
- **`main` HEAD:** `15d9ad5` — **PR #13 merged**. **5 rules / 87 tests** on `main`, `ruff` clean.
- **Engine now:** recurrence / gap / frequency / co-occurrence (opt-in `window_days`) /
  **cadence change** (new this session). All five run in `--report`.
- **Open PRs:** none from this session. The cadence work (PR #13) is merged; the
  duplicate co-occurrence take (PR #12) is closed.
- **Next coding task:** **OPEN — Scott's pick.** Both planned engine increments
  (window, cadence) are now landed. Candidates: free-text extraction (deferred), a
  6th rule, or polish (the deferred `--version`/`VERSION`/`tests/test_cli.py` from PR #6).
- **First action next session:** `git fetch origin`; **check `main` and open/merged PRs
  against the LIVE remote before building** (see the stale-clone lesson below — it bit
  this session); read `AGENTS.md` + `STATUS.md`; verify with
  `python -m unittest discover -s tests -t .` (87 OK) + `python recurrence.py --self-test` (6 OK).

## WHAT THIS SESSION DID (chronological, honest)
1. **Onboarded** (repo-onboard skill): read AGENTS/STATUS/cold-start. Held operator rules.
2. **Planned co-occurrence window** (rule #4 extension, opt-in `window_days`) with an
   **anchor-date** counting choice, built it on `claude/hopeful-einstein-C78CE`, opened draft **PR #12**.
3. **Caught a duplicate.** On subscribing to #12's CI, checked the real remote and found
   the co-occurrence window had **already merged via PR #10** (a *different* algorithm —
   greedy one-to-one). The container had cloned a **pre-#10 `main` snapshot**, so onboarding
   never saw it. Surfaced it instead of plowing ahead (operator rule: read the real state).
4. **Scott decided:** close #12, do cadence #5. **Closed PR #12** as a duplicate (with a note),
   reset the branch onto current `main`.
5. **Built cadence rule #5.** Scott had me **web-research the pivot method** rather than guess
   → **Pettitt's test** (the standard deterministic, non-ML, stdlib change-point method).
   Built oracle-first, ADR 0007, docs current. Force-pushed (Scott authorized) → draft **PR #13**.
6. **User-verified.** Scott ran the branch on his **Windows PC (Python 3.12.10)**: `--self-test`
   (6 scenarios), full suite (87 tests), and a hand-made record — all pass. Recorded as
   **CONFIRMED_USER_SIDE** in ADR 0007. Took #13 out of draft.
7. **Scott merged #13.** This handoff (docs-only) is the wrap-up.

## VERIFIED STATE
- **`main` (`15d9ad5`):** 5 rules, **87 tests OK**, self-test 6 OK, `ruff` clean. CI green on the
  merge. `detect_cadence_change` + `"cadence_change"` Expert present on `main` (checked via
  `git show origin/main:recurrence.py`).
- **CONFIRMED_USER_SIDE:** Scott ran the engine himself on Windows (see ADR 0007 Confirmation).

## CADENCE RULE #5 — what landed (PR #13)
- `detect_cadence_change(records, field="item", min_occurrences=4, ratio=2.0, normalize=False, synonyms=None, fuzzy_cutoff=None)`.
- Per item with `>= min_occurrences` **distinct dated days**: consecutive inter-event intervals →
  locate ONE change point with **Pettitt's rank statistic** (`_pettitt_pivot`: argmax `|U_k|`,
  ties broken by larger median ratio then earliest split) → flag when
  `max(median_before/median_after, median_after/median_before) >= ratio`.
- `CadenceChangeHit(record_id, item, before_interval, after_interval, pivot_date, dates, variants)`.
  Format: `"<item>" interval changed from ~Xd to ~Yd at <pivot> — <dates>` (firewall: states the
  change and where, never its meaning; BANNED list gained accelerat/increasing/escalat/… ).
- **Oracle kept OFF `SAMPLE_RECORDS`:** dedicated `CADENCE_CHANGE_RECORDS` + `CADENCE_CHANGE_ANSWER_KEY`
  (RC1 tightening / RC2 steady / RC3 too-few+undated). The rule still runs in `--report`, where
  **R016** (chest pain, 10d→79d) surfaces naturally — so `REPORT_ANSWER_KEY(_V1)` gained that one row.
- New `--demo-cadence-change`. Tests: `tests/test_cadence_change.py` (4 classes) + a report composition test.
- Decision record: **ADR 0007**.

## LESSONS / GOTCHAS (read before "fixing")
- **STALE CLONE — the big one.** This session's container was cloned from a `main` snapshot **two
  commits behind** the live remote (pre-#10/#11). Result: a whole feature (co-occurrence window)
  was built that already existed → duplicate PR #12, later closed. **At session start, `git fetch
  origin` and reconcile `main` + open/merged PRs against the LIVE remote BEFORE building anything.**
  Do not trust the initial checkout or even `STATUS.md` as necessarily current — verify.
- **Force-push needs explicit auth.** The auto-mode classifier blocks `git push --force[-with-lease]`
  unless Scott has explicitly authorized it that turn. Ask first; don't retry verbatim.
- **README was stale** (listed only 3 rules since co-occurrence shipped in #3) — fixed this session
  to all 5. Keep the README rules table in sync when adding a rule.
- **Windows local dev:** Scott runs on Windows (Python 3.12.10). **No `make`/`ruff`/`uv` locally** —
  run the components directly (`python -m unittest discover -s tests -t .`, `python recurrence.py
  --self-test`, `python -m compileall ...`). CI runs `ruff`. To run from a folder, the cmd prompt
  must be **inside** the project folder (prompt ends in the folder name, not `C:\>`).
- **This environment:** the git remote is a local proxy (`127.0.0.1`); GitHub PRs/CI are real (via
  the GitHub MCP). `send_later` and a "Workflow"/ultracode tool are **not available** here — can't
  schedule passive check-ins; rely on PR webhooks (failures only). Effort: normal/high fits this
  repo; **ultracode (auto multi-agent) is overkill** and conflicts with the repo's frugality rule.

## CONVENTIONS IN EFFECT (from AGENTS.md / architecture.md)
- **Librarian, not interpreter** — surface/count/cite; never score/rank/diagnose. Banned-word firewall, tested.
- Pure stdlib; zero real PHI; no network egress. Defaults stay exact-v0; new behavior opt-in.
- **Answer key written by hand FIRST**; code matched to it — never patch the key toward the code.
- Validate args (`ValueError`). Determinism (stable ordering). Log decisions as ADRs (with a Confirmation field + evidence level).
- A new rule is a **drop-in**: `detect_x` + `XHit` + `format_x` + one `Expert` appended to `EXPERTS`. Router/formatter unchanged.
- PRs draft until asked; **Scott merges, nothing auto-merges**; branch protection on `main` (4 `test` checks). Be frugal with GitHub comments.

## POINTERS
- Source of truth: `AGENTS.md` (rules) · `STATUS.md` (state) · `docs/agent-guides/architecture.md` (engine facts: 5 rules / EIGHT keys / 87 tests) · `docs/adr/` (0001–0007).
- Prior handoff: `docs/HANDOFF_2026-06-04_session.md` (had the Phase C cadence spec this session built).
- Quick check: `python -m unittest discover -s tests -t .` · `python recurrence.py --self-test` · demos `--demo* | --report | --report-v1`.

## ACCEPTANCE — next session is bootstrapped when
1. `AGENTS.md` + `STATUS.md` read; `main` + open/merged PRs confirmed against the **live remote** (not the initial clone).
2. State verified by running the suite (87 OK) + self-test (6 OK) — not assumed.
3. Scott asked what the next increment is (it's open), then built per the conventions (answer-key-first, ADR, draft PR), ≤1 clarifying question.

NOT complete if: the engine architecture is re-explained to Scott · the firewall is weakened · a feature is rebuilt without checking the live remote first · the answer key is patched toward the code.
