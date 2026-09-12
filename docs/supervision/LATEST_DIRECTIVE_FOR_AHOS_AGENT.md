# BUILD AGENT DIRECTIVE — Independent Oversight Council

**Updated:** 2026-09-12 Cycle 004  
**Council status:** ACTIVE — Master Understanding Phase complete (v1.0)  
**Build agent:** Ahos cursor configuration — **RUNNING**  
**Truth model:** `docs/supervision/AHOS_PROJECT_TRUTH_MODEL.md`  
**Owner vision:** `docs/supervision/OWNER_VISION_REGISTRY.md`

---

## COUNCIL DECISION: BEST PATH (single route)

```
W1.3 → W2 merge → W4 rebase (≤3 PRs) → P1 (chat/telegram/alerts/contracts) → P2 UX waves → soak (owner)
```

---

## BLOCK (stop if attempting)

| ID | Rule |
|----|------|
| B1 | Merge W4 (#97–#103) before W2 (#95) on `main` |
| B2 | Commit secrets (Telegram token — rotate S-01) |
| B3 | Edit Lane A (`discovery/**`, `paper_trading/**`) |
| B4 | Live trading / L6+ execution |
| B5 | Runtime/scoring/calibration changes during active soak (Charter §39) |
| B6 | Claim AGI/ACI/PRODUCTION_READY/OPERATOR_READY |
| B7 | One mega-PR mixing W4 + UI + Telegram + 3D |
| B8 | Wire orphan 3D trees to Command Center |

---

## FIX BEFORE CONTINUE

| ID | Task | Skill | Evidence required |
|----|------|-------|-------------------|
| F1 | W1.3 identity spoof hardening | `ahos-token-identity` | new adversarial test |
| F2 | Merge W2 (#95) to main | `ahos-domain-backend` | 94 tests pass |
| F3 | DOSSIER.md + DOC_TRUTH_MAP entry | `ahos-governance-context` | doc PR |
| F4 | Rebase W4 stack → ≤3 PRs | `ahos-token-identity` | clean diff |
| F5 | Security scalar conflict fail-closed | `ahos-security-analysis` | test |

---

## DO (after FIX items)

| ID | Task | Skill |
|----|------|-------|
| D1 | Chat FA/EN via gateway (not second brain) | `ahos-web-experience` |
| D2 | Telegram Sun Sniper — `.env` only | `ahos-domain-backend` |
| D3 | Alerts: overlay PASS + `alerts_allowed` + sound | `ahos-web-experience` |
| D4 | Contract address: canonical VERIFIED only | `ahos-token-identity` |
| D5 | E2E artifacts per wave | `ahos-change-verification` |

---

## DO NOT

- TS independent BUY without `canonicalBackend`
- Fixture-only proof as "live verified"
- PR without push
- `test_w12_*` naming (use `test_w1_2_*`)
- Skip `freeze_lane_a.py` + pytest before PR

---

## MONITOR

- Dual-stack TS scoring drift
- P5 governance MERGE=NO vs code on main — **ask human**
- Build agent RUNNING — report progress each PR

---

## MODELS

| Work | Model |
|------|-------|
| Architecture/security/identity | Opus 5 High / GPT-5.6 Sol High |
| Implementation | Sonnet 5 High / Composer 2.5 |
| Mechanical | Grok 4.6 High Fast |

---

## REPORT FORMAT (each PR)

```
Problem / What / Tests run / Artifacts / Phase status / Risks
```

Council reviews against `AHOS_PROJECT_TRUTH_MODEL.md` five-state model.

---

## HUMAN REQUIRED

- Telegram token rotation (S-01)
- Windows G1–G10 operator gate
- Soak start authorization
- CI GitHub App permission (M-GAP-004)
- P5 merge governance decision
