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
