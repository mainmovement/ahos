# Protocol: Connecting Supervision Agent ↔ Ahos cursor configuration Agent

## Reality (honest)

Cursor Cloud Agents **do not** have a private real-time chat channel between two
runs. Connection is **indirect** via:

1. **Shared repository** (same `github.com/mainmovement/ahos`)
2. **Supervision artifacts** this agent writes
3. **Your follow-up messages** to the Ahos agent (when urgent)
4. **GitHub PR comments** (optional, on Ahos PRs)

## Two-agent setup (recommended)

### Agent A — Supervision (this run)

- Name suggestion: `نظارت مستمر ایجنت آهوس`
- Job: hourly review, critique, write directives
- Reads: `docs/DOC_TRUTH_MAP.md`, `AGENTS.md`, cycles, Ahos agent events
- Writes: `docs/supervision/LATEST_DIRECTIVE_FOR_AHOS_AGENT.md`

### Agent B — Builder (Ahos cursor configuration)

- bcId: `bc-2773f4bf-6ae2-459f-82f0-44baa07d9500`
- Job: implement per owner goals
- **Must read before every significant action:**
  - `docs/supervision/LATEST_DIRECTIVE_FOR_AHOS_AGENT.md`
  - Latest `docs/supervision/cycles/CYCLE_*.md`
  - `docs/DOC_TRUTH_MAP.md` + `AGENTS.md`

## One-time instruction to paste into Ahos agent

Copy this as a **pinned follow-up** on the Ahos cursor configuration conversation:

```
قانون نظارت (الزامی):
قبل از هر commit، PR، یا تغییر معماری این فایل‌ها را بخوان:
- docs/supervision/LATEST_DIRECTIVE_FOR_AHOS_AGENT.md
- docs/supervision/cycles/ (آخرین CYCLE)
- docs/DOC_TRUTH_MAP.md و AGENTS.md

اگر directive گفت STOP یا BLOCK روی یک کار — انجام نده.
اگر directive گفت FIX_BEFORE_MERGE — اول آن را انجام بده.
هر ساعت directive به‌روز می‌شود؛ بعد از pull همیشه دوباره بخوان.
```

## When supervision must interrupt Ahos immediately

Supervision agent sets `status: STOP` or `status: BLOCK` in
`LATEST_DIRECTIVE_FOR_AHOS_AGENT.md`. You then send Ahos agent one line:

```
فوری: docs/supervision/LATEST_DIRECTIVE_FOR_AHOS_AGENT.md را بخوان و اطاعت کن.
```

## What supervision checks each hour

| Check | Source |
|-------|--------|
| Agent alive? | cursor-cloud list-cloud-agents |
| New PRs / failures? | agent events.json |
| On-track vs docs? | DOC_TRUTH_MAP, AGENTS.md, gap register |
| Code/doc quality? | specialist review + pytest |
| Off-rails? | Lane A edits, readiness inflation, authority leaks |

## What supervision cannot do alone

- Push messages into Ahos agent's chat without you
- Merge or kill Ahos PRs without your instruction
- Guarantee Ahos reads directives unless you paste the rule above
