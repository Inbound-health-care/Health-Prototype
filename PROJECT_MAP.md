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
| `SECURITY.md` | Public vulnerability-reporting front door; points to the detailed policy | — (public entrypoint) | Reporting a vulnerability |
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
| `audit.py` | Governance audit trail: hash-chained event log (digests+counts only) + deterministic monitor (ADR 0030) | yes (governance) | Audited runs / trail verification |
| `data/sample_records.py` | Synthetic records + hand-written answer keys + synonyms | yes (test oracle) | Editing fixtures/oracle |
| `data/RECORDS.md` | Data dictionary: field rationale, per-record reasons | yes (field meanings) | Need field meanings |
| `data/__init__.py` | Package marker | — | — |
| `scripts/branch_audit.py` | Read-only branch-cleanup audit (`make branch-audit`) | — | Branch cleanup |
| `tests/` | Behavior contract + Hypothesis properties + sensitive-change/workflow-security tests (ADR 0025/0027/0028) | **yes (behavior contract)** | Changing behavior or gates |
| `docs/agent-guides/architecture.md` | Engine facts: commands, map, hard rules, counts | **yes (engine facts)** | Coding the engine |
| `tools/scan_sensitive_changes.py` | Staged/PR diff gate for secrets and high-confidence identifiers; redacted output | yes (scanner behavior) | Commit/CI safety work |
| `.githooks/pre-commit` | Optional local entrypoint for the sensitive-change scanner | — | Local hook setup |

## Decisions / discipline / narrative
| File | Purpose | Canonical? | Load when |
|---|---|---|---|
| `docs/adr/` (`0001`–`0030` + `README.md`) | Decision log (build + assistant process) | **yes (decisions)** | "Why was X done" |
| `docs/DOC_DISCIPLINE.md` | Evidence levels + ADR-confirmation + drift control | **yes (evidence levels)** | Tagging claims / audits |
| `docs/LEARNINGS.md` | Append-only dated tool, failure-mode, and verification lessons | yes (practical lessons) | A reusable lesson is found |
| `JOURNAL.md` | Session narrative / lessons (ARCHIVED 2026-06-07 — historical only; diary is chat-only now, ADR 0024) | — (historical archive) | Want the why/story (pre-2026-06-07) |
| `docs/CLAUDE_OPERATING_MANUAL.md` | Operating manual | — | Deeper process |
| `docs/AGENT_AUDIT_METHOD.md` | Subagent-audit + code-review playbook | yes (audit method) | Running an audit |
| `docs/RESEARCH_2026-06-07_ai-verification.md` | RESEARCH_ONLY audit of 3 AI deep-research docs: corroborated findings + fabrication ledger (prompted ADR 0027) | — (dated research) | AI-verification research context |
| `docs/RESEARCH_2026-06-11_moe-clinical-rollout.md` | RESEARCH_ONLY fact-check of the "six experts" MoE doc + fabrication ledger; deterministic subset → ADR 0029 | — (dated research) | MoE rollout / clinical-expert context |
| `docs/RESEARCH_2026-06-11_audit-trail-standards.md` | RESEARCH_ONLY audit-log standards research (RFC 6962/8785, HIPAA/ASTM/FHIR refs, OWASP) → ADR 0030 | — (dated research) | Audit-trail design context |
| `docs/BRANCH_CLEANUP.md` | Branch-cleanup procedure | — | Cleaning branches |
| `docs/TOOLS_CHEAT_SHEET.md` | Token-frugal tool patterns | — | Tooling questions |
| `docs/PROMPT_AUDIT.md` | Prompt-audit notes | — | Prompt audits |
| `docs/COLD_START_HANDOFF.md` | Cold-start orientation | — | (see Tier 1) |
| _session handoffs + full session log_ | Per-session deep history (3 handoffs + full log) | — | **Archived to Drive:** `health-prototype/archive` (off-repo, keeps the tree lean) |

## Build / CI / meta / public
| File | Purpose | Canonical? | Load when |
|---|---|---|---|
| `Makefile` | Test, self-test, lint, exact dev install, sensitive scan, demos, HTML generation, audit, cleanup | — | Running tasks |
| `requirements-dev.txt` | Exact CI/dev versions for Ruff and Hypothesis; no runtime dependencies | yes (dev dependency versions) | CI/dev-tool updates |
| `.github/workflows/ci.yml` | CI: compileall + unittest + self-test + Hypothesis + HTML-validity (proof-html) | yes (CI gate) | CI changes |
| `.github/workflows/sensitive-scan.yml` | Read-only PR sensitive-change gate | yes (sensitive gate) | Scanner/workflow changes |
| `.github/workflows/dependency-review.yml` | Read-only PR dependency-change review | yes (dependency gate) | Dependency/workflow changes |
| `.github/dependabot.yml` | Weekly GitHub Actions and pip update checks | yes (update cadence) | Dependency automation changes |
| `.github/pull_request_template.md` | Intent, deviation, AI, health/provenance, verification, and records checklist | yes (PR process) | Opening a PR |
| `README.md` | Public-facing project description | yes (public face) | External readers |
| `SOVEREIGN_SCRIBE_SALVAGE.md` | Salvage of the separate clinical-scribe project | — | That project only |
| `.gitignore` | Ignore rules | — | — |
