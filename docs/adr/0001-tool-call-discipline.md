# 0001 — Tool-call discipline: one decisive call, trust exit codes over prose

**Date:** 2026-05-31
**Evidence level:** CONFIRMED_ASSISTANT_SIDE (the failure and the fix both
happened in this session's transcript)
**Type:** Process / assistant behavior (not a code change)

## Context
During the router/report build, the displayed tool output was intermittently
unreliable: results came back garbled, empty, or even carried injected
first-person prose ("the terminal is being unreliable, let me try again") that
the assistant had not written. Faced with self-contradictory output, the
assistant re-ran commands to find ground truth — but over-did it: the test
suite was run ~5 times and a couple of throwaway "is the channel alive" echoes
were fired. The underlying execution was actually deterministic and fine; only
the *display* of results was corrupted. The user flagged the repetition and
asked the assistant to log how it would change — and to do that logging as a
standing habit, including for its own behavior.

## Decision
Make verification **decisive on the first call** instead of re-running until the
output "looks clean":

1. **One robust call, not N noisy ones.** Capture output to a file, tie the
   verdict to the process **exit code**, and print a single distinctive sentinel
   (e.g. `rc=0 :: OK`). Exit codes and the harness's authoritative result are
   hard to corrupt; trust them over rendered prose.
2. **ASCII-safe summaries.** The garbling clustered on unicode (notably the
   em-dash `—` in report output). Prefer `grep`/printed ASCII summaries
   (`Ran 53 tests … OK`) over dumping unicode-heavy text through the channel.
3. **Batch verification.** Lint + suite + the specific assertion in one command,
   not three separate ones.
4. **Trust a strong signal once.** If `git push` returns rc=0 and `LOCAL==REMOTE`,
   do not re-verify it three different ways.
5. **Re-run only on genuine self-contradiction** — and design the *first* run to
   be conclusive, so a re-run is rare, not a fishing expedition.

## Consequences
- Fewer, sharper tool calls; no blind repeats; less context burned on noise.
- Verification is anchored to exit codes + sentinels, which survive a flaky
  display — more trustworthy "green", not just "looks green."
- Slight up-front cost: commands are a bit more elaborate (file capture +
  sentinel). Worth it.

## Confirmation
- This session's later verification calls already follow it: suite run captured
  to a file with `rc=` + `Ran N tests … OK` sentinels; the ADR README was
  checked for stray content via a Python `repr` dump rather than a re-read that
  could itself be garbled (which is how the leaked closing-tag bug in
  `docs/adr/README.md` was caught and fixed).
- Ongoing check: in future transcripts, a given verification command should
  appear **once** per state change, not repeated to "confirm the display."
