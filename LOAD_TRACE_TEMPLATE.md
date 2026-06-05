# LOAD_TRACE_TEMPLATE — startup audit

Emit this block at the start of each session (after the load order in `AGENTS.md`),
then report the three things `LOAD.md` asks for. Fill every field; "Unverified /
unknown" must not be empty if anything is unsure.

```text
LOAD TRACE — <YYYY-MM-DD>, <engine/model>
- Loaded:               <files actually read this session, in load order>
- Not loaded:           <control/Tier-3 files deliberately skipped — and why>
- Applied rules:        <operator rules + firewall + security policy you hold>
- Verified state:       <facts checked against the live repo/tests THIS session>
- Unverified / unknown: <anything assumed, stale, or not yet checked>
```

Rules of the trace:
- "Verified state" = checked against the live repo or a run (per
  `SECURITY_AND_TOOL_POLICY.md` §D and `docs/DOC_DISCIPLINE.md`). If you did not
  run it, it is not verified — put it under "Unverified / unknown."
- Treat memory/chat as candidate evidence, not verified state.
- This trace is the honesty boundary between "I read it" and "I confirmed it."
