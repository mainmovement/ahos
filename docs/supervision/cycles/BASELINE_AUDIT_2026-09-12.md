# Baseline Supervision Audit — 2026-09-12

**Trigger:** Supervision architecture v2 activation (First Action §22)  
**Council:** Independent AHOS Oversight Council  
**Architecture:** `docs/supervision/SUPERVISION_ARCHITECTURE.md` v2

---

## Record

| Field | Value |
|-------|-------|
| Timestamp | 2026-09-12T16:21Z |
| Trigger | Architecture upgrade + baseline mandate |
| Agent State | **IDLE** (was RUNNING briefly in Cycle 004) |
| Branch (build) | `cursor/calibration-identity-join-9500` (W4 tip) |
| Council branch | `cursor/ahos-agent-supervision-council-2701` PR #104 |
| Tests (last full) | 2128 passed (Cycle 001; not re-run this baseline) |
| Lane A | PASS (36 files) — not re-run |

---

## WHERE AHOS IS

| Dimension | State | Evidence |
|-----------|-------|----------|
| Classification | **INTEGRATION_READY** | `FINAL_TRUTH_AUDIT.md` |
| Operator | **NOT_VERIFIED** | No Windows operator JSON |
| Launch | **NOT LAUNCH_READY** | Gaps M-GAP-003/008/009 open |
| Mainline | W1 merged (#94); **W2 not merged** (#95 open) | git log |
| W4 stack | 7 slices PRs #97–#103; tip = calibration join | open PRs |
| AGI/ACI | Charter NOT IMPLEMENTED; P2–P5 isolated research | Charter, evolution index |
| Web | Command Center functional; not immersive/Awwwards | One Brain tests |
| Telegram | Code ready; **not live** | M-GAP-009 |
| Build agent | **IDLE** — no commits since ~15:17 UTC | agent fetch |

---

## WHAT AHOS SHOULD BE (Vision summary)

Evidence-first PAPER_ONLY crypto opportunity intelligence → evolving Domain-AGI/ACI cognitive platform with:

- Verified contract addresses (P0)
- FA/EN conversational chat + Telegram Sun Sniper
- Loud canonical-gated alerts
- Command Center ops surface
- Future: Environment Engine, 3D/audio, multi-market adapters
- Future: controlled execution ladder L0–L7

Sources: `OWNER_VISION_REGISTRY.md`, Charter, Master Vision (owner messages)

---

## Vision ↔ Implementation GAP

| Vision item | Designed | Implemented | Validated | Operational |
|-------------|----------|-------------|-----------|-------------|
| One Brain authority | ✅ | ✅ | ✅ tests | ⚠️ partial live |
| Token dossier W1 | ✅ | ✅ main | ✅ | ❌ not UI-wired |
| Evidence graph W2 | ✅ | ✅ branch | ✅ | ❌ not on main |
| Identity fusion W4 | ✅ | ✅ branch stack | ✅ unit | ❌ not merged |
| Chat quality (owner) | ✅ | ⚠️ gateway exists | ❌ E2E | ❌ |
| Telegram Sun Sniper | ✅ | ⚠️ code | ❌ live | ❌ |
| Loud alerts | ✅ | ⚠️ banner code | ❌ | ❌ |
| Environment Engine | ✅ | ❌ | — | — |
| 3D immersive UX | ✅ | ❌ (orphan trees) | — | — |
| Domain-AGI/ACI | ✅ | ⚠️ isolated P2–P5 | ❌ real market | ❌ |
| Multi-market trading | ✅ | ❌ | — | — |
| 168h soak | ✅ protocol | ❌ executed | — | — |

---

## WHAT IS MISSING (Launch-critical)

1. W2 on `main` (PR #95)
2. W1.3 identity hardening (spoof test)
3. Windows operator gate artifacts (G1–G10)
4. 168h soak evidence (M-GAP-003)
5. Telegram live E2E (M-GAP-009, S-01 token)
6. Calibration joined pairs (M-GAP-008)
7. CI on push optional but M-GAP-004 open

---

## WHAT IS WRONG

| Issue | Severity | Evidence |
|-------|----------|----------|
| W4 built before W2 merged | **HIGH** sequencing | PR #97–103 vs #95 |
| 9-stacked PR chain | **MEDIUM** review debt | open PRs |
| Build agent IDLE, no directive response | **MEDIUM** stall risk | cycles 002–004 |
| Telegram token in owner chat | **HIGH** security | S-01 |
| P5 governance MERGE=NO vs code on main | **LOW** doc conflict | evolution index |
| 5 orphan 3D Next trees | **LOW** confusion | tsconfig exclude |

---

## WHAT IS RISKY

- Merging W4 before W2 → split-brain knowledge layer
- Merging PR #103 before owner authorization → **BLOCK per owner §20**
- Starting W4 Slice 8 → **BLOCK per owner §20**
- Soak interruption via runtime changes → Charter §39
- Readiness inflation in agent PR descriptions
- Fixture tests presented as live proof

---

## WHAT IS UNPROVEN

- Provider live probes on Windows laptop
- Telegram conversational E2E
- Calibration measurement (0 pairs)
- Operator Windows gates
- Full suite at HEAD (baseline uses Cycle 001 run)
- W4 consumer migrations in production path

---

## MILESTONE GATE SNAPSHOT (baseline)

| Gate | Status | Blocker |
|------|--------|---------|
| G0 Vision/Truth | **PARTIAL** | Truth model v1.0 created; owner vision registered |
| G1 Architecture | **PASS** with caveats | One Brain intact; dual-stack TS scoring remains |
| G2 Core Engineering | **PASS** (stale) | 2128 tests; re-verify at HEAD |
| G3 Integration | **FAIL** | W2 not main; Telegram not live |
| G4 Operational | **FAIL** | No soak, no operator report |
| G5 Security | **PARTIAL** | Overlay implemented; S-01 token open |
| G6 Launch | **FAIL** | Multiple M-GAP-* open |

---

## CURRENT SAFETY CONSTRAINTS (owner §20 — authoritative until updated)

| Rule | Status |
|------|--------|
| Lane A untouched | ✅ enforced |
| W4 Slice 7 hold current state | ✅ PR #103 open, not merged |
| **Do not merge PR #103** | **BLOCK** |
| **Do not start Slice 8** | **BLOCK** |
| No new identity authority | **BLOCK** |
| No historical mapping | **BLOCK** |
| No readiness upgrade | **BLOCK** |
| No fixture patch to fake green | **BLOCK** |
| No aesthetic-only architecture | **BLOCK** |

---

## META-CRITIQUE (baseline)

| Finding | Valid? | Action |
|---------|--------|--------|
| Block all W4 forever | No | Sequence W2 first, then controlled W4 merge |
| Merge #103 now | No | Owner explicit BLOCK |
| Full repo scan each 30min | No | Delta-only per architecture v2 |
| Skip strategic 4h audit | No | Required for drift detection |

---

## RECOMMENDED BEST PATH (single)

### Problem
AHOS has strong foundation but Launch blockers and sequencing errors prevent trustworthy progress.

### Evidence
Baseline tables above; open PRs #95–#104; gap register; agent IDLE.

### Chosen Path

```
1. BUILD AGENT: PRE-FLIGHT → W1.3 + W2 merge (#95) → POST-FLIGHT
2. HOLD: PR #103, Slice 8, readiness claims (owner §20)
3. REBASE: W4 after W2 on main (human review per slice)
4. P1: chat/telegram/alerts with .env + E2E artifacts
5. OWNER: rotate token, Windows G1–G10, soak start
6. G3 re-audit after P1 evidence
```

### Risks
- Agent remains IDLE → ESCALATE_TO_HUMAN wake message
- W4 merge without review → BLOCK

### Required Evidence
- pytest at HEAD, freeze_lane_a, walkthrough for P1
- No secrets in diff

---

## DIRECTIVE (baseline)

**STATUS:** `FIX_BEFORE_CONTINUE` (build agent)  
**Council STATUS:** `MONITOR` (architecture v2 active)

See `LATEST_DIRECTIVE_FOR_AHOS_AGENT.md`

---

## Next reviews

| Layer | When |
|-------|------|
| L1 Event | On GitHub PR activity |
| L2 Operational | +30 min |
| L3 Strategic | +4 h |
| G3 Integration | After W2 merge |
