# AHOS DASHBOARD MASTER SPEC (owner-approved target) - Soltan 2026-10-13 23:00 Tehran
This file OVERRIDES older dashboard plans. Read it fully at the start of every dashboard session.

## Owner references (the bar - never ship below them)
- reports/dashboard/owner_reference/01_dashboard_target.jpg = THE LAYOUT AND RICHNESS TARGET.
- reports/dashboard/owner_reference/02_brand_story.jpg = mood: dark-to-gold light, golden path, cinematic.
- reports/dashboard/owner_reference/03_app_icon.jpg = THE OFFICIAL AHOS ICON (gold star with figure, black glass disc, gold ring). Use it as app icon (.ico 16-256), header logo, loading screen.
Open each image and study it before coding. Describe in PROGRESS_LOG.md what you will match.

## Layout to match (from 01)
- Desktop app window (no browser chrome). Full-screen command center, dense, glassmorphism panels with glowing edges.
- Top bar: AHOS logo + search, status chips (PAPER ONLY, System Health, Evidence Freshness, Uptime), clock (Tehran), owner avatar "Mehrdad".
- Left sidebar nav with counters: Command Center, Discovery, Opportunities, Market Intelligence, Auto Trading (Agents), AHOS University/Research Lab, Identity & Security, Evidence, Paper Trading, Learning, Agents, Chat with AHOS, Audit & Governance, Settings.
- Hero banner: greeting "Good evening, Mehrdad" + cinematic background.
- KPI cards row with sparklines (Total/Verified/Monitor/Rejected).
- CENTER: holographic 3D globe with orbit rings and floating opportunity badges, on a glowing pedestal.
- Live Market Scan table; Canonical Decision card with score ring; Security & Risk gauge.
- Right: Live Intelligence Feed + Quick Actions.
- Bottom row: University/Research Lab, Agent Society, Auto Trading performance chart, Chat with AHOS; bottom dock buttons (Evidence Graph, Knowledge Base, Learning Center, System Monitor, Audit Log).
- Persian/English both supported (Vazirmatn for Persian). Every number comes from REAL local data (soak, registry, ledger); if missing show a styled "waiting for data" state, never "UNKNOWN".

## Visual language
- Base: deep navy/black. Brand: gold (#D4AF37 family) from 02/03. Accents: cyan/electric blue holographic glow as in 01. Smooth gradients, bloom, depth, subtle motion; nothing flat or empty.
- Use vendor_assets: icons (Lucide/Tabler/Phosphor), Radix tokens, fonts, Arwes frames, ECharts/lightweight-charts, HDRIs, sounds. Build nothing from scratch that exists there.

## Quality gate (MANDATORY before every commit of visual work)
1. Take a real screenshot at 1920x1080 into reports/dashboard/screens/<mission>/.
2. Make a side-by-side image (screenshot | 01_dashboard_target.jpg) and save it next to it.
3. Score yourself 0-10 honestly on: layout match, richness/density, polish/glow/depth, real data, no visual bugs. Write the scores in PROGRESS_LOG.md.
4. If any score < 8, do NOT commit as done - improve first (max 2 tries per issue, then simplest vendor solution).
5. Never claim a fix without the screenshot path. Never regress below GLOBE_MEMORY.md reference.

## Build order
1. App window + working desktop launcher + new icon from 03.
2. Shell layout (top bar, sidebar, bottom dock) matching 01.
3. Center globe polished (no blobs) with rings and badges.
4. KPI cards, market scan, decision card, risk gauge, intelligence feed, quick actions - all on real data.
5. Bottom row panels, then each sidebar screen (University, Office, Evidence graph, Ledger, Chat).
6. Then QUEUE v2 A-H and the rest of the AHOS queue (see README STANDING ORDER).

## Use ALL existing design work and assets (owner order 2026-10-13 23:03)
Before building any part, check these and REUSE them; do not redo work that already exists:
- Soltan/Dashi designs: reports/grok/queue_2050/CLAUDE_DASHBOARD_2050.md, CLAUDE_DASHBOARD_2050_ADDENDUM_v1.19.md, OWNER_FEATURES_5_ADDENDUM_v1.md, M57_M59_UNIVERSITY_TEAMS_MEMORY_ADDENDUM_v1.md, FREE_HERO_FX_SOURCES_v1.md; reports/grok/dashboard/DASHBOARD_DESIGN_SPEC.md; reports/grok/autopilot/missions/M57-agent-subteams-org-design.md. Where they conflict, this MASTER_SPEC and the owner reference images win.
- Downloaded assets: vendor_assets/ (characters, charts, fonts, globe, hdri, hud, icons, loaders, sounds, tokens, vfx) - index in vendor_assets/README.md.
- If something needed is missing: download a FREE, license-safe (MIT/Apache/CC0/OFL) ready-made asset or library into vendor_assets/<area>/ and add it to vendor_assets/README.md, instead of hand-building it. Never paid, never GPL linked into AHOS.
- Goal: move FORWARD fast; no rework, no rebuilding what exists.

## STRATEGY CHANGE - TEMPLATE FIRST (owner order 2026-10-14 00:06, highest priority)
Stop hand-writing the dashboard. Do this instead:
1. Download a complete FREE open-source (MIT/Apache) dark admin/command-center dashboard template built on React/Next + Tailwind that is closest to owner_reference/01_dashboard_target.jpg (glassmorphism, sidebar, KPI cards, charts, feed). Candidates to evaluate quickly (pick 1, max 30 min): shadcn/ui dashboard blocks (shadcn-admin), Tremor dashboard templates, TailAdmin Next.js (free), Horizon UI, Mosaic Lite, Magic UI / Aceternity UI free components for glow/hologram effects. Put it in vendor_assets/templates/<name>/.
2. Reskin it to the AHOS look (dark navy + gold from 02/03, cyan holographic accents from 01), add the AHOS icon, Persian/English text, and drop the existing 3D globe component into the center.
3. Wire its cards/tables/charts to real local AHOS data.
4. Keep only what the template lacks as custom code. Target: a full first version of the whole layout in one working session, then polish.
Same quality gate (side-by-side with 01, score >= 8) and commit-by-path rules apply.
