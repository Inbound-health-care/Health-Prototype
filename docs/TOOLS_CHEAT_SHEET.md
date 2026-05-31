# Tools Cheat Sheet (plain English)

_For Scott. What the AI's tools actually do, and how to tell cheap from wasteful.
Written 2026-05-31. The big idea: **tokens = cost**. Anything that pulls raw file
bytes "through" the AI's reading costs tokens proportional to size. Copying or
moving a file server-side costs almost nothing._

## The one question that catches most waste
**"Does the AI need the file's CONTENTS, or just a RESULT?"**
- Needs a result (copy it, move it, is it gone?) → use a cheap operation.
- Needs to understand/synthesize the contents → reading is unavoidable (fine).

---

## Google Drive

| Want to... | Cheap way | Wasteful way (avoid) |
|---|---|---|
| Back up / duplicate a file | `copy_file` — Drive copies it itself, bytes never touch the AI | Read the whole file, then re-type it into a new file |
| Move a file | `copy_file` then delete original | same waste as above |
| Find files | `search_files` with small `pageSize` + `excludeContentSnippets: true` | pulling 100 files WITH their text snippets (huge) |
| Know what a file is | read just ONE as a sample, or check its title | reading all 100 to learn they're all the same kind |
| Read a doc to use its content | `read_file_content` (this one genuinely needs the bytes) | — |

**Note:** consolidating many files into ONE new doc (like the salvage doc) *must*
read + write — that's real synthesis, not a copy. That cost is legitimate.

## Subagents (the "send a helper" tool)
- A subagent reads files in **its own** context and reports back only a summary.
- So having a helper read 100 files costs YOU almost nothing — you get the 1-page
  answer, not 100 files of raw text. **This is the right tool for bulk reading.**
- Trade-off: you can't see exactly what it read; you trust its summary.

## Git (for code in the repo)
- `cp` / `mv` = copy/move files locally, free.
- `git commit` then `git push` = save a snapshot, then upload it.
- Reading a file you JUST wrote to "double-check" is usually wasteful — the write
  tool already confirmed it worked.

## Web search
- `WebSearch` = quick lookup, returns titles + snippets (cheap).
- `WebFetch` = pulls a whole page's text (more expensive; use when you need detail).

## Reading big things
- If a tool result is enormous (tens of thousands of characters), it overflows and
  gets dumped to a file — then it has to be parsed with extra steps. Better to ask
  for less up front (smaller page size, exclude snippets, sample first).

---

## How YOU can spot waste in real time
Watch for the AI:
- Reading a whole file right before creating a near-identical copy → should `copy_file`.
- Pulling a giant search result → should have filtered/paginated smaller.
- Re-reading a file it just wrote → usually unnecessary.
- Deep-reading dozens of files itself instead of sending a subagent.

If you see it, say "could you copy that instead?" or "use a subagent for that."
The AI should also **tell you** when it switches to a cheaper method — if it
changes approach silently, call it out.
