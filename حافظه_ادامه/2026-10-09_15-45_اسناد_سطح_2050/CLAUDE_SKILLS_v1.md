<!-- Tehran: 2026-10-09 15:45 (UTC+3:30) | Version: v1 | Author: Asi (اسی) for AHOS -->
<!-- Reason: free, low-RAM picks that make Claude Code build AHOS (Python brain + Next.js dashboard, Windows, 8 GB floor) faster and more reliably. -->
# CLAUDE_SKILLS v1 — AHOS

## ⚠️ Hard-law flag first
Claude Code itself needs a paid Claude plan or API credit. Everything below is free,
but only usable if Mehrdad already has Claude access. If not, the same MCP servers
work with free clients (e.g. Gemini CLI with his existing Gemini key). Do not buy anything.

## Vetting rules applied
Free + open source, runs on Windows, ~0 extra RAM (npx/stdio, no Docker),
no hard-coded paths (project/local scope only), no paid keys.

## 1. Claude Code Setup (approved, local scope)
Reason: per-project config keeps AHOS portable (M-PORT).
- Install: `npm i -g @anthropic-ai/claude-code`  (Node 18+)
- In repo root: `claude` then `/init` → creates `CLAUDE.md` (commit it; put AHOS laws there).
- Add servers with `--scope local` (or `project` to share via `.mcp.json`).
- Verify: `claude --version` and `claude mcp list`.

## 2. Task Observer (approved)
Reason: watches task progress so long builds don't silently stall.
- Install: `/plugin` → search "task observer" in the configured marketplace → install.
- Verify: `/plugin` shows it enabled; run a small task and confirm it reports status.
- Note: exact package name not re-verified by me (low-token budget) — Soltan to confirm source.

## 3. Context7 MCP — up-to-date library docs
Reason: stops Claude using stale Next.js/Python APIs. Free tier, no key needed.
- `claude mcp add --scope local context7 -- npx -y @upstash/context7-mcp`
- Verify: `claude mcp list` → connected; ask "use context7: Next.js app router fetch".

## 4. Playwright MCP — dashboard testing
Reason: Claude can open the Next.js dashboard and check it visually. Free.
- `claude mcp add --scope local playwright -- npx -y @playwright/mcp@latest`
- Verify: ask Claude to open http://localhost:3000 and screenshot.
- RAM: run headless; close when done on 8 GB.

## 5. Sequential Thinking MCP — planning the decision brain
Reason: structured step-by-step reasoning for brain logic. Official, free.
- `claude mcp add --scope local seq -- npx -y @modelcontextprotocol/server-sequential-thinking`
- Verify: `claude mcp list` → connected.

## 6. Official plugin marketplace
Reason: one free source for vetted plugins/skills.
- In Claude: `/plugin marketplace add anthropics/claude-code` then `/plugin` to browse.
- Verify: marketplace listed in `/plugin`.

## Dev techniques (free, zero install)
- Keep `CLAUDE.md` short: laws, stack, commands (`pytest`, `npm run dev`), no machine paths.
- Plan mode first (Shift+Tab) for big changes; then implement.
- Tests-first: ask Claude to write `pytest` / Playwright tests, then code to pass them.
- `/compact` and `/clear` often to save tokens.
- Hardware tiers read at runtime (`psutil.virtual_memory()`), never hard-coded.

## Rejected
Paid APIs, Docker-based servers (too heavy for 8 GB), cloud-hosted MCPs needing keys.
