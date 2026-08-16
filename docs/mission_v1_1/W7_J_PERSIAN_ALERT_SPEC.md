# PERSIAN ALERT SPECIFICATION (Deliverable J) — 2026-08-11
# Implementation: telegram_ai/alerts.py (C Tested). Alert quality > alert quantity (directive §18).

## 1. Classes (fixed enum — callers cannot invent spam)
🚨 OPPORTUNITY · 🟢 THESIS_STRENGTHENING · 🟡 SITUATION_CHANGING · 🟠 RISK_INCREASING ·
🔴 THESIS_INVALIDATED · 🚨 SECURITY_EVENT · 🚀 ABNORMAL_MOVEMENT

## 2. WHY-law (by construction)
build() raises ValueError unless: ≥1 non-empty reason AND ≥1 evidence reference (observation id,
feature key, probe id, or security verdict id) AND a subject symbol exist. A meaningless alert is a
type error. Test-pinned.

## 3. Rendering contract
Persian template: emoji+title, «چرا:» reasons bullets, «شواهد:» evidence refs, data-state banner
when STALE/UNKNOWN (staleness never hidden), and the mandated footer «تصمیم نهایی با کاربر است.»
on decisional classes (all except ABNORMAL_MOVEMENT — pure facts). Test-pinned.

## 4. Trigger law (research-honest until the gate)
- OPPORTUNITY requires: ranker placement (rank-first lists exist, C Tested) + security not FAIL +
  ≥1 BEFORE-event signal condition from the REGISTERED space only (B1/B2 cells), labeled as
  *descriptive statistics*, never "probability".
- SECURITY_EVENT fires from security_gate verdict changes (7 CRITICAL/3 HIGH veto registry).
- THESIS_* transitions reference monitored-position/watchlist state with explicit feature deltas.
- No thresholds from live data until B2 scan evidence exists (no constant-mining).

## 5. Rate & fatigue control (design)
Per-user daily cap (default 5), per-token cooldown (default 6h), escalation ladder forbids repeats
without NEW evidence ids. Config lands with bot glue (Phase-6) — values are config, triggers are law.
