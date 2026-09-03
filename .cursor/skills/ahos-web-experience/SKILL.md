---
name: ahos-web-experience
description: AHOS Next.js/React UX — RTL/LTR, dashboard, chat, realtime UI, accessibility, performance, Native Browser verification.
paths:
  - "app/**"
  - "**/*.tsx"
  - "**/*.ts"
  - "CommandCenter.tsx"
  - "globals.css"
---

# AHOS web experience

Preserve `CommandCenter.tsx` and existing `/api/*` routes. Do not rebuild the
frontend. Add bilingual architecture: Persian RTL, English LTR.

TypeScript must not independently recommend. Chat reads canonical evidence.
Escape HTML. Bind servers to `127.0.0.1`. Fail-closed `AHOS_WEB_API_TOKEN`.

Audio OFF by default; arm only after a user gesture.
Prefer CSS before WebGL; dynamic import WebGL; 2D fallback; reduced motion.

Verify with Native Browser: console/network, loading/empty/error states,
responsive layout. Playwright only when the same flow must regress across PRs.

Required routes are currently MISSING as App Router paths; SPA tabs are a
PARTIAL stand-in. Implement locales without destroying the existing command
center.
