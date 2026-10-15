<!-- Tehran: 2026-10-09 16:30 (UTC+3:30) | Version: v1 | Author: Soltan | Reason: owner request 2026-10-09 16:21 (University trains all teams, sub-agents, per-team memory, self-* loop, one integrated system). -->
# M57/M58/M59 ADDENDUM v1: University, teams, memory, self-* loop, end-to-end coherence
Status: PLAN ONLY (addendum to EXISTING missions; no new parallel mission ids). Input for M34.1 like DEDUP_MERGE_MAP.md.
Rule: everything already specified below in "Covered" is NOT restated; only the gaps are written here.

## 0. Coverage check (owner requirements of 16:21)
| # | Requirement | Already documented | Status | Gap closed here |
|---|---|---|---|---|
| 1 | University (President Farzaneh #35) trains all agents; research dept brings papers/code/techniques | VISION §8.2-8.3 (OA-06, INV-16/17), §9 (Shida -> Farzaneh), §14.10.1 flow M44->M45->M58.5; M57 §2.10 (9 faculties, UN-1..UN-11); M59 (sources, Saturday exam); M16; M52; code knowledge/oss_pipeline.py | COVERED for the 19 agents + M57 sub-teams; WEAK for new teams | A1, A2 |
| 2 | Every agent has many professional sub-agents | M57 §1-§2 (10 teams, 43 base / 68 max, full JDs) | WEAK: no roster for Didehban (M18.N/M80-A), Negahban (M64/M80-B), Kian/M35, Memory, Observability | A3 |
| 3 | All teams professional and kept updated by the University | M59 weekly exam >=90%, remediation, held-out banks | WEAK: OSINT/white-hat not examinees; no faculty mapping | A1 |
| 4 | Self-debug, self-develop, self-update behind gates | VISION §14.10 (M44-M52), INV-33/35/37/38/39/40; M58.5; M70 v2 (no self-editing of safety, rollback); DEDUP rows 30-32; code evolution/engine.py (rollback mandate), cognitive/evolution_gate.py | COVERED; perf regressions not wired as M46 input | A5 (one line) |
| 5 | Memory for AHOS and EVERY team; learn from failures AND successes; University reviews and updates | VISION §14.4 / M30 (bitemporal, PIT, per market, error/success, INV-23); M49 lessons; M58.2 (mistakes only); code cognitive/memory (agent_namespace, FAILURE/LESSON, no SUCCESS type) | WEAK (per-team scope, success lessons); MISSING (weekly University memory review -> curriculum -> re-cert) | A4 |
| 6 | One coherent, wired, end-to-end system | INV-31; VISION §14.9.1; M34.1-M34.5; DEDUP map | WEAK: no whole-chain integration test | A6 |

## A1. University = the single trainer (addendum to M59 + M57 §2.10)
- Every registered agent, sub-agent template AND team is an examinee: the 19 agents, M57 teams, Didehban (OSINT/news desk, M18.N), Negahban (white-hat, M64), Kian (M35), Arena (M28/M56) roles. No team trains itself; no second trainer/curriculum module (INV-31).
- Faculty mapping: Didehban -> new domain tag `osint_news` under the Narrative/Markets faculty (sources: M80-A v2 desks, two-source rule); Negahban -> existing "Security & White-hat" faculty (OWASP, MITRE, NIST, CISA KEV; lab-only, AHOS-only).
- Adding a team = registry entry + faculty + >=20 vetted sources + question bank (M59 §2 rule). No code fork.
- Certification (INV-17) gates ACTIVE for the new teams exactly like the others; certificate != permission.

## A2. Research intake pipeline (clarifies M59.1 + M44/M45/M58.5; one path only)
`M44/UN-1/UN-7 intake -> UN-9 source+licence/ToS check -> dedupe+score -> University queue (Farzaneh) -> UN-6 replication -> M45/cognitive/sandbox.py (isolated, INV-40) -> frozen evals (M58.4 = M70.3) -> UN-5 stats verdict (DSR/PBO) -> evolution_gate + QA/red team/evidence sign-off -> promotion = curriculum unit + skill/playbook version (M52) -> taught & examined (M59)`.
- Reuse architecture/knowledge/oss_pipeline.py stages and evolution/engine.py stages; map, do not duplicate. Reject on: licence unknown, not replicated, eval regression, any safety-file touch.

## A3. Sub-agent rosters for teams missing them (addendum to M57 §2; JD template = M57 §2)
Authority NONE, PAPER_ONLY, templates under the existing lead in config/agent_registry.yaml (one registry), bounded autoscale (M57 §1).
- Didehban (lead: Negar/news, M18.N): DB-1 wire/RSS collector, DB-2 social (Telegram/X public) collector, DB-3 whale/on-chain alert collector (reuses OC-1/OC-2), DB-4 two-source verifier (CONFLICT/UNKNOWN), DB-5 C*R*I prioritiser + digest. Output = evidence only.
- Negahban (lead: Security Architect agent.org.03 + Reza red team, M64): NG-1 secrets/redaction, NG-2 supply chain/SBOM (M48), NG-3 SAST/attack surface, NG-4 LLM-safety/injection corpus, NG-5 STRIDE/threat-model keeper. Defensive, AHOS-only (INV-29).
- Memory (Hooman/Dana, M30): MEM-1 ingestion+PIT guard, MEM-2 nightly consolidation, MEM-3 lesson curator (failures + successes).
- Each JD: mission, duties, inputs, outputs, tools, KPIs, handoffs, failure/escalation (M57 format). Totals row in M57 updated by Claude, not here.

## A4. Per-team memory + weekly University review (addendum to M30 + M49 + M58.2 + M59.5)
- Scope: one memory store (architecture/cognitive/memory, INV-31) with `agent_namespace` = team id (+ agent id). No per-team database copies.
- Append-only, bitemporal, point-in-time (INV-23): recall at t sees only `available_at <= t`; corrections are successor records.
- Lessons from BOTH outcomes: add `SUCCESS` (or LESSON with outcome=WIN) records with the same evidence fields as FAILURE; success = OOS, cost-inclusive, not LUCK (Hooman rule). M58.2 becomes "mistake AND success ledger".
- Weekly review (Friday, before the Saturday exam, Asia/Tehran): Farzaneh + Hooman + UN-8 read each team namespace -> top recurring failures + repeatable successes -> curriculum units + new held-out items (UN-10) -> Saturday exam -> remediation/re-certification (M59.5); playbook/prompt changes only as M58.5 proposals.
- Metric: per team, lessons in/out per week, % lessons converted to exam items, re-cert pass rate, paper PnL/calibration delta (reported honestly, can be 0 or negative).

## A5. Self-debug / self-develop / self-update loop (consolidates M46, M48, M51, M58.5, M70 v2)
detect (health, M58.4 perf or benchmark regression, test failure) -> M46 RCA with evidence_refs -> N candidate patches on a separate local branch/worktree -> tests + integrity receipt -> QA/red team/evidence -> Soltan or human promotion (manual merge) -> monitor -> auto-rollback on eval drop.
Gates: no self-editing of safety rules, gates, University criteria, eval sets, thresholds, Lane A, policy/registry (INV-33/37, M70.6 hash lock FIRST); proposer never verifies (INV-39); no push; rollback plan mandatory (evolution/engine.py).

## A6. M34 coherence: one integrated system (addendum to M34.2/M34.4 + new M34.6 test row)
- M34.2 canonical map adds owners for: trainer (University only), memory (one store), research intake (A2 path), sub-agent registry (one registry).
- M34.6 `tests/test_e2e_chain.py` (offline, seeded fixtures, PAPER_ONLY): data (2 sources) -> evidence record -> council/debate (advisory) -> decision record with memory_refs -> Ramin risk + Execution Gateway -> paper trade + ledger -> outcome (M58.1) -> memory write (team namespace) -> weekly University review -> curriculum item + exam -> updated agent version/certificate -> next decision recalls the lesson. One assert per hop; any missing hop = CI red. Runs in the M34.4 gate.
- Placement: M34 ships M34.6 as a skeleton early (hops not built yet are reported PENDING, never silently skipped) and turns each hop green as M13/M30/M58/M59 land.

## Laws (unchanged, binding on every row)
PAPER_ONLY (INV-01) - two-source rule (1 source = UNKNOWN, disagreement = CONFLICT) - zero cost (free/keyless or owner-approved $0 tiers) - portability (M62, no machine-specific paths) - no .env reads or edits - no push (INV-04) - Lane A frozen (INV-03) - no profit promises; North Star is aspirational only (INV-15) - no self-promotion (INV-07/33).

## Order (fits DEDUP_MERGE_MAP v1 §3, no new queue)
A6 (M34.2 owners + M34.6 skeleton) with step 3 (M34) -> A5 rides M70.6/M70.5/M46 (step 9) -> A4 with M30/M49 (steps 16/19) and M58.2/M59.5 (step 17) -> A1/A2/A3 with M57/M58/M59 (steps 17/19) and M18.N/M64 (steps 14/15).

## خلاصه فارسی
- بیشتر خواسته‌ها در سند چشم‌انداز و M57/M58/M59/M30/M46/M34 از قبل هست. این ضمیمه فقط شکاف‌ها را می‌بندد و مأموریت موازی نمی‌سازد.
- دانشگاه (رئیس فرزانه) تنها مربی همه تیم‌هاست، از جمله دیده‌بان و نگهبان. مسیر واحد پژوهش: ورود، بررسی مجوز، تکرار نتیجه، sandbox، ارزیابی، دروازه، درس و آزمون.
- برای دیده‌بان، نگهبان و حافظه زیرایجنت با شرح شغل تعریف شد.
- هر تیم حافظه خودش را دارد (فضای نام در همان یک حافظه)، فقط-افزودنی و نقطه‌در‌زمان، با درس از شکست و موفقیت. دانشگاه هر جمعه مرور می‌کند و شنبه آزمون و بازگواهی است.
- حلقه خوداشکال‌زدایی و خودبه‌روزرسانی با دروازه، بدون دست زدن به قوانین ایمنی، با تأیید انسان یا سلطان و rollback.
- M34.6: تست یکپارچه کل زنجیره از داده تا عامل به‌روزشده. قوانین: فقط کاغذی، دو منبع، هزینه صفر، قابل انتقال، بدون .env، بدون push، Lane A منجمد، بدون وعده سود.
