# AHOS Dream Dashboard: Claude Code Build Missions

Version 0.1 · 2026-10-09 (Tehran) · Grok Bot for Mehrdad Ghodrati · Paper-only plan. **Nothing here has been executed.**
Spec: `DASHBOARD_DESIGN_SPEC.md`. References: `REFERENCE_BOARD.md`.

Repo: `G:\robat\ahos` (laptop DESKTOP-DH7QOCK), branch `ahos`, HEAD `373516e` at read time. Paths below were verified by read-only listing unless marked **NEW** (to be created) or **TO-CONFIRM**.

## Standing rules for every mission (copy into each Claude prompt)
1. **Never push.** Local commits only (pushes are paused by the owner, D-H233). No force, no amend of existing commits.
2. **Never open, read or edit `.env`** (D-B08). Never print secrets or boot tokens to logs.
3. **Never touch Lane A** (`discovery/**`, `paper_trading/**`) or `config/lane_a_freeze.sha256` (AGENTS.md).
4. **TS stays presentation-only.** It creates no recommendation authority, and badges only render server states (AGENTS.md).
5. **Real data only.** No placeholder numbers. A missing source renders UNKNOWN or empty (spec §6, §7).
6. **npm installs need explicit owner approval.** The mission stops at an `OWNER_GATE` line listing the exact packages and versions.
7. Test against a **production build** (`npm run build && npm run start`, host 127.0.0.1), never `next dev` (D-B13). Stop only processes the launcher's PID files own. Never kill unrelated `node`/`claude` processes.
8. Read `node_modules/next/dist/docs/` for any Next 16 API before using it (AGENTS.md).
9. Respect the 259 existing uncommitted paths. Stage only files this mission created or changed.
10. **Reality ceiling:** self-tests reach at most **TESTED**. **OPERATIONAL** requires Mehrdad to double-click `AHOS.lnk` and confirm (D-D212).
11. Delivery review: QA (قاسم) + red team (رضا) + evidence (عرفان) per owner rule. Security (سپهر) also reviews M-D1 and M-D2.
12. **Screenshots** go to `reports/dashboard/screens/<mission-id>/` (**NEW** dir, TO-CONFIRM naming against `reports/` conventions). Capture the **app window** (not the full desktop) with `scripts/dashboard_screenshot.ps1` (**NEW** in M-D1). Each screenshot needs a sidecar `.json` holding the timestamp (Tehran), the mode/theme/tier, and the `generatedAt` of the snapshot shown.

---

## M-D1: Standalone AHOS window from the existing desktop icon (127.0.0.1 only, own profile, no external network)

**Goal.** Double-clicking the existing `C:\Users\Sniper\Desktop\AHOS.lnk` opens AHOS in its **own app window**: no tabs, no address bar, its own browser profile, loopback only. **The `.lnk` itself is not changed.**

**Verified current chain:**
- `AHOS.lnk` → `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "G:\robat\ahos\launcher\ahos.ps1" -Action start` (WorkingDirectory `G:\robat\ahos`, icon `G:\robat\ahos\launcher\ahos.ico,0`).
- That runs `python -m launcher start` (`launcher/__main__.py`), which calls `Orchestrator.start()` in `launcher/orchestrator.py`.
- About lines 773–777: `if overall in ("ONLINE","DEGRADED") and gateway HEALTHY and self.open_dashboard and not idle:` then `pk.open_url(self.bootstrap_url())`.
- `launcher/processkit.py` `open_url()` (about line 538) calls `os.startfile(url)`, which opens the **default browser tab**.
- The URL is `http://127.0.0.1:<port>/#boot=<one-time token>` (`launcher/components.py` `bootstrap_url`). The port comes from `scripts/gateway_port.py` + `config/gateway_ports.json` (candidates `[3100, 3200, 8300]`). The last `reports/launcher/status.json` shows `dashboard_url=http://127.0.0.1:3000/`.
- **`idle` (idempotent replay, about line 751) suppresses opening**, so a second click on the icon while AHOS runs opens nothing (TO-CONFIRM with the owner; see Q2).

**Paths:**
- **NEW** `launcher/appwindow.py`. Pure functions: `find_browser()`, `app_profile_dir()`, `build_app_argv(url, browser, profile_dir, size)`. Plus the side-effecting `open_app_window(url) -> bool`.
- **EDIT** `launcher/orchestrator.py` (the open block about lines 773–777, and the `idle` branch about line 751).
- **EDIT** `launcher/processkit.py`. Keep `open_url` as the fallback only.
- **NEW** `config/app_window.json`. Non-secret: browser preference `["chrome","edge"]`, window size, profile-dir template.
- **NEW** `tests/test_launcher_appwindow.py`. **EDIT** `tests/test_launcher_orchestrator.py` (existing).
- **EDIT** `docs/ONE_CLICK.md`. Add a section "App window" next to "Dashboard bootstrap (one-time `#boot=` token)".
- **NEW** `scripts/dashboard_screenshot.ps1`. Finds the app window by its profile-dir command line, then uses `System.Drawing` CopyFromScreen of its rect into a PNG.

**Steps:**
1. `find_browser()`: check `C:\Program Files\Google\Chrome\Application\chrome.exe`, then `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` (both exist on this laptop), then the registry App Paths. The order comes from `config/app_window.json`.
2. `app_profile_dir()`: `%LOCALAPPDATA%\AHOS\app-window-profile`. This is outside git and outside the repo, never the user's Chrome `Default` profile. Create it on first use.
3. `build_app_argv()` returns, in this order:
   - `--app=<bootstrap url>`
   - `--user-data-dir=<profile>`
   - `--no-first-run --no-default-browser-check --disable-sync --disable-extensions --disable-background-networking --disable-component-update --disable-default-apps --no-pings --no-proxy-server`
   - `--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE 127.0.0.1"`
   - `--window-size=1600,900`

   Verify each switch against the installed browser version (peter.sh list). Drop and document any switch the browser rejects.
4. Spawn **detached, with no console** (`CREATE_NO_WINDOW`, the processkit convention). Never pass the URL through `cmd.exe`. Never log the URL (it carries the token); log only `app_window: opened via chrome|edge|fallback`.
5. Fallback: if no browser is found or the spawn fails, call `open_url()` (the current behaviour) and write a Persian line to `logs/launcher/launcher.log`: "پنجره اختصاصی باز نشد؛ داشبورد در مرورگر پیش‌فرض باز شد" ("the dedicated window did not open; the dashboard opened in the default browser").
6. Idempotent replay (second click): if an app-window process with our `--user-data-dir` is alive, do nothing more than log "already open". Otherwise mint a **fresh** boot token and open. There must never be two AHOS app windows.
7. Session check. `/api/auth/session` requires `Sec-Fetch-Site: same-origin|none` and a loopback Host (`chat_auth.handleSessionIssuance`). Confirm that the `--app` first navigation bootstraps successfully. If it doesn't, stop and report; do not weaken the check.
8. Unit tests use pure functions only (they run on non-Windows too, using `PureWindowsPath` as `shortcuts.py` does). Cover: argv contents/order, quoting of a path containing spaces, `--user-data-dir` never equal to Chrome's default user-data root, URL absent from every log call, fallback path, and idle → no duplicate window.

**Acceptance tests:**
- `.venv\Scripts\python.exe -m pytest tests/test_launcher_appwindow.py tests/test_launcher_orchestrator.py -q` all pass. The rest of the launcher suite passes unchanged (`tests/test_launcher_smoke.py`, `tests/test_phase18_launchers.py`).
- `python -m launcher start` (via the hidden `ahos.ps1`) opens **one** window with no address bar or tabs. The title bar shows the AHOS title.
- Inside the window, the dashboard bootstraps a session. API calls return data, not `WEB_API_LOCKED_NO_TOKEN`.
- **Network proof:** `Get-CimInstance Win32_Process` filtered by our `--user-data-dir`, then `Get-NetTCPConnection -OwningProcess <pids>`. Every `RemoteAddress` must be `127.0.0.1` or `::1`. Save the output to `reports/dashboard/M-D1_network_proof.txt`.
- `Get-NetTCPConnection -LocalPort <gateway port> -State Listen` shows LocalAddress `127.0.0.1` only (not `0.0.0.0`).
- A second double-click opens no second window.
- The user's normal Chrome profile is untouched (no new tabs or history; the `Default` profile mtime is unchanged).
- With both browsers made unavailable (test via config override), the fallback opens the default browser and logs the Persian line.
- `AHOS.lnk` target, arguments and icon are byte-identical before and after.

**Required screenshots** (`reports/dashboard/screens/M-D1/`):
- `01_app_window.png` (the whole window, showing no address bar)
- `02_network_proof.png` (the terminal output)
- `03_second_click_no_duplicate.png`
- `04_fallback_log.png`

**Reality after delivery:** TESTED. OPERATIONAL only after Mehrdad double-clicks the icon and confirms.

---

## M-D2: Offline asset hardening (local fonts, CSP, zero external requests)

**Goal.** Nothing in the app requests the internet, at build or at runtime.

**Paths:**
- **EDIT** `app/layout.tsx`: replace `import { Orbitron, Vazirmatn } from "next/font/google"` with `next/font/local`.
- **NEW** `assets/fonts/` (TO-CONFIRM location; the repo has no `public/`) holding Vazirmatn, Lalezar, Markazi Text, IBM Plex Mono and Orbitron woff2 plus their OFL license texts.
- **EDIT** `next.config.ts`: add a `headers()` CSP alongside the existing `serverExternalPackages`.
- **NEW** `scripts/egress_scan.mjs`.
- **NEW** `docs/dashboard/FONT_LICENSES.md`.

**Steps:**
1. OWNER_GATE: either `npm i vazirmatn@33.0.3` (or `@fontsource/vazirmatn@5.3.0`) and `@fontsource/lalezar@5.3.0`, or vendor the woff2 files from the official repos with their OFL text.
2. Switch to `next/font/local`, keeping the CSS variables `--font-vazir` and `--font-orbitron`, so `globals.css` and `CommandCenter.tsx` keep working.
3. CSP for all routes:
   ```
   default-src 'self'; connect-src 'self'; img-src 'self' data: blob:; font-src 'self';
   media-src 'self' blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline';
   worker-src 'self' blob:; frame-ancestors 'none'
   ```
   Verify against the Next 16 docs whether nonces are preferable.
4. `egress_scan.mjs` scans `.next/static/**` and `.next/server/**` for absolute `http(s)://` origins other than `127.0.0.1`/`localhost`. It prints an allowlist report and exits non-zero on unknown hosts. News `sourceUrl` values are data and are exempt.

**Acceptance:**
- `npm run typecheck`, `npm run lint` and `npm run build` succeed with the proxy disabled and the network unplugged (or with `HTTPS_PROXY` pointed at a dead port).
- `node scripts/egress_scan.mjs` exits 0.
- In the M-D1 window, DevTools Network shows only `127.0.0.1` requests across a 5-minute session.
- The Persian text renders in Vazirmatn (DevTools Computed → Rendered Fonts).

**Screenshots:** `M-D2/01_rendered_fonts.png`, `02_network_panel_5min.png`, `03_egress_scan.png`.

---

## M-D3: Design tokens, two themes and the TruthBadge contract

**Goal.** Implement spec §2, §3 and §9 as code, with a selftest that **proves** UNKNOWN and CONFLICT can't look like success.

**Paths:**
- **NEW** `dashboard/tokens.ts` (TO-CONFIRM folder; the repo keeps TS modules at the root, so `dashboard_tokens.ts` at the root would match the existing style).
- **NEW** `dashboard_truth_badge.ts`: pure mapping and precedence functions, reusing `dashboard_truth.ts`.
- **NEW** `components/TruthBadge.tsx`.
- **EDIT** `globals.css`: CSS variables for `[data-theme="imperial"|"neon"]`.
- **NEW** `scripts/dashboard_truth_badge_selftest.ts`.
- **EDIT** `package.json`: add the script `"test:truth-badge"` in the same style as `test:dashboard-truth`.

**Steps:**
1. Read `canonical_read_model.ts` and `snapshot.ts` and list the **real** enum values of `canonicalStatus`, `identityState`, `securityState` and `decision`. Write the mapping table into the selftest header. Any unmapped value maps to UNKNOWN.
2. Implement precedence REJECTED > CONFLICT > UNKNOWN > STALE > VERIFIED. Display may only downgrade, never upgrade.
3. The tokens exactly match the spec hex values.
4. Check whether Vazirmatn has `tnum`. Record the result.

**Acceptance:** `npm run test:truth-badge` passes, covering:
- UNKNOWN and CONFLICT never get the VERIFIED colour, ✓ glyph, glow class or success sound id;
- a stale VERIFIED becomes STALE;
- `canonicalUnavailable` gives UNKNOWN;
- `disagreement` beats VERIFIED;
- an unrecognised enum gives UNKNOWN.

`npm run test:dashboard-truth` still passes.

**Screenshots:** `M-D3/01_badge_sheet_imperial.png` and `02_badge_sheet_neon.png`. These come from a dev-only badge sheet rendered with **fixture states**, clearly watermarked "FIXTURE".

---

## M-D4: RTL 2D shell refactor (the 2D fallback is built first)

**Goal.** Re-lay `CommandCenter.tsx` (1,371 lines, root) into the spec §4 RTL layout with real data, still pure 2D. This becomes the permanent 2D mode.

**Paths:**
- **EDIT** `CommandCenter.tsx`, which keeps its fetch loop (`/api/command`, `/api/alerts`, `/api/launcher` at about lines 323–325).
- **NEW** `components/shell/TopBar.tsx`, `RightNav.tsx`, `TelemetryStrips.tsx`, `CanonicalColumn.tsx`, `LiveFeed.tsx`, `OpportunityDossier.tsx` (TO-CONFIRM folder).
- `app/page.tsx` unchanged.

**Steps:**
1. Extract components without changing any fetch, auth or action semantics. The `/api/engine` start/stop stays propose → confirm, and `/api/paper` denial `hintFa` is shown.
2. Wire every widget to its spec §6 source. Widgets with no source (spend, University, agent maturity) render UNKNOWN or empty with Persian copy.
3. Implement all states from spec §7.
4. Persian digits, `<bdi dir="ltr">` for addresses and tickers, and the Tehran clock.

**Acceptance:**
- `npm run typecheck`, `npm run lint` and all existing `test:*` scripts pass.
- With the gateway stopped, every widget shows Error/STALE and none stays green (`presentStatus`).
- With the canonical model unavailable, the canonical column shows UNKNOWN.
- No hard-coded numbers: a grep for numeric literals in JSX text nodes is reviewed, and only layout constants are allowed.

**Screenshots:** `M-D4/01_command_live.png`, `02_gateway_down_stale.png`, `03_canonical_unavailable.png`, `04_1280x720.png`.

---

## M-D5: Review prior 3D prototypes, then the 3D stage foundation (quality tiers)

**Goal.** Add the R3F stage behind a lazy boundary, with quality tiers, low-power mode and automatic fallback to M-D4's 2D.

**Paths:**
- **READ ONLY:** `advanced-3d-audiovisual-website/`, `advanced-3d-audiovisual-website (1)/`, `درخت کاملتر immersive-3d-audiovisual-website/`, `سایت درختadvanced-3d-audiovisual-platform/`. These are excluded in `tsconfig.json`. Write a reuse note to `docs/dashboard/PROTOTYPE_REVIEW.md` (**NEW**).
- **NEW** `components/stage/Stage.tsx` (loaded via `next/dynamic` with `ssr:false`), `components/stage/quality.ts`, `ui_store.ts` (zustand).
- **NEW** `assets/gpu-benchmarks/` (self-hosted detect-gpu data).

**Steps:**
1. OWNER_GATE: install `three@0.186.x`, `@react-three/fiber@9.8.x`, `@react-three/drei@10.7.x`, `@react-three/postprocessing@3.1.x`, `postprocessing@6.39.x`, `detect-gpu@5.0.x`, `zustand@5.0.x`, and `r3f-perf@7.2.x` as a devDependency.
2. Tier selection: detect-gpu with a local `benchmarksURL`, then `PerformanceMonitor`, and keep the user's override. Use `frameloop="demand"` in Low tier, stop rendering on `visibilitychange`, and fall to 2D on context loss.
3. Settings toggles: theme, quality (Auto/High/Low/2D), reduced motion (defaulting to the OS setting).
4. Never use a drei `Environment preset` (it fetches from raw.githack). Build a procedural environment.

**Acceptance:**
- The 2D mode does **not** download the three chunk (Network panel).
- The 3D chunk is ≤650 KB gzip (`next build` output).
- An empty stage idles at ≤5% CPU.
- Forcing `WEBGL_lose_context` twice falls back to 2D with a Persian toast.
- `egress_scan` is still 0.

**Screenshots:** `M-D5/01_stage_empty_high.png`, `02_settings_quality.png`, `03_context_loss_fallback.png`, `04_r3f_perf_overlay.png` (dev).

---

## M-D6: Globe world (Natural Earth, real terminator, chain rings, opportunity beads)

**Goal.** Spec §1 globe: real Earth, real sun position, abstract chain rings, labelled honestly.

**Paths:**
- **NEW** `components/stage/Globe.tsx`, `components/stage/ChainRings.tsx`, `components/stage/sun.ts` (pure solar subpoint plus a selftest).
- **NEW** `assets/geo/land-110m.json` (from `world-atlas`, ISC; data from Natural Earth, public domain).

**Steps:**
1. OWNER_GATE: `three-globe@2.45.x`, `world-atlas@2.0.2`, `topojson-client@3.1.0`.
2. Instanced-dot or hex land, gold Tehran mark, and a terminator shader driven by `sun.ts`.
3. One ring per distinct `opportunities[].chain`. Each bead's angle is a stable hash of `tokenKey`. Bead badge and material come from `dashboard_truth_badge.ts`. UNKNOWN and CONFLICT beads get no bloom layer.
4. The in-scene caption "چیدمان مفهومی — موقعیت جغرافیایی ندارد" ("conceptual layout — has no geographic position"). The Geo layer toggle is disabled and shows UNKNOWN.
5. Clicking a bead flies the camera to it (a cut in reduced motion) and opens `OpportunityDossier`. A focusable DOM mirror list is provided.

**Acceptance:**
- The `sun.ts` selftest checks the solar subpoint against published values for 2 dates within 1°. Record the reference source in the test.
- Bead count equals `opportunities.length` from the same snapshot (`generatedAt` is logged).
- The same layout persists across refreshes.
- High tier: ≥50 fps target, ≥30 floor, draw calls ≤120, triangles ≤250k (r3f-perf).

**Screenshots:** `M-D6/01_globe_imperial.png`, `02_globe_neon.png`, `03_bead_dossier.png`, `04_reduced_motion.png`, `05_perf.png`.

---

## M-D7: Evidence pipeline graph and telemetry strips (ref 6)

**Goal.** Spec V4 plus the bottom strips, in 3D and as a React Flow 2D version.

**Paths:**
- **NEW** `components/stage/PipelineGraph.tsx`, `components/shell/PipelineGraph2D.tsx`, and **EDIT** `components/shell/TelemetryStrips.tsx`.
- Sources: `/api/command` (`opportunities`, `overlayCensus`, `canonicalDecisions`, `providers`, `paper`) and `/api/metrics` (`recent_cycles`, `provider_health`).

**Steps:**
1. OWNER_GATE: `@xyflow/react` (version pinned at gate time).
2. Fixed RTL node layout. Counts are grouped from real fields, with edge particles proportional to count (zero gives no particles).
3. The central node is labelled "مرجع تصمیم کانونی (پایتون)" ("canonical decision authority (Python)").
4. Strips: cycles (real durations/status), providers (with `COST_BLOCKED`/`OUT_OF_POLICY` in neutral grey), evidence coverage, paper ledger (real zeros), and alerts. **No spend strip** (source UNKNOWN).

**Acceptance:**
- The node counts sum consistently with `opportunities.length`, checked by a unit test.
- The 2D and 3D graphs show identical numbers for the same snapshot.
- Keyboard navigation works across nodes in 2D.

**Screenshots:** `M-D7/01_pipeline_3d.png`, `02_pipeline_2d.png`, `03_strips.png`.

---

## M-D8: Agent Society isometric tower (ref 5) with a read-only maturity endpoint

**Goal.** Spec V3. Floors are the `TEAM_META` teams. Maturity comes from a **new read-only** endpoint, if a truthful source exists.

**Paths:**
- **READ** `council.ts` (`TEAMS`, `TEAM_META` at about line 370), `ahos_org/registry.py`, `ahos_org/organization.py`, `agent_org/projections.py`, `agent_org/public.py`. The maturity source is **TO-CONFIRM** from these.
- **NEW** `app/api/agents/route.ts` (GET only, `authorizeDashboardEndpoint`, fail-closed `{ok:false,status:"UNAVAILABLE"}`), only if step 1 finds a real source.
- **NEW** `components/stage/AgentTower.tsx` and `components/shell/AgentGrid2D.tsx`.

**Steps:**
1. Find a real per-team or per-agent maturity or state record. If none exists, **do not create one**. Ship the tower with UNKNOWN maturity and file a dev-mission note in `data/dev_missions/dev_missions.jsonl` (via the existing `dev_missions.ts` path; TO-CONFIRM the intake rules).
2. The taxonomy caption names the source file. Never merge taxonomies (C-201, human-gated).
3. A desk glows only with fresh `council`/`votes` evidence.

**Acceptance:**
- No "active/thinking" visual appears without a timestamped record.
- The endpoint (if added) has a selftest in the repo's `scripts/*_selftest.ts` style and returns UNAVAILABLE when its store is missing.

**Screenshots:** `M-D8/01_tower.png`, `02_floor_detail.png`, `03_grid_2d.png`.

---

## M-D9: Sound system (muted by default, spatial, truth-safe)

**Goal.** Spec §8.2.

**Paths:**
- **NEW** `audio/engine.ts`, `audio/cues.ts` (cue id ↔ truth state table) and `audio/procedural.ts`.
- **NEW** `assets/audio/` holding Kenney CC0 OGG files.
- **NEW** `SOUND_CREDITS.md`.
- **NEW** `scripts/audio_cues_selftest.ts`.

**Steps:**
1. Create the AudioContext on the first unmute only. Master, three buses and a compressor. HRTF panners attached to scene objects.
2. Generate the VERIFIED, CONFLICT and REJECTED cues procedurally. Kenney files are for UI clicks and the ambience bed only.
3. Rate limiting, a silent hidden window, the volume slider and the `M` shortcut.

**Acceptance:**
- The selftest asserts that UNKNOWN and CONFLICT never map to the VERIFIED or any "positive" cue.
- First launch is silent until unmuted.
- Total audio is ≤3 MB.
- Every file is listed in `SOUND_CREDITS.md` with URL, author and licence (CC0).

**Screenshots:** `M-D9/01_sound_controls.png`, plus a 20 s screen recording `02_spatial_demo.mp4` (optional, owner listening test).

---

## M-D10: Boot sequence (golden path, ref 2) and the 3D emblem coin (ref 4)

**Goal.** Spec V0 and §14. Real launcher progress, a ≤4 s skippable sequence, and a static seal in reduced motion.

**Paths:**
- **NEW** `components/stage/Boot.tsx` and `components/stage/EmblemCoin.tsx` (procedural geometry).
- **NEW** `components/ornament/shamseh.ts` (procedural 10-fold rosette, SVG + shader).
- Data: `/api/launcher` component statuses.

**Steps:**
1. The coin is lathe-turned lacquer with a gold rim and an extruded star and figure. It uses no external model or texture fetch.
2. The golden path is a polyline shader on the floor from the desk silhouette (RTL: right) to the horizon (left).
3. Progress labels show real component statuses only.

**Acceptance:**
- `Esc` or a click skips.
- The full sequence plays only on the first launch of the day.
- Reduced motion shows the static seal.
- It never blocks the dashboard longer than the real launcher wait plus 1 s.

**Screenshots:** `M-D10/01_boot_dark.png`, `02_boot_path.png`, `03_seal.png`, `04_reduced_motion_seal.png`.

---

## M-D11: Accessibility, reduced-motion, low-power and performance verification

**Goal.** Prove spec §10–§12 on this laptop.

**Paths:**
- **NEW** `docs/dashboard/PERF_RECEIPT_<date>.md` and `docs/dashboard/A11Y_RECEIPT_<date>.md`.

**Steps and acceptance:**
1. Measure every spec §12 row in High, Low and 2D, on battery and on AC. Record GPU and driver strings.
2. Keyboard-only walkthrough of every view.
3. Windows "Animation effects" off: no flights, no rotation.
4. Font scale 130%: no clipping.
5. Contrast spot checks with DevTools.
6. Any budget miss blocks completion. Fix it or downgrade the default tier; do not edit the budget.

**Screenshots:** `M-D11/01_low_power.png`, `02_2d_mode.png`, `03_font_130.png`, `04_task_manager_idle.png`.

---

## M-D12: Owner acceptance pack

**Goal.** One Persian summary for Mehrdad (≤12 lines, short Persian, per the owner's style rules) with the screenshots index. This mission does **not** mark anything OPERATIONAL.

**Paths:**
- **NEW** `reports/dashboard/ACCEPTANCE_PACK_<date>.md`.

**Acceptance:**
- Every claim links to a receipt or screenshot.
- The ladder status is stated per mission (TESTED at most).
- The steps for the owner to double-click `AHOS.lnk` and confirm are listed.

---

## Suggested order and dependencies

M-D1 → M-D2 → M-D3 → M-D4 → M-D5 → (M-D6, M-D7, M-D8 in any order) → M-D9 → M-D10 → M-D11 → M-D12.

M-D1 to M-D4 need **no new 3D packages** (M-D2 needs only fonts), so they can start before the npm gates are approved.

## Open questions for Mehrdad (Q1–Q10)

1. **Q1 Browser:** Chrome or Edge for the app window? (Both are installed. Default plan: Chrome, then Edge.)
2. **Q2 Second click:** while AHOS is already running, should the icon re-open or focus the window? (Today the idempotent replay opens nothing.)
3. **Q3 npm approval:** do you approve installing the packages listed at each OWNER_GATE (three/r3f/drei/postprocessing/three-globe/world-atlas/detect-gpu/zustand/xyflow/fonts)?
4. **Q4 Geography:** should a backend source ever add real geography (e.g. exchange or team jurisdiction)? Until then the Geo layer stays UNKNOWN and the globe shows abstract chain rings.
5. **Q5 Default theme:** Imperial (crimson/gold) or Neon (blue) as the default?
6. **Q6 External links:** news `sourceUrl` clicks inside the locked-down window. Copy the link, or open it in your normal Chrome?
7. **Q7 Boot token on the command line:** passing `#boot=<token>` via `--app=` makes it visible to same-user processes for its short life (it is one-time). Accept this, or ask سپهر (security) to design an alternative handoff?
8. **Q8 Agent taxonomy:** which agent namespace should the Agent Society display as canonical? (Human-gated, C-201/D-H262.) Default: council teams from `council.ts`, captioned as such.
9. **Q9 Sound:** OK with procedural tones plus Kenney CC0 only (no Sonniss, whose licence is not CC0)?
10. **Q10 Faravahar and emblem art:** should we draw our own vector (recommended, licence-clean), and should the `ahos.ico` refresh be part of this work?
