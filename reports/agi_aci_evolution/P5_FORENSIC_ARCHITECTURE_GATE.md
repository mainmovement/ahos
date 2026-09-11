# P5 FORENSIC ARCHITECTURE GATE

**Kind:** READ-ONLY architectural audit. No production, test, threshold, soak, Lane-A, or calibration changes.  
**PR:** #93 (remains DRAFT)  
**Repository:** `mainmovement/ahos`  
**Data label of probes:** `SYNTHETIC_TEST_DATA`  
**Lane A:** untouched (`Lane-A integrity OK (36 files pinned)` at audit time)  
**Soak:** untouched, not restarted  
**PAPER_ONLY:** unchanged  

This is not formal entailment, NER, AGI, or ACI.

Honest capability name: **governed typed eligibility + closed-lexicon support classification + raw-text clause-force markers + identity-marker overlap + mode eligibility templates + critic constraint on some live paths**.

Distinguish throughout:

| Kind | Meaning here |
| --- | --- |
| Implementation capability | What the code can do on the live `reason()` path |
| Benchmark capability | What the labeled P5/P4.3 populations measured |
| Architectural guarantee | What the control flow *must* do if invariants are centralized and non-bypassable |
| Empirical evidence | What isolated probes / tests happened to show |
| NOT_IMPLEMENTED | Named, absent, or decorative |

**Do not confuse** “the current adversarial corpus produced zero leaks” with “the architecture mathematically guarantees zero leaks.”

**Do not confuse** “seven modes return different labels” with “seven genuine reasoning mechanisms exist.”

---

## 1. Executive Verdict

Per-item polarity/identity gates on `classify_support` → `positive_support_eligible` → `may_support_task()` **are load-bearing on the main DEDUCTIVE path** for the closed marker inventory. A *single* negated, uncertain, mismatched, or non-supporting statement does not become `DIRECT_SUPPORT + SUPPORTS` in probes.

That is **not** an episode-level or write-back guarantee.

**Blocking architectural failure (live, reproducible):** when one OBSERVED_FACT *supports* and another *contradicts* the same question, and no CONTRADICTS *graph edge* is present, DEDUCTIVE emits `WEAKLY_SUPPORTED` and the orchestrator mints reusable `HYPOTHESIS` + `LESSON` + `INFERENCE`. The contrary binding is classified correctly (`CONTRADICTS`, `may_support_task=False`) and then **ignored**. The critic ACCEPTs. Tests did not cover this mixed case without an edge.

That is a **positive-safety bypass at episode and persistence layers**, not a fixture miss.

Additional structural limits: `EvidenceBinding` is a mutable DTO (not a frozen security object); identity markers treat `Did`/`Can` as entities; METACOGNITIVE cites non-supporting lexical items beside a real supporter; modes are eligibility templates; assumptions are non-load-bearing; temporal state is a decay enum, not age reasoning.

`ARCHITECTURE_GATE = FAIL`  
`P5_STATUS = FIX_REQUIRED`

---

## 2. Scope and Safety Boundaries

| Boundary | Status |
| --- | --- |
| Lane A | Not modified; verify-only `freeze_lane_a.py` → 36/36 |
| Active soak | Not touched, not restarted |
| PAPER_ONLY | Unchanged |
| Live execution | None; probes used in-process SYNTHETIC_TEST_DATA only |
| Production data | Not rewritten |
| Code / tests / thresholds | Not modified |
| Merge / ready-for-review | Not performed |
| Reports | This file only |

Method: static call-path inspection first; then isolated `reason()` / `classify_support` / orchestrator probes. Tests passing were **not** treated as architectural proof.

---

## 3. Commit Audited

| Field | Value |
| --- | --- |
| Current commit | `7e88ad2ed782b35db84c1c1ea7261b1b5bfa6613` |
| Message | `Document P5 negation/entity remediation and keep polarity cues non-alien.` |
| Prior remediation | `ae3d6778a96c871438073d174d605975dddf282d` |
| Parent defect class (ae3d677) | sentential negation → `DIRECT+SUPPORTS`; short IDs dropped by `[a-z0-9_]{4,}` tokenizer |
| Retrieval | `architecture/cognitive/loop/retrieval.py` not redesigned in this remediation |

---

## 4. Production Call-Path Trace

```
MemoryRetriever.retrieve
  → assemble_context  (contradiction_present := graph edges only)
    → reason()
      → bind_context / bind_item
        → classify_support(statement, task)     # clause force, identity, support class
        → EvidenceBinding fields copied
      → MODE_FNS[mode](task, bindings)
        → _supporting := addresses_task AND may_support_task()
        → _contradicting := addresses_task AND contradicts_task()
      → critique_result / _inspect
      → apply_constraint
      → post-gates: unbound REFUSE; no may_support_task() REFUSE;
                    cited NEGATED/UNCERTAIN/MISMATCH/AMBIGUOUS REFUSE
      → never emit SUPPORTED (downgrade to WEAKLY)
    → CognitiveOrchestrator.run
      → reusable_writeback := (verdict == WEAKLY_SUPPORTED)
      → HYPOTHESIS / LESSON / SEMANTIC INFERENCE if write_back
      → EPISODIC "episode … {verdict}" always if write_back
        → future retrieve: LESSON is CONSTRAINT not FACTUAL_PREMISE;
           false WEAKLY still persists as reusable lesson/hypothesis text
```

**Where the invariant is created:** `support.classify_support` + `positive_support_eligible`.

**Where it is transformed:** `_combine_polarity`; `_pack` rewrite of illegal `DIRECT+SUPPORTS`; binding field copy.

**Where it is consumed:** `EvidenceBinding.may_support_task()` / `contradicts_task()`; `modes._supporting` / `_contradicting`; `reason._inspect` and post-gates.

**Bypass / overwrite:**

- Mixed SUPPORTS + CONTRADICTS without a graph edge never reaches the critic contradiction branch (`contradiction_present` is edge-based).
- `EvidenceBinding` is unfrozen; fields can be mutated so `may_support_task()` disagrees with the statement.
- `CandidateInference` can be constructed with `WEAKLY_SUPPORTED` by any caller of `reason_*` / `apply_constraint`.
- METACOGNITIVE cites `_relevant` (lexical), not `_supporting`.
- Dual “support” vocabularies: `support_strength` (`DIRECT` from typed OBSERVED_FACT+DATED) vs `support_class` (task support). Modes use the latter for eligibility; the former remains on the object.

Polarity is **not** re-derived at retrieval of written-back LESSON/HYPOTHESIS. Persistence stores conclusion text, not clause_force.

---

## 5. Full Gate Matrix

| Gate | Classification | Architectural guarantee? | Empirical on probes |
| --- | --- | --- | --- |
| 1 Polarity | **PARTIAL** | Closed-marker clause force is load-bearing per item | Listed 1–9 behave as designed; 10 over-negates; unseen adverbs fail-closed via *alien tokens*, not understanding |
| 2 Identity | **PARTIAL** | Marker overlap, not NER | A vs B families mismatch; unscoped Q + A evidence still positive; `Did`/`Can` false AMBIGUOUS |
| 3 Lexical vs support | **PARTIAL** | Per-item non-DIRECT cannot `_supporting` | High-overlap cousins insufficient; mixed polarity episode still WEAKLY |
| 4 Binding | **WEAK** as security boundary | None (mutable DTO) | Production bind copies classifier once |
| 5 Modes | **TYPED INFERENCE HEURISTIC / ELIGIBILITY GATE / TEMPLATE** | Different missing-premise rules | One-fact: DED/COMP/TEMP/ADV/META → WEAKLY; IND → insufficient n&lt;2; ABD → unresolved without hyp |
| 6 Critic | **PARTIAL** | Live REFUSE exists; not sole gate | REFUSE on META cafeteria-only; ACCEPT on mixed contra WEAKLY and on mode-already-CONTESTED |
| 7 Entailment | **LEXICAL + STRUCTURED COMPATIBILITY only** | Not entailment | Cafeteria non-support holds |
| 8 Temporal | **WEAK** | Decay enum roles, not clocks | ACTIVE+20s and ACTIVE+10000s identical WEAKLY; `CURRENT` never assigned |
| 9 Contradiction | **UNSAFE at episode layer** | Per-item CONTRADICTS cannot `_supporting` | Mixed no-edge → WEAKLY twice |
| 10 Assumptions | **NON-LOAD-BEARING** | Record presence | Hardcoded `ASM-000001`; changing text would not change DEDUCTIVE |
| 11 Write-back | **FAIL on mixed contra; PASS on single negation** | `reusable_writeback == WEAKLY` only | Negated: no lesson/hyp; mixed: lesson+hyp+inference minted |
| 12 Bypass | **PARTIAL / duplicated WEAKLY emitters** | `may_support_task` centralized per item | Seven mode templates emit WEAKLY independently |
| 13 Tests | **CURRENT FIXTURE BEHAVIOR + some properties** | — | Mixed no-edge untested; `Do` not `Did` |
| 14 Prod/test split | **PASS** | — | No cafeteria/kitchen/Service A/B in `loop/*.py` executable |
| 15 Reproducibility | **Deterministic, not correctness** | — | Mixed WEAKLY == WEAKLY on two runs |

---

## 6. Polarity Findings

**Created in:** `support._clause_force` (raw regex) + `_bag_polarity` (token sets + agent-before-reduce-fail order) + `_combine_polarity`.

**Carried as:** `SupportAssessment.clause_force` / `.polarity` (frozen) → `EvidenceBinding.clause_force` / `.support_polarity` (mutable).

**Consumed as:** `positive_support_eligible` (must be AFFIRMED + SUPPORTS + DIRECT + identity-ok); `contradicts_task` (DIRECT + NEGATED or CONTRADICTS, not mismatch).

**Not consumed as:** critic questions; write-back payload; retrieval scoring.

### Required examples (live `classify_support` + DEDUCTIVE `reason()`)

| # | Evidence | force | polarity | class | eligible | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | reduced failures | AFFIRMED | SUPPORTS | DIRECT_SUPPORT | True | WEAKLY_SUPPORTED |
| 2 | did not reduce | NEGATED | NEGATED | DIRECT_SUPPORT | False | CONTESTED |
| 3 | never reduced | NEGATED | NEGATED | DIRECT_SUPPORT | False | CONTESTED |
| 4 | failed to reduce | NEGATED | NEGATED | DIRECT_SUPPORT | False | CONTESTED |
| 5 | cannot reduce | NEGATED | NEGATED | DIRECT_SUPPORT | False | CONTESTED |
| 6 | unable to reduce | NEGATED | NEGATED | DIRECT_SUPPORT | False | CONTESTED |
| 7 | no evidence that | UNCERTAIN | UNCERTAIN | UNKNOWN_SUPPORT | False | INSUFFICIENT_EVIDENCE |
| 8 | uncertain whether | UNCERTAIN | UNCERTAIN | UNKNOWN_SUPPORT | False | INSUFFICIENT_EVIDENCE |
| 9 | increased failures | AFFIRMED | CONTRADICTS | DIRECT_SUPPORT | False | CONTESTED |
| 10 | reduced failures **without** reducing errors | NEGATED | NEGATED | UNKNOWN_SUPPORT | False | INSUFFICIENT_EVIDENCE |

#10 is **over-negation**: `\bwithout\b` forces NEGATED on a sentence whose main clause is positive. Fail-closed (not a leak). Shows marker scope is not clausal semantics.

None of 2–10 became `DIRECT_SUPPORT + SUPPORTS` at classification or binding.

### Generalization

Unseen forms (`hardly`, `no longer`, `rarely`, `neither`, `refused to`, `possible that`, `allegedly`) stayed **AFFIRMED** (markers missed) but did **not** leak: extra tokens were **alien**, so class became `UNKNOWN_SUPPORT`. That is **fail-closed accident of alien-noun policy**, not negation detection.

If an unseen mitigator were in-family or a stopword, the same bag `reduce`+`fail` would still be `SUPPORTS`. **Closed marker list, not a polarity calculus.**

`didn't they?` tagged NEGATED because of `didn't` — tag questions are not modeled.

**Loss in pipeline:** classifier → binding copy preserves fields for the episode. Write-back stores English conclusions, not `clause_force`. Future retrieval re-tokenizes the lesson/hypothesis statement; polarity is not a first-class memory field.

**Gate 1 class: PARTIAL** — load-bearing for the inventory; not a semantic state machine for language.

---

## 7. Identity Findings

Markers: isolated uppercase letters, alnum IDs, hyphen/underscore compounds, title-case `[A-Z][a-z]{2,}`. Not NER. Alignment is set overlap.

| Family | Same | Different | Notes |
| --- | --- | --- | --- |
| A / B | MATCH → WEAKLY | MISMATCH → INSUFFICIENT | mismatch ≠ CONTRADICTS (`contradicts_task=False`) |
| A1 / B1 | MATCH → WEAKLY | MISMATCH → INSUFFICIENT | |
| Service-A / Service-B | | MISMATCH | also stores `a`/`b` from the suffix letter |
| service_alpha / service_beta | | MISMATCH | tokenizer already keeps underscore tokens; marker still explicit |
| Alpha / Bravo | | MISMATCH | title-case |
| unscoped Q + A evidence | ENTITY_NONE | — | **WEAKLY_SUPPORTED** (A-specific fact supports a question with no ID) |
| no ID in evidence, A1 in Q | AMBIGUOUS | — | insufficient (preferred fail-closed) |
| A **and** B in evidence, Q about B | MATCH (intersection) | — | **WEAKLY** — not a mismatch |
| Cluster-AA vs Cluster-A | MISMATCH | — | |

**False identity markers:** questions starting with `Did` or `Can` extract title-case `did` / `can` (not in STOPWORDS). Unscoped “Did retries…?” vs evidence without those tokens → **AMBIGUOUS → INSUFFICIENT**, refusing the same proposition that “Do retries…?” accepts. Safety-preserving false negative; identity is a **finite marker inventory with auxiliary-verb pollution**.

Identity is not recomputed at write-back. LESSON text can mention the original question, not `entity_state`.

**Gate 2 class: PARTIAL.**

---

## 8. Support-vs-Lexical Findings

`addresses_task` = 4+ token overlap (lexical relevance).  
`classify_support` = closed lexicons + alien nouns + about-redirect + domain qualifier + clause force + identity.  
`may_support_task` = DIRECT + SUPPORTS + AFFIRMED + identity-ok.  
Modes require `_supporting` for WEAKLY on DED/IND/COMP/TEMP/ADV.

Live high-overlap cousins (not copied from fixtures as patches; audit-only):

| Statement vs “Do retries after timeout reduce failures?” | class | verdict |
| --- | --- | --- |
| cafeteria seating about-redirect | NON_SUPPORTING_MATCH | INSUFFICIENT |
| reduced latency | INDIRECT | INSUFFICIENT |
| Failures reduced retries (direction) | UNKNOWN | INSUFFICIENT |
| reduced documentation of failures | UNKNOWN | INSUFFICIENT |
| reduced queue depth | INDIRECT | INSUFFICIENT |
| lunch-window lookalike vs HTTP availability Q | UNKNOWN | INSUFFICIENT |

**Highest justified claim:** structured compatibility over a closed vocabulary, not propositional support in general, not entailment.

**Critical exception:** lexical/support separation **per item** can still yield episode WEAKLY when a qualifying supporter coexists with a contrary or non-supporting item (Gates 5, 9).

---

## 9. EvidenceBinding Findings

`EvidenceBinding` is `@dataclass` **not frozen**. `SupportAssessment` **is frozen**.

| Question | Answer |
| --- | --- |
| Immutable? | **No.** Probe mutated `support_polarity`/`clause_force`/`support_class` on a negated binding and `may_support_task()` flipped False → True without re-reading the statement. |
| evidence_id authoritative? | Synthesized `EVD-{index:06d}-{memory_id}`. Citations in modes use **memory_id**, not evidence_id. |
| Citations bound? | `cited_unbound_ids` + critic REFUSE if accepted+unbound. |
| typed_class vs may()? | Independent. OBSERVED_FACT may be FACTUAL_PREMISE while `may_support_task` is False (negation). |
| Mutated after bind? | Possible; production `reason()` does not, but nothing prevents it. |
| Manual positive binding? | Public constructor; tests and any importer can build DIRECT+SUPPORTS+AFFIRMED. |
| Unsafe → eligible later? | Yes, via field mutation or a second `classify_support` is not required. |
| relevance field | Hardcoded `"RETRIEVED"`. Real lexical flag is `addresses_task_flag`. |
| Why accepted? | `support_reason`, `alien_tokens`, `clause_force`, `entity_state` are on the object **if** bind_item was used. `as_dict` exports them. Dual `support_strength=DIRECT` on negated facts is misleading. |

**Verdict:** convenience **DTO with a load-bearing method**, not a security capability. The security property lives in `positive_support_eligible` **if** fields stay honest.

---

## 10. Seven-Mode Semanticity Matrix

All seven are **LLM-free templates** over bindings. Shared assumption `ASM-000001`. Shared WEAKLY ceiling. None performs proof, statistics, or search over possible worlds.

| Mode | Unique input | Unique transform | Unique failure | Contradiction | Uncertainty | Critic | Output semantics | Honest class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEDUCTIVE | FACTUAL_PREMISE ∩ `_supporting` | If ≥1 supporter and no contrary-only: WEAKLY | no supporter → INSUFFICIENT | contrary-only → CONTESTED; **mixed supporters+contrary without edge → WEAKLY** | lesson → UNCERTAIN epistemic | usually ACCEPT | “premises hold” template | **ELIGIBILITY GATE + TEMPLATE** |
| INDUCTIVE | ≥2 `_supporting` examples | count + `_opposes()` substring list | n&lt;2 | contrary-only CONTESTED; `_opposes` independent of clause_force | always UNCERTAIN if WEAKLY | ACCEPT typical | “pattern from n examples” | **TYPED HEURISTIC** |
| ABDUCTIVE | supporting obs + EXPLANATION candidates | **lexical overlap score** picks “best” hyp | no obs / no support / tie / no candidates | contrary-only CONTESTED | UNCERTAIN | ACCEPT | hyp may be cafeteria-worded if it overlaps | **ELIGIBILITY + OVERLAP RANK TEMPLATE** |
| COMPARATIVE | supporting facts vs non-facts counts | dimension dict in steps | no supporting side | edge contested → UNRESOLVED | lesson UNCERTAIN | ACCEPT | “typed dimensions” | **ELIGIBILITY + TEMPLATE** |
| TEMPORAL | `_supporting` ∩ DATED/AGING | buckets by `temporal_state` enum | stale-only INSUFFICIENT+STALE | contrary-only CONTESTED | PROBABLE if dated supporter | ACCEPT | dated ≠ current (stated, not computed) | **ENUM GATE + TEMPLATE** |
| ADVERSARIAL | search typed misuses | priority: edge, failure, opinion, hyp, lookalike, stale, contrary | many INSUFFICIENT branches | edge UNRESOLVED | WEAKLY still UNCERTAIN | ACCEPT | “seek falsifiers” copy | **CHECKLIST GATE + TEMPLATE** |
| METACOGNITIVE | inventory FACTUAL_PREMISE | **WEAKLY from `_relevant` (lexical), not `_supporting`** | empty facts INSUFFICIENT | not polarity-aware | UNCERTAIN | **REFUSE if no supporter at all** | inventory text | **INVENTORY TEMPLATE**; critic-dependent for cafeteria-only |

One supporting fact, seven modes (empirical):

`DEDUCTIVE/COMPARATIVE/TEMPORAL/ADVERSARIAL/METACOGNITIVE = WEAKLY`; `INDUCTIVE = INSUFFICIENT` (n&lt;2); `ABDUCTIVE = UNRESOLVED` (no explanation candidate).

Different labels **do not** imply different reasoning operators.

CAUSAL_HYPOTHESIS / COUNTERFACTUAL: **NOT_IMPLEMENTED** (explicit refuse).

---

## 11. Critic Integrity

The critic **is not** the only safety mechanism for single-item negation (mode `_supporting` already excludes it; DEDUCTIVE CONTESTS contrary-only). That matches the requirement that critic must not be the sole gate **for that class**.

The critic **is** the gate that stops METACOGNITIVE cafeteria-only WEAKLY (`REFUSE` + `lexical_match_without_support` + `no_direct_support`). Live REFUSE is reachable.

The critic **does not** first-class inspect `clause_force` or `entity_state`. It uses `may_support_task()`, lexical `addresses_task`, and `ctx.contradiction_present` (**graph flag**).

Mixed polarity without an edge: critic **ACCEPT**, findings empty. Post-gate `polarity_unsafe` only fires if a *cited* binding is NEGATED/UNCERTAIN/MISMATCH/AMBIGUOUS. A CONTRADICTS binding that is **not cited** (DEDUCTIVE cites only supporters) is invisible to that gate.

`or True`: **not found** in `architecture/cognitive/loop`.  
Evaluator comments mention “No or True”; that is documentation in `p5_eval.py`, not a production branch.

Metrics: `p5_critic_detection_rate` / `critic_constraint_rate` are live `reason()` based in p5_eval (prior correction). They **do not** include mixed no-edge contradiction.

When the mode already returned CONTESTED/INSUFFICIENT, `_inspect` returns **ACCEPT** (`already_refused`). Constraint is not applied; the non-positive verdict is kept. That is not a vacuous pass of a positive.

**Gate 6 class: PARTIAL.**

---

## 12. Relevance / Entailment Boundary

| Layer | Present? |
| --- | --- |
| LEXICAL RELEVANCE | Yes (`addresses_task`, retrieval tokenizer) |
| STRUCTURED COMPATIBILITY | Yes (closed eval lexicons, alien nouns, about-redirect, domain qualifier, clause-force regex, identity markers, reduce-fail order regex) |
| PROPOSITIONAL SUPPORT | Only inside that closed structure; not general |
| FORMAL ENTAILMENT | **No. NOT_IMPLEMENTED.** |

**Highest justified claim:** deterministic structured compatibility with fail-closed residual `UNKNOWN_SUPPORT`.

Cafeteria cousin: NON_SUPPORTING_MATCH → INSUFFICIENT (implementation + empirical). Not because the system “understood seating,” because ` about ` redirect + alien nouns.

---

## 13. Temporal Findings

`temporal_state_of`: SUPERSEDED/STALE/ARCHIVED/AGING from **store decay status**; else UNKNOWN_AGE if `observed_at is None`; else **DATED**.

`TEMP_CURRENT` is defined and used in `_support_strength` / TEMPORAL mode buckets, but **never returned** by `temporal_state_of`. Dead “freshness” path.

No clock-delta vs now. Two ACTIVE facts at t−20s and t−10000s: both DATED, both WEAKLY, identical. STALE/SUPERSEDED: cannot be FACTUAL_PREMISE → INSUFFICIENT. UNKNOWN_AGE: INSUFFICIENT.

**Not temporal reasoning.** Enum eligibility.

---

## 14. Contradiction / Uncertainty Findings

Distinct labels exist: SUPPORTS, CONTRADICTS, NEGATED, UNCERTAIN, UNKNOWN, CONTESTED, UNRESOLVED.

**Episode assembly** (`context.py`) sets `contradiction_present` from **memory CONTRADICTS edges**, not from opposite polarities.

Probe (repeated twice, identical):

```
A: "Retries after timeout reduced failures."   → SUPPORTS, may_support_task=True
B: "Retries after timeout increased failures." → CONTRADICTS, contradicts_task=True
no graph edge
DEDUCTIVE verdict = WEAKLY_SUPPORTED, critic=ACCEPT
```

With a CONTRADICTS edge: `UNRESOLVED` / CONTESTED (critic ACCEPT of already non-positive).

Uncertainty does not become support (probes 7–8).

**Gate 9: UNSAFE at episode layer.** Per-item contrary cannot be a premise; the *other* item can still authorize WEAKLY.

---

## 15. Assumption Findings

ASSUMPTIONS = **NON-LOAD-BEARING**.

Every mode attaches the same `ASM-000001` (“Retrieved memories are the only evidence…”). Origin `ASSUMED`. Critic records it as `weakest_assumption`. `_inspect` flags `UNSUPPORTED_ASSUMPTION` only if verdict is `SUPPORTED`, which P5 then downgrades anyway. No branch computes a different verdict from a different assumption object. Write-back does not store assumption ids on LESSON payload.

Changing the assumption string would not change DEDUCTIVE WEAKLY on a DIRECT+SUPPORTS fact.

---

## 16. Write-Back Safety

`CognitiveOrchestrator.reusable_writeback = (verdict == "WEAKLY_SUPPORTED")`.

| Input | verdict | HYPOTHESIS | LESSON | INFERENCE write-back |
| --- | --- | --- | --- | --- |
| single negated | INSUFFICIENT | no | no | no (reusable) |
| single increased | CONTESTED (mode) | no | no | no |
| mixed A supports + B contradicts, **no edge**, write_back=True INVESTIGATE | **WEAKLY_SUPPORTED** | **yes (`HYP-000001`)** | **yes** | **yes** |
| cafeteria-only | INSUFFICIENT | no | no | no |

**Persistence of false/incomplete positive:** mixed-contra LESSON text is the generic “Deductive reading: premises hold…” about the question. Future retrieval of that LESSON cannot be FACTUAL_PREMISE (role CONSTRAINT). It **can** still constrain later episodes (`lesson_applied`) and pollute hypothesis store. That is reusable positive-adjacent knowledge minted while contrary evidence was in context.

EPISODIC `episode {id} {verdict}` is always written when `write_back` and `use_memory`. Typed INFERENCE, not a LESSON. Unlikely to become DEDUCTIVE WEAKLY by itself.

**Gate 11: FAIL** for mixed polarity; **PASS** for single-item negation/uncertainty/mismatch probes.

---

## 17. Bypass / Alternate Path Findings

Positive semantics emitters:

1. `modes.reason_{deductive,inductive,abductive,comparative,temporal,adversarial,metacognitive}` — seven independent WEAKLY templates  
2. `reason()` governance: `SUPPORTED` → `WEAKLY_SUPPORTED` (cannot emit SUPPORTED; can still emit WEAKLY)  
3. `inference.apply_constraint` DOWNGRADE of SUPPORTED → WEAKLY; DOWNGRADE of WEAKLY may **keep WEAKLY** (epistemic UNCERTAIN only)  
4. Public `CandidateInference(verdict=WEAKLY_SUPPORTED)`  
5. Public mutable `EvidenceBinding` making `may_support_task()` true  
6. Orchestrator write-back if verdict string equals `WEAKLY_SUPPORTED`

Per-item eligibility is **centralized** in `positive_support_eligible`. Episode-level “any contrary blocks positive” is **not implemented**. METACOGNITIVE uses a **second** notion of cite-worthiness (lexical). `_opposes()` is a **third** negation detector (substring list, misses `increased` / `did not`).

`_support_strength == DIRECT` on negated OBSERVED_FACT is an alternate “DIRECT” that does not authorize `_supporting` (modes use `may_support_task`). Auditor confusion risk, not the mixed-contra leak.

No TypeScript/council path in this P5 stack. Canonical trading brain is out of this audit except: this loop cannot `authorize_execution`.

---

## 18. Test Generalization Findings

| Pattern | Assessment |
| --- | --- |
| 50+ new cases + 30 adversarial | Empirical coverage of the **marker inventory**, four domains, write-back of *single* unsafe items |
| `Do retries…` not `Did retries…` | Missed title-case auxiliary identity pollution |
| Contradiction tests | Single contrary **or** seeded `mem.contradict` edge — **not** mixed polarities without an edge |
| Evaluator | Calls live `reason()` (good). Ground-truth labels include cafeteria strings (eval-only). Metrics copy classifier taxonomy names |
| `blocks_positive() == not may_support_positive()` | Tautology; cannot fail independently |
| Production scanner in tests | Strips comments; loop has no cafeteria strings |
| Tests reimplementing classifier | Mostly call `classify_support` / `reason` — live path, not a second oracle. Still **cannot prove** unseen syntax or episode-level conflict |

**Tests establish current fixture behavior plus some per-item properties. They do not establish episode-level contradiction closure or identity-marker soundness.**

---

## 19. Production/Test Separation

Executable `architecture/cognitive/loop/*.py`: **no** cafeteria / kitchen / lunch / Service A / Service B / P5- / BM- case-ID branches.

Those strings appear in `p5_eval.py` and tests as **measurement labels**.

Closed lexicons were not widened for fixture recall in this audit’s static read of `support.py`. Threshold files were not edited in this audit.

---

## 20. Reproducibility

| Command / probe | Env | Result |
| --- | --- | --- |
| Isolated mixed-contra `reason()` | `/tmp/ahos-test-venv/bin/python`, in-process, SYNTHETIC_TEST_DATA, no soak DB | `WEAKLY_SUPPORTED` |
| Repeat immediately | same | `WEAKLY_SUPPORTED`; `run()==run()` True |
| `python scripts/freeze_lane_a.py` | repo checkout `7e88ad2` | Lane-A integrity OK (36 files pinned) |

Deterministic reproducibility of the **leak** is evidence that the architecture is stable, not that it is safe.

---

## 21. Findings Ranked

### CRITICAL

**C1 — Mixed polarity without graph edge → WEAKLY + reusable write-back**  
- **File/function:** `modes.reason_deductive` (`if contrary and not premises` only); `reason._inspect` (`contradiction_present`); `orchestrator.run` `reusable_writeback`  
- **Observed:** A SUPPORTS + B CONTRADICTS, no edge → `WEAKLY_SUPPORTED`, critic ACCEPT; write_back mints HYPOTHESIS, LESSON, INFERENCE  
- **Expected:** CONTESTED/UNRESOLVED; no reusable positive lesson/hypothesis  
- **Evidence:** isolated probe repeated twice; orchestrator tmp sqlite  
- **Impact:** contrary evidence is classified then ignored; false-positive WEAKLY becomes memory  

### HIGH

**H1 — EvidenceBinding is mutable; eligibility follows fields not statement**  
- **File/function:** `binding.EvidenceBinding`  
- **Observed:** mutate NEGATED binding → `may_support_task()` True  
- **Expected:** security boundary would freeze or reclassify from statement  
- **Evidence:** in-process mutation probe  
- **Impact:** any future caller can restore positive eligibility without `classify_support`  

**H2 — METACOGNITIVE cites non-supporting lexical items in a WEAKLY episode**  
- **File/function:** `modes.reason_metacognitive` (`_relevant` not `_supporting`)  
- **Observed:** cafeteria + good fact → WEAKLY, premises `('C','G')`, critic ACCEPT  
- **Expected:** supporting_ids only `may_support_task` bindings  
- **Evidence:** mixed META probe  
- **Impact:** NON_SUPPORTING_MATCH participates in a positive episode’s citation set  

**H3 — Title-case auxiliaries become identity tokens**  
- **File/function:** `support.identity_tokens` `_TITLE_ID`  
- **Observed:** “Did retries…?” / “Can retries…?” → AMBIGUOUS vs unscoped evidence; “Do retries…?” → WEAKLY  
- **Expected:** auxiliaries are not entities  
- **Evidence:** identity probe table  
- **Impact:** unstable identity boundary; false AMBIGUOUS (fail-closed, not a leak)  

**H4 — Unscoped question accepts entity-specific evidence (ENTITY_NONE)**  
- **File/function:** `entity_alignment`  
- **Observed:** Service A fact + “Do retries…?” → WEAKLY  
- **Expected (strict identity):** UNKNOWN/INSUFFICIENT if evidence is scoped and question is not — *or* document as intentional  
- **Evidence:** identity probe  
- **Impact:** A-facts transfer to unscoped questions  

### MEDIUM

**M1 — Dual DIRECT vocabularies** (`support_strength=DIRECT` on negated OBSERVED_FACT vs `support_class` NEGATED). Auditor/API confusion.  
**M2 — `_opposes()` independent of clause_force** (INDUCTIVE). Can disagree with `classify_support`.  
**M3 — Abductive “best explanation” is lexical overlap** including cafeteria-worded hypotheses when observations support.  
**M4 — `CURRENT` temporal state never assigned;** age not computed.  
**M5 — Intersection MATCH** for multi-entity evidence vs single-entity question.  
**M6 — Tests/evaluator overfit to `Do` questions and seeded contradiction edges.**  

### LOW

**L1 — `without` over-negates mixed clauses (#10).** False negative.  
**L2 — Assumption records decorative.**  
**L3 — Episode INFERENCE rows always written** (non-LESSON).  
**L4 — Closed polarity/uncertainty regex will miss unseen syntax; alien-token fail-closed is not understanding.**  

---

## 22. What Is Genuinely Guaranteed

On the **stock** `reason()` path, if bindings are produced only by `bind_item` and not mutated:

1. `may_support_task()` is false unless `DIRECT_SUPPORT ∧ SUPPORTS ∧ AFFIRMED ∧ entity not MISMATCH/AMBIGUOUS`.  
2. DEDUCTIVE/INDUCTIVE/COMPARATIVE/TEMPORAL/ADVERSARIAL `_supporting` cannot use a negated/uncertain/mismatched item as a premise.  
3. A *sole* contrary DIRECT+CONTRADICTS/NEGATED fact yields CONTESTED, not WEAKLY.  
4. A *sole* UNKNOWN/NON_SUPPORTING/CONTEXT fact yields INSUFFICIENT (META cafeteria-only via critic REFUSE).  
5. P5 `reason()` will not return `SUPPORTED` (forced WEAKLY cap).  
6. Orchestrator will not mint LESSON/HYPOTHESIS/INFERENCE unless the **string** verdict is `WEAKLY_SUPPORTED`.  
7. No fixture-name branches in loop production files.  
8. CAUSAL_HYPOTHESIS / COUNTERFACTUAL return NOT_IMPLEMENTED.

These are **control-flow guarantees**, not linguistic guarantees.

---

## 23. What Is Only Empirically Demonstrated

- Zero leak on the labeled P5 negation (8) and entity (6) evaluator probes and the 30 adversarial test cases.  
- Listed surface forms did not become `DIRECT+SUPPORTS`.  
- Unseen mitigators in this audit’s short list failed closed via **alien tokens**.  
- P4.3 retrieval numbers (from prior reports; retrieval.py not re-audited as a redesign).  
- Deterministic repeat of the mixed-contra **leak**.

Empirical zero-leak on a corpus **does not** prove the marker lists cover English, nor episode-level conflict closure.

---

## 24. What Remains NOT_IMPLEMENTED

- Formal entailment, NLI, compositional polarity, scope of `without`/`not`  
- NER / coreference / role labeling (subject–object)  
- Episode-level polarity conflict aggregation (unless a CONTRADICTS edge exists)  
- Frozen/capability-secure EvidenceBinding  
- Load-bearing assumptions  
- Temporal interval reasoning / CURRENT freshness  
- Genuine distinct reasoning operators (causal, counterfactual: explicit NOT_IMPLEMENTED)  
- Critic as a polarity/identity interpreter  
- Write-back that stores clause_force/entity_state as governed fields  
- AGI / ACI  

---

## 25. Exact Recommended Next Architectural Step

**Do not add more fixtures.**

Make **episode-level polarity conflict fail-closed in one place** before verdict and write-back:

If any bound FACTUAL_PREMISE `contradicts_task()` and any other `may_support_task()`, the episode verdict must be `CONTESTED` or `UNRESOLVED` (not WEAKLY), independent of graph edges. Then `reusable_writeback` cannot fire.

Second, freeze `EvidenceBinding` (or re-run `classify_support` inside `may_support_task()` from `statement`+task) so field mutation cannot restore eligibility.

Third, METACOGNITIVE (and ABDUCTIVE supporting_ids) must not list non-`may_support_task` items as supporting evidence of a positive verdict.

Identity: blocklist function words (`did`, `can`, …) from `_TITLE_ID`. Treat unscoped-question + scoped-evidence as a named policy, not an accident.

Do not lower thresholds. Do not widen lexicons for recall. Do not merge #93 until C1 is closed.

---

## 26. Final Decision

The negation+entity **per-item** remediation is real and load-bearing for its marker inventory. It is **not** yet an architectural guarantee that unsafe evidence cannot participate in, or sit beside, a reusable positive conclusion.

The general failure space is: **closed markers + alien-token fail-closed + graph-edge-only contradiction + mutable DTO + WEAKLY write-back.**

`MERGE = NO`

`READY_FOR_REVIEW = NO`

`CODE_CHANGES_REQUIRED = YES`

`ARCHITECTURE_GATE = FAIL`

`P5_STATUS = FIX_REQUIRED`
