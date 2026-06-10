# PROJECT_MAP — health-prototype

What each file is, whether it's canonical (the single source for that fact), and
when to load it. Generated from the repo tree; keep in sync when files are
added/removed. Counts and engine facts are NOT restated here — they live in their
canonical files.

## Control / startup (Tier 1 — every session)
| File | Purpose | Canonical? | Load when |
|---|---|---|---|
| `AGENTS.md` | Source of truth: operator rules, working limits, the librarian rule, commands, load order | **yes (rules)** | First, every session |
| `CLAUDE.md` | Thin pointer to AGENTS.md + Claude-Code-specific notes | — (pointer) | Claude Code only |
| `LOAD.md` | Startup procedure (read → report → stop) | yes (load order) | Every session start |
| `STATUS.md` | Current state / next step | **yes (current state)** | Every session start; update last |
| `docs/COLD_START_HANDOFF.md` | Fresh-session orientation | — | Cold start |
| `SECURITY_AND_TOOL_POLICY.md` | Untrusted input, tool-risk, PHI, source conflicts | **yes (security/tool policy)** | Before any write/delete/install/send |
| `LOAD_TRACE_TEMPLATE.md` | Startup audit block | yes (trace format) | Each session start |
| `PROJECT_MAP.md` | This file | — | Orienting to the tree |
| `.claude/settings.json` | Registers the SessionStart hook | yes (hook config) | Rarely |
| `.claude/hooks/session_start.sh` | Prints orientation + runs tests at start | — | Runs automatically |
| `.claude/skills/repo-onboard/SKILL.md` | "load repo settings" onboarding skill | — | Auto on trigger |
| `.claude/commands/handoff.md` | End-of-session handoff command | — | Session end |
| `.claude/commands/drift-check.md` | Drift / garbage-collection audit | — | Every ~3–5 cycles |
| `.claude/commands/new-phase.md` | Start-of-phase command | — | New phase |
| `.claude/commands/audit-prompt.md` | Prompt-audit command | — | Auditing a prompt |

## Engine (Tier 3 — load when coding)
| File | Purpose | Canonical? | Load when |
|---|---|---|---|
| `recurrence.py` | The engine: surfacing rules + matching layers + report router/CLI | **yes (engine code)** | Working on the engine |
| `extract.py` | Free-text FRONT-END: prose → canonical records (gazetteer + dates + matching modes + multi-patient) | **yes (extractor)** | Free-text extraction |
| `view_html.py` | Shared VIEW FLOOR: theme tokens, highlight/keyboard JS, print CSS, timeline, multi-patient chrome (ADR 0021) | **yes (view floor)** | Working on any view |
| `report_html.py` | Inspection view: cited spans ↔ findings, click-to-highlight (ADR 0014) | yes (inspection view) | The report view |
| `digest_html.py` | Clinician Pre-visit Pattern Digest: five lenses as cited cards (ADR 0015) | yes (product view) | The digest view |
| `data/sample_records.py` | Synthetic records + hand-written answer keys + synonyms | yes (test oracle) | Editing fixtures/oracle |
| `data/RECORDS.md` | Data dictionary: field rationale, per-record reasons | yes (field meanings) | Need field meanings |
| `data/__init__.py` | Package marker | — | — |
| `scripts/branch_audit.py` | Read-only branch-cleanup audit (`make branch-audit`) | — | Branch cleanup |
| `tests/` | Behavior contract (cooccurrence, frequency, fuzzy, gap, recurrence, report, sample_records) + Hypothesis properties (extractor + rule layer, ADR 0025/0027) | **yes (behavior contract)** | Changing behavior |
| `docs/agent-guides/architecture.md` | Engine facts: commands, map, hard rules, counts | **yes (engine facts)** | Coding the engine |

## Decisions / discipline / narrative
| File | Purpose | Canonical? | Load when |
|---|---|---|---|
| `docs/adr/` (`0001`–`0027` + `README.md`) | Decision log (build + assistant process) | **yes (decisions)** | "Why was X done" |
| `docs/DOC_DISCIPLINE.md` | Evidence levels + ADR-confirmation + drift control | **yes (evidence levels)** | Tagging claims / audits |
| `JOURNAL.md` | Session narrative / lessons (ARCHIVED 2026-06-07 — historical only; diary is chat-only now, ADR 0024) | — (historical archive) | Want the why/story (pre-2026-06-07) |
| `docs/CLAUDE_OPERATING_MANUAL.md` | Operating manual | — | Deeper process |
| `docs/AGENT_AUDIT_METHOD.md` | Subagent-audit + code-review playbook | yes (audit method) | Running an audit |
| `docs/RESEARCH_2026-06-07_ai-verification.md` | RESEARCH_ONLY audit of 3 AI deep-research docs: corroborated findings + fabrication ledger (prompted ADR 0027) | — (dated research) | AI-verification research context |
| `docs/BRANCH_CLEANUP.md` | Branch-cleanup procedure | — | Cleaning branches |
| `docs/TOOLS_CHEAT_SHEET.md` | Token-frugal tool patterns | — | Tooling questions |
| `docs/PROMPT_AUDIT.md` | Prompt-audit notes | — | Prompt audits |
| `docs/COLD_START_HANDOFF.md` | Cold-start orientation | — | (see Tier 1) |
| _session handoffs + full session log_ | Per-session deep history (3 handoffs + full log) | — | **Archived to Drive:** `health-prototype/archive` (off-repo, keeps the tree lean) |

## Build / CI / meta / public
| File | Purpose | Canonical? | Load when |
|---|---|---|---|
| `Makefile` | `test` / `selftest` / `lint` / `check` / `demo` / `html-demos` / `branch-audit` / `clean` | — | Running tasks |
| `.github/workflows/ci.yml` | CI: compileall + unittest + self-test + Hypothesis + HTML-validity (proof-html) | yes (CI gate) | CI changes |
| `.github/pull_request_template.md` | AI-assisted PR checklist pre-filled into every PR body (added by #42) | yes (PR process) | Opening a PR |
| `README.md` | Public-facing project description | yes (public face) | External readers |
| `SOVEREIGN_SCRIBE_SALVAGE.md` | Salvage of the separate clinical-scribe project | — | That project only |
| `.gitignore` | Ignore rules | — | — |
