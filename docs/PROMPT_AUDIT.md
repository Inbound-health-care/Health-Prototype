# Prompt Audit — self-check your prompts before sending

_Use a SECOND, different AI to critique a prompt before you run it in Claude Code.
Different model = outside opinion, not the same engine grading its own homework.
Free, phone-friendly. If building in Claude → audit in ChatGPT or Gemini._

## The wrapper (paste this into the other AI, with your prompt inside)

```
You are a prompt critic. Below is a prompt I'm about to send to an AI coding
agent. Do NOT answer it — instead audit it. Tell me:
1. What's ambiguous or could be misread
2. What context is missing
3. Where it might make the AI do too much, or the wrong thing
4. A tightened rewrite

My prompt:
"""
[paste your prompt here]
"""
```

The key line is **"Do NOT answer it — audit it."** Without that, the AI just runs
the prompt instead of critiquing it.

## When to use it
- Before a big/expensive task (a new build phase, a refactor, a cleanup).
- When a prompt feels vague and you want a second read.
- Not needed for small, obvious asks ("run the tests").

## The shape of a good prompt (what the audit is checking for)
1. **Orient** — point the agent at the truth first ("read STATUS.md first").
2. **One clear job** — the single thing that matters this turn.
3. **A stop point** — "then stop and show me," so you can check before it runs on.
"Orient → one job → checkpoint" beats "continue where we left off" every time,
especially on a phone where you can't babysit.

## Tools
- **ChatGPT** (chat.openai.com) or **Gemini** (gemini.google.com) — free tiers fine.
- No paid prompt apps needed. A second AI chat + this wrapper IS the auditor.
