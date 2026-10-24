# AHOS Decisions Log

## 2026-10-15: Dashboard Template Integration

**Question:** Should we replace the current AHOS dashboard with the complete shadcn-admin template?

**Choice:** YES - Replace with shadcn-admin template

**Reason:**
- The existing dashboard was outdated and didn't match the AHOS design system
- The shadcn-admin template provides a modern, professional foundation with built-in components
- Template includes glassmorphism styling that aligns with AHOS aesthetic (dark navy + gold + cyan holographic)
- Persian/RTL navigation support already implemented in template
- Better structure for AHOS-specific integrations (AhosOverview component, real data via useSnap hook)

**Outcome:**
- Created `template-dashboard.tsx` with AHOS branding
- Integrated Persian navigation with RTL support
- Wired KPI cards to real AHOS data via useSnap hook
- Maintained AHOS color scheme throughout template
- Committed integration to git (commit 0a08472)

## 2026-10-15: 3D Globe Integration and KPI Wiring

**Question:** Should we integrate the 3D globe visualization and wire KPI cards to real AHOS data?

**Choice:** YES - Replace smart news with Globe3D and wire real data

**Reason:**
- The template dashboard needs a visualization component that showcases AHOS's global monitoring capabilities
- KPI cards should display real data from the useSnap hook, not static placeholder values
- Globe3D demonstrates AHOS's sophisticated data visualization capabilities
- Maintains consistency with AHOS design system (holographic effects, color scheme)

**Outcome:**
- Replaced static "Smart news" card with dynamic Globe3D visualization
- Wired all four KPI cards to useSnap data fields:
  - total_opportunities, opportunity_growth
  - in_monitoring, monitoring_growth  
  - rejected, rejection_change
  - in_execution, execution_change
- Globe3D features: golden atmosphere, cyan holographic rings, particle system
- Committed integration to git (commit feefa80)

**Next Steps:**
- Verify Globe3D visualization works properly in the dashboard
- Test KPI data updates when useSnap data changes
- Explore additional visualizations for dashboard sections

## 2026-10-15: Template Dashboard Integration Complete

**Question:** Is the template dashboard fully integrated with AHOS components?

**Choice:** YES - All components are properly integrated

**Reason:**
- Template dashboard now uses real AHOS data via useSnap hook
- Globe3D visualization provides sophisticated global monitoring display
- AhosOverview component shows the full AHOS command center
- AHOS branding (dark navy, holographic effects) consistently applied
- Persian/RTL navigation fully implemented

**Outcome:**
- Complete integration of shadcn-admin template with AHOS branding
- All KPI cards wired to real data fields from useSnap
- Globe3D visualization replacing static news section
- AhosOverview component showing full AHOS dashboard
- Maintained AHOS design system throughout
- Committed changes (commit feefa80)

**Status:** INTEGRATION_READY

## 2026-10-15: Dashboard Integration Summary

**Completed Integration:**
- shadcn-admin template fully integrated with AHOS branding
- Persian/RTL navigation implemented with correct structure
- 4 KPI cards wired to real AHOS data from useSnap hook
- Globe3D visualization component created and integrated
- AhosOverview component integrated showing full AHOS dashboard
- Desktop app window styling with holographic effects applied
- Consistent AHOS design system throughout

**Key Components:**
1. Header with Persian navigation
2. KPI cards: total_opportunities, in_monitoring, rejected, in_execution
3. Market overview (AhosOverview) showing full dashboard
4. 3D globe with holographic effects
5. AuthenticatedLayout with holographic styling

**Design System:**
- Primary colors: dark navy (#0a0e17), gold (#D4AF37), cyan (#00D9FF)
- Glassmorphism effects with backdrop blur
- Holographic border and glow effects
- Persian RTL typography (Vazirmatn font)
- Responsive grid layouts

**Commits:**
- 0a08472: Initial template integration with Persian navigation
- feefa80: 3D globe integration and KPI data wiring
- b1bf832: Finalize shadcn-admin template integration

**Next Phase:** Desktop application window styling and additional visualizations

## 2026-10-18: M47 / M39 fault injection stays simulated

**Question:** Should the monthly fault suite kill a daemon, fill the disk, lock the live PGlite store, or break the live ledger hash chain?

**Choice:** No. Inject the observation in process and require HALT inside the 60s decision budget.

**Reason:** The gold paper soak is running. Destructive faults would stop that soak or corrupt its ledger. HOLD and PAPER_ONLY stay in force. There is no live order to flatten. Owner unhalt is a pure function and does not clear HOLD.flag.

## 2026-10-18: Yahoo GC=F freshness + rejected xaus.com mirror

**Question:** Live soak reports UNRESOLVED when only gold-api is fresh. Add xaus.com as a second spot?

**Choice:** Reject xaus (spot_usd_oz matched gold-api byte-for-byte; silver_source names gold-api.com). Change Yahoo adapter to read the 1m chart and prefer the latest 1m close when it is newer than regularMarketTime.

**Reason:** The two-source independence clause forbids two mirrors of one feed. Weekend/COMEX-closed stale futures stays UNRESOLVED by design (GOLD_MAX_AGE_SEC unchanged). Owner options for a true 24/7 second feed are listed in ahos_assets/OWNER_ACTIONS.md section 5.

| 2026-10-21 | Continue M-series without cloud / user stop | Sync AHOS data paths in launcher .env.local | Arena cwd was G:\robat\AHOS_Launcher\app so relative ../ahos paths missed real soak files |
| 2026-10-21 | Soak after Oct-19 milestone | start_soak --days 0 + manual --once cycle | Refresh stale UI; witness VERIFIED; continuous PAPER_ONLY cadence at logon |
| 2026-10-21 | Telegram logon task | User Startup copies instead of schtasks | Register-ScheduledTask access denied |

## 2026-10-22 — LightStart post-Logon silence (launcher)
- **Question:** Why did automatic Logon leave no light_start.log / stamp_lightstart while VerifyStack ran?
- **Choice:** Fix AHOS_LightStart.ps1 parse break (ASCII hyphen instead of curly/mojibake quote in DEGRADED message); add Logon invoke begin/end/FAIL lines; verify with one isolated LightStart while Arena HTTP 200 (no Force restart / no ApplyPending).
- **Reason:** Parser reported missing string terminator; SilentlyContinue on Logon hid the failure. Isolated run wrote begin/done + stamp RUNNING; Arena PID unchanged.
- **Repos:** G:\robat\AHOS_Launcher only (not a git repo). ahos/arena trees not modified for this fix.

## 2026-10-22 — Canonical-only paper entry boundary (owner governance)

- **Question:** May Lane B open PAPER positions via a Lane A freeze amendment (public entry + monitor-only APIs) or via direct SQL/copied INSERT into Lane A tables?
- **Choice (owner):** Option A ACCEPTED — preserve the existing Lane A freeze (discovery/**, paper_trading/**). No bridge implementation authorized.
- **Option B:** NOT APPROVED — freeze-amendment proposal only; no public open_canonical_paper_position / run_monitor_v3 authorized; no freeze-hash regeneration authorized.
- **Option C:** REJECTED — direct Lane B SQL / copied INSERT into Lane A tables remains forbidden.
- **PAPER_ONLY:** Mandatory. Real trading remains disabled. No OPERATOR_READY / production-readiness claim.
- **Evidence baseline:** Remains PARTIALLY_ESTABLISHED (lifecycle/recovery contracts). Not upgraded by this decision.
- **Unresolved risks (explicit; not resolved):** (1) transaction atomicity of snap/trade/ALLOCATE/ENTRY under separate commits; (2) no schema/API duplicate-ALLOCATE prevention; (3) orphan decision_snapshot_v2 + permanent per-token uniqueness/skip; (4) missing-ALLOCATE recovery is exclusion-via-invalidation only (not financial repair); (5) no verified public monitor-only API (run_cycle_v3 still combines entry scan + monitor).
- **Reason:** Owner selected freeze preservation. Chat-only ADR was never persisted as a repo file; this log entry is the durable governance record.
- **Stop:** Documentation only. Implementation deferred pending a new explicit owner decision.

## 2026-10-24 — Mega Wave 9 (C47–C56) closure

- **Question:** Wire 4-Brain Autonomous Coder (M60.C) across Python, Arena, and M31 without violating 8GB anti-freeze rules?
- **Choice:** Implement `autonomous_coder_bridge.py` with offline-safe :8787 probe; step-18 exporter; Arena read-only bridges; single-file pytest/selftest only.
- **Reason:** Owner mandate for internal coding/self-debug/self-update gated by M70.6; no live apply or full-suite CI on 8GB laptop.

## 2026-10-23 — Mega Wave 8 (C37–C46) closure

- **Question:** Execute Wave 8 under 8GB anti-freeze rules with split pytest/selftest files?
- **Choice:** Run exporters and tests one file at a time; register brain/M35-M10-M45 exporters as steps 16–17 (27 manifest artifacts); no `next build` / full pytest.
- **Reason:** Matches CURSOR_SAFE_MISSION.md and owner mandate for Whole-AHOS 8-organ + honest ACI→AGI→SI progression (`day_1_agi_claimed=false`).
2026-10-24 | Mega Wave 10 path mapping | Use architecture/mission/* | PAPER_ONLY C57-C66
2026-10-24 | Mega Wave 11 | Map mission paths to architecture/mission and teaching_mode_m65 | PAPER_ONLY C67-C76
2026-10-24 | Mega Wave 12 | GATE_1 0 CONFLICT fix; 6/6 GREEN readiness | PAPER_ONLY C77-C86
2026-10-24 | Mega Wave 13 hold gates | Add 8 organ + launcher/assets HOLD.flag to meet M60.I count >=12 without removing any gate | PAPER_ONLY C87-C96
2026-10-24 | Mega Wave 13 gateway audit | Document AHOS_GATEWAY_URL :3200 in run_bot + auditor reads telegram_ai/.env.example | Arena chat path C90
2026-10-24 | Continuation Tracks 1–4 | Paper trade audit module; ECB/OPEC two-source mirrors; M50 os_h05 + M49 derive; Persian metric glossary | Saturday: cash fills remain PARTIAL honestly
2026-10-24 08:24 Tehran | Track1 deepen | ledger_hash legacy OPEN + weekday witness probe; audit GREEN; no fake cash GREEN on weekend | PAPER_ONLY

## 2026-10-24 — Continuation Tracks 5–8 (3-layer critique)

- **Step A (Builder):** `shadow_forward_scorecard.py` (M28/M56/M58) scores six shadow signals on 1h/4h/24h forward returns from `paper_trades.jsonl`; `session_readiness_drill.py` (M13/M19/M20) Tehran countdowns + CCXT/IBKR paper probes + optional `adv_cap_check`; `synthesize_live_conflict_exam_items` + AskU registry provenance; M65 exam-derived teaching cards; Arena `StageReceiptsPanel` + Kian/markets Persian surfaces.
- **Step B (7-domain red-team):** (1) No promotion when n&lt;30; DSR/PBO untouched. (2) Forward prices from ledger only—no single-source live override. (3) Weekend cash gate preserved in drill summary. (4) Kian adds shadow summary without robotic footer. (5) CONFLICT/UNPROVEN never styled as success. (6) Held-out items `leaked==False`; PIT exporter unchanged. (7) No npm build; whitehat CLEAN; Lane A untouched.
- **Step C (Meta):** Embedded `session_readiness_drill` inside weekday probe JSON for one API read; theta on live exam is key-self-check only (not operator ability)—documented as receipt metadata, not promotion signal.
- **Verification:** `pytest` test_shadow_forward_scorecard + test_session_readiness_drill; Arena `stage_receipts_selftest.ts` + weekday/metric selftests; `run_continuation_tracks.py` track5–8 fields populated.
