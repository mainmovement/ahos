# W3 + W4 stack merge wave — supervision event

**Timestamp:** 2026-09-13T16:29–16:30Z  
**Trigger:** GitHub subscription — PRs #96–#104 merged / ready_for_review  
**Actor:** `mainmovement` (owner)

## PRs merged (verified via `gh` + `origin/main`)

| PR | Title | Base | On `main`? |
|----|-------|------|------------|
| #96 | W3 human feedback signal contract | `main` | **YES** (`a8ece43`) |
| #97 | W4 Slice 1 identity fusion foundation | `main` | **YES** (`4508397`) |
| #98 | W4 Slice 2 identity resolution contract | stack | **NO** |
| #99 | W4 Slice 3 Gecko new_pools boundary | stack | **NO** |
| #100 | W4 Slice 4 canonical join boundary | stack | **NO** |
| #101 | W4 Slice 5 ScoreLedger canonical join | stack | **NO** |
| #102 | W4 Slice 6 Security identity consumer | stack | **NO** |
| #103 | W4 Slice 7 Calibration identity consumer | stack | **NO** |
| #104 | Supervision council framework | `main` | **YES** (`f869dc1`) |

**Stack tip (slices 2–7):** `cursor/calibration-identity-join-9500` @ `5fdbb8a`  
**`main` HEAD:** `f869dc1` (after #104)

## Critical topology note

Owner merged the **full W4 PR chain** on GitHub (including #103, previously council-**BLOCKED** per §20), but only **Slice 1** landed on `main`. Slices 2–7 exist on the stack tip branch only. **No open PR** remains to promote the tip to `main` (verified 2026-09-13T16:35Z).

File spot-check on `main`:

- `architecture/identity/fusion.py` — present (Slice 1)
- `architecture/identity/resolution_contract.py` — **absent**
- `architecture/security/identity_join.py` — **absent**
- `architecture/learning/calibration_identity_join.py` — **absent**

## Governance impact

| Item | Before | After |
|------|--------|-------|
| W3 on `main` | NO | **YES** (#96) |
| W4 Slice 1 on `main` | NO | **YES** (#97) |
| W4 Slices 2–7 on `main` | NO | **STILL NO** (stack tip only) |
| §20 S20-3 (block #103) | ACTIVE | **OWNER OVERRIDE** — #103 merged to stack; council records, does not contest |
| §20 Slice 8 | BLOCK | **UNCHANGED** — do not start |
| Phase 1 D2 (W2 #95) | COMPLETE | COMPLETE |
| Supervision docs on `main` | NO | **YES** (#104) |
| Soak / evidence gates | D-009 open | **UNCHANGED** |
| Readiness | NO | **NO** — no inflation |

## Owner authority

Council §20 blocks were **advisory**. Owner merge of #103 into the stack is an explicit human gate decision. Council **withdraws** active BLOCK on #103 merge; **retains** BLOCK on Slice 8 and soak interference.

## Council STATUS

**`MONITOR`** — material sequencing gap: W4 consumer migrations (2–7) not on `main`.

## Required next (build agent / owner)

1. Open PR: `cursor/calibration-identity-join-9500` → `main` (slices 2–7 promotion) — **ESCALATE_TO_HUMAN** before merge
2. `pytest` + `freeze_lane_a` at stack tip before any `main` promotion
3. Phase 0 Windows primary export remains binding (D-009)
4. Do **not** start W4 Slice 8

## BEST PATH delta

Phase 3 (selective W4) partially executed by owner on stack branches. **Remaining:** single reviewed promotion PR for slices 2–7 → `main`. Phase 0 (Windows export) and Phase 2 (P1) sequencing unchanged.
