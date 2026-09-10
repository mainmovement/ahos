# P5 NEGATION + ENTITY REMEDIATION REPORT

**PR:** #93 (DRAFT — do not merge, do not mark ready)  
**Branch:** `cursor/agi-aci-p5-typed-evidence-reasoning-9500`  
**Data label:** `SYNTHETIC_TEST_DATA`  
**Lane A:** `Lane-A integrity OK (36 files pinned)`  
**Soak:** not touched (`SOAK_DATABASE_TOUCHED=NO`)

This is not formal reasoning, entailment, named-entity resolution, AGI, or ACI.

Honest capability name: **governed typed eligibility + deterministic support-class fail-closed + raw-text clause force + identity-marker boundary + critic-constrained templates**.

`LEXICAL_MATCH != RELEVANCE`  
`RELEVANCE != SUPPORT`  
`SUPPORT != ENTAILMENT`  
`ENTAILMENT != REASONING`  
`REASONING != DECISION`

`HONEST UNKNOWN > FALSE POSITIVE`

---

## 1. Commit Audited

| Field | Value |
| --- | --- |
| Audited commit | `ae3d6778a96c871438073d174d605975dddf282d` |
| Audited message | `Fail-close P5 positives unless evidence support is direct.` |
| Audit class | `🔴 DO_NOT_MERGE` |
| Blocking defect 1 | Sentential negation (`did not reduce`) became `DIRECT_SUPPORT + SUPPORTS → WEAKLY_SUPPORTED` |
| Blocking defect 2 | Short identity markers (`A`/`B`) dropped by `[a-z0-9_]{4,}` tokenizer, allowing Entity A evidence to support Entity B questions |
| This remediation | Subsequent commits on the same PR branch; retrieval.py not redesigned |

Root causes in the audited commit (live path, not merely benchmarks):

1. Retrieval tokenizer is `[a-z0-9_]{4,}`. `not` / `no` are dropped. `never` and `without` are stopwords. `_polarity()` was bag-of-tokens, so “did not reduce failures” still looked like `reduce` + `failure` = `SUPPORTS`.
2. Isolated letters and 2–3 character IDs vanish. Hyphenated `Service-A` tokenizes as `service` only. Distinct subjects collapsed.

---

## 2. Negation Architecture

Production path (unchanged retrieval tokenizer):

`raw statement`
→ `architecture.cognitive.loop.support.classify_support`
→ `SupportAssessment.{support_class, polarity, clause_force, entity_state}`
→ `EvidenceBinding` (same fields)
→ `modes._supporting` / `_contradicting` via `may_support_task()` / `contradicts_task()`
→ `reason()` fail-closed refuse if a positive cites negated/uncertain/mismatched evidence
→ critic / `apply_constraint`
→ verdict
→ orchestrator write-back only if `WEAKLY_SUPPORTED`

Clause force is scanned on **raw text** with regexes, independent of the 4+ tokenizer, so negation words are not deleted before polarity is decided.

Order:

1. Uncertain clause (`unknown whether`, `no evidence`, `unclear whether`, …) → `UNKNOWN_SUPPORT` + `UNCERTAIN`
2. Negated clause (`did not` / `never` / `failed to` / `cannot` / `unable to` / `without` / `\bnot\b`) + same-subject overlap → `DIRECT_SUPPORT` + `NEGATED` (not `SUPPORTS`)
3. Bag polarity (`reduce`+`fail` with agent-before-outcome order, or closed help lexicon) only if clause is affirmed
4. Defensive pack: `DIRECT_SUPPORT + SUPPORTS` is rewritten to `UNKNOWN` if `positive_support_eligible` is false

`retrieval.py` was not modified. P4.3 lookalike discrimination remains the baseline.

---

## 3. Polarity Representation

| Symbol | Meaning on this stack |
| --- | --- |
| `POSITIVE` / `SUPPORTS` | Affirmed closed evaluative cue aligned with the proposition |
| `NEGATED` | Clause-level negation of an otherwise aligned cue |
| `CONTRADICTORY` / `CONTRADICTS` | Affirmed contrary evaluative cue (`increased` / harm lexicon) |
| `UNCERTAIN` | Explicit uncertainty / “no evidence that” |
| `UNKNOWN` | Residual; fail-closed |

`clause_force ∈ {AFFIRMED, NEGATED, UNCERTAIN}` is load-bearing, not decorative.

Invariant (asserted in `positive_support_eligible` and tests):

`NEGATED evidence cannot satisfy positive-support eligibility.`

Eligibility requires all of:

- `support_class == DIRECT_SUPPORT`
- `polarity == SUPPORTS`
- `clause_force` not in `{NEGATED, UNCERTAIN}`
- `entity_state` not in `{MISMATCH, AMBIGUOUS}`

`EvidenceBinding.may_support_task()` delegates to that function. Modes cannot emit `WEAKLY_SUPPORTED` from negated premises. `reason()` additionally refuses a positive that cites negated/uncertain/mismatched bindings. The critic is not the only gate.

---

## 4. Negation Test Matrix

Live required examples (classifier + `reason()`):

| Evidence | Question | Observed class / polarity / verdict |
| --- | --- | --- |
| `Retries after timeout reduced failures.` | `Do retries after timeout reduce failures?` | `DIRECT_SUPPORT` + `SUPPORTS` → `WEAKLY_SUPPORTED` |
| `Retries after timeout did not reduce failures.` | same | `DIRECT_SUPPORT` + `NEGATED` → `CONTESTED` (not positive) |
| `Retries after timeout increased failures.` | same | `DIRECT_SUPPORT` + `CONTRADICTS` → `CONTESTED` |
| `It is unknown whether retries reduce failures.` | same | `UNKNOWN_SUPPORT` + `UNCERTAIN` → `INSUFFICIENT_EVIDENCE` |
| `There is no evidence that retries reduce failures.` | same | `UNKNOWN_SUPPORT` + `UNCERTAIN` → `INSUFFICIENT_EVIDENCE` |

New synthetic negation cases: **20** (software / finance / science / operations), covering did not / does not / do not / not reduced / never / failed to / cannot / unable / without / no evidence / unknown whether / unclear / not known / contractions.

Evaluator polarity probes (8): leak **0/8**.

`without reducing` remains `UNKNOWN_SUPPORT` + `NEGATED` because the gerund `reducing` is an alien token (not inflected to `reduce`). Verdict is `INSUFFICIENT_EVIDENCE`, not positive. Acceptable under `HONEST UNKNOWN > FALSE POSITIVE`.

---

## 5. Entity Architecture

Smallest general identity boundary. **Not NER. Not an ontology.**

Markers extracted even when length < 4 or hyphenated (tokenizer would drop or split them):

- isolated uppercase letters (`A`, `B`, `X`, `Y`)
- alphanumeric IDs (`A1`, `B1`)
- hyphen/underscore compounds (`Service-A`, `service_alpha`)
- title-case names of length ≥ 4 (`Alpha`, `Bravo`) excluding action/problem/in-family/stopword tokens

Alignment:

| Task IDs | Evidence IDs | `entity_state` | Positive support |
| --- | --- | --- | --- |
| empty | anything | `NONE` | allowed if other gates pass (unscoped question) |
| non-empty | empty | `AMBIGUOUS` | **no** |
| overlap | overlap | `MATCH` | other gates apply |
| disjoint | disjoint | `MISMATCH` | **no** (`NON_SUPPORTING_MATCH`) |

`ENTITY_MISMATCH` is not treated as contradiction of the other entity (`contradicts_task()` is false). Verdict is `INSUFFICIENT_EVIDENCE`, not `CONTESTED`.

Identity is **not** inferred from string coincidence of shared 4+ tokens such as `service` or `retries`.

---

## 6. Entity Boundary Test Matrix

New synthetic entity cases: **20**.

| Pair class | Example | Observed |
| --- | --- | --- |
| short IDs | Service A vs Service B | `MISMATCH`, not positive |
| short IDs | X vs Y | `MISMATCH`, not positive |
| alphanumeric | A1 vs B1 | `MISMATCH`, not positive |
| named | Alpha vs Bravo | `MISMATCH`, not positive |
| hyphenated | Service-A vs Service-B | `MISMATCH`, not positive |
| underscored | service_alpha vs service_beta | `MISMATCH`, not positive |

Evaluator entity probes (6): leak **0/6**.

Unscoped question + entity-bearing evidence stays `NONE` (does not require evidence entities). That is a documented limitation, not a claim of resolution.

---

## 7. Combined Adversarial Matrix

New combined cases: **10** (negation+mismatch, contradiction+mismatch, uncertainty+mismatch, stale+negation, unknown+negation, hyphen/underscore mixes).

New adversarial high-overlap non-positives: **30** (negated, contradicted, uncertain, different entity, different object, different direction, different outcome).

Suite minimum: 20 + 20 + 10 = **50**, plus **30** adversarial.

`unsupported_positive_verdict_rate` on the 30 adversarial live `reason()` calls: **0 / 30** (denominator > 0).

Different-direction bag-of-tokens (`Failures reduced retries…`) is blocked by a closed agent-before-reduce-fail raw-text order cue, not by fixture phrases.

---

## 8. Positive Safety

| Metric | Value | Denominator | Status |
| --- | --- | --- | --- |
| official `unsupported_positive_verdict_rate` | 0.0 | 27 | PASS (includes cafeteria×7 + kitchen/generic/context/negative/adversarial **and** negation + entity probes) |
| `direct_support_positive_rate` | 1.0 | 1 | PASS (affirmed exact support still allowed) |
| adversarial suite leak | 0.0 | 30 | PASS |

A false-positive `WEAKLY_SUPPORTED` would be a governance failure. None observed on the labeled no-support + polarity + entity populations.

---

## 9. Evaluator Metrics

Every metric has an explicit denominator. `make_metric` already returns `NOT_MEASURED` (never PASS) when denominator = 0.

| Metric | Kind | Threshold | Observed | Denom |
| --- | --- | --- | --- | --- |
| `negation_positive_leak_rate` | ZERO | 0 | 0.0 | 8 |
| `negation_safety_rate` | MIN | 1.0 | 1.0 | 8 |
| `entity_mismatch_positive_leak_rate` | ZERO | 0 | 0.0 | 6 |
| `entity_boundary_safety_rate` | MIN | 1.0 | 1.0 | 6 |
| `unsupported_positive_verdict_rate` | ZERO | 0 | 0.0 | 27 |

The audited evaluator omitted negation-B from `unsupported_positive_verdict_rate`. That population now includes the eight negation/uncertainty probes and six entity-mismatch probes.

---

## 10. Write-Back Safety

`CognitiveOrchestrator` still gates reusable `LESSON` / `HYPOTHESIS` / `INFERENCE` on `verdict == WEAKLY_SUPPORTED`.

Live `write_back=True` probes (none minted reusable positive lessons/hypotheses/inferences):

- negated evidence
- contradictory evidence
- unknown / no-evidence
- entity mismatch
- ambiguous entity (question has `A1`, evidence has no ID)
- contested / unresolved seeded contradiction episode

Because polarity/entity gates prevent false `WEAKLY_SUPPORTED`, write-back cannot launder negated or mismatched evidence into reusable positives on these probes.

---

## 11. Production / Test Separation

Executable production logic searched under `architecture/cognitive/loop/*.py` (support, binding, modes, reason, orchestrator, retrieval):

| Needle | Executable production | Comments / docs |
| --- | --- | --- |
| cafeteria / kitchen / lunch | **none** | **none** in loop (removed from support.py comments) |
| Service A / Service B | **none** | **none** |
| P5- / BM- case IDs | **none** as branches | version strings such as `p5-v1` exist in orchestrator producer_version; not case-ID rules |
| case_id compares to fixtures | **none** | — |

Those fixture strings appear only in **benchmark/eval and tests** (`architecture/cognitive/benchmark/p5_eval.py`, `tests/test_*.py`). Labels are ground truth for measurement. Production does not branch on them.

No closed lexicon was widened to recover cafeteria/kitchen/HTTP/Service recall. Thresholds were not lowered.

---

## 12. Generalization Limitations

Recorded separately from pass/fail. These are not treated as merge justification.

- Clause force is regex, not compositional semantics. Nested polarity, quotation, and “not only … but” are not modeled.
- `reducing` is not inflected to `reduce`; `without reducing` fail-closes to `UNKNOWN` rather than `DIRECT + NEGATED`.
- Identity markers are not coreference or world-model entity resolution. Lowercase articles are not IDs (`a` is not `A`).
- Unscoped questions (`Do retries…`) do not require evidence IDs; entity-bearing evidence can still support an unscoped question.
- Subject/action/object roles are not parsed. A shallow agent-before-reduce-fail cue is the only argument-order guard for that composition.
- Finance `cross_domain_consistency` remains FAIL: `paper` is alien to `_IN_FAMILY`. Honest. Not patched.
- Closed evaluative lexicons are small. Novel verbs yield `UNKNOWN`, not manufactured support.

---

## 13. Regression

| Suite | Result |
| --- | --- |
| `tests/test_evidence_support.py` + `tests/test_p5_negation_entity.py` run 1 | 106 passed |
| same, run 2 | 106 passed |
| + `tests/test_typed_reasoning.py` | 143 passed |
| `tests/test_cognitive_loop.py` + memory + core | 84 passed (with typed) |
| `tests/test_retrieval_lookalike.py` + panel + evolution + council | 114 passed |
| `tests/test_cognitive_benchmark.py` (P4.1/P4.3/P5 isolated) | 6 passed |
| `tests/test_security_hardening.py` + `test_security_intelligence.py` + phase2 invariants + Lane-A hash | 33 passed |
| `python scripts/freeze_lane_a.py` | Lane-A integrity OK (**36 files pinned**) |
| `python scripts/validate_imports.py` | IMPORTS clean (230 modules); FAIL only `.pytest_cache/` **ENVIRONMENT/ARTIFACT** |

P4.3 retrieval (isolated benchmark; `retrieval.py` not edited):

| metric | value |
| --- | --- |
| precision | 0.9091 |
| recall | 1.0 |
| F1 | 0.9524 |
| Recall@1 | 0.7857 |
| Recall@3 | 0.9481 |
| Recall@5 | 0.9610 |
| Recall@10 | 1.0 |
| MATCH_REASON | 1.0 |
| generic-overlap FP | 0 |
| hard-mismatch reject | 1.0 |
| lookalike recall | 1.0 |
| contradiction pollution | 0 |
| unknown refusal | 1.0 |

Soak was not started, restarted, or modified. Lane A was not modified. Calibration was not modified. Production observation state was not modified.

---

## 14. Reproducibility

| Check | Result |
| --- | --- |
| New suite twice | 106 = 106 |
| `run_twice` isolated cognitive benchmark | `equal=True` |
| Deterministic support/reason (no LLM, no embeddings) | yes |

---

## 15. Blocking Findings

### F1 — REMEDIATED (was CRITICAL)

- **Severity:** CRITICAL at audit; **remediated** on this branch  
- **File/function:** `architecture/cognitive/loop/support.py` `classify_support` / `_clause_force` / `positive_support_eligible`  
- **Observed (ae3d677):** `Retries after timeout did not reduce failures.` → `DIRECT_SUPPORT + SUPPORTS` → `WEAKLY_SUPPORTED`  
- **Expected:** never `DIRECT_SUPPORT + SUPPORTS`  
- **Evidence:** live probe `P5-SUP-negation_did_not` now `DIRECT_SUPPORT + NEGATED` → `CONTESTED`; `negation_positive_leak_rate = 0/8`  
- **Impact:** negated premises can no longer satisfy positive-support eligibility or reusable write-back on the measured population  

### F2 — REMEDIATED (was HIGH)

- **Severity:** HIGH at audit; **remediated** on this branch  
- **File/function:** `architecture/cognitive/loop/support.py` `identity_tokens` / `entity_alignment`; `binding.py` `contradicts_task`  
- **Observed (ae3d677):** `Service A retries reduced failures` supported a Service B question because `A`/`B` were dropped  
- **Expected:** `ENTITY_MISMATCH` → no positive support  
- **Evidence:** `P5-SUP-entity_a_vs_b` `NON_SUPPORTING_MATCH` → `INSUFFICIENT_EVIDENCE`; `entity_mismatch_positive_leak_rate = 0/6`  
- **Impact:** short/hyphenated/title-case identity markers no longer silently transfer support  

No remaining live-path defect of the audited class was reproduced after remediation on the new 50+30 case population.

---

## 16. Non-Blocking Findings

### N1 — Gerund after `without`

- **Severity:** LOW  
- **File/function:** `classify_support` / retrieval `INFLECTIONS`  
- **Observed:** `without reducing failures` → `UNKNOWN_SUPPORT` + `NEGATED` → `INSUFFICIENT_EVIDENCE`  
- **Expected (preferred):** `DIRECT_SUPPORT` + `NEGATED` or explicit contradiction  
- **Evidence:** `P5-SUP-negation_without`  
- **Impact:** extra false negative; not a false positive  

### N2 — Finance adapter invariance

- **Severity:** LOW (pre-existing, honest)  
- **File/function:** `p5_eval` domain suite / `_IN_FAMILY`  
- **Observed:** `cross_domain_consistency` FAIL (`paper` alien)  
- **Expected:** not patched; do not add `paper` for recall  
- **Evidence:** isolated benchmark metric FAIL  
- **Impact:** domain wording gaps remain UNKNOWN  

### N3 — `.pytest_cache` import-gate FAIL

- **Severity:** ENVIRONMENT/ARTIFACT  
- **File/function:** `scripts/validate_imports.py`  
- **Observed:** `FAIL: build artifact present: .pytest_cache/`  
- **Expected:** local pytest creates cache  
- **Evidence:** validate_imports output  
- **Impact:** not a product defect  

---

## 17. Architectural Debt

- `EvidenceBinding` now carries `clause_force`, `entity_state`, `evidence_entities`, `task_entities`. It still does **not** carry a parsed subject/action/object graph. Identity is marker overlap, not role labeling.  
- Gap: if two markers co-occur without knowing who did what to whom, the system fail-closes rather than claiming understanding.  
- Support classification is still closed-lexicon + structural cues. It is not NLI.  
- Critic remains a second line; polarity is now first-line in `classify_support` / `_supporting`.  

---

## 18. P6 Gaps

- Compositional negation and quantification  
- True argument-structure / semantic role labeling  
- General entity resolution and coreference  
- Cross-sentence polarity  
- Any claim of formal entailment, AGI, or ACI  

P6 must not lower thresholds or widen lexicons to buy recall.

---

## 19. Final Verdict

The two audited live-path defects are remediated with a general polarity + identity-marker architecture. Official polarity safety metrics have non-zero denominators and leak rate 0. P4.3 retrieval numbers are unchanged. PR #93 stays draft.

This stack is still **not** entailment, NER, AGI, or ACI.

`MERGE = NO`

`READY_FOR_REVIEW = NO`

`CODE_CHANGES_REQUIRED = NO`
