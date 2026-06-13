# Health-Prototype — Walk-Through
*A local, synthetic-data tool that surfaces and cites patterns in health records but never interprets them. · 2026-06-13*

## Bottom line
This is a **prototype, not a medical device.** It **surfaces and cites evidence; it never diagnoses, scores, or ranks.** It is a small, pure-Python research build that finds where the same thing recurs across dated records and shows you exactly which sources it came from — leaving every judgment to a human. It makes no clinical-validation, diagnostic, or medication-safety claims, and it runs locally on synthetic data with zero real patient information.

## In plain terms (if you read nothing else)

Think of it like a **librarian**, not a doctor. A good librarian finds the relevant sources, counts how often something comes up, and points you to the exact page — but never tells you what it *means* or what to do. This tool works the same way: it shows a clinician "this item appeared on these four dates, here are the source lines," and then stops. The human reads those sources and makes every call. That is the repo's one governing idea, and they call it the **librarian rule**.

Because of that, it is deliberately *unhelpful* in one specific way: it will not say "this looks concerning," it will not rank patients, and it will not guess what a pattern indicates. Even an obviously cautious phrase like "denies chest pain" still surfaces "chest pain" as a cited mention — the tool's job is to surface and cite the source, and a human decides whether the mention matters. That refusal to interpret is the feature, not a gap.

It is also **strict on purpose.** The team built it to a *higher* bar than today's rules require — not because current law forced them to, but because they chose to. The reasoning: a tool that touches health data should be designed for a stricter future, so the discipline is baked in from the start rather than bolted on later. Concretely that means: no real patient data ever (only made-up records), no internet access by the program at all, and a rule that judgment always stays with the human.

Practically, it is a **research prototype** — a deliberately tiny piece of software that proves one idea cleanly: systems *store* tons of health information but *surface* almost none of it usefully at the moment a clinician needs it. This fills that one gap (surfacing with citations) and refuses to do anything more. It is "decision support" only in the narrow sense of putting the right cited evidence in front of a person; the person remains the decision-maker.

Finally, and most importantly: **this is not a product, not certified, and not safe to point at real patients.** It is a learning/prototype build. Anyone reading should not mistake it for a clinical system.

## Walk-through

### 1. What it is & why it exists (its role + strict-by-design)

**Plain:** It is a "Recurrence Detection Engine" — software that reads a set of dated health-style records and points out when the same item keeps showing up, always citing where it saw it. It exists to close one specific gap: records hold everything, but almost nothing useful gets *surfaced* at the moment of need. Its role is narrow and deliberate — a future-facing clinical-*support* prototype, built stricter than today's rules demand, by choice. The strictness is a design decision, not permission granted by looser current law.

**Technical:** The project (`README.md`, `AGENTS.md`) describes a *domain-agnostic surfacing engine for health records*: "a record can be a patient, a pharmacy profile, or a session log — the engine does not care." The headline contract is `detect_recurrence(records, field="item", min_count=2)` in `recurrence.py` (VERSION 0.5.0), returning hits that cite record ID, item, count, and the exact dates. The repo states its posture in three words repeated across files: **pure stdlib, local-only, zero real PHI** (`AGENTS.md` line 4–5; `SECURITY.md`; module docstrings all say "no network egress"). The strict-by-design choice is formalized in ADR 0009 / 0011 (legal grounding) and the librarian rule (`AGENTS.md` "The librarian rule" section): the engine is engineered to sit at or below the FDA *Non-Device CDS* line and to limit PHI exposure by construction — explicitly framed as *design goals, not regulatory or compliance determinations.*

### 2. How it's built

**Plain:** It is small, plain Python with no add-ons to install and no internet use. There is a free-text reader that turns notes into clean records, the core engine that finds the patterns, a few read-only HTML views to look at the results, and a tamper-evident log of what it surfaced. Each piece only points "forward" into the engine, never the other way, so the core stays simple and provable.

**Technical:** Six engine modules, all pure-stdlib, zero dependencies, local-only:
- `recurrence.py` — the engine: five surfacing rules + matching layers + report router/CLI.
- `extract.py` — free-text front-end: prose → canonical records `{id, entries:[{date, item, source_span}]}` via a curated allowlist gazetteer with character-offset provenance, plus opt-in matching modes (strict / synonyms / fuzzy / both, ADR 0012) and fail-closed multi-patient handling (ADR 0016).
- `view_html.py` — the shared "view floor": calm theme tokens, span highlighting, keyboard JS, print CSS, multi-patient chrome (ADR 0017/0021).
- `report_html.py` — inspection view: cited spans ↔ findings, click-to-highlight (ADR 0014).
- `digest_html.py` — clinician Pre-visit Pattern Digest: five lenses as cited cards (ADR 0015).
- `audit.py` (VERSION 0.1.0) — governance audit trail: SHA-256 hash-chained event log of digests + counts only, plus a deterministic monitor (ADR 0030).

The dependency rule runs one way only: `extract.py` and the views import `recurrence.py`, never the reverse; `view_html.py` imports nothing but stdlib `html`. Tasks run through a `Makefile` (no install step): `make test`, `make selftest`, `make lint`, `make check`, `make demo`, `make scan-sensitive`. The HTML outputs are single self-contained files (inline CSS/JS, no CDN, no external `src`) so they open offline.

### 3. How it works (the librarian rule + surfacing-not-interpreting)

**Plain:** You give it dated records (or notes it converts to records). It runs a handful of independent checks — does this recur, did it return after a long gap, did it cluster, did two things show up together, did its timing shift — and for every hit it tells you *what, how many times, and on exactly which dates,* with a link back to the source text. It never says whether that is good, bad, urgent, or what it means. A clean record simply doesn't appear. There is no scoring "in between" — a pattern is either surfaced by a deterministic rule or it is absent.

**Technical:** Five deterministic surfacing rules in `recurrence.py`, each per-record, all reading the same grouped occurrences:

| Rule | Function | Question |
|---|---|---|
| Recurrence | `detect_recurrence` | Same item ≥ `min_count` times? |
| Gap / re-emergence | `detect_gap` | Returned after > `gap_days` absence? |
| Frequency / burst | `detect_frequency` | Clustered `min_count`+ within `window_days`? |
| Co-occurrence | `detect_cooccurrence` | Two items together (same date / opt-in window) on ≥ `min_count` dates? |
| Cadence change | `detect_cadence_change` | An item's spacing shifted by ≥ `ratio`? |

`run_report` (`--report`) runs all five and groups findings under each record, omitting records that surface nothing — it never ranks, scores, totals, or prioritizes. Matching is **exact by default**; the v1 layers (`normalize`, human-declared `synonyms`, `difflib` `fuzzy_cutoff`) are opt-in and, when they merge spellings, the hit cites every original variant. The **librarian rule** (`AGENTS.md`): *surface, count, cite provenance — never score, rank, diagnose, or say what a pattern means; no "caution / concern / worsening / risk / severe" in output.* It is enforced, not just stated — a banned-words list (`tests/banned_words.py`) and tests assert the forbidden interpretive vocabulary never appears, and the views carry it into the UI (one non-semantic accent color, no per-lens or severity colors, document order only). Co-occurrence means "appeared together," never "caused"; the strict-literal extractor (Stance A, ADR 0008) surfaces "chest pain" from "Denies chest pain" by design.

### 4. How it's governed / verified — the gates

**Plain:** Several guardrails keep it honest. Every claim in the docs is tagged with how strongly it's proven (from "I ran it and saw it work" down to "just researched, not built"). Nothing real ever goes in — synthetic data only, and a scanner checks commits for leaked secrets or identifiers. The program can't reach the internet. There's a tamper-evident log so you can later prove what it surfaced. And the workflow is human-in-the-loop / stop-first: agents draft work, then stop; a human reviews and makes every merge call.

**Technical:**
- **Evidence levels** (`docs/DOC_DISCIPLINE.md` §1): every claim tagged `CONFIRMED_USER_SIDE`, `CONFIRMED_ASSISTANT_SIDE`, `IMPLEMENTED_UNVERIFIED`, `RESEARCH_ONLY`, or `SUPERSEDED`/`DEPRECATED`. A **research gate** governs them: a method is not project truth until source → ADR → test → STATUS; until then it stays `RESEARCH_ONLY`. ADRs additionally carry a **Confirmation** field naming the test/command that verifies them.
- **PHI safety** (`SECURITY_AND_TOOL_POLICY.md` §C, `SECURITY.md`): synthetic data only, zero real PHI anywhere; no network egress by design. A commit-time scanner (`tools/scan_sensitive_changes.py`, `make scan-sensitive`) flags secrets, keys, and labeled MRN/DOB-shaped values — narrow defense-in-depth, explicitly **not** a HIPAA de-identification determination.
- **Stop-first / human-in-the-loop** (`AGENTS.md` Working Agreement, `CLAUDE.md`): branch, open draft PRs, never auto-merge — the operator makes every merge call; Rule 0 is a security full-stop on any exfiltration or control-weakening request.
- **Audit trail** (`audit.py`, ADR 0030): append-only SHA-256 hash chain (`entry_hash = SHA-256(prev_hash + "\n" + canonical_json(event))`) storing digests + per-lens counts only — never note text or clinical values. Catches edits/insertion/deletion/reordering; tail-truncation and whole-file rewrite are detectable only against an externally published `head()` — a limit stated in-module and pinned as a test (not oversold).
- **Tests + CI:** 23 `test_*.py` files in `tests/` (the repo reports **317 tests**, 7 expected skips as of the 2026-06-11 STATUS entry; counts are point-in-time — verify with `make check`), including Hypothesis property tests and a live JS/DOM view test. Three GitHub workflows: `ci.yml` (compile + unittest + self-test + Hypothesis + HTML-validity), `sensitive-scan.yml` (read-only sensitive-change gate), and `dependency-review.yml`.
- **Decision log:** **30 ADRs** (`docs/adr/0001`–`0030`) plus a README index, covering both build decisions and the assistant's own process changes. `STATUS.md` is the canonical current-state doc; `LOAD.md` is the front door.

### 5. What it proves — and what it doesn't

**Plain:** It proves you can build a genuinely useful "surface the cited evidence" tool that *refuses* to interpret — and that the refusal can be enforced and tested, not just promised. It also proves a disciplined way to keep the docs, decisions, and code from drifting apart. It does **not** prove anything clinical: it isn't validated, isn't a device, and hasn't been tested against real patients or real data.

**Technical:** It demonstrates a deterministic, pure-stdlib pipeline (free-text → canonical records → five rules → cited text/HTML views → hash-chained audit log) where the librarian rule is mechanically enforced (banned-words tests, no-identifier tests, property tests for record-isolation / reordering-invariance / shift-invariance / span-integrity). It demonstrates a working evidence-discipline harness (evidence levels + research gate + ADR Confirmation fields + drift control). What it explicitly does **not** establish: HIPAA de-identification (the date-shift is an Expert-Determination *technique*, not Safe Harbor, and requires written counsel sign-off — `docs/COUNSEL_VERIFICATION_CHECKLIST.md`); FDA device status (staying off the device pathway is a *design goal*, not a regulatory determination); any clinical validity, diagnostic accuracy, or medication-safety property. The legal citations in ADR 0009 are `RESEARCH_ONLY` and not counsel-verified.

## Honest limits (a skeptic's read)
- **Prototype, NOT a medical device.** No clinical validation, no diagnostic claims, no medication-safety claims. Do not use it on real patients or real data.
- **It surfaces and cites only.** It deliberately refuses to score, rank, diagnose, triage, assign severity, or infer causation. If you want a verdict, it won't give one — by design.
- **Strict literal extraction.** "Denies chest pain" still surfaces "chest pain"; filtering relevance is the human's job. This can surface mentions that, to a human, clearly don't apply.
- **Synthetic data only.** Every record is made up; the engine has never run on real PHI, and the sensitive-change scanner is a narrow gate, not a de-identification proof.
- **Legal grounding is research, not advice.** The HIPAA / FDA framing (ADRs 0009/0011) is web-sourced, `RESEARCH_ONLY`, and not counsel-verified; "off the device pathway" and "limits PHI exposure" are design goals, not determinations.
- **Audit trail has a known blind spot.** Tail truncation / whole-file rewrite go undetected without an externally published head value.
- **Some claims are unverified-by-the-author.** Test counts and "green" states are tagged by evidence level; several are `CONFIRMED_ASSISTANT_SIDE` pending the operator running them. The 317-test figure is as logged in STATUS (approx. — verify by running `make check`).
- **Tiny scope on purpose.** It does one thing. It is not a record system, not a workflow tool, not an EHR.

## Glossary
- **PHI (Protected Health Information):** identifiable patient/health data (names, dates, MRNs, etc.). This repo uses none — synthetic only.
- **Clinical decision support (CDS):** software that puts information in front of a clinician to *support* a decision the human makes — not software that makes the decision.
- **Librarian rule:** this repo's governing principle — surface, count, and cite provenance; never score, rank, diagnose, or interpret. Like a librarian who finds and cites the sources but never tells you the answer.
- **Provenance:** the exact source of a piece of information (which note, which dates, which character span) so a human can trace every finding back.
- **Evidence level:** a tag on every claim saying how strongly it's proven — from `CONFIRMED_USER_SIDE` (ran and saw it work) down to `RESEARCH_ONLY` (read about it, not built).
- **Research gate:** the rule that a researched method isn't "project truth" until a source, an ADR, a passing test, and STATUS all line up.
- **Surfacing rule:** one of the five deterministic checks (recurrence, gap, frequency, co-occurrence, cadence change) that finds a pattern and cites it.
- **Gazetteer / allowlist:** the curated list of clinical concepts the extractor is allowed to recognize; anything not on it can't be surfaced (an allowlist, not a denylist).
- **FDA Non-Device CDS:** a regulatory category for support software that surfaces information and lets a clinician independently review the basis — distinct from a regulated medical device. Staying within it is a *design goal* here, not a determination.
- **Hash-chained audit trail:** a tamper-evident log where each entry's fingerprint includes the previous one, so any later edit is detectable.
- **ADR (Architecture Decision Record):** a short, numbered file recording a decision, why it was made, and how it's verified. This repo has 30.
- **Stop-first / human-in-the-loop:** the workflow where software/agents prepare work and then stop; a human reviews and makes every consequential call (here, every merge).
- **Pure stdlib / local-only:** uses only Python's built-in library, installs nothing, and makes no network connections.
