# Architecture & process decision records (ADRs)

A running, append-as-you-go log of decisions on this project — **both** durable
build/architecture choices **and the assistant's own process/behavior changes**
(what it started doing differently, and why). The log is written *as the work
happens*, not reconstructed at session end. The session narrative lives in
`JOURNAL.md`; this directory is the finer-grained "decision + why + how it's
checked" record.

Why a log at all: an improvement that lives only in chat dies at the session
reset. Writing it here (a file the next memory-less instance can read) is how a
decision actually persists. See `docs/CLAUDE_OPERATING_MANUAL.md` and
`docs/DOC_DISCIPLINE.md`.

## Format (per `DOC_DISCIPLINE.md` §2)

Each ADR is `NNNN-short-slug.md` and states:

- **Context** — what prompted the decision; the problem or need.
- **Decision** — what was chosen (and notable alternatives rejected).
- **Consequences** — what this makes easier/harder; trade-offs.
- **Confirmation** — *how the decision is verified* (a test, a command, a
  transcript check). No ADR is ceremony; every one is checkable.
- **Evidence level** — `CONFIRMED_USER_SIDE` / `CONFIRMED_ASSISTANT_SIDE` /
  `IMPLEMENTED_UNVERIFIED` / `RESEARCH_ONLY` / `SUPERSEDED`.

Mark a superseded decision `SUPERSEDED` (point to its replacement); don't delete
it — history is the point.

## Index

- [0001 — Tool-call discipline: one decisive call, trust exit codes over prose](0001-tool-call-discipline.md)
- [0002 — Combined report: expert registry, omit clean records, additive formatter kwarg](0002-combined-report-architecture.md)
- [0003 — Co-occurrence: the fourth surfacing rule (two items, same dates)](0003-cooccurrence-rule.md)
- [0004 — `--report-v1`: the combined report with v1 opt-in matching](0004-report-v1.md)
