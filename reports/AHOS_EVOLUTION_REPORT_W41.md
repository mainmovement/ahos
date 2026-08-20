# AHOS EVOLUTION REPORT — W41 (2026-08-20)

Engineering completeness (W40: 1407 passed) was **not** product completeness.
This wave audited the repository adversarially and implemented the highest-value
*internal* gaps. External blockers were recorded, not simulated.

## REAL STATE

AHOS is a laptop-first crypto **opportunity intelligence** system (not a trading
bot). Deterministic scoring, security veto, paper-only execution, and UNKNOWN
honesty are real. Live market egress, live Telegram, 168h soak, and calibration
on real outcomes are **not** proven here.

W32–W40 claims that were **verified**: calibration harness exists and reports
INSUFFICIENT_DATA; DEXTools adapter exists and is inert without a key; CMC and
pump.fun adapters exist; evidence package cadence exists; `select_highest_value`
existed but was **not** in the daemon package until this wave.

W32–W40 claims that were **falsified as completion**:
- Social Intelligence = RSS only (vision requires a source registry + pipeline)
- Ranking = highest opportunity_score
- AI council operational expert roles = historical-thinker data cards only
- "No IMPLEMENTABLE NOW gaps" (AHOS_GAP_REGISTER.md) — several internal gaps existed
- PR #14 core/infrastructure/utils was a merged parallel subsystem, not canonical

## COMPLETED (this wave, inside the repository)

- Social Intelligence abstraction + honesty tests
- Multi-factor anti-hype ranking wired into the production pipeline
- 20 operational role lenses + disagreement-preserving synthesis
- Historical-lens False-on-missing fix
- Invalidation thresholds no longer treat UNKNOWN as $0
- Evidence-package improvement selection artifact
- PR #14 isolation + neutralization of eval()/SECRET_KEY
- `.gitignore` secret-material coverage
- Architecture truth model (`reports/architecture_truth_model_w41.json`)

## PARTIAL

- Live AI council (contracts + debate machinery; no live keys)
- Narrative RSS still not fetched by the collector cycle (on-demand only)
- Whale classification without identity evidence correctly abstains (capability
  exists, live wallet graphs do not)

## MISSING

- Calibrated probability (forbidden until real outcomes accrue)
- Real-money execution (intentionally blocked)
- Live social collection from X/Reddit/YouTube/Telegram channels

## EXTERNAL BLOCKED

- M-GAP-003 168h soak (user laptop)
- M-GAP-007 live provider SUCCESS (egress)
- M-GAP-008 calibration measurement (data accrual)
- M-GAP-009 live Telegram (credential)
- DEXTools live (DEXTOOLS_API_KEY + egress)
- X/Twitter (COST_BLOCKED)
- Reddit / YouTube (AUTH_REQUIRED)

## GOVERNANCE REQUIRED

- Import-cycle proposals already filed (explanations↔scoring↔intelligence;
  findings↔selection) — human gate, not auto-applied
- WAL switch (M-GAP-005) still post-soak
- Deletion of PR #14 files (currently KEEP_LEGACY / DUPLICATE, not deleted)

## DUPLICATES REMOVED

None deleted. PR #14 isolated and neutralized. Lane-A ranker not replaced.

## SECURITY FINDINGS

- Closed: `eval()` cache in `utils/decorators.py`; hardcoded SECRET_KEY default;
  import-time mkdir in parallel settings; gitignore gap for pem/key/wallet/secrets
- Residual: operator must still keep `.env` out of git (already ignored)

## PERFORMANCE

No performance claim this wave. Ranking is O(n log n) over the already-scored
candidate list (n is the pipeline limit, typically ≤20).

## BENCHMARKS

None run (no optimization claimed).

## TESTS

New: `tests/test_social_intelligence.py`, `tests/test_candidate_ranking.py`,
`tests/test_operational_lenses.py`, `tests/test_pr14_isolation.py`, plus honesty
regressions in expert lenses and evidence-package selection.

Count is not the goal. Quality: UNKNOWN honesty, anti-hype, source-status
semantics, canonical-import isolation.

## NEW CAPABILITIES

Social Intelligence (canonical). Multi-factor ranking (canonical scoring).
Operational expert lenses (canonical knowledge). Selection in the evidence
package.

## LEARNING GAIN

Failed "everything internal is done" claim recorded. Lesson: green tests on
scaffolded social/ranking/council surfaces are not those capabilities.

## AUTONOMY GAIN

Each evidence cadence now answers "what is the highest-value next improvement?"
with SELECTED or INSUFFICIENT_EVIDENCE — never a guess.

## REMAINING GAPS

See AHOS_GAP_REGISTER.md W-GAP-* plus M-GAP-003/007/008/009.

## NEXT HIGHEST-VALUE ACTION

Internal: optionally wire on-demand RSS into the pipeline as **evidence only**
(still no scoring points) once a transport is injected — do not hit the network
from tests. External: laptop `--probe-providers` SUCCESS (M-GAP-007) so
discovery is not permanently empty.

**PROJECT COMPLETE: no.**
