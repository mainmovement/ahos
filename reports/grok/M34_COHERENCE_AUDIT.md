# M34 — Coherence audit (M34.1–M34.3) + merge plan

Written: 2026-10-09, Asia/Tehran (night run, step 5). HEAD before this pass:
`59b2548`. Scope: read-only audit plus the doc drift it surfaced.

**Mandate.** `CLAUDE_AUTOPILOT_QUEUE.md:18` — "Coherence audit M34.1–M34.2: one
core, one ledger, one registry, one bus, one bot, one memory; map duplicates,
merge plan, number mapping." `AHOS_AUTONOMOUS_VISION.md:2246–2250` adds M34.3
(merge plan, deprecate-with-shim), M34.4 (CI lint rejecting a second
ledger/bus/registry/bot), M34.5 (coherence score). The night order's step 5
forbids silently deciding the owner-gated contradictions and requires listing
them instead.

**One mandate-level finding before anything else.** INV-31
(`AHOS_AUTONOMOUS_VISION.md:1219`) names **seven** canonical sources — core,
ledger, agent registry, event bus, **design system**, bot, memory. The queue
row names **six** and drops the design system. M34.2's canonical-source map
below therefore carries seven axes, and the design system is the one with a
live deliverable already (`docs/design/`, `app/` tokens, Persian RTL) but no
named canonical owner or test. That is a spec-level gap in the mandate itself,
not a code defect; it is listed for the owner in §6 as **M-AXIS-7**.

---

## 1. The seven axes (M34.1 + M34.2 canonical-source map)

### 1.1 CORE — one AI core

**Canonical:** `architecture/decision/authority.py` — "the single Lane B
decision brain", wrapping `DecisionAdvisor`; the pipeline
IDENTITY → EVIDENCE → SECURITY → LIQUIDITY → SCORING → RISK → CONFIDENCE →
optional AI downgrade → decision. Supporting: `architecture/decision/advisor.py`,
`read_model.py`, `paper_eligibility.py`.

**Also present, and legitimately separate:**
- `architecture/cognitive/` — the AGI/ACI substrate (`loop/` 17 modules,
  `memory/`, `benchmark/`, `reasoning.py`, `world_model.py`, `hypothesis.py`,
  `counterfactual.py`, `evolution_gate.py`). Its charter
  (`docs/architecture/AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md:20,47`) calls it
  PARTIAL — an isolated P3 loop, not soak-wired — and forbids it to import
  `discovery`, `paper_trading`, `telegram_ai` or `engine`.
- `architecture/pipeline/orchestrator.py` — the opportunity pipeline.
- The TypeScript stack (`scoring.ts`, `council.ts`, `opportunity_canonical.ts`,
  `canonical_read_model.ts`), **deliberately subordinated**:
  `AGENTS.md:20-33` and `docs/CANONICAL_IMPLEMENTATION_MATRIX.md:28` both record
  the dual stack as an intentional read-model boundary; `docs/supervision/
  AHOS_VISION_ALIGNMENT_AUDIT.md:33` keeps it as P0-MUST.

**Two `engine` namespaces.** Root `engine.ts` (a TS cycle writer, one of the
live `@/db` importers) is a *different thing* from the `engine/` Python CLI
package. Not a duplicate — a name collision. Flagged because it makes grep
results ambiguous; renaming either is M53's job, not M34's.

**Verdict: no merge required.** The boundary is documented, test-pinned, and
the two cores do not compete. Vision 14.9.1 (`:2206`) marks the shared-AI-core
status `UNKNOWN` pending this audit — it can now be recorded as
**TWO BOUNDED CORES, DOCUMENTED** (decision brain + cognitive loop), with the TS
stack non-authoritative by law.

### 1.2 LEDGER — the most fragmented axis

**Canonical target:** `architecture/mission/ledger.py` (vision `:2207`, status
PARTIAL). **M42 is the owner-approved merge and is not built** — it exists only
as queue text (`CLAUDE_AUTOPILOT_QUEUE.md:20`, `OWNER_DIRECTIVE_MISSION_PLAN.md:407`):
extend `mission/ledger.py` + `paper_trading/ledger.py` into ONE append-only
hash-chained ledger with nightly reconcile.

**Measured 2026-10-09** (this audit, `mode=ro`; `paper_trading` read-only):

| Store | Tables | UPDATE/DELETE-abort triggers | Guarded? |
|---|---|---|---|
| `paper_trading.sqlite` (Lane A) | 19 | 34 | full |
| `control_plane_ledger.sqlite` | 4 | 6 | full |
| `e01_discovery.sqlite` (Lane A) | 18 | 10 | partial |
| `ahos_local.sqlite` | 8 | 4 | partial |
| `ahos_knowledge.sqlite` | 2 | 0 | **none** |
| `ahos_cognitive_memory.sqlite` | 0 | 0 | **empty store** |

**The drift this table kills:** `config/control_plane.yaml:60` declared
"**3 governed sqlite stores**". That was the W10A-02 census scope
(`docs/architecture/F1_RESOLUTION_PLAN.md:11` and `docs/mission_v1_1/
W10_ARCHITECTURE_READINESS.md:188`, both 2026-08-13, which also recorded that
triggers then guarded only 1/3 of that scope). Six stores exist today, and the
W10A-02 trigger counts themselves are stale — `e01_discovery` and `ahos_local`
have since gained partial coverage (10/18 and 4/8). The claim was never false
about its original scope; it is unqualified in a file that reads as total
coverage, and both its store count and its trigger counts have moved under it.
**Fix applied:** the line now names the census provenance and the measured
reality.

**Declared-but-absent stores — both explained, neither a defect:**
- `data/mission_ledger/` — `ledger.py:356` does `path.parent.mkdir(parents=True,
  exist_ok=True)` at first write. The directory is *lazy*, and no caller has
  appended in this checkout. Live consumers exist: `architecture/ai/
  credential_store.py`, `mission_guard.py`, `provider_status.py`,
  `launcher/components.py`, `scripts/mission_ledger.py`.
- `data/architecture_registry.sqlite` — `architecture/registry.py` is a builder
  with **no production caller**; only `tests/test_architecture_p1.py` exercises
  it, against a tmp store. Nothing ever builds the real file. This is a genuine
  gap: a declared append-only registry store that does not exist because nothing
  runs the builder. Listed for the owner in §6 as **M-LEDGER-3**.

**Verdict: real fragmentation — 3+ append-only ledgers on 6 stores.** Merge is
M42, gated by the owner, not by this audit. M34's contribution is the measured
table above, which M42's plan must reconcile against.

### 1.3 REGISTRY — five namespaces, separated *by law*

| Namespace | Artifact | Count | Role |
|---|---|---|---|
| `AG-*` | `config/agent_registry.yaml` + `architecture/registry.py` | **43** | ops matrix; live source of truth |
| `agent.*` | `ahos_org/registry.py` (`CANONICAL_AGENT_IDS`) | **19** | Slice-1 logical anchors |
| `agent.org.*` | `docs/agents/PLANNED_19_AGENT_MAP.md` | **19** | blueprint, all PLANNED |
| `AGENT-*` | `docs/AGENT_MAPPING.md` | 10 × 15 | runtime actors × expert roles; SUPERSEDED banner, retained |
| `A-H` | `docs/governance/agent_taxonomy_map.json:55-58` | 8 | M0 evaluation roles, "not repo ids" |
| cross-map | `docs/governance/agent_taxonomy_map.json` | — | `RECONCILED_NOT_MERGED` |

**The separation is mandated, not accidental.** `agent_taxonomy_map.json:7-12`
carries SILENT_MERGE_FORBIDDEN, PROVENANCE_REQUIRED and
NAMESPACE_COLLISIONS_ARE_EXPLICIT (P2§63). The map's own law block records that
short ids `01` and `10` each have four meanings and are **explicitly not
aliases**. **Verdict: not a duplicate surface — the code is correct; the doc
census was not.** §4 maps the numbers, §5 lists what was stale.

**Council personas are not agents.** `config/cognitive_registry_100.yaml` holds
100 `THINKER-*` personas, marketed `README.md:15` as "100 roles · 10 teams".
`docs/supervision/AHOS_REALITY_MAP_v1.md:32` already flags this as an overclaim
risk — the AG-11 council agent is PLANNED. No action; the flag stands.

### 1.4 BUS — zero implementations, one real contradiction

**No event bus exists in code.** What exists is a decision *not* to build one:
- `config/control_plane.yaml:47-49` — `event_bus` is `OPTIONAL`,
  `NOT_JUSTIFIED` ("NATS/Kafka — replayable event log only at justified
  scale"), fallback "append-only ledger + cycle files".
- `docs/mission_v1_1/W11_UNIFIED_RUNTIME_ARCHITECTURE.md:22` — "NOT JUSTIFIED —
  scale unproven".
- `docs/architecture/runtime_dependency_graph.md:38` — "OPTIONAL (never affects
  status)".

**Against:** `AHOS_AUTONOMOUS_VISION.md:2163` specifies 11 versioned topics
(`token.discovered` … `alert.out`), `:2103` has M33.17 depend on `chain-stream`
"on the same event bus", `:2234` routes leader commands over it, and INV-31
makes "one bus" a law. `docs/architecture/AGENT_14_...md:36` designs an
"Orchestrator-Mediated Message Bus (SQLite WAL, local)" as one of six runtime
components — design only.

**Verdict: this is a specification contradiction, not a duplicate.** Three ops
docs say the bus is unjustified and never affects status; the vision makes it a
law that later missions consume. It cannot be closed by code — the vision would
have to be amended or the NOT_JUSTIFIED verdict overturned, both owner acts.
Listed as **M-BUS-1** in §6.

### 1.5 BOT — one genuine duplicate

| # | Artifact | Status |
|---|---|---|
| 1 | `telegram_ai/` (`bot.py`, `service.py`, `adapter.py`, `envelope.py`, …) | **canonical**; vision `:2211` IMPLEMENTED+TESTED, sending BLOCKED to AD-0128 |
| 2 | `run_bot.py:126`, `scripts/run_sun_sniper_bot.py:39-44` | two runners into #1 — one implementation |
| 3 | **`engine/bot_skeleton.py`** | **a second implementation**: its own polling loop, a divergent HIGH-risk-command design that "write[s] DB flags consumed by n8n/engine" |
| 4 | `engine/telegram_live_test.py` | test harness, REAL/SIMULATE, TEST-ONLY |
| 5 | `docs/archive/.../ahos_03_telegram_control.json` | quarantined (GM-06), enforced by `tests/test_n8n_governance_rules.py` |
| 6 | `alerts.ts` | TS alert path; requires Python `alerts_allowed` **and** overlay PASS |

**Verdict: `engine/bot_skeleton.py` is the one true M34 duplicate on this axis.**
It has **no live caller** (verified: only `scripts/validate_imports.py`'s allowlist
and `tests/test_m9_import_side_effects.py`, which exists precisely to assert it
refuses to run without credentials). Its stated consumer — n8n — was retired by
M10. `AHOS_ROADMAP_v3.md:71` already plans the consolidation ("legacy shim
only"). **Merge plan §7.5.**

### 1.6 MEMORY — four real stores, canonical target empty

| # | Artifact | Store | State |
|---|---|---|---|
| 1 | `architecture/cognitive/memory/` | `ahos_cognitive_memory.sqlite` | **0 bytes**; "append-only revisions, contradictions are edges not overwrites" |
| 2 | `architecture/knowledge/` | `ahos_knowledge.sqlite` (2 tables, **0 triggers**) + DuckDB | Claim & Evidence Store |
| 3 | `architecture/learning/` (+ `paper_trading/lessons.py`) | `ahos_local.sqlite` (87 MB) | score ledger / calibration / drift / lifecycle |
| 4 | `chat_memory.ts` | in-process only | last N turns, expires on inactivity |

**Canonical target:** vision §14.4 / M30.1 — bitemporal schema in
`architecture/cognitive/memory/`; `:1073` records "PARTIAL (ماژول هست، DB خالی)".

**Verdict: real fragmentation; the merge is M30's, not M34's.** M34's finding is
measurable: the canonical memory store is **empty and unguarded** (0 tables, 0
triggers) while `ahos_local.sqlite` — 87 MB of it — carries the actual learning
history with only 4 triggers on 8 tables. Listed as **M-MEM-1** in §6.

### 1.7 DESIGN SYSTEM — the axis the queue row dropped

**Named canonical:** `:2210` "one token/component set for `app/`,
`CommandCenter.tsx`, Persian RTL", status PARTIAL. Present: `docs/design/`,
`app/` token usage, RTL support. **No canonical-owner declaration, no test, no
lint** — nothing asserts a single token source, which is exactly what M34.4 is
supposed to reject a second of. Listed as **M-AXIS-7** in §6.

---

## 2. The two launcher surfaces (vision `:2213`)

Vision §14.9.1 names "several parallel launchers" as an explicit duplicate
(`start_ahos.bat/.ps1`, `AHOS_WINDOWS_OPS.bat`, `AHOS_PRE_SOAK_NOW.bat` and
others; witness AD-0344). Verified present in the repo root: `start_ahos.bat`,
`AHOS_MAIN_FIRST.bat`, `AHOS_APPLY_TIP.bat`, `AHOS_BOOTSTRAP_PRESOAK.bat`,
`AHOS_FIX_G2_AND_GATE.bat`, `AHOS_PRE_SOAK_NOW.bat`, `AHOS_VALIDATE_G2_NOW.bat`,
`AHOS_PULL_OPS_UNLOCK.bat`, `AHOS_PUSH_EVIDENCE_NOW.bat`, `AHOS_WINDOWS_OPS.bat`,
`RUN_ME_WINDOWS.txt`, `WINDOWS_RUN_THIS_FIRST.txt`, alongside the `launcher/`
package (`ahos.bat`, `ahos.ps1`, `__main__.py`, `orchestrator.py`) and
`launcher/_retired_shortcuts/`.

**Which is canonical is already settled by M11.1–M11.4** (launcher finish,
hidden path, gateway identity, Telegram health) — `launcher/` is the one
operator entry; M11.x are DONE. The `.bat` crowd is therefore **not an open
duplicate but an unexecuted cleanup**, and cleanup is **M53's** scope
(`reports/grok/autopilot/missions/M53-cleanup-dead-trees.md`, which explicitly
names this class of artifact), not a coherence merge. Listed as **M-LAUNCH-1**
in §6 with that disposition so M53 picks it up.

### 2.1 Correction to a vision claim: `slills/` is not a duplicate

Vision `:2215` describes "a misspelled duplicate folder `slills/` with
same-sized files (probable duplication)". **Verified otherwise.** `slills/`
holds 16 files named `SKILL (1).md` … `SKILL (15).md` — uploaded third-party
material, not AHOS skills. The canonical `.cursor/skills/` has **11** curated
AHOS skill directories. The sizes do not correspond, the names do not
correspond, and nothing in the repo references `slills/` except the archive:
`docs/archive/consolidation_2026-09-26/ahos022_divergent/docs/DOC_TRUTH_MAP.md:22`
already records — "**`slills/` is uploaded third-party material, not AHOS
Cursor skills**".

So this is **not** an M34 coherence duplicate. It is unmanaged untrusted
downloaded material sitting in the repo root — an M53 quarantine item, and a
hygiene one at that (nothing may import or execute it). Recorded here so the
vision line does not send a future pass looking for a duplication that is not
there.

---

## 3. Number mapping (consolidated)

Registry truth is **43**. Counts that differ are not automatically wrong — most
are honest counts of *other* namespaces.

| Number | Meaning | Canonical source | Stale? |
|---|---|---|---|
| **43** | AG-* registry (9 EXISTS / 12 PARTIAL / 21 PLANNED / 1 MISSING) | `agent_registry.yaml:1268-1278`; `agent_matrix_v2.md:8`; `agent_taxonomy_map.json:29-35` | **current** |
| 19 | Slice-1 logical agents (`agent.*`) | `ahos_org/registry.py:10`; `AGENT_MAPPING.md:5`; `PLANNED_19_AGENT_MAP.md:1` | no — different namespace |
| 19 | vision §2.2 existing-agent roster | `AHOS_AUTONOMOUS_VISION.md:115` | no — vision roster |
| 10 × 15 | runtime actors × expert roles | `AGENT_MAPPING.md:14` (SUPERSEDED banner) | no — documentary |
| 8 | M0 evaluation roles (A–H) | `agent_taxonomy_map.json:55-56` | no — "not repo ids" |
| 100 | council personas (THINKER-*) | `cognitive_registry_100.yaml:1` | no — overclaim already flagged |
| 6 | six-component minimum org runtime | `AGENT_14_...md:30-40` | no — design, unbuilt |
| 6 | six retired n8n cadences | `DECKER_N8N_MIGRATION.md:120` | no — current (M10) |
| 16 | mandated matrix fields | `docs/canonical/KNOWLEDGE_MAP.md:85` | no |
| 36 | Lane-A frozen paths | `AHOS_REALITY_MAP_v1.md:55` | no |
| 25 | pre-M12 AG-* census | — | **YES — superseded by 43** |
| 37 | highest vision # registered | `M12_REGISTERED_AGENTS.md:266` | superseded by the 43 delivered |
| 39 | vision's full certified roster (19 + 20) | `AHOS_AUTONOMOUS_VISION.md:1059`, table `:163-182` | **partly stale — see M-TAX-2** |
| 7 | INV-31 canonical sources | `AHOS_AUTONOMOUS_VISION.md:1219` | live law (queue row says 6) |
| 6 | M34's axes | `CLAUDE_AUTOPILOT_QUEUE.md:18` | **under-counts — drops design system** |

---

## 4. Stale-doc census — corrected this pass

M12 corrected five docs and missed nine. All nine fixed here; `git grep` now
finds no live doc treating 25 as the present census.

| File | Was | Now |
|---|---|---|
| `config/agent_registry.yaml:1` | "(25-agent matrix; …)" — the source of truth contradicting its own `totals` | 43 |
| `docs/supervision/AHOS_REALITY_MAP_v1.md:50` | "Census: 25 registered IDs, not 19" — in the file whose job is stopping census overclaims | 43, both folk numbers named |
| `docs/architecture/AGENT_14_...md:85` | "25 product agents (AG-01…AG-25)", `orchestrated=0/25`, `[VERIFIED]` | 43, with the 25+18 provenance kept |
| `docs/architecture/AGENT_18_...md:1804` | roster `AG-01..AG-25` | `AG-01..AG-43` |
| `docs/governance/M3_...md:171` | reads registry `(AG-01…AG-25)` | `AG-01…AG-43` |
| `docs/governance/M3_...md:192` | `(AG-01..AG-25); orchestrated=0` | `AG-01..AG-43` |
| `docs/architecture/cognitive_agent_fabric.md:11,14` | `0/25` + a 9/12/3/1 tally that no longer summed with the "43 total" on the next line | `0/43`; the W12 tally now dated, the current one beside it |
| `docs/governance/agent_taxonomy_map.json:145` | `orchestrated=0/25` | `orchestrated=0/43` |
| `AHOS_GAP_REGISTER.md:235` | quoted the map's old `0/25` with a citation | quote updated to match its source |

**Left alone deliberately:** dated/historical statements (`reports/phase22_*`
carry a `STALE — 2026-08-15` header; `AHOS_PHASE17_OPERATOR_READY_REPORT.md` is
superseded), and every file under `docs/archive/` — the archive is history and
editing it would falsify the record. Slice-1 "19" statements are accurate for
their namespace.

**Pinned so it cannot recur:** new `tests/test_m34_coherence.py` — the registry
header must state its own `totals.agents`, the taxonomy map's ops-matrix count
and status counts must equal the registry's, and every `orchestrated=0/N` in a
live doc must name the registry's denominator (the one expression that can only
refer to the AG-* tally). 204 passed; the negative path was verified to fire.
This is the M34.4 lint's down payment — full ledger/bus/registry/bot
second-instance rejection comes with the merges, since there is nothing to
detect a second of until a merge creates the risk.

---

## 5. Owner-gated contradictions — LISTED, NOT DECIDED

Per the night order these are recorded for the owner. None was resolved here;
none was silently folded into a merge plan.

### The four the night order named

- **M-DB-1 — database choice.** `INSTALLATION.md:62-63` and the archive README
  present embedded PGlite as the documented default; three live operator docs
  (`WINDOWS_OPERATOR_HANDOFF.md:32,103`, `OPERATOR_VALIDATION_PROTOCOL.md:25`)
  make Postgres a **hard G2-PASS requirement**, and the live container holds
  all 778 rows. M10's flip is PREPARED, NOT EXECUTED and stays BLOCKED_OWNER —
  the one owner act is `DATABASE_URL=pglite:G:/robat/ahos_runtime/pglite/ahos`.
  This audit never opened `.env`.
- **M-TRADE-1 — live trading vs PAPER_ONLY.** Uniform PAPER_ONLY across
  `AGENTS.md`, `README.md`, `docs/canonical/*`, `hygiene.py` and the vision's
  own INV-01; **no doc claims live trading is active**. The tension is that the
  vision is a *live-trading fund charter* (§۴–§۷ execution, treasury, transfers)
  while every present-tense artifact says live is closed until the owner signs
  G-L2. `CANONICAL_IMPLEMENTATION_MATRIX.md:50` records it as
  DEFERRED_BY_DESIGN. Not a doc defect — a charter-vs-state gap the owner holds.
- **M-TAX-1 — agent taxonomy count.** Five namespaces, separated by law
  (P2§63). The registry truth is 43. **No merge is proposed**; the live defect
  was the census drift, which §4 fixed.
- **M-TAX-2 — the vision's internal 39-vs-18 defect.** `AHOS_AUTONOMOUS_VISION.md:6`
  says "۱۸ عامل جدید (۲۰ تا ۳۷)" — 18 new agents — while its own §2.3 table
  (`:163-182`) lists 20 rows through #39 کیان. M12 registered the header's 18
  (#20–#37 → AG-26..AG-43). **#38 سروش and #39 کیان are therefore
  unregistered.** This is the owner's approved charter document: it was **not
  edited**, and the mismatch is recorded rather than reconciled by fiat.
  `:1059` claims "۳۹ عامل گواهی‌دار" — 39 certified — which is only true of the
  table, not of what any registry holds.
- **M-WIN-1 — desktop window vs browser tab.** `owner_directive_part2.txt:1522`
  says the website is the primary intelligence surface; `owner_directive_part1.txt:4282`
  asks for a desktop icon double-click; the shipped behaviour is a browser tab
  (`launcher/processkit.py:541`); the owner's recorded wish (D-D10) is a desktop
  app window; `OWNER_DECISIONS_Q1-Q10.md` decided Chrome/Edge `--app` mode with a
  dedicated profile (Tauri as the documented upgrade path, Electron rejected on
  8 GB RAM); the spec's `launcher/appwindow.py` + `config/app_window.json` are
  **not built**. Explicitly open as C-205. Step 8 (M-D1..M-D4) is where this
  lands tonight, if at all.

### Carried forward from M12 for this audit to hold

- **OWN-AV-06** — vision `:2208` says vision agents #20–#39 register in
  `ahos_org/registry.py`; M12 registered #20–#37 in `config/agent_registry.yaml`
  as AG-26..AG-43, per the charter template's own prohibition on a second
  registry. **Unresolved. M34 is the named carrier.** The registration stands
  (it is committed, tested, and the charter template forbids the alternative);
  the *path* conflict is the owner's to settle.
- **OWN-AV-56** — the AG-* ↔ agent.org.* mapping. Still UNRESOLVED; no
  cross-taxonomy edge was created in either direction, by decision, because a
  silent edge would decide a human gate.
- **OWN-AV-04** — the veto matrix is still not encoded. مریم's uncancellable
  veto remains recorded in neither authority list.
- **OWN-AV-62** — ACTIVE requires a university certificate; registration
  performed no lifecycle transition.
- **§2.7 open seats** — GH-2, the second Guardian seat, and three AGI/ACI team
  seats remain unregistered, by decision: registering one member of a mandated
  team without its seats presents a complete team that does not exist.

### New findings this audit adds

- **M-AXIS-7** — INV-31 names seven canonical sources, the queue row six. The
  design system has no declared canonical owner, test, or lint. Decide whether
  M34's mandate covers it; if yes, `docs/design/` needs an ownership line like
  the other six axes have.
- **M-BUS-1** — the event-bus specification contradiction (§1.4). Either the
  vision's INV-31 bus law and the missions that consume it move, or the three
  NOT_JUSTIFIED verdicts move. Both are owner acts.
- **M-LEDGER-3** — `architecture/registry.py` is a registry builder with no
  production caller, so `data/architecture_registry.sqlite` is declared and
  never built. Either wire it (M42's scope) or delete the builder and its dead
  DEFAULT_STORE.
- **M-MEM-1** — the canonical memory store is empty and unguarded (0 tables,
  0 triggers) while 87 MB of real learning history sits in `ahos_local.sqlite`
  under 4 triggers. M30 owns the consolidation; the asymmetry is recorded here.
- **M-LAUNCH-1** — the root `.bat` crowd is canonical-settled (`launcher/` wins,
  M11.x DONE) but not cleaned up. Disposition recorded as **M53**, not a merge.
- **M-CRYPTO-DRIFT** — CRYPTO-02's "UPDATE/DELETE-abort triggers on all stores"
  was already measured CONTRADICTED at W10A-02 (true for 1/3 stores) and is
  still true for 2/6 today. §1.2's table is the current measurement.

---

## 6. Merge plan (M34.3) — deprecate-with-shim, ordered, none executed here

The plan only covers merges that are **safe under PAPER_ONLY and the locked
list**. Nothing below was executed; each row states its prerequisite.

| # | Merge | From → canonical | Mechanism | Prerequisite |
|---|---|---|---|---|
| 1 | **Legacy bot** | `engine/bot_skeleton.py` → `telegram_ai/` | replace with a deprecated shim that re-exports `telegram_ai.service` and logs a one-time deprecation; delete its `HIGH_CMDS` DB-flag surface (its consumer n8n is retired). `AHOS_ROADMAP_v3.md:71` already commits to "legacy shim only" | owner sign-off; keep `tests/test_m9_import_side_effects.py` asserting refusal-to-run until the shim lands, then repoint it |
| 2 | **Ledgers** | `paper_trading/ledger.py` + `control_plane.py`'s run-ledger → `architecture/mission/ledger.py` | **M42 owns this.** M34 supplies §1.2's measured table as its input | owner-gated; M42 stays PENDING |
| 3 | **Memory** | `ahos_local` learning tables + `ahos_knowledge` → `architecture/cognitive/memory/` | **M30 owns this** | M30; M-MEM-1 recorded |
| 4 | **Registry builder** | delete or wire `architecture/registry.py` | delete is safe (no production caller) | owner decision on M-LEDGER-3 |
| 5 | **Launcher `.bat` crowd** | root `AHOS_*.bat` etc. → archive under M53's quarantine convention | `git mv`, README, re-anchor `test_deployment_config.py`-class references | **M53**, not M34 |
| 6 | **`slills/`** | quarantine as unmanaged untrusted downloads | M53 quarantine; never import or execute | M53 |

**Explicitly not in any merge:** the five agent namespaces (separation is law,
P2§63); the two cores (documented boundary); the TS stack (subordinated by
`AGENTS.md`); the quarantined n8n bot (GM-06, name-enforced, never
re-implemented); the `agent_registry.yaml` ↔ `ahos_org/registry.py` path
conflict (OWN-AV-06).

---

## 7. What M34 deliberately did not do

- No code merge was executed. M34.3 is a *plan*; execution is gated per row.
- `.env` was never opened; no database flip; no Lane A edit (all `paper_trading`
  and `e01_discovery` reads were `mode=ro`).
- `AHOS_AUTONOMOUS_VISION.md` was not edited — it is the owner's approved
  charter and counts as evidence. Its 39-vs-18 defect is recorded, not repaired.
- No doc under `docs/archive/` was touched.
- M34.4 (the full CI lint) is a down payment only; M34.5 (coherence score) is
  not attempted — scoring coherence before the merges land would measure the
  fragmentation, not the fix.
- The two declared-but-absent stores were diagnosed, not created: `mission_ledger/`
  is lazy-by-design and `architecture_registry.sqlite` needs an owner decision.

## 8. Verification

- `tests/test_m34_coherence.py` — **204 passed**; negative paths verified to fire.
- `git grep` for live 25-census statements → none.
- Trigger/table census measured live on all six stores (`mode=ro`).
- Every "canonical" claim above was re-checked at the file:line level in this
  session rather than quoted from a prior report; the three prior claims that
  did not survive re-checking (`slills/` duplication, `mission_ledger/` absence
  as a defect, the model name as a run-killer) are corrected in §2.1, §1.2 and
  `M10_1_MODEL_BLOCKER.md` respectively.

**AUTOPILOT_RESULT: DONE**
