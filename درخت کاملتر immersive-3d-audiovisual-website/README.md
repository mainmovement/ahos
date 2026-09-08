# AHOS — Artificial Hybrid Opportunity Scoring System

> **Evidence Before Decision.** آهوس یک ربات معامله‌گر نیست؛ یک «موجودیتِ هوشمند» است — درخت دانای فرصت‌های پنهان بازار.

AHOS is a crypto **Opportunity Intelligence System**: it discovers tokens early, gathers evidence from many independent sources, gates everything through a security layer, convenes a 10-team AI Expert Council, scores opportunities *and* confidence separately, paper-trades the winners, post-mortems everything, and learns from wins, losses — and skips.

## The Wise Tree · درخت دانا

| Metaphor | System |
|---|---|
| Roots | Data sources (market, on-chain, social, news, GitHub) |
| Soil | Internet · GitHub · blockchains · markets |
| Stones | Errors, failed APIs, wrong assumptions — every obstacle is data |
| Water | Knowledge |
| Underground ocean | Collective intelligence |
| Trunk | Core architecture |
| Branches | Ten expert teams |
| Golden fruit | Exceptional opportunities |
| Falling leaf | Post-mortems feeding the roots |

## Stack

- **Web**: Next.js 16 (App Router) · React 19 · Tailwind CSS 4
- **3D**: three.js · React Three Fiber · postprocessing (bloom/vignette) — the procedural **Wise Tree scene** (no textures, no models, 100% geometry + shaders)
- **Audio**: fully synthesized Web Audio — UI sounds + three ambient scenes (Cosmic Citadel / Solana Rainforest / Underground Ocean). No sample files.
- **i18n**: Full FA/EN with RTL switching. Persian copy is first-class; numerals stay Latin for market precision.
- **Data**: PostgreSQL + Drizzle ORM (tokens, evidence, council verdicts, paper trades, alerts, news, learning events, system nodes)
- **Ops worldview**: no VPS — n8n agents orchestrate collectors/council/learning; Docker when needed; Python where it earns its place; provider abstraction with automatic fallback A→B→C.

## Routes

```
/                  Cinematic landing — boot sequence, 3D wise tree, doctrine, funnel, council, roadmap
/dashboard         Command center — book PnL, top candidates, narrative radar, signal stream
/tokens            Token Discovery — search + stage filters, ranked candidacy dossiers
/tokens/[id]       Token Dossier — 7-score matrix, evidence ledger, council verdicts, scenarios
/council           AI Expert Council — live debate chamber, 10 teams, consensus meter
/security          Security Gate — honeypot sim, authority checks, vetoes, gate passes
/paper-trading     Paper Trading Lab — open/closed trades, lessons extracted
/learning          Learning Engine — post-mortems, patterns, model evals, self-improvement
/news              Intelligence Feed — verified news with credibility + sentiment
/alerts            Signal Stream — Telegram-mirrored alert timeline
/ai-chat           Council Chat — deterministic evidence-based assistant (FA/EN)
/system            System Status — node health, provider fallback chain, architecture
/settings          Settings — language, sound engine, ambient scenes, motion density
/api/*             JSON APIs feeding every page (/api/health for bootstrap checks)
```

## GitHub Structure (target workspace)

```
ahos/
├── app/                 # This web shell (Next.js)
├── docs/                # VISION.md · ROADMAP.md · ARCHITECTURE.md · DECISIONS/
├── agents/              # n8n workflows (collectors, council orchestrator, learning)
├── workers/             # Python workers (scoring, simulation, post-mortems)
├── db/                  # Drizzle schema + seeds
├── scripts/             # seed.ts, provider health checks
└── .github/             # issues, PRs, experiments, releases — knowledge must survive the developer
```

## Run

```bash
npm install
npx drizzle-kit push      # create tables
npx tsx scripts/seed.ts   # seed intelligence corpus (API routes also lazy-seed)
npm run dev
```

## Doctrine

1. Evidence before decision. 2. Rumor ≠ fact. 3. High opportunity + critical security risk = REJECT, non-negotiable. 4. No score without a dossier; no thesis without a paper trade; no trade without post-mortem. 5. Never fabricate: UNKNOWN · INSUFFICIENT EVIDENCE · CONFLICTED · UNVERIFIED are first-class answers. 6. Anti-FOMO: virality never changes a verdict by itself. 7. Every failure is an experiment; every skip is data.
