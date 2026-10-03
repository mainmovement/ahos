# ALL GOVERNING DOCUMENTS — TRACEABILITY MATRIX — ماتریس ردیابی همه اسناد حاکم

Companion to [`OWNER_DIRECTIVE_TRACEABILITY.md`](OWNER_DIRECTIVE_TRACEABILITY.md) (rows `OD-###`). This file adds rows `AD-####` (every other governing doc), `CH-##` (owner chat instructions 2026-10-03), `NS-##` (North Star capability items), `OWN-AV-##` (owner vision doc AHOS_AUTONOMOUS_VISION.md). It also holds the document inventory, the supersession register, the DECIDED contradictions and the North Star alignment. Generated 2026-10-03 (Asia/Tehran) against repo HEAD `f07877c (laptop HEAD, generated on the laptop)`. Plan: [`OWNER_DIRECTIVE_MISSION_PLAN.md`](OWNER_DIRECTIVE_MISSION_PLAN.md). Guide: [`CLAUDE_CONTINUATION_GUIDE.md`](CLAUDE_CONTINUATION_GUIDE.md).

## Rules applied — قواعد

1. **Trust order:** human (owner) instruction > repo reality > governance/safety > evidence > MASTER CONTEXT v2.0 > AGI/ACI Charter v1.0 > roadmap > experimental.
2. **Supersession:** for each requirement, the NEWEST owner statement wins (doc date or commit date). Older versions are marked **SUPERSEDED** with a pointer to the newer source and are never active. Deleted items are marked **REMOVED**. Contradictions that newer docs resolve are not escalated.
3. **Locked regardless of date** (never superseded; HUMAN-GATE): PAPER_ONLY / no real money; no secrets in git, logs or prompts; no push (push URL `NO_PUSH_owner_rule_local_only`); constitution, governance and authority changes; Lane A / CDA changes.
4. **Remaining real contradictions** are resolved by a recorded technical decision (**DECIDED**), not left as a question.
5. **Dedupe:** a requirement already in the matrix gets a source reference (status MERGED → existing row id), not a new row.
6. **Honesty:** VISION ≠ IMPLEMENTED. IMPLEMENTED+TESTED means code and tests exist in the repo; it doesn't claim the feature is operating. AGI/ACI/SI is a north star, never a claim.
7. **No duplicates:** before building any row, search the repo and extend the module named in Evidence (hard rule in the plan and the guide).
8. **Every mission ticks its rows** (OD/AD/CH/NS) at close, with commit and test evidence.

## Unified summary — خلاصه یکپارچه

Rows across both files: **1888** active-or-historical requirement rows (OD 594 + AD 1211 + CH 9 + NS 11 + OWN-AV 63). Another 8 extracted statements were merged into existing rows.

| Status | Count |
|---|---|
| IMPLEMENTED+TESTED | 227 |
| EXISTS-PARTIAL (reuse/extend) | 1384 |
| PLANNED | 16 |
| MISSING→added to plan | 129 |
| HUMAN-GATE (locked) | 124 |
| UNKNOWN | 5 |
| SUPERSEDED | 3 |
| REMOVED | 0 |

Method note: AD rows are normative statements (MUST/NEVER/SHALL/REQUIRED/FORBIDDEN/باید/نباید/ممنوع…) extracted line by line from every governing doc, deduplicated, then mapped to the matrix's evidence keys. A row inherits the key's repo evidence unless a supersession or locked rule applies. Column *map* says whether the key came from the statement text or from its document's subject. Owning missions must re-verify the inherited statuses when they tick rows.

## 1. Document inventory — فهرست اسناد

673 doc files (md/txt/pdf/docx) in the repo at HEAD, excluding node_modules/.venv/.next/build. Third-party/prototype website trees are listed but not split.

| Type | Count | Split into requirements? |
|---|---|---|
| REPORT/EVIDENCE | 213 | no (evidence/historical; cited as evidence) |
| ARCHIVE (historical) | 170 | no (evidence/historical; cited as evidence) |
| SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 93 | yes |
| PLAN/ROADMAP/MISSION PLAN | 54 | yes |
| OTHER DOC | 43 | no (evidence/historical; cited as evidence) |
| AGENT/SKILL INSTRUCTIONS | 31 | yes |
| OPERATOR/README | 19 | no (evidence/historical; cited as evidence) |
| DEBUG/FAILURE/GAP | 16 | yes |
| BASE/MASTER (charter/constitution/governance) | 11 | yes |
| GOVERNANCE/DIRECTIVE | 10 | yes |
| UPDATE/CHANGE | 4 | yes |
| OWNER INSTRUCTIONS/HANDOFF (reports/grok) | 3 | yes |
| 3RD-PARTY/PROTOTYPE WEB TREE DOC | 3 | no (evidence/historical; cited as evidence) |
| BASE/MASTER (owner directive: Master Directive, MASTER CONTEXT v2.0, Charter, Completion Mandate) | 2 | yes |
| TRACEABILITY/VISION (this matrix set; not re-split) | 1 | no (evidence/historical; cited as evidence) |

Docs deleted from the tree (present in git history, absent at HEAD): **41**. Their content is **REMOVED** as requirements. The 2026-09-26 consolidation moved most of them to `docs/archive/` (see `docs/archive/consolidation_2026-09-26/MANIFEST.md`), and archived docs are historical (superseded), not active.

<details><summary>Full inventory (path · type · last commit date · bytes · AD rows)</summary>

| Path | Type | Last commit | Bytes | AD rows |
|---|---|---|---|---|
| `درخت کاملتر immersive-3d-audiovisual-website/README.md` | 3RD-PARTY/PROTOTYPE WEB TREE DOC | untracked/— | 4417 | 0 |
| `سایت درختadvanced-3d-audiovisual-platform/README.md` | 3RD-PARTY/PROTOTYPE WEB TREE DOC | untracked/— | 525 | 0 |
| `سایت درختadvanced-3d-audiovisual-platform/docs/VISION.md` | 3RD-PARTY/PROTOTYPE WEB TREE DOC | untracked/— | 770 | 0 |
| `.cursor/agents/python-core.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-03 | 921 | 0 |
| `.cursor/agents/security-review.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-03 | 794 | 0 |
| `.cursor/agents/verification.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-03 | 952 | 0 |
| `.cursor/agents/web.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-03 | 835 | 1 |
| `.cursor/skills/ahos-ai-council/SKILL.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-03 | 1148 | 1 |
| `.cursor/skills/ahos-change-verification/SKILL.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-03 | 1226 | 2 |
| `.cursor/skills/ahos-domain-backend/SKILL.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 1329 | 0 |
| `.cursor/skills/ahos-governance-context/SKILL.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 1462 | 4 |
| `.cursor/skills/ahos-market-intelligence/SKILL.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-03 | 1050 | 0 |
| `.cursor/skills/ahos-opportunity-hunter/SKILL.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-03 | 811 | 1 |
| `.cursor/skills/ahos-product-intelligence/SKILL.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-03 | 804 | 0 |
| `.cursor/skills/ahos-research-intelligence/SKILL.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-03 | 858 | 1 |
| `.cursor/skills/ahos-security-analysis/SKILL.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-03 | 1434 | 1 |
| `.cursor/skills/ahos-token-identity/SKILL.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-03 | 1411 | 4 |
| `.cursor/skills/ahos-web-experience/SKILL.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-03 | 1021 | 1 |
| `slills/SKILL (1).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 5383 | 0 |
| `slills/SKILL (10).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 5879 | 2 |
| `slills/SKILL (11).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 4922 | 0 |
| `slills/SKILL (12).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 5459 | 0 |
| `slills/SKILL (13).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 5459 | 0 |
| `slills/SKILL (14).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 20584 | 2 |
| `slills/SKILL (15).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 18529 | 1 |
| `slills/SKILL (2).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 4591 | 0 |
| `slills/SKILL (3).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 4943 | 0 |
| `slills/SKILL (4).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 4384 | 2 |
| `slills/SKILL (5).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 2738 | 1 |
| `slills/SKILL (6).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 10982 | 2 |
| `slills/SKILL (7).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 3536 | 1 |
| `slills/SKILL (8).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 4802 | 0 |
| `slills/SKILL (9).md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 4922 | 0 |
| `slills/SKILL.md` | AGENT/SKILL INSTRUCTIONS | 2026-09-08 | 18529 | 0 |
| `docs/archive/FINAL_DELIVERY_wave1.md` | ARCHIVE (historical) | 2026-08-16 | 3009 | 0 |
| `docs/archive/ISSUES_REGISTER_wave1_longform.md` | ARCHIVE (historical) | 2026-08-16 | 4417 | 0 |
| `docs/archive/consolidation_2026-09-26/MANIFEST.md` | ARCHIVE (historical) | 2026-09-26 | 10374 | 0 |
| `docs/archive/consolidation_2026-09-26/ahos022_divergent/AHOS_GAP_REGISTER.md` | ARCHIVE (historical) | 2026-09-26 | 21101 | 0 |
| `docs/archive/consolidation_2026-09-26/ahos022_divergent/docs/DOC_TRUTH_MAP.md` | ARCHIVE (historical) | 2026-09-26 | 4891 | 0 |
| `docs/archive/consolidation_2026-09-26/ahos022_divergent/docs/PRE_SOAK_PROTOCOL.md` | ARCHIVE (historical) | 2026-09-26 | 2998 | 0 |
| `docs/archive/consolidation_2026-09-26/ahos022_divergent/docs/engineering/PHASE0_MASTER_AUDIT_AND_FOUNDATION.md` | ARCHIVE (historical) | 2026-09-26 | 11323 | 0 |
| `docs/archive/consolidation_2026-09-26/ahos022_divergent/docs/engineering/PHASE2_SECURITY_GATE.md` | ARCHIVE (historical) | 2026-09-26 | 14788 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_architecture_freeze/AHOS Architecture Freeze v1.1.md` | ARCHIVE (historical) | 2026-09-26 | 0 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_architecture_freeze/AHOS_Roadmap_v1.2.1_Change_Record.md` | ARCHIVE (historical) | 2026-09-26 | 60629 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_chats/lead_engineer_context_prompt_202607171934.txt` | ARCHIVE (historical) | 2026-09-26 | 1874 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_chats/project_chat_protocol.txt` | ARCHIVE (historical) | 2026-09-26 | 3074 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_chats/project_constitution_v1_frozen.txt` | ARCHIVE (historical) | 2026-09-26 | 8216 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_chats/session_initialization_prompt_official_v2.txt` | ARCHIVE (historical) | 2026-09-26 | 7058 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_chats/wf_numbering_proposal_202607171900.txt` | ARCHIVE (historical) | 2026-09-26 | 445 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_daily_reports/AHOS_Daily_Engineering_Report_ADER_2026-07-17_v1.0.txt` | ARCHIVE (historical) | 2026-09-26 | 7136 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_daily_reports/AHOS_SDR-2026-07-22-001_Development_Session_Report.md.txt` | ARCHIVE (historical) | 2026-09-26 | 4639 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_daily_reports/آرشیو/(1) سند مکمل تاریخ 07-07-2026.txt` | ARCHIVE (historical) | untracked/— | 9090 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_daily_reports/آرشیو/(1) سند مکمل تاریخ 10-07-2026.txt` | ARCHIVE (historical) | untracked/— | 5436 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_daily_reports/آرشیو/(1) سند مکمل تاریخ 14-07-2026.txt` | ARCHIVE (historical) | untracked/— | 2022 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_daily_reports/آرشیو/(1) سند مکمل تاریخ 9-07-2026.txt` | ARCHIVE (historical) | untracked/— | 8333 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_daily_reports/آرشیو/(2) سند مکمل تاریخ 07-07-2026.txt` | ARCHIVE (historical) | untracked/— | 15441 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_daily_reports/آرشیو/(2) سند مکمل تاریخ 10-07-2026.txt` | ARCHIVE (historical) | untracked/— | 6290 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_daily_reports/آرشیو/(3) سند مکمل تاریخ 07-07-2026.txt` | ARCHIVE (historical) | untracked/— | 4349 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_daily_reports/آرشیو/(3) سند مکمل تاریخ 10-07-2026.txt` | ARCHIVE (historical) | untracked/— | 6129 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_daily_reports/آرشیو/سند مکمل تاریخ 06-07-2026.txt` | ARCHIVE (historical) | untracked/— | 12468 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_daily_reports/آرشیو/سند مکمل روزانه 202607152241.txt` | ARCHIVE (historical) | untracked/— | 8187 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_prompt_library/prompt_001_senior_architect_202607141751.txt` | ARCHIVE (historical) | 2026-09-26 | 12756 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_root_new_text_document.txt` | ARCHIVE (historical) | 2026-09-26 | 10454 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_standards/AHOS Code Review Standard.md` | ARCHIVE (historical) | 2026-09-26 | 0 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_standards/AHOS Database Standard.md` | ARCHIVE (historical) | 2026-09-26 | 0 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_standards/AHOS Error Standard.md` | ARCHIVE (historical) | 2026-09-26 | 0 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_standards/AHOS JSON Standard.md` | ARCHIVE (historical) | 2026-09-26 | 0 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_standards/AHOS Logging Standard.md` | ARCHIVE (historical) | 2026-09-26 | 0 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_standards/AHOS Naming Standard.md` | ARCHIVE (historical) | 2026-09-26 | 0 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_standards/AHOS Prompt Standard.md` | ARCHIVE (historical) | 2026-09-26 | 0 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_standards/AHOS Versioning Standard.md` | ARCHIVE (historical) | 2026-09-26 | 0 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_standards/AHOS Workflow Standard.md` | ARCHIVE (historical) | 2026-09-26 | 0 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_standards/AHOS_Universal_Market_Object_Standard_v1.0.md` | ARCHIVE (historical) | 2026-09-26 | 86426 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/AHOS_AI_Engineering_and_Collaboration_Standard_AECS_v1.0.txt` | ARCHIVE (historical) | 2026-09-26 | 7774 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/AHOS_Architecture_Engine_Specification_AES_v1.0_Frozen.txt` | ARCHIVE (historical) | 2026-09-26 | 6356 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/AHOS_Database_Design_Specification_DDS_v1.0.txt` | ARCHIVE (historical) | 2026-09-26 | 5433 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/AHOS_Functional_Requirements_Specification_FRS_v1.0.txt` | ARCHIVE (historical) | 2026-09-26 | 5416 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/AHOS_Intelligence_Pipeline_AIP_v1.0_Frozen.txt` | ARCHIVE (historical) | 2026-09-26 | 7845 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/AHOS_System_Architecture_Overview_SAO_v1.0.txt` | ARCHIVE (historical) | 2026-09-26 | 13593 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/AHOS_System_Objectives_v1.0.txt` | ARCHIVE (historical) | 2026-09-26 | 4950 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/AHOS_System_Vision_and_Functional_Objectives_v1.0.txt` | ARCHIVE (historical) | 2026-09-26 | 3884 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/AHOS_Workflow_Catalog_AWC_v1.0.txt` | ARCHIVE (historical) | 2026-09-26 | 8027 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/.md/AHOS_WFC-001_Master_Scheduler_Contracts_v1.0.md` | ARCHIVE (historical) | 2026-09-26 | 25834 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/.md/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P1.md` | ARCHIVE (historical) | 2026-09-26 | 36218 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/.md/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P2.md` | ARCHIVE (historical) | 2026-09-26 | 30557 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/.md/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P3.md` | ARCHIVE (historical) | 2026-09-26 | 61500 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/.md/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P4.md` | ARCHIVE (historical) | 2026-09-26 | 46076 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/.md/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P5.md` | ARCHIVE (historical) | 2026-09-26 | 51086 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/.md/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P6.md` | ARCHIVE (historical) | 2026-09-26 | 53987 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/.md/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P7.md` | ARCHIVE (historical) | 2026-09-26 | 30393 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/.md/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P8.md` | ARCHIVE (historical) | 2026-09-26 | 28330 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/AHOS_WFC-001_Master_Scheduler_Contracts_v1.0.txt` | ARCHIVE (historical) | 2026-09-26 | 26284 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P1.txt` | ARCHIVE (historical) | 2026-09-26 | 35934 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P2.txt` | ARCHIVE (historical) | 2026-09-26 | 30183 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P3.txt` | ARCHIVE (historical) | 2026-09-26 | 62219 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P4.txt` | ARCHIVE (historical) | 2026-09-26 | 47240 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P5.txt` | ARCHIVE (historical) | 2026-09-26 | 51149 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P6.txt` | ARCHIVE (historical) | 2026-09-26 | 54898 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P7.txt` | ARCHIVE (historical) | 2026-09-26 | 30845 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-001 Version 3.0/AHOS_WSS_WF-001_Master_Scheduler_v3.0_P8.txt` | ARCHIVE (historical) | 2026-09-26 | 28623 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-002 Version 3.0/AHOS_WSS_WF-002_Master_Scheduler_v3.0_P1.txt` | ARCHIVE (historical) | 2026-09-26 | 21070 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-002 Version 3.0/AHOS_WSS_WF-002_Master_Scheduler_v3.0_P2.txt` | ARCHIVE (historical) | 2026-09-26 | 16595 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-002 Version 3.0/AHOS_WSS_WF-002_Master_Scheduler_v3.0_P3.txt` | ARCHIVE (historical) | 2026-09-26 | 12151 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-002 Version 3.0/AHOS_WSS_WF-002_Master_Scheduler_v3.0_P4.txt` | ARCHIVE (historical) | 2026-09-26 | 6208 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-002 Version 3.0/AHOS_WSS_WF-002_Master_Scheduler_v3.0_P5.txt` | ARCHIVE (historical) | 2026-09-26 | 6117 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-002 Version 3.0/AHOS_WSS_WF-002_Master_Scheduler_v3.0_P6.txt` | ARCHIVE (historical) | 2026-09-26 | 5971 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-002 Version 3.0/AHOS_WSS_WF-002_Master_Scheduler_v3.0_P7.txt` | ARCHIVE (historical) | 2026-09-26 | 6069 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-002 Version 3.0/AHOS_WSS_WF-002_Master_Scheduler_v3.0_P8.txt` | ARCHIVE (historical) | 2026-09-26 | 7385 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-003 Version 3.0/AHOS_WF-003_Execution_Manager_Architecture_Completion_Statement_v1.0.md.txt` | ARCHIVE (historical) | 2026-09-26 | 5154 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-003 Version 3.0/AHOS_WSS_WF-003_Master_Scheduler_v3.0_P1.txt` | ARCHIVE (historical) | 2026-09-26 | 5983 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-003 Version 3.0/AHOS_WSS_WF-003_Master_Scheduler_v3.0_P2.txt` | ARCHIVE (historical) | 2026-09-26 | 6212 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-003 Version 3.0/AHOS_WSS_WF-003_Master_Scheduler_v3.0_P3.txt` | ARCHIVE (historical) | 2026-09-26 | 6073 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-003 Version 3.0/AHOS_WSS_WF-003_Master_Scheduler_v3.0_P4.txt` | ARCHIVE (historical) | 2026-09-26 | 5921 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-003 Version 3.0/AHOS_WSS_WF-003_Master_Scheduler_v3.0_P5.txt` | ARCHIVE (historical) | 2026-09-26 | 5987 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-003 Version 3.0/AHOS_WSS_WF-003_Master_Scheduler_v3.0_P6.txt` | ARCHIVE (historical) | 2026-09-26 | 5754 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-003 Version 3.0/AHOS_WSS_WF-003_Master_Scheduler_v3.0_P7.txt` | ARCHIVE (historical) | 2026-09-26 | 6195 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-003 Version 3.0/AHOS_WSS_WF-003_Master_Scheduler_v3.0_P8.txt` | ARCHIVE (historical) | 2026-09-26 | 5948 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-004 Version 3.0/AHOS_WSS_WF-004_Master_Scheduler_v3.0_P1.txt` | ARCHIVE (historical) | 2026-09-26 | 3613 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-004 Version 3.0/AHOS_WSS_WF-004_Master_Scheduler_v3.0_P2.txt` | ARCHIVE (historical) | 2026-09-26 | 5892 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-004 Version 3.0/AHOS_WSS_WF-004_Master_Scheduler_v3.0_P3.txt` | ARCHIVE (historical) | 2026-09-26 | 5838 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-004 Version 3.0/AHOS_WSS_WF-004_Master_Scheduler_v3.0_P4.txt` | ARCHIVE (historical) | 2026-09-26 | 5850 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-004 Version 3.0/AHOS_WSS_WF-004_Master_Scheduler_v3.0_P5.txt` | ARCHIVE (historical) | 2026-09-26 | 5747 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-004 Version 3.0/AHOS_WSS_WF-004_Master_Scheduler_v3.0_P6.txt` | ARCHIVE (historical) | 2026-09-26 | 5752 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-004 Version 3.0/AHOS_WSS_WF-004_Master_Scheduler_v3.0_P7.txt` | ARCHIVE (historical) | 2026-09-26 | 5227 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-004 Version 3.0/AHOS_WSS_WF-004_Master_Scheduler_v3.0_P8.txt` | ARCHIVE (historical) | 2026-09-26 | 5616 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-005 Version 3.0/AHOS_WSS_WF-005_Master_Scheduler_v3.0_P1.txt` | ARCHIVE (historical) | 2026-09-26 | 3843 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-005 Version 3.0/AHOS_WSS_WF-005_Master_Scheduler_v3.0_P2.txt` | ARCHIVE (historical) | 2026-09-26 | 6158 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-005 Version 3.0/AHOS_WSS_WF-005_Master_Scheduler_v3.0_P3.txt` | ARCHIVE (historical) | 2026-09-26 | 5238 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-005 Version 3.0/AHOS_WSS_WF-005_Master_Scheduler_v3.0_P4.txt` | ARCHIVE (historical) | 2026-09-26 | 5483 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-005 Version 3.0/AHOS_WSS_WF-005_Master_Scheduler_v3.0_P5.txt` | ARCHIVE (historical) | 2026-09-26 | 4944 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-005 Version 3.0/AHOS_WSS_WF-005_Master_Scheduler_v3.0_P6.txt` | ARCHIVE (historical) | 2026-09-26 | 4904 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-005 Version 3.0/AHOS_WSS_WF-005_Master_Scheduler_v3.0_P7.txt` | ARCHIVE (historical) | 2026-09-26 | 5081 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/WF-005 Version 3.0/AHOS_WSS_WF-005_Master_Scheduler_v3.0_P8.txt` | ARCHIVE (historical) | 2026-09-26 | 4711 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/آرشیو/AHOS_WF-001_Master_Scheduler_Engineering_Review_v1.0_Approved_With_Critical_Enhancements.txt` | ARCHIVE (historical) | untracked/— | 18128 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/workflow/آرشیو/AHOS_Workflow_Specification_Sheet_WSS_WF-001_Master_Scheduler_v1.0_Draft.txt` | ARCHIVE (historical) | untracked/— | 4532 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/آرشیو/AHOS Architecture Bible Season 3.txt` | ARCHIVE (historical) | untracked/— | 262768 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/آرشیو/AHOS Architecture Bible v4.0 — Ultimate Production Lock Edition.txt` | ARCHIVE (historical) | untracked/— | 162249 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/آرشیو/AHOS Architecture Bible v4.1 — Production Lock Edition Section 2 Complete System Architecture.txt` | ARCHIVE (historical) | untracked/— | 192746 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/آرشیو/AHOS Architecture Bible v4.1 — Production Lock Edition.txt` | ARCHIVE (historical) | untracked/— | 99656 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/آرشیو/AHOS Architecture Bible v4.1 — Production Lock EditionSection 1.txt` | ARCHIVE (historical) | untracked/— | 10335 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/آرشیو/AHOS Strategic Master Plan v10.0.txt` | ARCHIVE (historical) | untracked/— | 7924 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/آرشیو/AHOS Technical Architecture Specification v1.1.txt` | ARCHIVE (historical) | untracked/— | 160573 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/آرشیو/AHOS Ultimate Vision v1.0.txt` | ARCHIVE (historical) | untracked/— | 194997 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/آرشیو/AHOS_Data_Architecture_Specification_v1.0.txt` | ARCHIVE (historical) | untracked/— | 125892 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/آرشیو/Engine Specifications.txt` | ARCHIVE (historical) | untracked/— | 74612 | 0 |
| `docs/archive/consolidation_2026-09-26/booklet_strategic_specs/آرشیو/Roadmap.txt` | ARCHIVE (historical) | untracked/— | 60629 | 0 |
| `docs/archive/consolidation_2026-09-26/n8n_legacy/readme.md` | ARCHIVE (historical) | 2026-09-26 | 135 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project/PROJECT_BIBLE.md` | ARCHIVE (historical) | 2026-09-26 | 2979 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project_docs/CHANGELOG.md` | ARCHIVE (historical) | 2026-09-26 | 0 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project_docs/INDEX.md` | ARCHIVE (historical) | 2026-09-26 | 1447 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project_docs/adr/ADR-0001-CognitiveCycle-Specification-Required.md` | ARCHIVE (historical) | 2026-09-26 | 4356 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project_docs/architecture/ADR-0001-CognitiveCycle-Specification-Required.md` | ARCHIVE (historical) | 2026-09-26 | 1276 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project_docs/architecture/AR-007_Lifecycle_Service_Architecture_Review_APPROVED.md` | ARCHIVE (historical) | 2026-09-26 | 8355 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project_docs/architecture/ARCHITECTURE_COMPLETION_ROADMAP_v1.0.md` | ARCHIVE (historical) | 2026-09-26 | 2449 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project_docs/architecture/CAS_v1.0.md` | ARCHIVE (historical) | 2026-09-26 | 3686 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project_docs/architecture/DEB_v1.0.md` | ARCHIVE (historical) | 2026-09-26 | 343 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project_docs/architecture/DLV-007_Lifecycle_Service_v1.0_FROZEN.md` | ARCHIVE (historical) | 2026-09-26 | 32977 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project_docs/architecture/DMS_v1.0.md` | ARCHIVE (historical) | 2026-09-26 | 480 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project_docs/architecture/LSS-001 - Lifecycle Service Specification v1.0.md` | ARCHIVE (historical) | 2026-09-26 | 13126 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project_docs/architecture/RAS_v1.1.md` | ARCHIVE (historical) | 2026-09-26 | 479 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project_docs/architecture/SPS_v1.1.md` | ARCHIVE (historical) | 2026-09-26 | 761 | 0 |
| `docs/archive/consolidation_2026-09-26/robot_project_records/MR-2026-07-29-006_CognitiveCycle_Approved.md` | ARCHIVE (historical) | 2026-09-26 | 48263 | 0 |
| `docs/archive/feature_store_v1_src_20260814.txt` | ARCHIVE (historical) | 2026-08-16 | 14456 | 0 |
| `docs/archive/observe_active_v1_src_20260813.txt` | ARCHIVE (historical) | 2026-08-16 | 9662 | 0 |
| `docs/archive/oss_research/OSS_AGENT_ARCHITECTURE_PLAN.md` | ARCHIVE (historical) | 2026-08-27 | 9840 | 0 |
| `docs/archive/oss_research/OSS_AHOS_MAPPING.md` | ARCHIVE (historical) | 2026-08-27 | 10965 | 0 |
| `docs/archive/oss_research/OSS_AI_PROVIDER_MAP.md` | ARCHIVE (historical) | 2026-08-27 | 7170 | 0 |
| `docs/archive/oss_research/OSS_BACKTEST_UPGRADE_PLAN.md` | ARCHIVE (historical) | 2026-08-27 | 7722 | 0 |
| `docs/archive/oss_research/OSS_CAPABILITY_MATRIX.md` | ARCHIVE (historical) | 2026-08-27 | 10062 | 0 |
| `docs/archive/oss_research/OSS_DATA_PROVIDER_MAP.md` | ARCHIVE (historical) | 2026-08-27 | 7265 | 0 |
| `docs/archive/oss_research/OSS_FINAL_RECOMMENDATION.md` | ARCHIVE (historical) | 2026-08-27 | 5157 | 0 |
| `docs/archive/oss_research/OSS_INTEGRATION_BACKLOG.md` | ARCHIVE (historical) | 2026-08-27 | 10460 | 0 |
| `docs/archive/oss_research/OSS_INTEGRATION_PLAN.md` | ARCHIVE (historical) | 2026-08-27 | 12210 | 0 |
| `docs/archive/oss_research/OSS_LICENSE_SECURITY_AUDIT.md` | ARCHIVE (historical) | 2026-08-27 | 8914 | 0 |
| `docs/archive/oss_research/OSS_REJECTED_PROJECTS.md` | ARCHIVE (historical) | 2026-08-27 | 7126 | 0 |
| `docs/archive/oss_research/OSS_TOP20_RESEARCH.md` | ARCHIVE (historical) | 2026-08-27 | 38762 | 0 |
| `docs/archive/oss_research/README.md` | ARCHIVE (historical) | 2026-08-27 | 382 | 0 |
| `docs/archive/test_observe_active_v1_src_20260813.txt` | ARCHIVE (historical) | 2026-08-16 | 11928 | 0 |
| `reports/archive/snaps/README.md` | ARCHIVE (historical) | 2026-08-27 | 413 | 0 |
| `reports/archive/snaps/ahos_snap_w12_after.txt` | ARCHIVE (historical) | 2026-08-27 | 35985 | 0 |
| `reports/archive/snaps/ahos_snap_w12r_after.txt` | ARCHIVE (historical) | 2026-08-27 | 37114 | 0 |
| `reports/archive/snaps/ahos_snap_w13_after.txt` | ARCHIVE (historical) | 2026-08-27 | 38100 | 0 |
| `reports/archive/snaps/ahos_snap_w13b_after.txt` | ARCHIVE (historical) | 2026-08-27 | 38688 | 0 |
| `reports/archive/snaps/ahos_snap_w13c_after.txt` | ARCHIVE (historical) | 2026-08-27 | 38796 | 0 |
| `reports/archive/snaps/ahos_snap_w13d_after.txt` | ARCHIVE (historical) | 2026-08-27 | 39147 | 0 |
| `reports/archive/snaps/ahos_snap_w14_after.txt` | ARCHIVE (historical) | 2026-08-27 | 32310 | 0 |
| `reports/archive/snaps/ahos_snap_w15_after.txt` | ARCHIVE (historical) | 2026-08-27 | 32632 | 0 |
| `reports/archive/snaps/ahos_snap_w15b_after.txt` | ARCHIVE (historical) | 2026-08-27 | 33983 | 0 |
| `reports/archive/snaps/ahos_snap_w15c_after.txt` | ARCHIVE (historical) | 2026-08-27 | 34788 | 0 |
| `reports/archive/snaps/ahos_snap_w16_after.txt` | ARCHIVE (historical) | 2026-08-27 | 35306 | 0 |
| `reports/archive/snaps/ahos_snap_w17_after.txt` | ARCHIVE (historical) | 2026-08-27 | 36842 | 0 |
| `reports/archive/snaps/ahos_snap_w18_after.txt` | ARCHIVE (historical) | 2026-08-27 | 46502 | 0 |
| `reports/archive/snaps/ahos_snap_w19_after.txt` | ARCHIVE (historical) | 2026-08-27 | 52788 | 0 |
| `reports/archive/snaps/ahos_snap_w20_after.txt` | ARCHIVE (historical) | 2026-08-27 | 58414 | 0 |
| `reports/archive/snaps/ahos_snap_w21_after.txt` | ARCHIVE (historical) | 2026-08-27 | 60253 | 0 |
| `reports/archive/snaps/ahos_snap_w22_after.txt` | ARCHIVE (historical) | 2026-08-27 | 64188 | 0 |
| `reports/archive/snaps/ahos_snap_w24_after.txt` | ARCHIVE (historical) | 2026-08-27 | 64914 | 0 |
| `reports/archive/snaps/ahos_snap_w25_after.txt` | ARCHIVE (historical) | 2026-08-27 | 68571 | 0 |
| `reports/archive/snaps/ahos_snap_w26_after.txt` | ARCHIVE (historical) | 2026-08-27 | 68650 | 0 |
| `reports/archive/snaps/ahos_snap_w27_after.txt` | ARCHIVE (historical) | 2026-08-27 | 68914 | 0 |
| `reports/archive/snaps/ahos_snap_w28_after.txt` | ARCHIVE (historical) | 2026-08-27 | 69176 | 0 |
| `reports/archive/snaps/ahos_snap_w29_after.txt` | ARCHIVE (historical) | 2026-08-27 | 69811 | 0 |
| `reports/archive/snaps/ahos_snap_w30_after.txt` | ARCHIVE (historical) | 2026-08-27 | 69811 | 0 |
| `reports/archive/snaps/ahos_snap_w31_after.txt` | ARCHIVE (historical) | 2026-08-27 | 69811 | 0 |
| `docs/agents/AGENT_MISSION_CHARTER_TEMPLATE.md` | BASE/MASTER (charter/constitution/governance) | 2026-09-15 | 4266 | 3 |
| `docs/architecture/ADR_ACI_001_CHARTER_VS_DEFERRED_EVOLUTION.md` | BASE/MASTER (charter/constitution/governance) | 2026-09-09 | 3013 | 3 |
| `docs/architecture/AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md` | BASE/MASTER (charter/constitution/governance) | 2026-09-09 | 10276 | 8 |
| `docs/canonical/GOVERNANCE.md` | BASE/MASTER (charter/constitution/governance) | 2026-08-16 | 1658 | 2 |
| `docs/canonical/MASTER_DIRECTIVE_W43.md` | BASE/MASTER (charter/constitution/governance) | 2026-08-21 | 3846 | 4 |
| `docs/canonical/MASTER_DIRECTIVE_v1.md` | BASE/MASTER (charter/constitution/governance) | 2026-08-16 | 3674 | 2 |
| `docs/canonical/MISSION.md` | BASE/MASTER (charter/constitution/governance) | 2026-08-16 | 1954 | 2 |
| `docs/canonical/SECURITY.md` | BASE/MASTER (charter/constitution/governance) | 2026-08-28 | 1667 | 3 |
| `docs/governance/AGENT_04_GOVERNANCE_AND_CONSTITUTION_ARCHITECTURE.md` | BASE/MASTER (charter/constitution/governance) | 2026-09-15 | 50978 | 52 |
| `docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md` | BASE/MASTER (charter/constitution/governance) | 2026-09-15 | 15453 | 12 |
| `docs/governance/M3_CONSTITUTIONAL_AND_KNOWLEDGE_RECONCILIATION.md` | BASE/MASTER (charter/constitution/governance) | 2026-09-28 | 23517 | 8 |
| `docs/owner_directives/owner_directive_part1.txt` | BASE/MASTER (owner directive: Master Directive, MASTER CONTEXT v2.0, Charter, Completion Mandate) | 2026-10-03 | 97155 | 0 |
| `docs/owner_directives/owner_directive_part2.txt` | BASE/MASTER (owner directive: Master Directive, MASTER CONTEXT v2.0, Charter, Completion Mandate) | 2026-10-03 | 146676 | 0 |
| `AHOS_CONTROLLED_FAILURE_TEST_REPORT.md` | DEBUG/FAILURE/GAP | 2026-08-18 | 5967 | 0 |
| `AHOS_GAP_REGISTER.md` | DEBUG/FAILURE/GAP | 2026-10-01 | 91348 | 13 |
| `AHOS_ISSUE_REGISTER.md` | DEBUG/FAILURE/GAP | 2026-08-28 | 136620 | 26 |
| `docs/ISSUES_REGISTER.md` | DEBUG/FAILURE/GAP | 2026-08-16 | 333 | 0 |
| `docs/STRATEGIC_GAP_ANALYSIS.md` | DEBUG/FAILURE/GAP | 2026-08-27 | 3724 | 1 |
| `docs/verification/AGENT_16_INDEPENDENT_VERIFICATION_AND_ORGANIZATIONAL_FORENSICS.md` | DEBUG/FAILURE/GAP | 2026-09-15 | 50789 | 4 |
| `reports/FAILURE_MEMORY.md` | DEBUG/FAILURE/GAP | 2026-10-03 | 12329 | 1 |
| `reports/agi_aci_evolution/GAP_REGISTER.md` | DEBUG/FAILURE/GAP | 2026-09-13 | 5001 | 6 |
| `reports/agi_aci_evolution/P4_4_COGNITIVE_STACK_FORENSIC_AUDIT.md` | DEBUG/FAILURE/GAP | 2026-09-09 | 53991 | 12 |
| `reports/agi_aci_evolution/P5_FORENSIC_ARCHITECTURE_GATE.md` | DEBUG/FAILURE/GAP | 2026-09-10 | 33750 | 13 |
| `reports/agi_aci_evolution/P5_POST_IMPLEMENTATION_FORENSIC_AUDIT.md` | DEBUG/FAILURE/GAP | 2026-09-11 | 31682 | 6 |
| `reports/agi_aci_evolution/P5_SECOND_FORENSIC_VERIFICATION.md` | DEBUG/FAILURE/GAP | 2026-09-10 | 19884 | 6 |
| `reports/agi_aci_evolution/P5_V3_POST_IMPLEMENTATION_FORENSIC_AUDIT.md` | DEBUG/FAILURE/GAP | 2026-09-11 | 26883 | 7 |
| `reports/agi_aci_evolution/P5_V3_TEST_INDEPENDENCE_FORENSIC_DESIGN.md` | DEBUG/FAILURE/GAP | 2026-09-11 | 28326 | 20 |
| `reports/agi_aci_evolution/P5_V4_POST_IMPLEMENTATION_FORENSIC_AUDIT.md` | DEBUG/FAILURE/GAP | 2026-09-11 | 18039 | 4 |
| `reports/grok/reviews/FIX_MATRIX_PHASE9_5_9_6.md` | DEBUG/FAILURE/GAP | 2026-10-03 | 8775 | 3 |
| `SECURITY.md` | GOVERNANCE/DIRECTIVE | 2026-08-16 | 1099 | 0 |
| `docs/AGENT_MODE_OPERATIONAL_DIRECTIVE_FA.md` | GOVERNANCE/DIRECTIVE | 2026-08-20 | 14219 | 9 |
| `docs/governance/AGENT_01_GOVERNANCE_PROPAGATION_ADOPTION_REPORT.md` | GOVERNANCE/DIRECTIVE | 2026-09-15 | 25962 | 7 |
| `docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md` | GOVERNANCE/DIRECTIVE | 2026-09-15 | 11199 | 16 |
| `docs/governance/AGENT_REGISTRY_MODEL.md` | GOVERNANCE/DIRECTIVE | 2026-09-15 | 3781 | 1 |
| `docs/governance/AGENT_TAXONOMY_MAP.md` | GOVERNANCE/DIRECTIVE | 2026-09-28 | 7308 | 6 |
| `docs/governance/M4_WAVE_DIRECTIVE_DECLARATION.md` | GOVERNANCE/DIRECTIVE | 2026-09-28 | 10858 | 5 |
| `docs/governance/ORGANIZATIONAL_ARCHITECTURE_BASELINE_v0.1.md` | GOVERNANCE/DIRECTIVE | 2026-09-15 | 39486 | 23 |
| `docs/supervision/LATEST_DIRECTIVE_FOR_AHOS_AGENT.md` | GOVERNANCE/DIRECTIVE | 2026-09-13 | 2174 | 1 |
| `reports/grok/OWNER_DIRECTIVE_MISSION_PLAN.md` | GOVERNANCE/DIRECTIVE | 2026-10-03 | 18807 | 8 |
| `.pytest_cache/README.md` | OPERATOR/README | untracked/— | 302 | 0 |
| `AHOS_OPERATOR_QUICKSTART_WINDOWS.md` | OPERATOR/README | 2026-08-28 | 9009 | 0 |
| `AHOS_SOAK_OPERATOR_START.md` | OPERATOR/README | 2026-08-18 | 6917 | 0 |
| `AHOS_WINDOWS_DEPLOYMENT_GUIDE.md` | OPERATOR/README | 2026-08-19 | 2702 | 0 |
| `AHOS_WINDOWS_OPERATOR_RUNBOOK.md` | OPERATOR/README | 2026-08-18 | 3095 | 0 |
| `CONTRIBUTING.md` | OPERATOR/README | 2026-08-27 | 1638 | 0 |
| `INSTALLATION.md` | OPERATOR/README | 2026-08-18 | 1747 | 0 |
| `QUICKSTART.md` | OPERATOR/README | 2026-08-17 | 7082 | 0 |
| `README.md` | OPERATOR/README | 2026-09-26 | 3482 | 0 |
| `RUN_ME_WINDOWS.txt` | OPERATOR/README | 2026-08-29 | 1680 | 0 |
| `docs/OPERATOR_VALIDATION_PROTOCOL.md` | OPERATOR/README | 2026-08-28 | 4372 | 0 |
| `docs/RUNBOOK_OPERATIONS.md` | OPERATOR/README | 2026-08-16 | 3699 | 0 |
| `docs/TELEGRAM_OPERATOR_E2E_PROTOCOL.md` | OPERATOR/README | 2026-08-28 | 1778 | 0 |
| `docs/WINDOWS_OPERATOR_HANDOFF.md` | OPERATOR/README | 2026-08-28 | 8983 | 0 |
| `docs/n8n_setup_guide.md` | OPERATOR/README | 2026-08-27 | 2140 | 0 |
| `drizzle/README.md` | OPERATOR/README | 2026-08-28 | 356 | 0 |
| `requirements-optional.txt` | OPERATOR/README | 2026-08-19 | 749 | 0 |
| `requirements.txt` | OPERATOR/README | 2026-08-19 | 1513 | 0 |
| `strategy_lab/README.md` | OPERATOR/README | 2026-08-16 | 1907 | 0 |
| `.github/PULL_REQUEST_TEMPLATE.md` | OTHER DOC | 2026-09-03 | 838 | 0 |
| `AGENTS.md` | OTHER DOC | 2026-09-08 | 4186 | 0 |
| `AHOS_LAPTOP_READINESS_CHECKLIST.md` | OTHER DOC | 2026-08-20 | 4760 | 0 |
| `AHOS_LOCAL_ACTIVATION_CHECKLIST.md` | OTHER DOC | 2026-08-18 | 8320 | 0 |
| `AHOS_LOCAL_SOAK_PROTOCOL.md` | OTHER DOC | 2026-09-28 | 7222 | 0 |
| `AHOS_MONTH1_OPERATIONAL_GATE.md` | OTHER DOC | 2026-08-20 | 3714 | 0 |
| `AHOS_MONTH1_SOAK_PROTOCOL.md` | OTHER DOC | 2026-08-18 | 6792 | 0 |
| `AHOS_MONTH2_RECOMMENDATION.md` | OTHER DOC | 2026-08-18 | 2770 | 0 |
| `AHOS_WEB_COMMAND_CENTER.md` | OTHER DOC | 2026-08-21 | 1790 | 0 |
| `WINDOWS_RUN_THIS_FIRST.txt` | OTHER DOC | 2026-08-29 | 1676 | 0 |
| `docs/AGENT_MAPPING.md` | OTHER DOC | 2026-10-03 | 3660 | 0 |
| `docs/CALIBRATION_LIFECYCLE.md` | OTHER DOC | 2026-08-27 | 3140 | 0 |
| `docs/COMPONENT_REUSE_MAP.md` | OTHER DOC | 2026-10-03 | 2522 | 0 |
| `docs/DATA_SOURCE_MATRIX.md` | OTHER DOC | 2026-08-16 | 4230 | 0 |
| `docs/MISSING_COMPONENT_REGISTER.md` | OTHER DOC | 2026-08-27 | 2295 | 0 |
| `docs/N8N_OPERATIONAL_PROCEDURE.md` | OTHER DOC | 2026-10-02 | 1194 | 0 |
| `docs/NEXT_DEVELOPMENT_BACKLOG.md` | OTHER DOC | 2026-08-27 | 1176 | 0 |
| `docs/ONE_CLICK.md` | OTHER DOC | untracked/— | 9732 | 0 |
| `docs/OSS_HARVEST_LOG.md` | OTHER DOC | 2026-08-17 | 4552 | 0 |
| `docs/OWNER_ACTION_REQUIRED.md` | OTHER DOC | 2026-08-27 | 1204 | 0 |
| `docs/PRE_SOAK_PROTOCOL.md` | OTHER DOC | 2026-09-09 | 3610 | 0 |
| `docs/SUN_SNIPER_TELEGRAM.md` | OTHER DOC | 2026-08-21 | 2033 | 0 |
| `docs/TELEGRAM_TEST_PROCEDURE.md` | OTHER DOC | 2026-08-16 | 2446 | 0 |
| `docs/WINDOWS_ONE_SHOT_RECONCILE.md` | OTHER DOC | 2026-08-28 | 2622 | 0 |
| `docs/supervision/AHOS_AGENT_SUPERVISION_COUNCIL.md` | OTHER DOC | 2026-09-12 | 4888 | 0 |
| `docs/supervision/AHOS_AGENT_WAKE_MESSAGE.md` | OTHER DOC | 2026-09-12 | 1874 | 0 |
| `docs/supervision/AID_M1_POSTMERGE_STATIC_PR108.md` | OTHER DOC | 2026-09-24 | 8643 | 0 |
| `docs/supervision/CONNECTION_PROTOCOL.md` | OTHER DOC | 2026-09-12 | 2641 | 0 |
| `docs/supervision/M3_W14_RESOLVER_MINT_BRIEF.md` | OTHER DOC | 2026-09-24 | 8750 | 0 |
| `docs/supervision/OWNER_VISION_REGISTRY.md` | OTHER DOC | 2026-09-12 | 5765 | 0 |
| `docs/supervision/cycles/CYCLE_001_2026-09-12.md` | OTHER DOC | 2026-09-12 | 4526 | 0 |
| `docs/supervision/cycles/CYCLE_002_2026-09-12.md` | OTHER DOC | 2026-09-12 | 4158 | 0 |
| `docs/supervision/cycles/CYCLE_003_2026-09-12.md` | OTHER DOC | 2026-09-12 | 2839 | 0 |
| `docs/supervision/cycles/CYCLE_004_2026-09-12.md` | OTHER DOC | 2026-09-12 | 6454 | 0 |
| `docs/supervision/cycles/CYCLE_005_2026-09-12.md` | OTHER DOC | 2026-09-12 | 1095 | 0 |
| `docs/supervision/cycles/CYCLE_OP_2026-09-12_1644.md` | OTHER DOC | 2026-09-12 | 1400 | 0 |
| `docs/supervision/cycles/CYCLE_OP_2026-09-13_1330.md` | OTHER DOC | 2026-09-13 | 2056 | 0 |
| `docs/supervision/cycles/CYCLE_OP_2026-09-13_1400.md` | OTHER DOC | 2026-09-13 | 930 | 0 |
| `docs/supervision/cycles/CYCLE_PR95_MERGED_2026-09-13.md` | OTHER DOC | 2026-09-13 | 1352 | 0 |
| `docs/supervision/cycles/CYCLE_STRATEGIC_2026-09-13.md` | OTHER DOC | 2026-09-13 | 6137 | 0 |
| `docs/supervision/gates/G0_BASELINE_2026-09-12.md` | OTHER DOC | 2026-09-12 | 818 | 0 |
| `scripts/WINDOWS_OWNER_PASTE_TEMPLATE.txt` | OTHER DOC | 2026-08-28 | 805 | 0 |
| `scripts/WINDOWS_OWNER_THREE_COMMANDS.txt` | OTHER DOC | 2026-08-28 | 486 | 0 |
| `reports/grok/CLAUDE_CONTINUATION_GUIDE.md` | OWNER INSTRUCTIONS/HANDOFF (reports/grok) | 2026-10-03 | 50395 | 14 |
| `reports/grok/GROK_HANDOFF.md` | OWNER INSTRUCTIONS/HANDOFF (reports/grok) | 2026-10-03 | 80312 | 23 |
| `reports/grok/ORCHESTRATION_LOG.md` | OWNER INSTRUCTIONS/HANDOFF (reports/grok) | 2026-10-03 | 3550 | 0 |
| `AHOS_ROADMAP_v3.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-18 | 7340 | 1 |
| `docs/DEVELOPMENT_ROADMAP.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2303 | 0 |
| `docs/architecture/F1_RESOLUTION_PLAN.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 7252 | 3 |
| `docs/architecture/unified_control_plane.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 3612 | 6 |
| `docs/canonical/ROADMAP.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 1197 | 0 |
| `docs/mission_v1_1/A_CURRENT_PAL_AUDIT.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 3890 | 2 |
| `docs/mission_v1_1/A_PROJECT_DOCUMENT_INVENTORY.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 904 | 0 |
| `docs/mission_v1_1/B_CURRENT_E01_AUDIT.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2743 | 3 |
| `docs/mission_v1_1/B_DUPLICATE_REDUNDANCY_REPORT.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2203 | 1 |
| `docs/mission_v1_1/C_CANONICAL_DOCUMENT_MAP.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 1549 | 0 |
| `docs/mission_v1_1/C_DISCOVERY_DATA_MODEL.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 4312 | 2 |
| `docs/mission_v1_1/D_CLEANUP_MANIFEST.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 1682 | 0 |
| `docs/mission_v1_1/D_FEATURE_STORE_SCHEMA.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 4504 | 1 |
| `docs/mission_v1_1/E01_GATE_PROTOCOL_v1.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 4320 | 2 |
| `docs/mission_v1_1/E_FEATURE_EXPANSION_PLAN.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2526 | 2 |
| `docs/mission_v1_1/E_SECURITY_GATE_DESIGN.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 3384 | 3 |
| `docs/mission_v1_1/F12_DECISION_MEMO.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 7339 | 3 |
| `docs/mission_v1_1/F_PUMP_EVENT_RESEARCH_SPEC.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2270 | 1 |
| `docs/mission_v1_1/F_STATE_MACHINE_72H.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 3210 | 1 |
| `docs/mission_v1_1/G_BASELINE_LIFT_DESIGN.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2167 | 3 |
| `docs/mission_v1_1/G_PROVIDER_MATRIX.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-20 | 5219 | 4 |
| `docs/mission_v1_1/H_COUNCIL_15_EXECUTION_MODEL.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 3123 | 2 |
| `docs/mission_v1_1/H_H14_GENERATION_DESIGN.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2262 | 3 |
| `docs/mission_v1_1/I_HOLDER_WHALE_ARCHITECTURE.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 3186 | 1 |
| `docs/mission_v1_1/I_TELEGRAM_PERSIAN_CONTRACT.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 3976 | 1 |
| `docs/mission_v1_1/J_IMPLEMENTATION_PLAN.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2570 | 1 |
| `docs/mission_v1_1/J_SOCIAL_NARRATIVE_ARCHITECTURE.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2620 | 1 |
| `docs/mission_v1_1/K_TELEGRAM_AI_IMPLEMENTATION_PLAN.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2486 | 3 |
| `docs/mission_v1_1/L_COUNCIL_WAVE6_DECISION_LOG.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 3016 | 2 |
| `docs/mission_v1_1/W10_ARCHITECTURE_READINESS.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 33384 | 12 |
| `docs/mission_v1_1/W11_UNIFIED_RUNTIME_ARCHITECTURE.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 6860 | 1 |
| `docs/mission_v1_1/W13_REALITY_AUDIT.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 11919 | 1 |
| `docs/mission_v1_1/W7_A_MASTER_PLAN.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 3732 | 0 |
| `docs/mission_v1_1/W7_B_H14_RESEARCH_PLAN.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 3520 | 1 |
| `docs/mission_v1_1/W7_C_TELEGRAM_AI_ARCHITECTURE.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2712 | 2 |
| `docs/mission_v1_1/W7_D_FREE_AI_PROVIDER_MATRIX.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2129 | 0 |
| `docs/mission_v1_1/W7_E_IRAN_RESILIENCE_MATRIX.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2480 | 0 |
| `docs/mission_v1_1/W7_F_DOC_HYGIENE_POLICY_V2.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2211 | 6 |
| `docs/mission_v1_1/W7_G_CLEANUP_EXECUTION_REPORT.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2505 | 1 |
| `docs/mission_v1_1/W7_H_CANONICAL_KNOWLEDGE_MAP_V2.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 1794 | 1 |
| `docs/mission_v1_1/W7_I_POSITION_MONITORING_SPEC.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2191 | 1 |
| `docs/mission_v1_1/W7_J_PERSIAN_ALERT_SPEC.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 1798 | 0 |
| `docs/mission_v1_1/W7_K_COUNCIL_DECISION_LOG.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 3405 | 1 |
| `docs/mission_v1_1/W7_L_H14_SEARCH_REGISTRY_UPDATE.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 2173 | 0 |
| `docs/mission_v1_1/W9_COGNITIVE_ARCHITECTURE.md` | PLAN/ROADMAP/MISSION PLAN | 2026-08-16 | 3444 | 3 |
| `reports/agi_aci_evolution/BENCHMARK_PLAN.md` | PLAN/ROADMAP/MISSION PLAN | 2026-09-09 | 2593 | 3 |
| `reports/agi_aci_evolution/PR93_DOCUMENTATION_RECONCILIATION_PLAN.md` | PLAN/ROADMAP/MISSION PLAN | 2026-09-11 | 25527 | 19 |
| `reports/grok/_claude_task_10.txt` | PLAN/ROADMAP/MISSION PLAN | untracked/— | 4820 | 1 |
| `reports/grok/_claude_task_11.txt` | PLAN/ROADMAP/MISSION PLAN | untracked/— | 4372 | 0 |
| `reports/grok/_claude_task_8.txt` | PLAN/ROADMAP/MISSION PLAN | untracked/— | 4123 | 0 |
| `reports/grok/_claude_task_9.txt` | PLAN/ROADMAP/MISSION PLAN | untracked/— | 4718 | 0 |
| `reports/grok/_claude_task_9_5.txt` | PLAN/ROADMAP/MISSION PLAN | untracked/— | 6440 | 1 |
| `reports/grok/_claude_task_9_6.txt` | PLAN/ROADMAP/MISSION PLAN | untracked/— | 4108 | 0 |
| `reports/grok/_claude_task_phase8.txt` | PLAN/ROADMAP/MISSION PLAN | untracked/— | 2318 | 0 |
| `AHOS_FINAL_STATUS.md` | REPORT/EVIDENCE | 2026-08-27 | 3423 | 0 |
| `AHOS_LAPTOP_OPERATION_REPORT.md` | REPORT/EVIDENCE | 2026-10-03 | 11232 | 0 |
| `AHOS_LOCAL_PRODUCTION_GATE_REPORT.md` | REPORT/EVIDENCE | 2026-08-18 | 3250 | 0 |
| `AHOS_MONTH1_PRE_SOAK_AUDIT.md` | REPORT/EVIDENCE | 2026-08-18 | 6891 | 0 |
| `AHOS_PHASE16_PRESTART_AUDIT.md` | REPORT/EVIDENCE | 2026-08-18 | 9836 | 0 |
| `AHOS_PHASE17_OPERATOR_READY_REPORT.md` | REPORT/EVIDENCE | 2026-08-18 | 7967 | 0 |
| `AHOS_PHASE18_OPERATOR_LAUNCHER_REPORT.md` | REPORT/EVIDENCE | 2026-08-19 | 6689 | 0 |
| `AHOS_PHASE7_REPORT.md` | REPORT/EVIDENCE | 2026-08-18 | 9215 | 0 |
| `AHOS_PHASE_PROGRESS_SNAPSHOT.md` | REPORT/EVIDENCE | 2026-08-18 | 8948 | 0 |
| `AHOS_PHASE_XX_COMPLETION_REPORT.md` | REPORT/EVIDENCE | 2026-08-16 | 6697 | 0 |
| `AHOS_PRODUCTION_READINESS_REPORT.md` | REPORT/EVIDENCE | 2026-08-27 | 2638 | 0 |
| `AHOS_PROJECT_STATE_MAP.md` | REPORT/EVIDENCE | 2026-10-03 | 15192 | 0 |
| `AHOS_REALITY_AUDIT_REPORT.md` | REPORT/EVIDENCE | 2026-08-28 | 3116 | 0 |
| `AHOS_REALITY_AUDIT_v2.md` | REPORT/EVIDENCE | 2026-08-20 | 12584 | 0 |
| `AHOS_SYSTEM_STATUS.md` | REPORT/EVIDENCE | 2026-10-03 | 9915 | 0 |
| `docs/CONSOLIDATION_REPORT_2026-09-26.md` | REPORT/EVIDENCE | 2026-09-26 | 12088 | 0 |
| `docs/CURRENT_TRUTH_SNAPSHOT.md` | REPORT/EVIDENCE | 2026-08-27 | 1820 | 0 |
| `docs/DOC_TRUTH_MAP.md` | REPORT/EVIDENCE | 2026-09-28 | 11237 | 0 |
| `docs/FINAL_FILE_LEVEL_CLEANUP_REPORT_2026-09-26.md` | REPORT/EVIDENCE | 2026-09-26 | 8801 | 0 |
| `docs/FINAL_TRUTH_AUDIT.md` | REPORT/EVIDENCE | 2026-08-27 | 1546 | 0 |
| `docs/MERGE_READINESS_AUDIT.md` | REPORT/EVIDENCE | 2026-08-27 | 2806 | 0 |
| `docs/OPERATOR_VALIDATION_REPORT.md` | REPORT/EVIDENCE | 2026-08-27 | 1841 | 0 |
| `docs/WINDOWS_EVIDENCE_INBOX.md` | REPORT/EVIDENCE | 2026-08-28 | 838 | 0 |
| `docs/supervision/AHOS_OWNER_JOURNEY_LAUNCH_ACCEPTANCE_AUDIT.md` | REPORT/EVIDENCE | 2026-09-12 | 33379 | 0 |
| `docs/supervision/AHOS_PROJECT_TRUTH_MODEL.md` | REPORT/EVIDENCE | 2026-09-13 | 17986 | 0 |
| `docs/supervision/AHOS_REALITY_MAP_v1.md` | REPORT/EVIDENCE | 2026-09-24 | 10146 | 0 |
| `docs/supervision/AHOS_VISION_ALIGNMENT_AUDIT.md` | REPORT/EVIDENCE | 2026-09-12 | 21598 | 0 |
| `docs/supervision/cycles/BASELINE_AUDIT_2026-09-12.md` | REPORT/EVIDENCE | 2026-09-12 | 6872 | 0 |
| `docs/supervision/cycles/CYCLE_OWNER_JOURNEY_AUDIT_2026-09-12.md` | REPORT/EVIDENCE | 2026-09-12 | 1395 | 0 |
| `docs/supervision/cycles/CYCLE_VISION_AUDIT_2026-09-12.md` | REPORT/EVIDENCE | 2026-09-12 | 1037 | 0 |
| `reports/BACKTEST_REPORT_EXACT.md` | REPORT/EVIDENCE | 2026-08-16 | 3940 | 0 |
| `reports/FINAL_DELIVERY.md` | REPORT/EVIDENCE | 2026-08-16 | 248 | 0 |
| `reports/FINAL_EXECUTION_REPORT.md` | REPORT/EVIDENCE | 2026-08-16 | 19523 | 0 |
| `reports/G2_MISSION_REPORT_20261002.md` | REPORT/EVIDENCE | 2026-10-03 | 13484 | 0 |
| `reports/GOAL_STATUS_WINDOWS_PAPER_ONLY_20260828.md` | REPORT/EVIDENCE | 2026-08-28 | 1134 | 0 |
| `reports/LATEST_WINDOWS_GATE.txt` | REPORT/EVIDENCE | untracked/— | 266 | 0 |
| `reports/N8N_LIVE_SMOKE_TEST_EVIDENCE.txt` | REPORT/EVIDENCE | 2026-08-16 | 3482 | 0 |
| `reports/ORPHAN_ANALYSIS_W36.md` | REPORT/EVIDENCE | 2026-08-20 | 4401 | 0 |
| `reports/OWNER_CARD_WEB_API_AUTH_PRE_SOAK_FA.md` | REPORT/EVIDENCE | 2026-08-29 | 1064 | 0 |
| `reports/OWNER_PASTE_WINDOWS_GATE.txt` | REPORT/EVIDENCE | untracked/— | 8470 | 0 |
| `reports/OWNER_PASTE_WINDOWS_GATE_SLIM.txt` | REPORT/EVIDENCE | untracked/— | 619 | 0 |
| `reports/PHASE_STATE.md` | REPORT/EVIDENCE | 2026-10-03 | 40918 | 0 |
| `reports/PRE_SOAK_STATUS.txt` | REPORT/EVIDENCE | untracked/— | 1423 | 0 |
| `reports/QA_REPORT_FINAL.md` | REPORT/EVIDENCE | 2026-08-16 | 3020 | 0 |
| `reports/TELEGRAM_INTEGRATION_TEST_REPORT.md` | REPORT/EVIDENCE | 2026-08-16 | 2749 | 0 |
| `reports/TELEGRAM_RESEARCH_REPORT.md` | REPORT/EVIDENCE | 2026-08-16 | 2345 | 0 |
| `reports/TEST_REPORT_FINAL.md` | REPORT/EVIDENCE | 2026-08-16 | 5008 | 0 |
| `reports/W44_INTELLIGENCE_SPEED_UPGRADE.md` | REPORT/EVIDENCE | 2026-08-21 | 2582 | 0 |
| `reports/W45_TELEGRAM_CONVERSATIONAL_INTELLIGENCE_UPGRADE.md` | REPORT/EVIDENCE | 2026-08-21 | 5761 | 0 |
| `reports/WAVE5_EXECUTION_REPORT.md` | REPORT/EVIDENCE | 2026-08-16 | 6792 | 0 |
| `reports/WAVE6_EXECUTION_REPORT.md` | REPORT/EVIDENCE | 2026-08-16 | 3459 | 0 |
| `reports/WAVE7_EXECUTION_REPORT.md` | REPORT/EVIDENCE | 2026-08-16 | 5947 | 0 |
| `reports/agi_aci_evolution/AUDIT_REPORT.md` | REPORT/EVIDENCE | 2026-09-09 | 6502 | 0 |
| `reports/agi_aci_evolution/CAPABILITY_MATRIX.md` | REPORT/EVIDENCE | 2026-09-13 | 6099 | 0 |
| `reports/agi_aci_evolution/COGNITIVE_LOOP_AUDIT.md` | REPORT/EVIDENCE | 2026-09-09 | 3373 | 0 |
| `reports/agi_aci_evolution/COGNITIVE_LOOP_BENCHMARK.md` | REPORT/EVIDENCE | 2026-09-09 | 2234 | 0 |
| `reports/agi_aci_evolution/COGNITIVE_LOOP_IMPLEMENTATION_EVIDENCE.md` | REPORT/EVIDENCE | 2026-09-09 | 2186 | 0 |
| `reports/agi_aci_evolution/EVOLUTION_INDEX.md` | REPORT/EVIDENCE | 2026-09-13 | 4924 | 0 |
| `reports/agi_aci_evolution/EVOLUTION_RECORD_0001.md` | REPORT/EVIDENCE | 2026-09-09 | 1310 | 0 |
| `reports/agi_aci_evolution/EVOLUTION_RECORD_0002.md` | REPORT/EVIDENCE | 2026-09-09 | 1615 | 0 |
| `reports/agi_aci_evolution/EVOLUTION_RECORD_0003.md` | REPORT/EVIDENCE | 2026-09-09 | 2035 | 0 |
| `reports/agi_aci_evolution/EVOLUTION_RECORD_0004.md` | REPORT/EVIDENCE | 2026-09-09 | 2471 | 0 |
| `reports/agi_aci_evolution/EVOLUTION_RECORD_0005.md` | REPORT/EVIDENCE | 2026-09-09 | 2305 | 0 |
| `reports/agi_aci_evolution/EVOLUTION_RECORD_0006.md` | REPORT/EVIDENCE | 2026-09-09 | 2555 | 0 |
| `reports/agi_aci_evolution/EVOLUTION_RECORD_0007.md` | REPORT/EVIDENCE | 2026-09-09 | 2314 | 0 |
| `reports/agi_aci_evolution/EVOLUTION_RECORD_0008.md` | REPORT/EVIDENCE | 2026-09-09 | 1074 | 0 |
| `reports/agi_aci_evolution/EVOLUTION_RECORD_0009.md` | REPORT/EVIDENCE | 2026-09-09 | 921 | 0 |
| `reports/agi_aci_evolution/EVOLUTION_RECORD_0010.md` | REPORT/EVIDENCE | 2026-09-09 | 1068 | 0 |
| `reports/agi_aci_evolution/LANE_A_CHANGE_PROPOSAL.md` | REPORT/EVIDENCE | 2026-09-09 | 568 | 0 |
| `reports/agi_aci_evolution/MEMORY_IMPLEMENTATION_EVIDENCE.md` | REPORT/EVIDENCE | 2026-09-09 | 1503 | 0 |
| `reports/agi_aci_evolution/P4_1_BENCHMARK_AUDIT.md` | REPORT/EVIDENCE | 2026-09-09 | 1916 | 0 |
| `reports/agi_aci_evolution/P4_1_COGNITIVE_BENCHMARK_REPORT.md` | REPORT/EVIDENCE | 2026-09-09 | 5507 | 0 |
| `reports/agi_aci_evolution/P4_2_RETRIEVAL_BENCHMARK_REPORT.md` | REPORT/EVIDENCE | 2026-09-09 | 5860 | 0 |
| `reports/agi_aci_evolution/P4_2_RETRIEVAL_RELEVANCE_AUDIT.md` | REPORT/EVIDENCE | 2026-09-09 | 5421 | 0 |
| `reports/agi_aci_evolution/P4_3_LOOKALIKE_DISCRIMINATION_AUDIT.md` | REPORT/EVIDENCE | 2026-09-09 | 3372 | 0 |
| `reports/agi_aci_evolution/P4_3_RETRIEVAL_BENCHMARK_REPORT.md` | REPORT/EVIDENCE | 2026-09-09 | 3916 | 0 |
| `reports/agi_aci_evolution/P5_FINAL_BOUNDARY_AUDIT.md` | REPORT/EVIDENCE | 2026-09-10 | 27671 | 0 |
| `reports/agi_aci_evolution/P5_FINAL_CLOSURE_GATE_REVIEW.md` | REPORT/EVIDENCE | 2026-09-11 | 24238 | 0 |
| `reports/agi_aci_evolution/P5_FIX_CORRECTION_REPORT.md` | REPORT/EVIDENCE | 2026-09-09 | 5625 | 0 |
| `reports/agi_aci_evolution/P5_MEMORY_AUTHORIZATION_BOUNDARY_AUDIT.md` | REPORT/EVIDENCE | 2026-09-10 | 20054 | 0 |
| `reports/agi_aci_evolution/P5_MEMORY_AUTHORIZATION_BOUNDARY_V2.md` | REPORT/EVIDENCE | 2026-09-10 | 23257 | 0 |
| `reports/agi_aci_evolution/P5_NEGATION_ENTITY_REMEDIATION_REPORT.md` | REPORT/EVIDENCE | 2026-09-10 | 17183 | 0 |
| `reports/agi_aci_evolution/P5_OBSERVATIONGRANT_IMPLEMENTATION_REPORT.md` | REPORT/EVIDENCE | 2026-09-10 | 14021 | 0 |
| `reports/agi_aci_evolution/P5_OBSERVATIONGRANT_THREAT_MODEL.md` | REPORT/EVIDENCE | 2026-09-10 | 28036 | 0 |
| `reports/agi_aci_evolution/P5_PRECISION_REMEDIATION_REPORT.md` | REPORT/EVIDENCE | 2026-09-09 | 2399 | 0 |
| `reports/agi_aci_evolution/P5_TYPED_EVIDENCE_REASONING_AUDIT.md` | REPORT/EVIDENCE | 2026-09-09 | 6743 | 0 |
| `reports/agi_aci_evolution/P5_TYPED_EVIDENCE_REASONING_BENCHMARK.md` | REPORT/EVIDENCE | 2026-09-09 | 3485 | 0 |
| `reports/agi_aci_evolution/P5_V3_IMPLEMENTATION_REPORT.md` | REPORT/EVIDENCE | 2026-09-11 | 12530 | 0 |
| `reports/agi_aci_evolution/P5_V4_AUTHORITY_CONSTRUCTION_BOUNDARY.md` | REPORT/EVIDENCE | 2026-09-11 | 33724 | 0 |
| `reports/agi_aci_evolution/P5_V4_FINAL_RESIDUAL_BOUNDARY_REVIEW.md` | REPORT/EVIDENCE | 2026-09-11 | 17313 | 0 |
| `reports/agi_aci_evolution/P5_V4_IMPLEMENTATION_REPORT.md` | REPORT/EVIDENCE | 2026-09-11 | 18327 | 0 |
| `reports/agi_aci_evolution/PR93_DOCUMENTATION_RECONCILIATION_VALIDATION.md` | REPORT/EVIDENCE | 2026-09-11 | 6162 | 0 |
| `reports/agi_aci_evolution/PR93_FINAL_POST_RECONCILIATION_INTEGRITY_AUDIT.md` | REPORT/EVIDENCE | 2026-09-11 | 10574 | 0 |
| `reports/agi_aci_evolution/PR93_INDEPENDENT_PRE_REVIEW_INTEGRITY_AUDIT.md` | REPORT/EVIDENCE | 2026-09-11 | 22388 | 0 |
| `reports/agi_aci_evolution/SELF_RESEARCH_FINDINGS.md` | REPORT/EVIDENCE | 2026-09-09 | 1439 | 0 |
| `reports/agi_aci_evolution/TEST_EVIDENCE.md` | REPORT/EVIDENCE | 2026-09-13 | 7751 | 0 |
| `reports/e01_experimental_validation_report_20260814.md` | REPORT/EVIDENCE | 2026-08-16 | 8875 | 0 |
| `reports/e01_experimental_validation_report_20260815.md` | REPORT/EVIDENCE | 2026-08-16 | 5235 | 0 |
| `reports/e01_gate_cohort_report_20260814.md` | REPORT/EVIDENCE | 2026-08-16 | 3137 | 0 |
| `reports/e01_gate_cohort_report_20260815.md` | REPORT/EVIDENCE | 2026-08-16 | 2289 | 0 |
| `reports/grok/DASHBOARD_ONECLICK_REALITY.md` | REPORT/EVIDENCE | 2026-10-02 | 5382 | 0 |
| `reports/grok/DOCKER_N8N_DEPENDENCY_MAP.md` | REPORT/EVIDENCE | 2026-10-02 | 6934 | 0 |
| `reports/grok/G11_LIVE_E2E_RUNBOOK.md` | REPORT/EVIDENCE | 2026-10-02 | 8165 | 0 |
| `reports/grok/GM04_TELEGRAM_CONTROL_CAPABILITY_GATE_PROPOSAL.md` | REPORT/EVIDENCE | 2026-10-02 | 15089 | 0 |
| `reports/grok/GM06_N8N_QUARANTINE.md` | REPORT/EVIDENCE | 2026-10-02 | 3786 | 0 |
| `reports/grok/GM09_PROVIDER_STATUS_AND_CREDENTIAL_STORE.md` | REPORT/EVIDENCE | 2026-10-02 | 8592 | 0 |
| `reports/grok/LAUNCHER_ICON_NOTE.md` | REPORT/EVIDENCE | 2026-10-03 | 2196 | 0 |
| `reports/grok/MISSION_DISCOVERY_2026-10-02.md` | REPORT/EVIDENCE | 2026-10-02 | 13032 | 0 |
| `reports/grok/REMAINING_REALITY_REGISTER.md` | REPORT/EVIDENCE | 2026-10-03 | 37197 | 0 |
| `reports/grok/TELEGRAM_REALITY_MAP.md` | REPORT/EVIDENCE | 2026-10-02 | 8237 | 0 |
| `reports/grok/UNIVERSITY_AND_AGENTS_DISCOVERY.md` | REPORT/EVIDENCE | 2026-10-03 | 24686 | 0 |
| `reports/grok/_claude_10_result.txt` | REPORT/EVIDENCE | untracked/— | 6118 | 0 |
| `reports/grok/_claude_10_runlog.txt` | REPORT/EVIDENCE | untracked/— | 191 | 0 |
| `reports/grok/_claude_11_result.txt` | REPORT/EVIDENCE | untracked/— | 946 | 0 |
| `reports/grok/_claude_11_result_fail1.txt` | REPORT/EVIDENCE | untracked/— | 1002 | 0 |
| `reports/grok/_claude_11_result_fail2.txt` | REPORT/EVIDENCE | untracked/— | 1002 | 0 |
| `reports/grok/_claude_11_result_fail3.txt` | REPORT/EVIDENCE | untracked/— | 1002 | 0 |
| `reports/grok/_claude_11_result_fail4.txt` | REPORT/EVIDENCE | untracked/— | 1110 | 0 |
| `reports/grok/_claude_11_result_fail5.txt` | REPORT/EVIDENCE | untracked/— | 1110 | 0 |
| `reports/grok/_claude_11_result_fail6.txt` | REPORT/EVIDENCE | untracked/— | 1110 | 0 |
| `reports/grok/_claude_11_runlog.txt` | REPORT/EVIDENCE | untracked/— | 650 | 0 |
| `reports/grok/_claude_8_result.txt` | REPORT/EVIDENCE | untracked/— | 5048 | 0 |
| `reports/grok/_claude_8_result_fail1.txt` | REPORT/EVIDENCE | untracked/— | 2086 | 0 |
| `reports/grok/_claude_8_result_firstattempt.txt` | REPORT/EVIDENCE | untracked/— | 2144 | 0 |
| `reports/grok/_claude_8_runlog.txt` | REPORT/EVIDENCE | untracked/— | 178 | 0 |
| `reports/grok/_claude_9_5_result.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_5_result_fail1.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_5_result_fail10.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_5_result_fail11.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_5_result_fail12.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_5_result_fail2.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_5_result_fail3.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_5_result_fail4.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_5_result_fail5.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_5_result_fail6.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_5_result_fail7.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_5_result_fail8.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_5_result_fail9.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_5_runlog.txt` | REPORT/EVIDENCE | untracked/— | 545 | 0 |
| `reports/grok/_claude_9_6_result.txt` | REPORT/EVIDENCE | untracked/— | 3870 | 0 |
| `reports/grok/_claude_9_6_result_fail1.txt` | REPORT/EVIDENCE | untracked/— | 1002 | 0 |
| `reports/grok/_claude_9_6_result_fail2.txt` | REPORT/EVIDENCE | untracked/— | 1002 | 0 |
| `reports/grok/_claude_9_6_result_fail3.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_6_result_fail4.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_6_result_fail5.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_6_result_fail6.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_6_result_fail7.txt` | REPORT/EVIDENCE | untracked/— | 1254 | 0 |
| `reports/grok/_claude_9_6_runlog.txt` | REPORT/EVIDENCE | untracked/— | 591 | 0 |
| `reports/grok/_claude_9_result.txt` | REPORT/EVIDENCE | untracked/— | 3862 | 0 |
| `reports/grok/_claude_9_result_fail1.txt` | REPORT/EVIDENCE | untracked/— | 1002 | 0 |
| `reports/grok/_claude_9_runlog.txt` | REPORT/EVIDENCE | untracked/— | 178 | 0 |
| `reports/grok/_claude_phase8_result.txt` | REPORT/EVIDENCE | untracked/— | 2334 | 0 |
| `reports/grok/_probe_err.txt` | REPORT/EVIDENCE | untracked/— | 0 | 0 |
| `reports/grok/_probe_out.txt` | REPORT/EVIDENCE | untracked/— | 0 | 0 |
| `reports/grok/reviews/LOCAL_COMMITS_5_HARDMODE_REVIEW.md` | REPORT/EVIDENCE | 2026-10-03 | 26393 | 0 |
| `reports/grok/reviews/REDTEAM_19_LOCAL_COMMITS_20261002-2313.md` | REPORT/EVIDENCE | 2026-10-03 | 11612 | 0 |
| `reports/m9/BASELINE.md` | REPORT/EVIDENCE | 2026-10-03 | 4435 | 0 |
| `reports/m9/IMPORT_SIDE_EFFECTS.md` | REPORT/EVIDENCE | 2026-10-03 | 5863 | 0 |
| `reports/m9/batch_00.txt` | REPORT/EVIDENCE | untracked/— | 530 | 0 |
| `reports/m9/batch_01.txt` | REPORT/EVIDENCE | untracked/— | 605 | 0 |
| `reports/m9/batch_02.txt` | REPORT/EVIDENCE | untracked/— | 601 | 0 |
| `reports/m9/batch_03.txt` | REPORT/EVIDENCE | untracked/— | 553 | 0 |
| `reports/m9/batch_04.txt` | REPORT/EVIDENCE | untracked/— | 593 | 0 |
| `reports/m9/batch_05.txt` | REPORT/EVIDENCE | untracked/— | 627 | 0 |
| `reports/m9/batch_06.txt` | REPORT/EVIDENCE | untracked/— | 651 | 0 |
| `reports/m9/batch_07.txt` | REPORT/EVIDENCE | untracked/— | 640 | 0 |
| `reports/m9/batch_08.txt` | REPORT/EVIDENCE | untracked/— | 609 | 0 |
| `reports/m9/batch_09.txt` | REPORT/EVIDENCE | untracked/— | 587 | 0 |
| `reports/m9/batch_10.txt` | REPORT/EVIDENCE | untracked/— | 460 | 0 |
| `reports/m9/testfiles.txt` | REPORT/EVIDENCE | untracked/— | 6273 | 0 |
| `reports/m9_6/pytest_95_static.txt` | REPORT/EVIDENCE | 2026-10-03 | 275 | 0 |
| `reports/m9_6/receipts_95.txt` | REPORT/EVIDENCE | 2026-10-03 | 1433 | 0 |
| `reports/periodic_report_20260812.txt` | REPORT/EVIDENCE | 2026-08-16 | 1569 | 0 |
| `reports/periodic_report_20260812_080522.txt` | REPORT/EVIDENCE | 2026-08-16 | 1403 | 0 |
| `reports/periodic_report_20260812_084219.txt` | REPORT/EVIDENCE | 2026-08-16 | 3922 | 0 |
| `reports/periodic_report_20260813_005513.txt` | REPORT/EVIDENCE | 2026-08-16 | 3922 | 0 |
| `reports/periodic_report_20260813_010556.txt` | REPORT/EVIDENCE | 2026-08-16 | 3922 | 0 |
| `reports/periodic_report_20260813_012214.txt` | REPORT/EVIDENCE | 2026-08-16 | 3922 | 0 |
| `reports/periodic_report_20260813_015526.txt` | REPORT/EVIDENCE | 2026-08-16 | 3922 | 0 |
| `reports/periodic_report_20260813_025748.txt` | REPORT/EVIDENCE | 2026-08-16 | 3922 | 0 |
| `reports/periodic_report_20260813_032731.txt` | REPORT/EVIDENCE | 2026-08-16 | 3922 | 0 |
| `reports/periodic_report_20260813_034259.txt` | REPORT/EVIDENCE | 2026-08-16 | 3922 | 0 |
| `reports/periodic_report_20260813_040157.txt` | REPORT/EVIDENCE | 2026-08-16 | 3923 | 0 |
| `reports/periodic_report_20260813_043935.txt` | REPORT/EVIDENCE | 2026-08-16 | 3924 | 0 |
| `reports/periodic_report_20260813_052451.txt` | REPORT/EVIDENCE | 2026-08-16 | 3925 | 0 |
| `reports/periodic_report_20260813_053443.txt` | REPORT/EVIDENCE | 2026-08-16 | 3925 | 0 |
| `reports/periodic_report_20260814_050006.txt` | REPORT/EVIDENCE | 2026-08-16 | 3925 | 0 |
| `reports/periodic_report_20260814_051716.txt` | REPORT/EVIDENCE | 2026-08-16 | 3925 | 0 |
| `reports/phase21_execution_report.md` | REPORT/EVIDENCE | 2026-08-16 | 7558 | 0 |
| `reports/phase21_production_readiness.md` | REPORT/EVIDENCE | 2026-10-03 | 5460 | 0 |
| `reports/phase21_reality_audit.md` | REPORT/EVIDENCE | 2026-10-03 | 8163 | 0 |
| `reports/phase22_global_intelligence_audit.md` | REPORT/EVIDENCE | 2026-10-03 | 5060 | 0 |
| `reports/phase22_global_intelligence_execution.md` | REPORT/EVIDENCE | 2026-08-16 | 10932 | 0 |
| `reports/phase24_operational_activation_report.md` | REPORT/EVIDENCE | 2026-10-03 | 8694 | 0 |
| `reports/pt_x3_v2_24h_report_20260814.md` | REPORT/EVIDENCE | 2026-08-16 | 2431 | 0 |
| `reports/telegram_e2e/telegram_e2e_20261002T1221Z.md` | REPORT/EVIDENCE | untracked/— | 1002 | 0 |
| `reports/telegram_e2e_20260909_165348.md` | REPORT/EVIDENCE | 2026-09-09 | 4585 | 0 |
| `reports/validate_imports_run_20261002_phase8.txt` | REPORT/EVIDENCE | untracked/— | 471 | 0 |
| `reports/web_api_auth_e2e_agent_host.md` | REPORT/EVIDENCE | 2026-08-28 | 1013 | 0 |
| `reports/windows_db_state_b_classification.md` | REPORT/EVIDENCE | 2026-08-28 | 2502 | 0 |
| `reports/windows_gate_evidence/LATEST_WINDOWS_GATE.txt` | REPORT/EVIDENCE | 2026-08-30 | 242 | 0 |
| `reports/windows_gate_evidence/OWNER_PASTE_20260828_215716.txt` | REPORT/EVIDENCE | 2026-08-29 | 4444 | 0 |
| `reports/windows_gate_evidence/OWNER_PASTE_20260828_220220.txt` | REPORT/EVIDENCE | 2026-08-29 | 5606 | 0 |
| `reports/windows_gate_evidence/OWNER_PASTE_20260828_220318.txt` | REPORT/EVIDENCE | 2026-08-29 | 7961 | 0 |
| `reports/windows_gate_evidence/OWNER_PASTE_WINDOWS_GATE.txt` | REPORT/EVIDENCE | 2026-08-30 | 8483 | 0 |
| `reports/windows_gate_evidence/OWNER_PASTE_WINDOWS_GATE_SLIM.txt` | REPORT/EVIDENCE | 2026-08-30 | 632 | 0 |
| `reports/windows_gate_evidence/README_EVIDENCE.md` | REPORT/EVIDENCE | 2026-08-30 | 402 | 0 |
| `reports/windows_web_api_auth_harden_20260828.md` | REPORT/EVIDENCE | 2026-08-28 | 1287 | 0 |
| `research/reports/RESEARCH_FINDINGS_v2.0.md` | REPORT/EVIDENCE | 2026-08-16 | 6932 | 0 |
| `research/reports/RESEARCH_META_ANALYSIS_v1.md` | REPORT/EVIDENCE | 2026-08-16 | 6480 | 0 |
| `scripts/WINDOWS_EVIDENCE_INBOX_LIVE.txt` | REPORT/EVIDENCE | 2026-08-28 | 402 | 0 |
| `scripts/WINDOWS_EVIDENCE_INBOX_OPEN_SINK.txt` | REPORT/EVIDENCE | 2026-08-28 | 438 | 0 |
| `scripts/WINDOWS_EVIDENCE_INBOX_STAY_OPEN.txt` | REPORT/EVIDENCE | 2026-08-28 | 530 | 0 |
| `AHOS_SELF_REPAIR_DESIGN.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 1671 | 1 |
| `ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-18 | 2115 | 0 |
| `architecture/knowledge/EVIDENCE_GRAPH.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-12 | 1838 | 2 |
| `architecture/knowledge/FEEDBACK.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-12 | 2572 | 4 |
| `docs/ARCHITECTURE_FINAL.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 3753 | 3 |
| `docs/CANONICAL_COMMAND_REFERENCE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-26 | 8834 | 3 |
| `docs/CANONICAL_IMPLEMENTATION_MATRIX.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-10-03 | 11462 | 3 |
| `docs/COUNCIL_15_DESIGN.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 2218 | 2 |
| `docs/OPPORTUNITY_SCORE_DESIGN_v0.1.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 3046 | 1 |
| `docs/SECURITY_CHECKLIST.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-27 | 2839 | 1 |
| `docs/SECURITY_SCORE_DESIGN_v0.1.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 1478 | 1 |
| `docs/STRATEGY_SPEC_v1.0.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 2016 | 3 |
| `docs/TARGET_ARCHITECTURE_vNext.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 2408 | 0 |
| `docs/TELEGRAM_PERSIAN_UX_DESIGN.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 2575 | 0 |
| `docs/agents/AGENT_ORGANIZATION_README.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 4891 | 4 |
| `docs/agents/PLANNED_19_AGENT_MAP.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 4331 | 0 |
| `docs/architecture/AGENT_01_ORGANIZATIONAL_FEDERATION_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 28440 | 6 |
| `docs/architecture/AGENT_01_ORGANIZATIONAL_FEDERATION_READINESS_MATRIX.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 8919 | 4 |
| `docs/architecture/AGENT_05_EPISTEMIC_REASONING_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 51074 | 39 |
| `docs/architecture/AGENT_06_RESEARCH_METHODOLOGY_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 60365 | 44 |
| `docs/architecture/AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 74242 | 47 |
| `docs/architecture/AGENT_08_CRYPTO_MARKET_INTELLIGENCE_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 70599 | 25 |
| `docs/architecture/AGENT_09_ON_CHAIN_INTELLIGENCE_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 63398 | 25 |
| `docs/architecture/AGENT_10_TOKEN_SECURITY_SCAM_INTELLIGENCE_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 64244 | 13 |
| `docs/architecture/AGENT_11_RISK_INTELLIGENCE_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 59899 | 27 |
| `docs/architecture/AGENT_12_QUANTITATIVE_INTELLIGENCE_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 51141 | 13 |
| `docs/architecture/AGENT_13_AI_ML_INTELLIGENCE_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 61292 | 28 |
| `docs/architecture/AGENT_14_AGENT_RUNTIME_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 57759 | 20 |
| `docs/architecture/AGENT_14_RUNTIME_FOUNDATION_RECONCILIATION_AND_MVOR_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 49868 | 19 |
| `docs/architecture/AGENT_15_PROMPT_INSTRUCTION_DELEGATION_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 71173 | 36 |
| `docs/architecture/AGENT_17_HUMAN_AGENT_ORGANIZATION_UX_AND_PRODUCT_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 57440 | 33 |
| `docs/architecture/AGENT_18_FRONTEND_VISUALIZATION_AND_TRUST_INTERFACE_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 97670 | 38 |
| `docs/architecture/AGENT_ORGANIZATION_SECURITY_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 45016 | 7 |
| `docs/architecture/AHOS_COGNITIVE_BENCHMARK_ARCHITECTURE_v1.0.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-09 | 2112 | 2 |
| `docs/architecture/AHOS_COGNITIVE_LOOP_ARCHITECTURE_v1.0.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-09 | 9280 | 5 |
| `docs/architecture/AHOS_COGNITIVE_MEMORY_ARCHITECTURE_v1.0.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-09 | 3742 | 2 |
| `docs/architecture/AHOS_RUNTIME_ARCHITECTURE_v1.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 16732 | 2 |
| `docs/architecture/OSS_CAPABILITY_DISCOVERY.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 3969 | 1 |
| `docs/architecture/PROCESS_ISOLATED_RESEARCH_WORKER.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 1899 | 0 |
| `docs/architecture/PRODUCTION_RUNTIME_SPEC.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 5173 | 0 |
| `docs/architecture/PRODUCTION_SCHEDULER_SPEC.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 2759 | 5 |
| `docs/architecture/RESEARCH_AGENT_HOST.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 3050 | 0 |
| `docs/architecture/RESEARCH_ANALYST_AGENT.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 4803 | 7 |
| `docs/architecture/SELF_EVOLUTION_LOOP.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 3814 | 3 |
| `docs/architecture/SLICE_2A_EPISTEMIC_CORE_AND_TCB_SPEC.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 22191 | 23 |
| `docs/architecture/SLICE_2B_DEFERRED_DECISIONS_ADR.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 2947 | 1 |
| `docs/architecture/SLICE_2B_IMPLEMENTATION_REPORT.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 14682 | 5 |
| `docs/architecture/SLICE_2B_REMEDIATION_01_IMPLEMENTATION_VS_SPEC.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 15911 | 2 |
| `docs/architecture/agent_matrix_v2.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 32411 | 1 |
| `docs/architecture/ai_council_architecture.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 4791 | 3 |
| `docs/architecture/cognitive_agent_fabric.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 3485 | 2 |
| `docs/architecture/cognitive_agent_mapping_w10.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 24064 | 10 |
| `docs/architecture/cognitive_agent_runtime_matrix.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 4985 | 0 |
| `docs/architecture/cognitive_principle_matrix.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 5471 | 2 |
| `docs/architecture/orchestration_comparison.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 3255 | 1 |
| `docs/architecture/pg_parity_audit_w9.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-20 | 2589 | 1 |
| `docs/architecture/runtime_dependency_graph.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 3081 | 1 |
| `docs/architecture/single_start_runtime.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 2654 | 5 |
| `docs/canonical/AGENT_COUNCIL.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 1296 | 1 |
| `docs/canonical/ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 1717 | 0 |
| `docs/canonical/DATA_MODEL.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 1636 | 1 |
| `docs/canonical/DISCOVERY.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 1526 | 0 |
| `docs/canonical/EXECUTION_STATE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-28 | 4755 | 2 |
| `docs/canonical/KNOWLEDGE_MAP.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-28 | 50117 | 12 |
| `docs/canonical/PROJECT_STATE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-28 | 3356 | 0 |
| `docs/canonical/PROVIDERS.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-20 | 2209 | 3 |
| `docs/canonical/RESEARCH.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 1373 | 1 |
| `docs/canonical/TELEGRAM.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-08-16 | 1289 | 0 |
| `docs/engineering/ALERTS_WEB_BANNER.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-09 | 812 | 1 |
| `docs/engineering/CANONICAL_OVERLAY_CENSUS.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-09 | 1523 | 0 |
| `docs/engineering/GECKO_PAIR_CREATED_TS_E2E.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-09 | 3047 | 0 |
| `docs/engineering/PHASE0_MASTER_AUDIT_AND_FOUNDATION.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-09 | 11884 | 7 |
| `docs/engineering/PHASE1_CANONICAL_IDENTITY.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-03 | 5487 | 0 |
| `docs/engineering/PHASE2_SECURITY_GATE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-09 | 15155 | 6 |
| `docs/engineering/PHASE3_CANONICAL_DECISION.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-09 | 15488 | 5 |
| `docs/engineering/SKILL_REGISTRY.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-08 | 1812 | 0 |
| `docs/engineering/TELEGRAM_HTML_ESCAPE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-09 | 1470 | 0 |
| `docs/protocols/AGENT_COMMUNICATION_PROTOCOL.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 3096 | 5 |
| `docs/protocols/AGENT_ESCALATION_PROTOCOL.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 2101 | 2 |
| `docs/protocols/AGENT_EVIDENCE_PROTOCOL.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 2863 | 3 |
| `docs/protocols/AGENT_RESPONSE_PROTOCOL.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 2533 | 3 |
| `docs/protocols/AGENT_SUPERVISION_PROTOCOL.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 2526 | 7 |
| `docs/security/AGENT_19_RED_TEAM_AND_ADVERSARIAL_ORGANIZATIONAL_SECURITY_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-15 | 67241 | 12 |
| `docs/supervision/SUPERVISION_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-12 | 7573 | 5 |
| `reports/agi_aci_evolution/ARCHITECTURE_MAP.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-13 | 3002 | 2 |
| `reports/agi_aci_evolution/MEMORY_ARCHITECTURE_AUDIT.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-09 | 2015 | 1 |
| `reports/agi_aci_evolution/P5_EPISODE_POLARITY_ARCHITECTURE_REPORT.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-10 | 13062 | 6 |
| `reports/agi_aci_evolution/P5_HYBRID_D_V3_REMEDIATION_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-11 | 37196 | 18 |
| `reports/agi_aci_evolution/P5_MEMORY_AUTHORIZATION_BOUNDARY_ARCHITECTURE_DESIGN.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-10 | 42876 | 33 |
| `reports/agi_aci_evolution/P5_V3_FINAL_REFINEMENT_ARCHITECTURE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-11 | 22836 | 21 |
| `reports/agi_aci_evolution/P5_V4_FINAL_SECRET_BOUNDARY_DESIGN.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-09-11 | 31046 | 31 |
| `reports/grok/GROK_SESSION_2026-10-02_REALITY_INSPECTION.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-10-02 | 11463 | 3 |
| `reports/grok/PHASE3_ARCHITECTURE_NOTE.md` | SUPPLEMENTARY/ANNEX (architecture/spec/protocol) | 2026-10-02 | 1493 | 0 |
| `reports/grok/OWNER_DIRECTIVE_TRACEABILITY.md` | TRACEABILITY/VISION (this matrix set; not re-split) | 2026-10-03 | 176613 | 0 |
| `AHOS_PHASE19_RELEASE_GATE.md` | UPDATE/CHANGE | 2026-08-20 | 11693 | 3 |
| `AHOS_UPDATE_POLICY.md` | UPDATE/CHANGE | 2026-08-16 | 1134 | 4 |
| `docs/protocols/AGENT_UPDATE_PROTOCOL.md` | UPDATE/CHANGE | 2026-09-15 | 3337 | 5 |
| `reports/grok/DECKER_N8N_MIGRATION.md` | UPDATE/CHANGE | 2026-10-03 | 26533 | 13 |

</details>

<details><summary>Removed docs (in history, not at HEAD)</summary>

- `01a00f79-b48c-7afb-87e7-3850b1bc66f5 (1).md` (last seen 2026-08-20) — REMOVED
- `01a01560-4c5e-7430-a0dd-8558799869d4.md` (last seen 2026-08-20) — REMOVED
- `01a015c9-a9ed-7bac-9220-3ad2d8321825.md` (last seen 2026-08-20) — REMOVED
- `OSS_AGENT_ARCHITECTURE_PLAN.md` (last seen 2026-08-19) — REMOVED
- `OSS_AHOS_MAPPING.md` (last seen 2026-08-19) — REMOVED
- `OSS_AI_PROVIDER_MAP.md` (last seen 2026-08-19) — REMOVED
- `OSS_BACKTEST_UPGRADE_PLAN.md` (last seen 2026-08-19) — REMOVED
- `OSS_CAPABILITY_MATRIX.md` (last seen 2026-08-19) — REMOVED
- `OSS_DATA_PROVIDER_MAP.md` (last seen 2026-08-19) — REMOVED
- `OSS_FINAL_RECOMMENDATION.md` (last seen 2026-08-19) — REMOVED
- `OSS_INTEGRATION_BACKLOG.md` (last seen 2026-08-19) — REMOVED
- `OSS_INTEGRATION_PLAN.md` (last seen 2026-08-19) — REMOVED
- `OSS_LICENSE_SECURITY_AUDIT.md` (last seen 2026-08-19) — REMOVED
- `OSS_REJECTED_PROJECTS.md` (last seen 2026-08-19) — REMOVED
- `OSS_TOP20_RESEARCH.md` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w12_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w12r_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w13_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w13b_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w13c_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w13d_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w14_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w15_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w15b_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w15c_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w16_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w17_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w18_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w19_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w20_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w21_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w22_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w24_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w25_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w26_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w27_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w28_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w29_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w30_after.txt` (last seen 2026-08-19) — REMOVED
- `ahos_snap_w31_after.txt` (last seen 2026-08-19) — REMOVED
- `marge4.md` (last seen 2026-08-20) — REMOVED

</details>

## 2. Supersession register — ثبت جایگزینی‌ها

| Older statement (source) | Status | Newer source that wins |
|---|---|---|
| Plan 18:47 'double-click → Docker/DB up' (OWNER_DIRECTIVE_MISSION_PLAN.md / .v2) | SUPERSEDED | 18:49 remove Docker/n8n; decision 2026-10-03; CH-01 |
| Original mission list numbering (M10 identity/provenance, M11 agent org) | SUPERSEDED | Owner order 2026-10-02 18:49 (authoritative) |
| Decision 2026-10-03 'native portable PostgreSQL via pg_ctl' | SUPERSEDED (kept as fallback) | M10 d80b5b7 PGlite + 7ace415 parity (D3) |
| P2§93 roadmap phase order crypto→…→gold (OD-416) | SUPERSEDED (priority) | OWN-18 gold first on paper (D4) |
| docs/n8n_setup_guide.md, docker-compose.yml, n8n/workflows/* as runtime requirements | SUPERSEDED | M10 de-Docker/de-n8n; files archived, not deleted; GM-06 quarantine (8e48cf3) |
| database/postgresql_schema.sql as canonical schema | SUPERSEDED | D6 |
| docs/archive/** (consolidation 2026-09-26, 170+ docs) | SUPERSEDED (historical) | docs/archive/consolidation_2026-09-26/MANIFEST.md; current docs in docs/canonical, docs/governance |
| Twelve older readiness/truth maps bannered STALE by M9 (d2aa09b) | SUPERSEDED | reports/grok/REMAINING_REALITY_REGISTER.md |
| docs/canonical/MASTER_DIRECTIVE_v1.md vs MASTER_DIRECTIVE_W43.md | v1 superseded where W43 restates it; Class A rules never demoted (per the docs' own text) | MASTER_DIRECTIVE_W43.md, master_directive_registry.json |
| OD CREDAG/FINXFER transfer design (P1§30–31) | SUPERSEDED (refined) | AHOS_AUTONOMOUS_VISION.md §7 treasury + M22/M27 (D11) |
| OD LIFE maturity states (P1§14) | SUPERSEDED (maturity axis) | AHOS_AUTONOMOUS_VISION.md §2.3 lifecycle (D12) |
| The "do not touch architecture/ " rule was the Phase 18 scope grant, and (`AHOS_PHASE19_RELEASE_GATE.md:97`, 2026-08-20) | SUPERSEDED | Phase-specific scope grants expired with their phase; current scope = OWNER_DIRECTIVE_MISSION_PLAN.md mission definitions |
| Tomorrow (host exists): the same surface wraps docker compose + Temporal; the operator NEVER (`docs/architecture/single_start_runtime.md:9`, 2026-08-16) | SUPERSEDED | Owner update 2026-10-02 18:49 (remove Docker/n8n) + M10 Stage-1 decision d80b5b7 (embedded PGlite, verified to parity 7ace415); Docker volumes kept for rollback |

## 3. Contradictions — DECIDED (with both sources and the trust-order basis)

| # | Source A | Source B | Decision | Rationale (trust order / technical) |
|---|---|---|---|---|
| D1 | OWN-7 / OWN-21: live trade for all parts (OD-564, OD-578) | PAPER_ONLY locked rule (P1§28 OD LIVEOFF; governance) | **DECIDED: PAPER_ONLY stays.** Gold first on real market data with fake money (OWN-18); live only through the permission ladder with an explicit owner gate | Locked safety rule, not superseded by date. OWN-18 is the owner's own clarification |
| D2 | OWN-6: no permission needed for self-development (OD-563) | Governance gates P1A§16, constitution | **DECIDED:** full autonomy for safe reversible engineering (debug, refactor, tests, docs, local commits). Locked items stay gated | The newest owner statement wins except for the locked set |
| D3 | Owner decision 2026-10-03: M10 = native portable PostgreSQL (pg_ctl) | M10 Stage-1 decision d80b5b7: embedded PGlite, parity verified 7ace415 (newer, with evidence) | **DECIDED: keep PGlite** as the M10 store. Portable PG via pg_ctl stays the documented fallback if PGlite fails parity/performance. Docker volumes are kept untouched for rollback | PGlite needs no service, port or console window, so it matches CH-02 (no visible consoles) and the one-click goal. Repo reality (parity-tested) > earlier plan text. Both satisfy the owner's intent (no Docker, data outside git, local only) |
| D4 | P2§93 roadmap: crypto phases first, gold later (OD-416) | OWN-18: gold FIRST (OD-575, newer) | **DECIDED:** gold-paper track runs inside M13. The infrastructure mission order M9→M19 is unchanged | Newest owner statement wins on trading-line priority; the mission order is a separate, also owner-set axis |
| D5 | P2§48 / G32:26: Telegram is the secondary interface (OD-361) | OWN-36: same super-AI in Telegram and dashboard (OD-593) | **DECIDED:** one AI core (chat_agent.ts / gemini_chat.py) serves both surfaces; the dashboard stays canonical for state | Compatible once the AI core is shared; no second decision authority (TGCANON) |
| D6 | Postgres canonical (database/postgresql_schema.sql, older docs) | M9: SQLite canonical, Postgres never live; M10 PGlite | **DECIDED:** SQLite stores stay canonical; former Postgres tables live in PGlite. `postgresql_schema.sql` is historical | Repo reality > older docs |
| D7 | P1§15: agent count is not a goal (OD-034) | OWN-17 / OWN-25: add as many agents as needed; University proposes agents (newer) | **DECIDED:** add agents freely when a mission needs them, each with charter, boundary, evidence and lifecycle; count is never a KPI | Both are satisfied; the newer statement removes any cap |
| D8 | P1§106: preserve the 3D/web trees | No-duplicates rule + CH-03: extend CommandCenter.tsx/app | **DECIDED:** keep the trees as read-only design references; build only in CommandCenter.tsx/app (M17) | Preserves evidence while avoiding parallel UIs |
| D9 | Plan v2 / 18:47: launcher 'Docker/DB up' | 18:49 remove Docker + decision 2026-10-03 + CH-01 | **SUPERSEDED:** the launcher has no Docker | Newest owner statement |
| D11 | P1§30–31: credential agent for account opening, transfers and cash-out (OD CREDAG/FINXFER) | AHOS_AUTONOMOUS_VISION.md §6–§7, §11–§12 (2026-10-03, newer) | **DECIDED/SUPERSEDED:** the treasury/custody/withdrawal design in the vision doc replaces the earlier credential-agent transfer idea. It is built on testnet only (M22/M27); real funds stay locked behind G-L2 + owner signature | Newest owner statement; locked invariants INV-01/02/06/13 keep it gated |
| D12 | OD LIFE state list (REGISTERED→IDLE→…→WAITING_FOR_VERIFICATION) | AHOS_AUTONOMOUS_VISION.md §2.3 lifecycle (PROPOSED→CHARTERED→IN_UNIVERSITY→CERTIFIED→ACTIVE→PROBATION→RETIRED) | **DECIDED:** use the vision-doc lifecycle for agent maturity and keep the older states as runtime activity states inside ACTIVE | The newer owner doc wins on maturity; runtime activity states are still needed for observability |
| D13 | OA-05 $100→$1M in a month (owner, 20:20, newest) | Risk invariants, G-L2/G-L3 gates, quarter-Kelly cap (locked safety) | **DECIDED:** recorded as an aspirational North Star and capability benchmark with an honest dashboard panel and a $100 paper sandbox; it never changes risk caps, leverage or gates (INV-15) | Safety rules are locked regardless of date; the vision doc itself states this resolution |
| D10 | Original plan mission numbers (M10 identity, M11 agents) | Owner order 2026-10-02 18:49 | **SUPERSEDED:** use the 18:49 order | Newest owner statement |

No contradiction is left for the owner to answer. The locked items above stay HUMAN-GATE by rule: the owner may lift them explicitly, but agents never do.

## 4. North Star alignment — هم‌راستایی با ستاره شمالی (SI/AGI/ACI per Charter v1.0)

The Charter (`docs/architecture/AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md`, P2C rows) sets AGI/ACI as direction, not as a claim. Each mission below is mapped to the cognitive capability it actually builds. The VISION column is the target; the IMPLEMENTED column is what exists today.

| Mission | Charter capability advanced | VISION (target) | IMPLEMENTED today (honest) |
|---|---|---|---|
| M9 truth baseline (done) | Perception of self / reality grounding | AHOS knows its true state | register + baseline + 0 import side effects (629e757, 3b0da90, f056256) |
| M10 de-Docker (PGlite) | Robust memory substrate | durable local stores without external services | PGlite client + restore, parity verified (7ace415) |
| M11 one-click launcher | Embodiment / homeostasis | self-starting, self-checking organism | launcher package in progress (2270146, 9e74645) |
| M12 agents | Society of minds | lifecycle-managed specialist agents | 19 agents REGISTERED; registry + TCB exist; no lifecycle runtime |
| M13 paper + learning (+gold paper) | Learning from experience; calibration | closed loop outcome→lesson→calibration | code exists; 0 paper rows; not wired |
| M14 autonomous engineering core | Self-improvement under governance; self-evaluation | governed self-development with checkpoints and sign-off | ledger + provider status + intake exist; no controller |
| M15 contradictions + council | Multi-agent reasoning; metacognition | dissent-preserving calibrated council | council code + anti-echo tests; not on live decisions |
| M16 University / GitHub | Research, novelty, world model, knowledge acquisition | continuous research ecosystem | docs + self_research/oss_pipeline code; knowledge store 0 claims |
| M17 dashboard | Transparent cognition (explainability) | world-class honest cognitive UI | CommandCenter + truthfulness; 3D prototypes separate |
| M18 news / gold / accounting | Domain breadth | gold division, news intelligence, accounting | news module (credential-gated); no gold code; ledger exists |
| M19 multi-market / low latency / environment | Generalization across domains | multi-market, fast research path | not started |

### Capability-building items added (NS rows)

| ID | Requirement | Status | Evidence (extend these) | Mission |
|---|---|---|---|---|
| NS-01 | Closed learning loop: paper outcome → lesson → calibration → scoring-change proposal (never auto-promote) | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/{calibration,prediction_lifecycle,score_ledger}.py, 202f8c9 | M13 |
| NS-02 | Self-evaluation on every mission: cognitive benchmark + regression scorecard recorded in the mission ledger | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/benchmark/, scripts/run_cognitive_benchmark.py, architecture/mission/ledger.py | M14 |
| NS-03 | Persistent cognitive/organizational memory actually populated (episodic, semantic, failure, procedural) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite = 0 bytes (M9) | M14/M16 |
| NS-04 | Multi-agent reasoning with preserved dissent and calibrated aggregation | EXISTS-PARTIAL (reuse/extend) | architecture/ai/council_live.py, debate_council.py, architecture/knowledge/anti_echo.py, tests/test_multi_mind_council_anti_echo.py | M15 |
| NS-05 | Autonomous engineering under gates: a mission controller consumes the dev-mission queue → plan → build → test → review/sign-off → local commit, with checkpoints | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py (d1571c4), dev_missions.ts (d10383e), architecture/ai/mission_guard.py (b4e67be) | M14 |
| NS-06 | Metacognition: every answer carries confidence, unknowns and evidence links (no false certainty) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/metacognition.py, agent_org/epistemic.py | M15/M17 |
| NS-07 | World model updated from observations and outcomes | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/world_model.py | M16 |
| NS-08 | Novelty → research task → University → validated knowledge pipeline | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/novelty.py, self_research.py, architecture/knowledge/oss_pipeline.py | M16 |
| NS-09 | Governed self-improvement: proposals via evolution_gate with independent verification before adoption | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, contracts/improvement_proposal_contract_v1.json | M16 |
| NS-10 | Honest capability scorecard in the dashboard: each capability labeled VISION / DESIGN / IMPLEMENTED / TESTED / OPERATING | MISSING→added to plan | no UI; data in reports/grok/REMAINING_REALITY_REGISTER.md + this matrix | M17 |
| NS-11 | Cross-domain transfer: the same cognitive loop serves crypto, gold and later markets (no per-market forks) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ is domain-agnostic; gold/multi-market not wired | M13/M18/M19 |

## 5. Owner chat instructions 2026-10-03 (newest; they win over older statements)

| ID | Requirement | Status | Evidence | Mission |
|---|---|---|---|---|
| CH-01 | One-click desktop icon starts the whole of AHOS; no Docker | PLANNED | launcher package 2270146 + 9e74645 (M11, in progress by Claude); M10 PGlite removes the Docker need (d80b5b7, 7ace415) | M11 |
| CH-02 | No visible console windows when launching (hidden/windowless processes, status via dashboard/tray) | MISSING→added to plan | not verified in the repo; extend the M11 launcher package (pythonw / hidden window style), don't add a new launcher | M11 |
| CH-03 | Dashboard extremely beautiful and world-class, giving a feeling of super-intelligence; honest, no fake data; extend CommandCenter.tsx/app | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, dashboard_truth.ts (789dfa2 no fake OK/STALE); 3D prototypes in advanced-3d-audiovisual-website*, 01/src (consolidate) | M17 |
| CH-04 | Bot replies fully Persian, short and tidy | EXISTS-PARTIAL (reuse/extend) | response_composer.ts (7dd075f), chat_replies.ts, c127f68 Persian confirm words, tests/test_telegram_persian_nlu_matrix.py, test_telegram_reply_presentation.py | M17 (+every mission touching chat) |
| CH-05 | Every mission's prompt is reviewed before work by آرش + the domain specialist + پروانه + گیتی | MISSING→added to plan | no stage protocol in repo; reviews are ad-hoc in reports/grok/GROK_HANDOFF.md; add a stage-gate checklist to the mission ledger (architecture/mission/ledger.py) and mission template | M14 (process applies now) |
| CH-06 | Build is done by domain agents (the agents owning the domain) | EXISTS-PARTIAL (reuse/extend) | ahos_org/registry.py roles; dev_missions.ts intake (d10383e); no domain routing yet | M12/M14 |
| CH-07 | Delivery sign-off by قاسم, رضا, عرفان before a mission is accepted | EXISTS-PARTIAL (reuse/extend) | partial: security reviews by سپهر/قاسم/رضا recorded in GROK_HANDOFF.md (GM-04); add a sign-off record to architecture/mission/ledger.py | M14 (process applies now) |
| CH-08 | No duplicates: search first and extend existing code | EXISTS-PARTIAL (reuse/extend) | hard rule in OWNER_DIRECTIVE_MISSION_PLAN.md + CLAUDE_CONTINUATION_GUIDE.md (564b6e2) | all |
| CH-09 | Local commits only, never push | HUMAN-GATE (locked) | push URL = NO_PUSH_owner_rule_local_only (git remote -v); .cursor/hooks.json ahos-guard | locked |

## 5b. OWN-AV rows — owner vision doc `AHOS_AUTONOMOUS_VISION.md` v1.0 (2026-10-03, newest owner statement)

Source: [`AHOS_AUTONOMOUS_VISION.md`](AHOS_AUTONOMOUS_VISION.md). It defines the target, not an order to enable real money. VISION items without code are MISSING→added (new missions M20–M27); money/custody items are HUMAN-GATE (locked).

| ID | § | Requirement | Status | Evidence (extend these) | Mission |
|---|---|---|---|---|---|
| OWN-AV-01 | §1.1 | North Star: governed autonomous multi-agent fund trading gold, oil, crypto, tokens and US/EU/Asia equities; spot+futures/perp/CFD; long+short | MISSING→added to plan | VISION; paper only via M13/M18/M19/M20; live = HUMAN-GATE | M13/M18/M19/M20 |
| OWN-AV-02 | §1.1 | USDT treasury: allocate per trade, convert, move between venues, sweep profit, withdraw only to the owner's personal wallet | HUMAN-GATE (locked) | VISION; nothing in repo; testnet-only build (M22/M27); real funds locked (INV-01/06) | M22/M24/M27 (gate) |
| OWN-AV-03 | §1.2 | KPIs G1–G6 (capital safety, net risk-adjusted profit, epistemic honesty Brier/ECE, real learning, gradual autonomy, market coverage) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py (Brier), paper_trading/reports.py; no KPI dashboard | M17/M25 |
| OWN-AV-04 | §2.1 | Three lines of defense; Risk (رامین), Compliance (مریم), Security (سپهر) hold independent vetoes; the CIO can't change risk caps | EXISTS-PARTIAL (reuse/extend) | agent_org/authority.py, agent_org/governance.py, ahos_org/policy.py; veto matrix not encoded | M12 |
| OWN-AV-05 | §2.2 | New duties for the 19 existing agents (آرش…رضا) as in the table | EXISTS-PARTIAL (reuse/extend) | ahos_org/registry.py (19 REGISTERED), docs/agents/PLANNED_19_AGENT_MAP.md — extend, don't fork | M12 |
| OWN-AV-06 | §2.3 | 18 new agents (#20–#37: CIO, macro, commodities, US/EU/Asia equities, futures, news-NLP, chart vision, research scout, SI research, treasury, execution, compliance, attribution, dean, accounting, audit), each with charter and boundary | MISSING→added to plan | register via ahos_org/registry.py (c7ed457 path); no new org plane | M12 |
| OWN-AV-07 | §2.3 | Agent lifecycle PROPOSED→CHARTERED→IN_UNIVERSITY→CERTIFIED(L1..L4)→ACTIVE→PROBATION→RETIRED; no uncertified vote; count is not a KPI | MISSING→added to plan | supersedes the OD LIFE state list for agents (newer owner doc); extend ahos_org/registry.py | M12/M16 |
| OWN-AV-08 | §2.4 | Mission flow: prompt review (آرش+specialist+پروانه+گیتی) → build by domain agents → sign-off (قاسم+رضا+عرفان), recorded in architecture/mission/ledger.py | MISSING→added to plan | = CH-05..07; ledger exists (d1571c4), stage records missing | M14 |
| OWN-AV-09 | §3.1 | Licensed data sources with provenance (CCXT, IBKR data, FRED, EIA, LBMA/WGC, CFTC COT, SEC EDGAR, GDELT, explorers) | EXISTS-PARTIAL (reuse/extend) | architecture/providers/ registry + adapters (crypto only); extend registry, no parallel loader | M13/M18/M19 |
| OWN-AV-10 | §3.2 | Point-in-time data: event_time, ingest_time, available_at; backtests use only available_at ≤ t | MISSING→added to plan | not in providers/feature_store; extend discovery/feature_store.py + architecture/providers/ | M13 |
| OWN-AV-11 | §3.2 | Survivorship-free universe incl. delisted and dead tokens | MISSING→added to plan | extend discovery/lifecycle.py | M13 |
| OWN-AV-12 | §3.2 | Corporate actions and futures roll recorded explicitly | MISSING→added to plan | no equity/futures data yet | M19 |
| OWN-AV-13 | §3.2 | Automatic data-quality checks (gap/spike/stale/duplicate) → UNKNOWN, no signal | EXISTS-PARTIAL (reuse/extend) | dashboard_truth.ts STALE, engine/coverage_audit.py, architecture/providers/probe.py | M13 |
| OWN-AV-14 | §3.2 | External text is untrusted data, never an instruction (prompt-injection defense) | EXISTS-PARTIAL (reuse/extend) | agent_org/untrusted.py | M15/M18 |
| OWN-AV-15 | §3.2 | LLM look-ahead defense: entity anonymization and test periods after the model's cutoff | MISSING→added to plan | none; add to strategy_lab/ validation | M16/M18 |
| OWN-AV-16 | §3.3 | Chart reading: deterministic numeric path is canonical; vision (CNN/multimodal) is a second vote only; time-series foundation models only if they beat baselines after costs | MISSING→added to plan | strategy_lab/vector_engine.py numeric only | M16/M19 |
| OWN-AV-17 | §3.4 | Evidence grades A–D on knowledge claims; post-publication decay assumed; multiple-testing t ≥ 3 | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/trust_registry.py, evidence_graph.py; grades not encoded | M16 |
| OWN-AV-18 | §4.1 | Independent signal sleeves (TSMOM, carry, value/momentum, crypto factors, news/event, regime + meta-labeling) | EXISTS-PARTIAL (reuse/extend) | strategy_lab/hypotheses.py, architecture/intel/regimes.py; sleeves not separated | M13/M19 |
| OWN-AV-19 | §4.2 | Multi-agent decision protocol: analysts → bull/bear council keeping dissent → CIO Black-Litterman views → deterministic risk → compliance → execution (paper) → reconciliation → journal | EXISTS-PARTIAL (reuse/extend) | architecture/ai/council_live.py, debate_council.py, architecture/decision/; chain not wired | M15 |
| OWN-AV-20 | §4.2 | Golden rule: the LLM proposes, deterministic code decides; no LLM text becomes an order without risk and compliance stamps (INV-05) | EXISTS-PARTIAL (reuse/extend) | architecture/decision/authority.py, paper_eligibility.py; ApprovedOrder type missing | M20/M21 |
| OWN-AV-21 | §4.3 | Mandatory decision record with fields decision_id … data_snapshot_id | EXISTS-PARTIAL (reuse/extend) | paper_trading/ledger.py, architecture/decision/read_model.py — extend fields | M13 |
| OWN-AV-22 | §4.4 | Entry only when expected edge after all costs (incl. venue switching) exceeds the hurdle; defined exit triggers; opportunity-cost reallocation (day-4 example) | EXISTS-PARTIAL (reuse/extend) | paper_trading/entry_rules.py, exit_rules.py, cost_model.py; no cross-asset allocator | M13/M24 |
| OWN-AV-23 | §5.1 | Sizing = min(fractional Kelly c∈[0.10,0.25] with shrinkage, vol-target 10% (pilot 5%), ≤0.5% NAV risk per trade (pilot 0.25%), ≤1% ADV, margin cap) | EXISTS-PARTIAL (reuse/extend) | paper_trading/risk.py, bankroll.py, architecture/risk/engine.py — extend | M21 |
| OWN-AV-24 | §5.2 | Exposure/correlation caps (asset, class, HRP cluster, gross/net leverage, margin, per-venue ≤25%, CVaR 97.5% ≤2%) with Ledoit-Wolf + stress correlations | MISSING→added to plan | not encoded; extend architecture/risk/engine.py | M21 |
| OWN-AV-25 | §5.3 | Drawdown ladder −3%/−5%/−10%/−15% (pilot −8%) with automatic actions and demotion | EXISTS-PARTIAL (reuse/extend) | max_drawdown in paper_trading/reports.py; ladder actions missing | M21 |
| OWN-AV-26 | §5.4 | Kill-switch hierarchy, pre-trade checks (price band, notional, rate limit, idempotent client_order_id), dead-man switch, owner kill button always available, monthly drill | EXISTS-PARTIAL (reuse/extend) | engine/health_manager.py, kill switch notes in docs; owner button + drills missing | M21/M17 |
| OWN-AV-27 | §5.5 | Stress replay (2008, Mar-2020, negative WTI, LUNA, FTX, USDC depeg, 2013 gold) + hypothetical USDT depeg / address freeze / exchange closure | MISSING→added to plan | none; extend strategy_lab/ backtests | M21 |
| OWN-AV-28 | §6.1 | Single BrokerAdapter interface + OMS state machine + PaperAdapter as the only active adapter; live adapters only behind an owner-signed gate file; never in Lane A | MISSING→added to plan | architecture/execution/ doesn't exist yet; extend paper_trading/engine as the PaperAdapter, no parallel engine | M20 |
| OWN-AV-29 | §6.1 | Execution algos TWAP/VWAP/POV, Almgren-Chriss, TCA after each fill | MISSING→added to plan | none | M20 |
| OWN-AV-30 | §6.3 | Extend paper_trading/; external engines (NautilusTrader, LEAN, vectorbt, Qlib, FinRL…) only as parity references | EXISTS-PARTIAL (reuse/extend) | paper_trading/ + strategy_lab/; = no-duplicates rule | M13/M20 |
| OWN-AV-31 | §6.4 | No sanctions evasion, VPN geo-block bypass, fake KYC or third-party accounts (INV-08); only lawful venues; non-eligible markets stay paper-only | HUMAN-GATE (locked) | locked rule; compliance review required | locked |
| OWN-AV-32 | §6.4 | venue_eligibility registry; ordering on a non-ELIGIBLE venue is structurally impossible | MISSING→added to plan | none | M23 |
| OWN-AV-33 | §7.1 | Layered custody: cold ≥60% multisig/hardware (owner only), warm ≤25% MPC/TSS + policy, hot ≤15% with no-withdrawal keys + IP allowlist | HUMAN-GATE (locked) | VISION; design + testnet only (M22); mainnet keys only after L2 signature | M22 (gate) |
| OWN-AV-34 | §7.2 | Withdrawal allowlist = owner wallet only; allowlist changes by the owner with a 48h timelock; human approval above max(1,000 USDT, 5% NAV); fixed network; test transfer; stablecoin depeg monitor; profit-sweep rule | HUMAN-GATE (locked) | VISION; testnet workflow M27; real transfers locked (INV-06) | M22/M27 (gate) |
| OWN-AV-35 | §7.2 | Honest limit: USDT can't fund traditional brokers directly; switching_cost includes ramp feasibility, else paper-only | EXISTS-PARTIAL (reuse/extend) | recorded; allocator M24 | M24 |
| OWN-AV-36 | §7.3 | Whole treasury built and red-teamed on testnet first; no mainnet key before the L2 signature | PLANNED | M22 | M22 |
| OWN-AV-37 | §8.1 | Self-monitoring loop: decision record → outcome → attribution → error taxonomy (DATA/MODEL/CALIBRATION/RISK/EXECUTION/PROCESS/LUCK) → lesson → hypothesis → sandbox (walk-forward/CPCV) → gate → champion/challenger → promote by signature only | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/, architecture/cognitive/memory/ (NS-01/NS-03) | M13/M14 |
| OWN-AV-38 | §8.1 | Drift monitoring (rolling Sharpe, Brier/ECE, TCA) → automatic PROBATION | EXISTS-PARTIAL (reuse/extend) | architecture/learning/drift.py | M14 |
| OWN-AV-39 | §8.2 | University faculties (markets, quant, risk, commodities/macro, AI/agents, safety/compliance, epistemology), certification L0–L4, golden sets + external benchmarks, mandatory retest after model/prompt/data change; University proposes new agents | MISSING→added to plan | docs only (UNIVERSITY_AND_AGENTS_DISCOVERY.md); build on self_research/strategy_lab/research_worker | M16 |
| OWN-AV-40 | §9 | 9-step research→upgrade pipeline (scout, triage+license, security/SBOM, reproduce, evaluate, red team, proposal in the M14 ledger, gate, local-commit integrate) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/oss_pipeline.py, engine/oss_audit.py, architecture/mission/ledger.py | M16 |
| OWN-AV-41 | §10 | SI/AGI/ACI phases C1–C5 with an honest scorecard; AGI/SI never claimed (INV-14) | EXISTS-PARTIAL (reuse/extend) | = NS rows + NS-10; architecture/cognitive/ | M12–M19 |
| OWN-AV-42 | §11 | Autonomy ladder L0–L5; each money step needs the owner's explicit signature (gate file, no secrets); agents never self-promote; automatic demotion | HUMAN-GATE (locked) | locked; PAPER_ONLY until G-L2 signed | gate |
| OWN-AV-43 | §11 | G-L2 gate metrics: ≥12 months live-data paper, ≥300 trades, Sharpe ≥1.5, DSR ≥0.95, PBO ≤0.2, MaxDD ≤10%, ≥20%/yr net, walk-forward ≥8 folds, live/backtest ≥0.6, ECE ≤0.05, 3 kill drills, sign-offs + owner signature | MISSING→added to plan | gate evaluator missing; build in M25 on strategy_lab/ + architecture/learning/ | M25 |
| OWN-AV-44 | §11 | G-L3 scale gate and demotion rules; Chief of Staff oversight until L5; the owner's kill and withdrawal rights never removed | HUMAN-GATE (locked) | locked | gate |
| OWN-AV-45 | §12 | INV-01 PAPER_ONLY until the owner signs G-L2; no live adapter without a signed gate file | IMPLEMENTED+TESTED | PAPER_ONLY markers + tests; locked | locked |
| OWN-AV-46 | §12 | INV-02 no secrets in files/git/logs/prompts/docs; secret scan in CI | EXISTS-PARTIAL (reuse/extend) | redaction in ledger (d1571c4), 0638643; CI secret scan not verified | locked + M14 |
| OWN-AV-47 | §12 | INV-03 Lane A frozen (CDA + paper E-01); verify with scripts/freeze_lane_a.py | IMPLEMENTED+TESTED | scripts/freeze_lane_a.py, Lane A tests | locked |
| OWN-AV-48 | §12 | INV-04 no push (NO_PUSH_owner_rule_local_only) | IMPLEMENTED+TESTED | git remote push URL | locked |
| OWN-AV-49 | §12 | INV-05..07, 09..14 (LLM never orders directly; allowlist withdrawals; no self-promotion; constitution changes by HUMAN-GATE only; no fabricated data; owner kill always available; daily reconciliation; trading keys have no withdrawal right; AGI/SI only VISION) | HUMAN-GATE (locked) | locked set; enforcement code partly missing (M20–M22) | locked |
| OWN-AV-50 | §13 | New missions M20 broker abstraction, M21 risk engine v2, M22 treasury/custody on testnet, M23 compliance/venue eligibility, M24 capital allocator, M25 paper marathon + gate evaluator, M26 real-pilot readiness (HUMAN-GATE), M27 owner withdrawal workflow (testnet) | PLANNED | added to OWNER_DIRECTIVE_MISSION_PLAN.md | M20–M27 |
| OWN-AV-51 | §15 | Owner Additions register OA-xx (newest wins except invariants); OA-01..04 assigned | EXISTS-PARTIAL (reuse/extend) | AHOS_AUTONOMOUS_VISION.md §15 | all |
| OWN-AV-52 | §1.3 | Aspirational North Star '$100 → $1M in under a month' (OA-05): research direction + capability benchmark only, not a target, commitment or forecast; honest math shown (≈36%/day compounding, ruin risk) | EXISTS-PARTIAL (reuse/extend) | recorded as VISION in the vision doc; no code | M16/M17 |
| OWN-AV-53 | §1.3 | North Star dashboard panel: log progress, g_real vs g_req, S_req vs S_live, implied Kelly (cap 0.25), ruin probabilities (formula + Monte Carlo), growth-risk curve, fixed disclaimer text | MISSING→added to plan | none; build in CommandCenter.tsx/app (M17) on paper NAV data | M17 |
| OWN-AV-54 | §1.3 | Separate $100 paper sandbox account NS-SANDBOX under the same invariants and risk caps; results only reported | MISSING→added to plan | extend paper_trading/bankroll.py (multi-account), no new engine | M13/M25 |
| OWN-AV-55 | §2.5 | No-duplicates register: owner-defined agents reused (ژاله = Accounting agent; رامین = Risk Governor; تینا = token identity; نگار leads News; زرین leads Gold with @gold profiles; Chief of Staff/Agent-01 is not کوروش); Credential/Identity stays a separate seat CRED-ID | EXISTS-PARTIAL (reuse/extend) | = CH-08; ahos_org/registry.py profiles | M12 |
| OWN-AV-56 | §2.6 | Two taxonomies (19 owner roles vs 19 Persian names) are never silently merged; candidate mapping stays UNRESOLVED until a Giti + owner governance decision | HUMAN-GATE (locked) | docs/governance/AGENT_TAXONOMY_MAP.md, agent_taxonomy_map.json (e0ac1dd); merge = governance change (locked) | M12 (gate) |
| OWN-AV-57 | §2.7 | Fill required team seats: GH-2, SKILL-1..4, ACI-2..4, FRONT-1..2, GUARD-2, University research roles, 5 engineering agents, GOLD-SCI, GOLD-STRAT, CRED-ID, council OSINT + SOCIAL | MISSING→added to plan | register in ahos_org/registry.py; count is not a KPI | M12/M16 |
| OWN-AV-58 | §8.3 | University as continuous learning engine: permanent research → ranked claims in the knowledge store → knowledge packs/RAG to agents; AskU API mandatory when an agent hits UNKNOWN/PARTIAL; research tickets | MISSING→added to plan | architecture/knowledge/store.py (0 claims), research_worker/ — extend | M16 |
| OWN-AV-59 | §8.3 | Curriculum + periodic exams, certification and re-certification with pass marks before paper-trading duty (OA-06) | MISSING→added to plan | architecture/cognitive/benchmark/ as exam engine (extend) | M16 |
| OWN-AV-60 | §12 | INV-15 the $1M North Star never changes risk caps, leverage, gates or invariants; the risk engine never reads it | HUMAN-GATE (locked) | locked | locked |
| OWN-AV-61 | §12 | INV-16 a University UNKNOWN on a BLOCKING decision means no trade or smaller size, never a guess | HUMAN-GATE (locked) | locked; enforce in architecture/decision/ | locked + M16 |
| OWN-AV-62 | §12 | INV-17 an agent is ACTIVE only in domains with a valid University certificate; certificate ≠ permission | HUMAN-GATE (locked) | locked; enforce in ahos_org/registry.py | locked + M12 |
| OWN-AV-63 | §15 | OA-07: build agents on the owner's own charter template (P1§11/13/14/15, P2§65) and reuse owner-defined agents | EXISTS-PARTIAL (reuse/extend) | docs/agents/AGENT_MISSION_CHARTER_TEMPLATE.md, ahos_org/registry.py | M12 |

## 6. Status changes to OD rows (supersession applied)

- **OD-416** → SUPERSEDED: superseded on priority by OD-575 (OWN-18 gold first) — D4

## 7. AD rows — all governing docs (grouped by document)

### `.cursor/agents/web.md` — AGENT/SKILL INSTRUCTIONS, 2026-09-03 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0001 | 15 | Preserve the existing Persian RTL Command Center. English must be LTR | TG (text) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |

### `.cursor/skills/ahos-ai-council/SKILL.md` — AGENT/SKILL INSTRUCTIONS, 2026-09-03 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0002 | 28 | TS council.ts is a heuristic duplicate — do not extend it as authority | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |

### `.cursor/skills/ahos-change-verification/SKILL.md` — AGENT/SKILL INSTRUCTIONS, 2026-09-03 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0003 | 11 | Default ladder (skip inapplicable steps, do not skip Lane A): | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-0004 | 28 | Phase record must include PHASE STATUS , PASS GATES , FAILED GATES , | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |

### `.cursor/skills/ahos-governance-context/SKILL.md` — AGENT/SKILL INSTRUCTIONS, 2026-09-08 (4)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0005 | 8 | Read, do not copy: docs/DOC TRUTH MAP.md , docs/canonical/MASTER DIRECTIVE v1.md , | SYNC (text) | EXISTS-PARTIAL (reuse/extend) | scripts/doc_drift.py, docs/CANONICAL_IMPLEMENTATION_MATRIX.md, reports/grok/GROK_HANDOFF.md, d2aa09b (12 stale maps bannered) | all + M14 |  |
| AD-0006 | 18 | UNKNOWN / INCOMPLETE / CONFLICT never become PASS or a positive recommendation | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0007 | 23 | Existing dual-stack (do not widen | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0008 | 31 | New work must consume canonical Python state rather than grow this gap | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |

### `.cursor/skills/ahos-opportunity-hunter/SKILL.md` — AGENT/SKILL INSTRUCTIONS, 2026-09-03 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0009 | 11 | Pipeline the hunter must respect: | SKILLREG (doc) | EXISTS-PARTIAL (reuse/extend) | .cursor/skills/ (11 ahos-*), slills/ (16, typo dup), docs/engineering/SKILL_REGISTRY.md; no runtime registry | M16 |  |

### `.cursor/skills/ahos-research-intelligence/SKILL.md` — AGENT/SKILL INSTRUCTIONS, 2026-09-03 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0010 | 20 | Missing feed ⇒ UNAVAILABLE, never a bullish default | RESSTD (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |

### `.cursor/skills/ahos-security-analysis/SKILL.md` — AGENT/SKILL INSTRUCTIONS, 2026-09-03 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0011 | 23 | INCOMPLETE ⇐ unknown critical (do not call this PASS | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `.cursor/skills/ahos-token-identity/SKILL.md` — AGENT/SKILL INSTRUCTIONS, 2026-09-03 (4)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0012 | 17 | Required model (implement in Lane B, do not fork TS tokenKey ): | SKILLREG (doc) | EXISTS-PARTIAL (reuse/extend) | .cursor/skills/ (11 ahos-*), slills/ (16, typo dup), docs/engineering/SKILL_REGISTRY.md; no runtime registry | M16 |  |
| AD-0013 | 25 | EVM: length + checksum-aware validation; do not treat symbol as identity | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0014 | 26 | Solana: preserve canonical representation; do not lowercase | SKILLREG (doc) | EXISTS-PARTIAL (reuse/extend) | .cursor/skills/ (11 ahos-*), slills/ (16, typo dup), docs/engineering/SKILL_REGISTRY.md; no runtime registry | M16 |  |
| AD-0015 | 28 | Pool must belong to the same canonical token | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |

### `.cursor/skills/ahos-web-experience/SKILL.md` — AGENT/SKILL INSTRUCTIONS, 2026-09-03 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0016 | 17 | TypeScript must not independently recommend. Chat reads canonical evidence | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `slills/SKILL (10).md` — AGENT/SKILL INSTRUCTIONS, 2026-09-08 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0017 | 25 | Write .cursor/skills/verify-<app /SKILL.md with YAML frontmatter ( name: verify-<app and a description that names the app, the surface, and when to reach for it — without frontmatter the skill never registers) and these sections, each grounded in what the interview actually found (no placeholders left): | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0018 | 31 | Cleanup: how to tear down instances the run created. Never kill by process name; kill what you started. Cleanup removes instances and scratch state, never the evidence: proof artifacts survive the teardown, in a location the skill names | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `slills/SKILL (14).md` — AGENT/SKILL INSTRUCTIONS, 2026-09-08 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0019 | 109 | When the prefix legitimately needs to change , never edit an earlier | SKILLREG (doc) | EXISTS-PARTIAL (reuse/extend) | .cursor/skills/ (11 ahos-*), slills/ (16, typo dup), docs/engineering/SKILL_REGISTRY.md; no runtime registry | M16 |  |
| AD-0020 | 339 | Hard rules (never violate): | SKILLREG (doc) | EXISTS-PARTIAL (reuse/extend) | .cursor/skills/ (11 ahos-*), slills/ (16, typo dup), docs/engineering/SKILL_REGISTRY.md; no runtime registry | M16 |  |

### `slills/SKILL (15).md` — AGENT/SKILL INSTRUCTIONS, 2026-09-08 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0021 | 73 | Never Block on the Human ( principle-never-block-on-the-human ). Tempted to ask "should I do X?" on reversible work. Proceed, present the result, let the human course-correct | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate | ; also: slills/SKILL.md:73 |

### `slills/SKILL (4).md` — AGENT/SKILL INSTRUCTIONS, 2026-09-08 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0022 | 23 | Present the framing and tradeoffs before committing to a long run. Reversible work proceeds (the never-block-on-the-human principle skill), but a multi-hour run earns one checkpoint | LEDGER (text) | IMPLEMENTED+TESTED | architecture/mission/ledger.py + scripts/mission_ledger.py + tests/test_mission_ledger.py (d1571c4) | M14 extend |  |
| AD-0023 | 41 | Verify by inspecting the artifact, never a self-report. When something passes too easily, suspect the observation method before the system | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `slills/SKILL (5).md` — AGENT/SKILL INSTRUCTIONS, 2026-09-08 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0024 | 56 | The explanation uses the sections defined in references/explainer-prompt.md , dropping any that do not apply: Overview, Key Concepts, How It Works, Where Things Live, Gotchas | SKILLREG (doc) | EXISTS-PARTIAL (reuse/extend) | .cursor/skills/ (11 ahos-*), slills/ (16, typo dup), docs/engineering/SKILL_REGISTRY.md; no runtime registry | M16 |  |

### `slills/SKILL (6).md` — AGENT/SKILL INSTRUCTIONS, 2026-09-08 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0025 | 60 | Sound like a knowledgeable friend. No buzzwords, no figurative language, no "please" in instructions, and never "simply", "easy", or "quickly" in a procedure. If it were simple, the reader would not be here | SKILLREG (doc) | EXISTS-PARTIAL (reuse/extend) | .cursor/skills/ (11 ahos-*), slills/ (16, typo dup), docs/engineering/SKILL_REGISTRY.md; no runtime registry | M16 |  |
| AD-0026 | 77 | Write procedures as direct commands, never as narration and never in the passive: "Install the component", not "the component must be installed" | SKILLREG (doc) | EXISTS-PARTIAL (reuse/extend) | .cursor/skills/ (11 ahos-*), slills/ (16, typo dup), docs/engineering/SKILL_REGISTRY.md; no runtime registry | M16 |  |

### `slills/SKILL (7).md` — AGENT/SKILL INSTRUCTIONS, 2026-09-08 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0027 | 16 | Choose the narrowest executable check. Prefer the closest unit, component, integration, or regression test already used for that codepath. If no practical test path is obvious, do not create one from scratch just to satisfy the workflow | FAILMEM (text) | EXISTS-PARTIAL (reuse/extend) | reports/ failure memory entries (1b88fcb), architecture/cognitive/loop/contracts.py | M14 |  |

### `docs/agents/AGENT_MISSION_CHARTER_TEMPLATE.md` — BASE/MASTER, 2026-09-15 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0028 | 59 | NON-RESPONSIBILITIES must include being final verifier of own output | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-0029 | 118 | Policies (pointers, do not fork | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |
| AD-0030 | 155 | Charters must not claim TESTED without citing tests | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/architecture/ADR_ACI_001_CHARTER_VS_DEFERRED_EVOLUTION.md` — BASE/MASTER, 2026-09-09 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0031 | 37 | Soak T0 ( 2026-09-10 00:27:41 +03:30 , run id run 1788987515 7ad11528 ) is an independent evidence experiment. Evolution research must stay parallel and isolated | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0032 | 42 | Developers may not enable autonomous evolution, live trading, or Lane A changes from this ADR | LIVEOFF (text) | IMPLEMENTED+TESTED | PAPER_ONLY markers + tests (12 test files, e.g. tests/test_paper_api_security_gate.py); M9.5 0638643 | keep |  |
| AD-0033 | 43 | After soak, a separate human-reviewed proposal is required before calibration or M-GAP-003 closure | CALIB (text) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |

### `docs/architecture/AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md` — BASE/MASTER, 2026-09-09 (8)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0034 | 23 | Finance is the first proving domain. The Cognitive Core must not import discovery , paper trading , telegram ai , or engine | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |
| AD-0035 | 35 | Controlled evolution proposals : architecture/evolution/engine.py (AI may propose, never self-approve | SELFIMP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0036 | 52 | Creativity Classified IDEA/HYPOTHESIS/… never as truth NOT IMPLEMENTED CreativeClass enum only | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0037 | 57 | Counterfactual Reasoning Observed vs alternative; never overwrite facts PARTIAL Financial hindsight PARTIAL; general engine NOT IMPLEMENTED | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0038 | 71 | Execution Layer After permission only NOT IMPLEMENTED (live) Paper path exists in Lane A; live must stay disabled | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-0039 | 106 | Score ledger / soak observations Existing; not this DB never merged | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0040 | 127 | Soak protection: do not stop/start the Windows daemon, reset T0, rewrite observations, retune calibration, or change Lane-A scoring semantics to “make cognition look live” | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-0041 | 143 | Self-research reports from explicit snapshots (never treating Cloud sqlite as soak authority | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |

### `docs/canonical/GOVERNANCE.md` — BASE/MASTER, 2026-08-16 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0042 | 13 | No rescue-tuning : failed hypothesis → new pre-registered card, never parameter fiddling (R-06/R | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0043 | 17 | SIMULATED vs LIVE VERIFIED can never be conflated; probes/states labeled per environment | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |

### `docs/canonical/MASTER_DIRECTIVE_W43.md` — BASE/MASTER, 2026-08-21 (4)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0044 | 14 | AHOS باید به‌صورت یک سیستم یکپارچه، قابل‌اندازه‌گیری، قابل‌توضیح، قابل‌ممیزی، مقاوم در برابر خطا، خودمشاهده‌گر، خودتشخیص‌گر و دارای مسیر حکمرانی‌شده برای خودبهبود تکامل پیدا کند | PRINC (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0045 | 53 | سایت باید رابط اصلی عملیاتی AHOS باشد: | PRINC (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0046 | 75 | ۱۰۰ نقش در ۱۰ تیم. مشورتی. ABSTAIN و UNKNOWN معتبر است. میانگین‌گیری کور ممنوع | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0047 | 112 | AHOS نباید وانمود کند که باهوش است؛ باید با evidence ثابت کند که باهوش‌تر شده است | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/canonical/MASTER_DIRECTIVE_v1.md` — BASE/MASTER, 2026-08-16 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0048 | 12 | MUST be recorded in AHOS ISSUE REGISTER.md (R-series) in the SAME wave, with both sha | SYNC (text) | EXISTS-PARTIAL (reuse/extend) | scripts/doc_drift.py, docs/CANONICAL_IMPLEMENTATION_MATRIX.md, reports/grok/GROK_HANDOFF.md, d2aa09b (12 stale maps bannered) | all + M14 |  |
| AD-0049 | 89 | REGISTRATION LAW: every versioned directive's sha256 must appear in AHOS ISSUE REGISTER.md on | SYNC (text) | EXISTS-PARTIAL (reuse/extend) | scripts/doc_drift.py, docs/CANONICAL_IMPLEMENTATION_MATRIX.md, reports/grok/GROK_HANDOFF.md, d2aa09b (12 stale maps bannered) | all + M14 |  |

### `docs/canonical/MISSION.md` — BASE/MASTER, 2026-08-16 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0050 | 11 | Absolute laws (never negotiable | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |
| AD-0051 | 18 | Rejected hypotheses/failed tests/provider failures = immutable evidence (never hidden, never deleted | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |

### `docs/canonical/SECURITY.md` — BASE/MASTER, 2026-08-28 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0052 | 9 | UNKNOWN among CRITICAL ⇒ PASS WITH UNKNOWN (recommendation ≤ WATCH). UNKNOWN never = PASS | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0053 | 11 | Fixture veto set = 7/7 (labeled FIXTURE; never a real-world detection claim | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0054 | 18 | Raw evidence append-only; verdicts supersede by timestamp (never overwrite | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/governance/AGENT_04_GOVERNANCE_AND_CONSTITUTION_ARCHITECTURE.md` — BASE/MASTER, 2026-09-15 (52)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0055 | 46 | [VERIFIED] Agent One is not implemented ( AGENT ONE STATUS = FUTURE NON AUTHORITY ROOT ). Slice 1 contains a logical agent.chief-orchestrator role — this is not Agent One and must not be silently merged | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0056 | 90 | Relationship types (must not be collapsed | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0057 | 101 | Coordinator (orchestrator) Coordination May synthesize; may not approve or execute [DESIGN ONLY] Constitution §3.1, Agent One definition | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0058 | 202 | Power Holder Agent may not assume | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0059 | 211 | Dual-19 resolution Human [UNRESOLVED] — HUMAN DECISION REQUIRED | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0060 | 228 | Emergency constitutional amendment (see §13) requires human initiation; agents may not invoke emergency paths autonomously | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0061 | 233 | Humans remain accountable for decisions they approve. Agents produce recommendations and evidence; they do not absorb human accountability through synthesis or automation | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0062 | 241 | These are distinct and must not be treated as synonyms: | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0063 | 271 | Plane mapping (do not merge silently | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0064 | 287 | Authority must be explicit, bounded, revocable, time/scoped, auditable, non-self-expandable | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0065 | 315 | MUST NOT automatically become: source of truth, unilateral verifier, unilateral approver, unrestricted executor, constitutional sovereign, production authority | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0066 | 387 | Delegate beyond possession? PROHIBITED [IMPLEMENTED] attenuation logic | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0067 | 389 | Delegate promotion authority? PROHIBITED by default ; REQUIRES HUMAN if ever allowed [IMPLEMENTED] research path denies KNOWLEDGE PROMOTE | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0068 | 390 | Delegate execution authority? PROHIBITED — EXECUTION globally denied in TCB policy [IMPLEMENTED] | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0069 | 391 | Subordinate appoint commander? PROHIBITED [PROPOSED] | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0070 | 392 | Peer activate peer? PROHIBITED without commander authorization [PROPOSED] | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0071 | 426 | Own analysis result ALLOWED ALLOWED as SELF CHECK only PROHIBITED PROHIBITED | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0072 | 427 | Own mission completion ALLOWED PROHIBITED as independent PROHIBITED N/A | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0073 | 428 | Own knowledge candidate ALLOWED PROHIBITED as independent PROHIBITED PROHIBITED | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0074 | 429 | Own agent maturity PROHIBITED PROHIBITED PROHIBITED PROHIBITED | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0075 | 497 | [IMPLEMENTED] [TESTED] TCB denies memory promotion to truth. Stored memory, confidence, recency, audit inclusion never imply truth | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0076 | 537 | Agents may not invoke emergency amendment autonomously | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0077 | 603 | Source of truth Epistemic ownership must stay in evidence/TCB/human | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0078 | 612 | [VERIFIED] Slice 1 logical role ≠ Master Orchestrator runtime ≠ Agent One. Three names; do not merge silently . HUMAN DECISION REQUIRED for future mapping | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0079 | 677 | New agents must declare plane: A ( agent. ), B ( principal. ), C (research), or D ( agent.org. documentary). Plane D agents are not registry facts until human approves seeding | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0080 | 702 | Suspend ALLOWED CONDITIONALLY ALLOWED (subordinate) PROPOSE only PROPOSE PROPOSE PROHIBITED | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0081 | 703 | Quarantine ALLOWED PROHIBITED PROPOSE only PROPOSE (escalate) PROPOSE PROHIBITED | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0082 | 704 | Revoke grants ALLOWED PROHIBITED PROHIBITED PROPOSE PROPOSE PROHIBITED | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0083 | 705 | Retire ALLOWED PROHIBITED PROPOSE PROPOSE PROPOSE PROHIBITED | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0084 | 706 | Restore from SUSPEND ALLOWED CONDITIONALLY ALLOWED PROHIBITED ADVISORY ADVISORY PROHIBITED | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0085 | 707 | Restore from QUARANTINE ALLOWED ( + security review) PROHIBITED PROHIBITED ADVISORY ADVISORY PROHIBITED | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0086 | 723 | Escalate; do not arbitrate by capability, eloquence, or orchestration position | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |
| AD-0087 | 730 | Specialist vs Master Orchestrator Orchestrator must not override by rank Independent verifier Human | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-0088 | 736 | Plane A vs Plane D taxonomy Do not merge Record DUAL 19 HUMAN DECISION REQUIRED | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0089 | 894 | Legend: A = ALLOWED, C = CONDITIONALLY ALLOWED, P = PROHIBITED, H = REQUIRES HUMAN, V = REQUIRES INDEPENDENT VERIFICATION, U = UNRESOLVED | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-0090 | 954 | Dual-19 resolution — Which taxonomy is canonical? Mapping table A↔D? Retire either list? → HUMAN DECISION REQUIRED | TAXO (text) | EXISTS-PARTIAL (reuse/extend) | ahos_org/registry.py, docs/agents/PLANNED_19_AGENT_MAP.md, docs/governance/agent_taxonomy_map.json (e0ac1dd); all 19 at REGISTERED | M12 |  |
| AD-0091 | 955 | Agent One operational charter — All questions in §16 → HUMAN DECISION REQUIRED | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0092 | 956 | Master Orchestrator ↔ agent.chief-orchestrator ↔ Agent One — naming and authority mapping → HUMAN DECISION REQUIRED | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0093 | 957 | Constitution adoption — When does v0.1.0 become L2? → HUMAN DECISION REQUIRED | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0094 | 958 | Cursor-to-runtime federation — How do chat missions bind to Slice 1/2B tasks? → FUTURE MISSION REQUIRED | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0095 | 959 | Quarantine authority model — Who may quarantine vs suspend in production org? → HUMAN DECISION REQUIRED | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0096 | 960 | Approval delegation policy — May approval authority ever be delegated? → HUMAN DECISION REQUIRED | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0097 | 961 | Agent maturity promotion criteria — What evidence promotes REGISTERED → OPERATIONALLY TRUSTED? → HUMAN DECISION REQUIRED | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0098 | 962 | Independent verifier assignment — Service vs ad-hoc human? → FUTURE MISSION REQUIRED | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-0099 | 963 | Emergency constitutional amendment — Threshold and expiry rules → HUMAN DECISION REQUIRED | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0100 | 964 | AHOS read access for org agents — Any bounded read for analysis? → HUMAN DECISION REQUIRED | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0101 | 965 | Plane D charter issuance process — Who authorizes blueprint → operational? → HUMAN DECISION REQUIRED | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0102 | 966 | Governance agent self-review — How Agent 04 class avoids reviewing its own constitutional changes as final? → HUMAN DECISION REQUIRED | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0103 | 967 | Incident restore from QUARANTINED — Evidence bar for reactivation → HUMAN DECISION REQUIRED | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0104 | 968 | Unified registry — Single ID namespace or permanent federation? → HUMAN DECISION REQUIRED | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0105 | 998 | The following are recommendations only . Agent-04 must not execute them | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0106 | 1061 | Role before Capability — Correct as documentation order; enforcement must use capability tokens , not role names | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |

### `docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md` — BASE/MASTER, 2026-09-15 (12)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0107 | 70 | This Constitution does not add new deny tokens. It restates that implied AHOS authority is forbidden | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0108 | 94 | Agent One may not by title: own truth, approve, promote, execute, modify protected resources, connect to AHOS, or override this Constitution | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0109 | 156 | Resolution (DESIGN ONLY, no code change): keep L0–L6 as the document/authority hierarchy for agents. Do not replace Slice 2B artifact types. Map them; do not merge IDs | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0110 | 177 | L0 Files, running processes, package constants, git contents if present Always for “what exists now” Replaced on disk; never cite deleted files as current Report CONTRADICTION vs any L1–L6 that disagrees | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0111 | 178 | L1 Test results, audit hash-chain contents, TCB verification records For the claim the evidence actually supports , in the environment that produced it New failing tests; expired sessions; STALE labels; soak/live evidence from another system Escalate; do not pick the convenient side | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0112 | 183 | L6 Agent interpolations Never Always until converted to labeled HYPOTHESIS Must be labeled; never stored as Evidence | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0113 | 197 | Agents must use these tokens for claim/document/finding status. Do not invent synonyms | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0114 | 223 | These are distinct capabilities . A role name never implies the set | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0115 | 241 | Mapping to existing code ( DESIGN ONLY compatibility — do not refactor now | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0116 | 256 | DEFERRED IMPLEMENTATION : unify Slice 1 capability strings with Slice 2B Capability enum. Until then, agents must cite which plane they mean | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0117 | 271 | Every future agent charter must include: | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0118 | 296 | DEFERRED IMPLEMENTATION : extend AgentRecord only after human approval. Until then, extra identity fields live in charters ( DESIGN ONLY ) and must not be treated as registry facts | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |

### `docs/governance/M3_CONSTITUTIONAL_AND_KNOWLEDGE_RECONCILIATION.md` — BASE/MASTER, 2026-09-28 (8)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0119 | 41 | DEPRECATED (superseded + must not be cited | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0120 | 74 | A.3 Superseded / deprecated — must not be cited as current | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0121 | 98 | D6 Two-lane law: Lane A never stops for Lane-B architecture W12-added law, AHOS RUNTIME ARCHITECTURE v1.md ARCHITECTURE — — CI-pinned ( test architecture p1.py | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-0122 | 102 | D10 AI may never self-approve, never touch Lane A, never promote itself SELF EVOLUTION LOOP.md ; improvement proposal v1.json CONTRACT LAW — — CI lints + human gate (never software | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-0123 | 150 | The real, narrower finding is a composition-root ambiguity (DECISION REQUIRED, not a defect): | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |
| AD-0124 | 315 | Do not treat W43 as registered doctrine, and do not treat its absence from the registry as | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0125 | 317 | Do not merge the AG-\ and CANONICAL AGENT IDS namespaces, and do not treat the M2 map as | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0126 | 320 | When two statements in PART B conflict, record the contradiction; do not resolve it | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |

### `AHOS_GAP_REGISTER.md` — DEBUG/FAILURE/GAP, 2026-10-01 (13)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0127 | 7 | Phase-8 class (this mission): PROVEN · MITIGATED · OPEN · BLOCKED — never PASS without an artifact | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-0128 | 23 | M-GAP-009 2026-08-18 (audit v2 carry-over) 1 Safety-adjacent (operational) Telegram never run live (token rotation pending) — alerts unverified end-to-end telegram ai needs real token Month 4; user blocker ① USER: token rotation live transcript archived OPEN (blocked on user | TG (text) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |
| AD-0129 | 35 | Evidence classification (do not collapse these | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0130 | 70 | Unproven (must not be labeled PASS | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-0131 | 116 | M-GAP-021 (owner actions scattered) CLOSED docs/OWNER ACTION REQUIRED.md | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0132 | 118 | AG-25 GitHub live harvest NOT IMPLEMENTED (by design PLANNED) Honest in matrix; do not claim COMPLETE | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0133 | 122 | Owner actions: docs/OWNER ACTION REQUIRED.md | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0134 | 243 | Third and fourth defects found in the same local-evidence pipeline, again all invisible to Linux CI. Theme: the soak evidence path was written against a clean Linux checkout and never exercised on the warm Windows soak host, because until M-GAP-033 the suite could not even be collected there | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0135 | 278 | Area 5 — local dashboard. app/ is a real Next.js surface ( api/ , layout.tsx , page.tsx ). Doable but needs a design decision about what the dashboard must show; no external blocker | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0136 | 370 | MASTER DIRECTIVE W43.md , news.ts , page.tsx — never the registry, the test, or the issue | NEWS (text) | EXISTS-PARTIAL (reuse/extend) | architecture/intel/news.py, c62340c narrative RSS into scoring, root news.ts; paid credential gated | M18 |  |
| AD-0137 | 401 | Add a wave directives key to master directive registry.json (schema 1 → 2) DECISION REQUIRED The cleanest model, but it changes the registry schema, which is constitutional enforcement. AGENTS.md forbids weakening tests and the owner must ratify; needs an R-series entry | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0138 | 402 | Rename MASTER DIRECTIVE W43.md so it cannot be mistaken for doctrine DECISION REQUIRED Breaks 9 referencing files; disposition of an operationally governing document is owner review under docs/canonical/GOVERNANCE.md (autonomous deletion prohibited). M4 deliberately did neither | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0139 | 489 | Addendum 2026-09-30 (10) — the failure matrix shelled out to POSIX grep , so six soak-pre-registration tests could never pass on Windows (M-GAP-041 RESOLVED | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |

### `AHOS_ISSUE_REGISTER.md` — DEBUG/FAILURE/GAP, 2026-08-28 (26)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0140 | 5 | FAILURES OF PROCESS (learned — the "never again" list | LEARN (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/prediction_lifecycle.py, 202f8c9 learning bridge | M13 |  |
| AD-0141 | 19 | HOW: script that produced numbers was never itself delivered → non-reproducible | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-0142 | 27 | HOW: verification reported against local files never handed over | DAILY (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/reports.py, engine/research_report_bot.py, TELEGRAM_RESEARCH_REPORT | M17 |  |
| AD-0143 | 94 | WHERE: S ≥0.8 conviction extreme never occurs within composite feature scale | FAILMEM (doc) | EXISTS-PARTIAL (reuse/extend) | reports/ failure memory entries (1b88fcb), architecture/cognitive/loop/contracts.py | M14 |  |
| AD-0144 | 249 | UNKNOWN never guessed, security veto blocks, SL-before-TP gap rule, stale-price exits forbidden | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |
| AD-0145 | 296 | TOTAL LOSS exact, UNKNOWN-liquidity⇒NO DATA-never-TRAP (v2 law mirrored), divergence & decay | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0146 | 333 | "do NOT create a second bot" rule — single canonical bot must be confirmed by the user | TG (text) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |
| AD-0147 | 334 | REQUIRED USER ACTIONS (none delegable — no platform-config tool exists in this sandbox): | WORKER (text) | EXISTS-PARTIAL (reuse/extend) | research_worker/ + agent_org/research_host/ (process-isolated, 5 test files) | M12 |  |
| AD-0148 | 456 | F2 (cycle removed; acyclic CI-pinned), F5 (AG-23 = human gateway, never-software law), F6/F | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0149 | 577 | Tier-1 executor (AG-25 duties 1/ 10; never assigns final verdict; API error ⇒ UNVERIFIED | FAILMEM (doc) | EXISTS-PARTIAL (reuse/extend) | reports/ failure memory entries (1b88fcb), architecture/cognitive/loop/contracts.py | M14 |  |
| AD-0150 | 701 | WHY existing components did not recover: gap recording was designed to RECORD, never to FETCH; | FAILMEM (doc) | EXISTS-PARTIAL (reuse/extend) | reports/ failure memory entries (1b88fcb), architecture/cognitive/loop/contracts.py | M14 |  |
| AD-0151 | 756 | F12 status: MITIGATED, monitored — trajectory EARLY; verdict must improve over cadence | OBS (text) | EXISTS-PARTIAL (reuse/extend) | engine/health_manager.py, architecture/runtime/observability_snapshot.py, scripts/gateway_port.py (06e44e6) | M11/M14 |  |
| AD-0152 | 762 | When due it must carry: 11/11 NO DATA streak + this entry's root cause + 0 exits + cash | FAILMEM (text) | EXISTS-PARTIAL (reuse/extend) | reports/ failure memory entries (1b88fcb), architecture/cognitive/loop/contracts.py | M14 |  |
| AD-0153 | 806 | MITIGATION DEPLOYED (never "SOLVED" | FAILMEM (doc) | EXISTS-PARTIAL (reuse/extend) | reports/ failure memory entries (1b88fcb), architecture/cognitive/loop/contracts.py | M14 |  |
| AD-0154 | 994 | R2 PRE 987 obs/762 tok vs POST 749 obs/451 tok. Horizon coverage (never merged): s+15m | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0155 | 1001 | NOT YET VALIDATED (never upgraded to VALIDATED); independently, data forces INSUFFICIENT DATA | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-0156 | 1093 | Controlled Self-Evolution ( architecture/evolution/engine.py ): 14-stage improvement proposal v1 validator enforcing LANE A FORBIDDEN immediate reject, AI self-approval prohibition, and rollback plan validation | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-0157 | 1204 | This is the acceptance tool the roadmap names for weight changes: a PR that changes scoring constants must attach a diff produced by this tool (the report's weight fingerprints / score engine versions make the change visible even when both artifacts are INSUFFICIENT DATA | SCORING (text) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0158 | 1217 | WHY: The learning priority list (P3) includes drift detection; StreamingDriftDetector existed but had no production consumer. A calibration cohort that pools distinct score regimes over time misleads — the report must surface the shift | CALIB (text) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0159 | 1229 | Benchmark gate (§5): scripts/benchmark performance.py — every run recorded as ahos.benchmark run.v1 (git sha + env + results); compare subcommand - ahos.benchmark diff.v1 per-benchmark absolute/relative deltas, NOT COMPARABLE when a benchmark is missing on either side (never a fake delta | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0160 | 1230 | Dead-code detection (§4B): scripts/validate imports.py ORPHANS section (WARN-level) using a full import graph (absolute + resolved relative incl. lazy in-function imports); packages never flagged; current tree reports 14 honest candidates (standalone entrypoints + architecture.security.engine | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0161 | 1247 | P12 regression intelligence: regression report.py diffs evidence states (test deltas, benchmark direction-aware, schema drift, UNKNOWN growth, storage, cycles, Lane-A); NOT COMPARABLE never invented | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-0162 | 1265 | Finding prioritization (Candidate D): priority derived from severity + evidence strength (CORRELATED/UNKNOWN downgrade one step; OBSERVED/DERIVED keep severity; weak evidence never inflates); findings returned highest-first with deterministic tie-break | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0163 | 1284 | Added docs/OWNER ACTION REQUIRED.md ; bannered stale SECURITY/MISSING/STRATEGIC docs | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0164 | 1285 | Matrix/audit: AG-25 NOT IMPLEMENTED; CALIBRATION READY BUT DATA REQUIRED; SOAK INFRASTRUCTURE READY / SOAK NOT YET EXECUTED; acceptance matrix; class DEVELOPMENT READY | CALIB (text) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0165 | 1305 | WHY: 348 local predictions / 0 outcome pairs — Lane-B scored into ScoreLedger + production observations but never called frozen Lane-A register/observe APIs, so observation state stayed empty and calibration reported no matching label | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |

### `docs/STRATEGIC_GAP_ANALYSIS.md` — DEBUG/FAILURE/GAP, 2026-08-27 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0166 | 44 | Theoretical-only: every new product layer above. Opportunity weights are FORBIDDEN until E-01 outcome data exists | LEARN (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/prediction_lifecycle.py, 202f8c9 learning bridge | M13 |  |

### `docs/verification/AGENT_16_INDEPENDENT_VERIFICATION_AND_ORGANIZATIONAL_FORENSICS.md` — DEBUG/FAILURE/GAP, 2026-09-15 (4)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0167 | 26 | Do 251 tests prove organizational readiness? NO — they prove in-memory TCB semantics, Slice 1 authz, and one Class A worker path; they do not prove inter-agent messaging, mission orchestration, or Agent One | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0168 | 32 | Human operational burden today? HIGH — Mehrdad must orchestrate agents manually via Cursor | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0169 | 130 | Three implemented control planes (verified — do not invent a fourth | REALCLASS (text) | EXISTS-PARTIAL (reuse/extend) | ahos_org/registry.py states, reports/grok/REMAINING_REALITY_REGISTER.md | M9 (done) / M12 |  |
| AD-0170 | 815 | Human must manually orchestrate all agents | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |

### `reports/FAILURE_MEMORY.md` — DEBUG/FAILURE/GAP, 2026-10-03 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0171 | 13 | FM-001 — Scheduler cycle never returned against the production discovery DB | PERSIST (text) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |

### `reports/agi_aci_evolution/GAP_REGISTER.md` — DEBUG/FAILURE/GAP, 2026-09-13 (6)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0172 | 10 | ACI-GAP-002 No general causal world model; financial hindsight ≠ causal engine Cannot represent multi-domain alternatives without mutating facts charter/world-model P5 charter/world-model P5 world model.py ; hindsight.py PARTIAL Isolated CF records; never mutate observation tables OPEN UNVALIDATED | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0173 | 12 | ACI-GAP-004 Autonomous evolution doctrine-OFF; human gate required Self-improvement ≠ self-modification of production/Lane A P8 P8 PROJECT STATE Evolution A (OFF); evolution/engine.py Keep proposal ledger; B ONLY gate; never auto-promote PARTIAL HUMAN GATE REQUIRED | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-0174 | 13 | ACI-GAP-005 M-GAP-003 ≥7-day soak not closed by 72h soak Reliability questions remain after T+72h Operational soak P0 AHOS GAP REGISTER.md M-GAP-003; owner T0 2026-09-10 Post-soak proposal only; do not auto-calibrate OPEN SOAK IN PROGRESS | CALIB (text) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0175 | 15 | ACI-GAP-007 Creative intelligence not implemented No classified novel hypotheses/strategies from a measured generator P7 P7 CreativeClass enum only Generator later; never present IDEA as truth OPEN UNVALIDATED | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0176 | 19 | ACI-GAP-011 Multi-market adapters beyond tokens/crypto; P3 adds thin synthetic finance/science/software/operations helpers Core must stay domain-general; real markets not integrated P10 P10 loop/adapters.py SYNTHETIC TEST DATA Keep adapters thin; do not hardcode crypto in the loop PARTIAL SYNTHETIC ADAPTERS ONLY | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0177 | 20 | ACI-GAP-012 Live execution / L6–L7 Out of scope; PAPER ONLY P12 P12 PAPER ONLY doctrine Remain disabled; connectors default off OPEN (intentionally) FORBIDDEN NOW | LIVEOFF (text) | IMPLEMENTED+TESTED | PAPER_ONLY markers + tests (12 test files, e.g. tests/test_paper_api_security_gate.py); M9.5 0638643 | keep |  |

### `reports/agi_aci_evolution/P4_4_COGNITIVE_STACK_FORENSIC_AUDIT.md` — DEBUG/FAILURE/GAP, 2026-09-09 (12)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0178 | 162 | Isolation (CONFIRMED): dedicated ahos cognitive memory.sqlite ; constructor rejects FORBIDDEN DB NAMES ( e01 discovery.sqlite , paper trading.sqlite , ahos local.sqlite , ahos knowledge.sqlite | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0179 | 231 | No (CONFIRMED). Precision 0.9091 and recall 1.0000 on the frozen vector. The remaining 2/22 unrelated inclusions are real and should stay on the register. They do not dominate competence relative to a reasoner that keyword-scores whatever arrives | SCORING (text) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0180 | 308 | Any SUPPORTED result is immediately downgraded to WEAKLY SUPPORTED (“P3 never upgrades to certainty” | RES2ARCH (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0181 | 386 | SUPPORTED requires a linked experiment id (CONFIRMED). The loop never transitions to SUPPORTED from analysis placeholders | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0182 | 433 | Autonomous self-improvement NO / FORBIDDEN sandbox + evolution engine | WORKER (text) | EXISTS-PARTIAL (reuse/extend) | research_worker/ + agent_org/research_host/ (process-isolated, 5 test files) | M12 |  |
| AD-0183 | 652 | Soak / discovery collectors DOMAIN-BOUND must stay adapters | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0184 | 692 | Residual retrieval cousins L L L H H H M L 2/22 FPs; do not ignore, do not prioritize | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0185 | 743 | Adversarial: ADV-HYP / ADV-FIN-OPINION / ADV-LOOKALIKE must not be WEAKLY SUPPORTED without typed support | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0186 | 744 | Retrieval P4.1–P4.3 recall/precision floors must not regress | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0187 | 750 | What MUST NOT be built yet: | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 | ; also: reports/agi_aci_evolution/P4_4_COGNITIVE_STACK_FORENSIC_AUDIT.md:767 |
| AD-0188 | 769 | Another retrieval-only phase as the primary program (record residual FPs; do not make them the strategy | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0189 | 859 | Human review is required before any implementation directive | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |

### `reports/agi_aci_evolution/P5_FORENSIC_ARCHITECTURE_GATE.md` — DEBUG/FAILURE/GAP, 2026-09-10 (13)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0190 | 21 | Architectural guarantee What the control flow must do if invariants are centralized and non-bypassable | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0191 | 110 | Mixed SUPPORTS + CONTRADICTS without a graph edge never reaches the critic contradiction branch ( contradiction present is edge-based | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0192 | 131 | Temporal WEAK Decay enum roles, not clocks ACTIVE+20s and ACTIVE+10000s identical WEAKLY; CURRENT never assigned | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0193 | 148 | Consumed as: positive support eligible (must be AFFIRMED + SUPPORTS + DIRECT + identity-ok); contradicts task (DIRECT + NEGATED or CONTRADICTS, not mismatch | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0194 | 271 | Different labels do not imply different reasoning operators | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0195 | 279 | The critic is not the only safety mechanism for single-item negation (mode supporting already excludes it; DEDUCTIVE CONTESTS contrary-only). That matches the requirement that critic must not be the sole gate for that class | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0196 | 290 | Metrics: p5 critic detection rate / critic constraint rate are live reason() based in p5 eval (prior correction). They do not include mixed no-edge contradiction | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0197 | 317 | TEMP CURRENT is defined and used in support strength / TEMPORAL mode buckets, but never returned by temporal state of . Dead “freshness” path | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0198 | 408 | Tests establish current fixture behavior plus some per-item properties. They do not establish episode-level contradiction closure or identity-marker soundness | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0199 | 480 | M4 — CURRENT temporal state never assigned; age not computed | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0200 | 543 | If any bound FACTUAL PREMISE contradicts task() and any other may support task() , the episode verdict must be CONTESTED or UNRESOLVED (not WEAKLY), independent of graph edges. Then reusable writeback cannot fire | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0201 | 547 | Third, METACOGNITIVE (and ABDUCTIVE supporting ids) must not list non- may support task items as supporting evidence of a positive verdict | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0202 | 565 | CODE CHANGES REQUIRED = YES | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |

### `reports/agi_aci_evolution/P5_POST_IMPLEMENTATION_FORENSIC_AUDIT.md` — DEBUG/FAILURE/GAP, 2026-09-11 (6)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0203 | 27 | Those paths were re-executed. They do not yield FACTUAL PREMISE | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0204 | 157 | Serialization grant dict in payload json ; secret never serialized | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0205 | 272 | V2: expired / future observations must not become current factual premises merely because they were inserted or reloaded recently. The check uses an attacker-controlled task clock , not episode now . That weakens temporal authority ( HIGH | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0206 | 352 | Orchestrator write-back kinds remain HYP/LESSON/INFERENCE, never OBSERVED FACT ( PROVEN source + hop tests | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-0207 | 410 | Verify failures return False (fail-closed), do not fall back to stored roles | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0208 | 488 | Implementation vs V2 ( f50cba4..e93b3c0 ): 17 files, all REQUIRED for the ObservationGrant change or its report. UNRELATED = | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `reports/agi_aci_evolution/P5_SECOND_FORENSIC_VERIFICATION.md` — DEBUG/FAILURE/GAP, 2026-09-10 (6)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0209 | 4 | PR: 93 (DRAFT; do not merge | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0210 | 110 | EPISODIC records of unresolved episodes are allowed . They are memory type=EPISODIC , epistemic kind=INFERENCE , statement episode {task id} {verdict} . They must not become OBSERVED FACT on retrieval (two-hop PROVEN | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0211 | 199 | Hard invariant: NO MODE emits a live reason() WEAKLY SUPPORTED on unresolved mixed evidence. PROVEN ( test seven modes mixed never weakly | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0212 | 236 | MODE FNS loop/modes.py library PARTIAL WEAKLY candidates exist; must go through reason() new caller skipping reason() do not call MODE FNS then remember | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0213 | 311 | TEMP CURRENT is still never assigned | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0214 | 356 | CODE CHANGES REQUIRED = NO for P5 write-back (remaining full-suite failures are unrelated doc-drift | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |

### `reports/agi_aci_evolution/P5_V3_POST_IMPLEMENTATION_FORENSIC_AUDIT.md` — DEBUG/FAILURE/GAP, 2026-09-11 (7)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0215 | 34 | The two later commits ( f7cee47 , 8167cf8 ) add only the self-PASS implementation report. They do not change architecture/ or tests/ | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0216 | 156 | Package all mint exports architecture.cognitive , .memory , .loop do not export BoundIngestPort / ObservationAuthority / IngestPort | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0217 | 399 | These consumption properties do not close C1 (attacker mints a fresh matching latest row | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0218 | 453 | Layer 4 file imports the mint helper. tests/test p5 v3 authority boundary.py docstring says it must not import p5 grant fixtures , then imports persist test observation for clock and several authority cases. Independent Layer 4 is not mint-free | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0219 | 457 | Same test key ( TEST VECTOR KEY ) is used for positive FACTUAL proofs and for Layer 4 cases that mint then expect reject-on-mutation. Negative remember/sqlite tests in that file do not mint; the module as a whole is mixed | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0220 | 461 | Constructor TypeError tests do not attempt push grant verify context + BoundIngestPort (the surviving matching pair). Green orchestrator-DI tests do not cover C | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0221 | 526 | M3 MEDIUM Orchestrator DI tests never attack the contextvar join | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |

### `reports/agi_aci_evolution/P5_V3_TEST_INDEPENDENCE_FORENSIC_DESIGN.md` — DEBUG/FAILURE/GAP, 2026-09-11 (20)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0222 | 42 | V3 ARCHITECTURE = REFINEMENT REQUIRED | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 | ; also: reports/agi_aci_evolution/P5_V3_TEST_INDEPENDENCE_FORENSIC_DESIGN.md:416 |
| AD-0223 | 84 | Access SECRET ? No test file reads secret or process authority . They do not need to: they call mint indirectly. Equivalent to using the production key. grep of tests/ | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0224 | 162 | Tests that do not mint (Layer-2-like | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0225 | 170 | Three authorities (must not be conflated | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0226 | 185 | Layer 4 modules do not import it | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0227 | 203 | Inputs: canonical bytes; ObservationGrant dicts; MAC under a published test-vector key that never appears in production runtime | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0228 | 261 | A Static precomputed fixtures High if key never in production Low vs process urandom High Low if vectors live only in tests/ MAC yes; latest-state/TOCTOU need a store + some key Low | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0229 | 274 | Production runtime: os.urandom(32) , never TEST VECTOR SECRET , never AHOS TEST GRANT KEY | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0230 | 275 | Public CognitiveOrchestrator. init must not take ingest= / verifier= that let an ordinary caller install a matching mint+verify pair (Attack P). Wiring lives in a composition root. Tests duplicate wiring under tests/ , not via a production kwarg | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-0231 | 277 | This does not implement a second brain. It splits key ownership so tests never need production SECRET | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0232 | 285 | YES, but only as Test Authority B under a test key, or as production compose-root mint that ordinary Layer-4 tests do not hold | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0233 | 319 | CognitiveOrchestrator(ingest=, verifier=) UNRESOLVED in V3 text — if added as public kwargs, OPEN (matching pair = mint) must not exist on public ctor | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-0234 | 322 | Env AHOS TEST GRANT KEY not in V3 must not exist (Option C | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0235 | 332 | Clock tests (must not reintroduce H | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0236 | 355 | Invariant: sweeping CognitiveTask.created at must not change grant validity when episode ts is fixed | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0237 | 366 | No public mint RPC import/call persist / IngestPort / mint getter those callables production observation.py Layer 4: call them, bind fail or AttributeError, module must not be pre-minted all / hasattr issue | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0238 | 386 | §9 test adapter must not take statement= . Layer 3 uses a typed acquired result + fixed template. Otherwise GRANT issuance proofs stay signer tests | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0239 | 387 | No process-wide mint singleton shared with tests. Bind verifies with a composition-root key. Tests inject a test vector key via tests/ wiring. Public CognitiveOrchestrator must not accept a matching ingest+verifier pair | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-0240 | 393 | These refinements do not reopen ordinary-caller mint if persist RPC stays gone and adapters stay non- statement= . They make the boundary provable | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0241 | 401 | Future test specification (do not implement now | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |

### `reports/agi_aci_evolution/P5_V4_POST_IMPLEMENTATION_FORENSIC_AUDIT.md` — DEBUG/FAILURE/GAP, 2026-09-11 (4)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0242 | 218 | Production modules do not import tests.observation test runtime / TEST VECTOR KEY (Layer 4 asserts this | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0243 | 219 | Layer 4 must not import tests.p5 grant fixtures | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0244 | 223 | Tests do not call a production signer to mint expected evidence. Auditor isolation ACCEPT used instance secrets only in /tmp probes, not in the test suite | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0245 | 225 | TEST INDEPENDENCE = PASS . TEST AUTHORITY SEPARATION = PASS . PRODUCTION SECRET EXPOSURE TO TESTS = BLOCKED (tests never read production K O | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |

### `reports/grok/reviews/FIX_MATRIX_PHASE9_5_9_6.md` — DEBUG/FAILURE/GAP, 2026-10-03 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0246 | 20 | B1 FIXED 0638643 npm run test:chat-auth (23) — identity is server-side: Telegram HMAC signature, httpOnly session cookie; an unproven caller is never owner. isOwner unproven-claim cases in scripts/chat actions selftest.ts ("owner identity" | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0247 | 59 | MN-2 FIXED 0638643 tests/test ai provider status.py::test windows backend is read only and injectable — CredentialStore.has credential returns bool \ None , never the value | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0248 | 64 | MN-7 FIXED 0638643 chat actions.ts:502 ( confirmCode: a.code ) → dev missions.ts:255 stores hashId("confirm code", …) , never the raw code; covered by npm run test:dev-missions | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |

### `docs/AGENT_MODE_OPERATIONAL_DIRECTIVE_FA.md` — GOVERNANCE/DIRECTIVE, 2026-08-20 (9)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0249 | 37 | هیچ توسعه‌ای نباید بدون بررسی این سند انجام شود | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0250 | 71 | Agent Mode قبل از هر Commit باید همزمان نقش‌های زیر را اجرا کند: | GIT (text) | EXISTS-PARTIAL (reuse/extend) | CLAUDE_CONTINUATION_GUIDE.md commit rules, .cursor/hooks.json ahos-guard | all |  |
| AD-0251 | 273 | AHOS باید دارای سیستم ارزیابی چنددیدگاهی باشد | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0252 | 289 | AI Council نباید تصمیم کور ایجاد کند | COUNCIL (text) | EXISTS-PARTIAL (reuse/extend) | architecture/ai/council_live.py, architecture/ai/debate_council.py, council.ts, tests/test_ai_council_live.py, test_multi_mind_council_anti_echo.py | M15 |  |
| AD-0253 | 328 | وضعیت فعلی: لنزهای خبره در architecture/knowledge/lenses.py و پنل در architecture/knowledge/panel.py . جعل شخصیت ممنوع است | NEWS (text) | EXISTS-PARTIAL (reuse/extend) | architecture/intel/news.py, c62340c narrative RSS into scoring, root news.ts; paid credential gated | M18 |  |
| AD-0254 | 334 | AHOS باید اشتباهات گذشته را تحلیل کند | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0255 | 354 | وضعیت فعلی: architecture/evolution/hindsight.py و architecture/evolution/engine.py وجود دارند. هر یادگیری باید Evidence-backed و بدون بازنویسی تاریخچه باشد | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0256 | 364 | باید مکالمه طبیعی فارسی داشته باشد | TG (text) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |
| AD-0257 | 646 | معامله واقعی: ممنوع و بسته | LIVEOFF (text) | IMPLEMENTED+TESTED | PAPER_ONLY markers + tests (12 test files, e.g. tests/test_paper_api_security_gate.py); M9.5 0638643 | keep |  |

### `docs/governance/AGENT_01_GOVERNANCE_PROPAGATION_ADOPTION_REPORT.md` — GOVERNANCE/DIRECTIVE, 2026-09-15 (7)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0258 | 110 | NO CONTACT means the identity was discovered, but no supported send/issue mechanism exists from this session to the prior completed conversation/persona. It must not be read as refusal or objection | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0259 | 192 | It should record the improvement as a DEFERRED FINDING with impact, urgency, dependency, and proposed owner/gate if known, then complete the current mission when its acceptance and stop conditions are satisfied. It must not expand the mission indefinitely | AUTOCONT (text) | EXISTS-PARTIAL (reuse/extend) | process rule; enforced via reports/grok/CLAUDE_CONTINUATION_GUIDE.md, docs/canonical/GOVERNANCE.md, .cursor/skills/; reports/grok/OWNER_DIRECTIVE_MISSION_PLAN.m | all |  |
| AD-0260 | 196 | The agent must state the disagreement explicitly, identify the affected principle and evidence/reasoning, preserve any conflict with current code or governance, and escalate through the defined chain. It must not write ACK or claim adoption merely to appear compliant | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0261 | 240 | Understanding cannot be assessed. Existing architecture documents contain partial alignment—for example evidence/status distinctions and idle-after-mission lifecycle—but they predate baseline v1, do not answer all six scenarios, and do not prove receipt or adoption | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0262 | 309 | Slice 1 authorization, Slice 2B TCB, and research IPC enforce their own bounded controls. They do not enforce this entire baseline. DOCUMENTED CONTROL ≠ ENFORCED CONTROL | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0263 | 361 | AGENT-01 identity wording remains ambiguous and must not resolve Dual-19 by implication | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-0264 | 368 | Whether AGENT-03 through AGENT-11 must be reactivated in their original contexts for actual scenario responses | FEDSEC (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |

### `docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md` — GOVERNANCE/DIRECTIVE, 2026-09-15 (16)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0265 | 30 | It applies prospectively to every Cursor Control-Plane mission and must be referenced by future issued specialist charters. Planned identities and dormant prior mission personas do not adopt it merely because this file exists | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0266 | 75 | Every meaningful completion claim must identify what was built, where it was integrated, what was independently verified, what remains unverified, and who owns acceptance | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0267 | 94 | The exact trajectory may stop earlier when authority, scope, or safety requires it. Stopping must produce one of these terminal deliverables: | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0268 | 108 | Non-blocking improvements must be recorded as DEFERRED FINDING with rationale and owner/gate if known. They must not keep the active mission open indefinitely | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0269 | 125 | The agent must remain within its mission, security, and authority boundary. Direct inspection does not authorize protected mutation | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0270 | 151 | Independent verification must evaluate the integrated result, not only the builder’s report or isolated unit | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-0271 | 173 | Independence requires more than a different display name. Correlated models, prompts, source material, test logic, or shared unsupported assumptions must be disclosed | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0272 | 175 | Self-review may be labeled SELF CHECK or FORENSIC REVIEW ; it must not be represented as independent verification | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-0273 | 195 | When three agents agree, what must be checked before treating that as independent verification? | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-0274 | 198 | How must the agent behave when it disagrees with this baseline? | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0275 | 214 | No delivery/contact channel BLOCKED / CAPABILITY GAP Record target and continue; do not infer receipt | AUTOCONT (text) | EXISTS-PARTIAL (reuse/extend) | process rule; enforced via reports/grok/CLAUDE_CONTINUATION_GUIDE.md, docs/canonical/GOVERNANCE.md, .cursor/skills/; reports/grok/OWNER_DIRECTIVE_MISSION_PLAN.m | all |  |
| AD-0276 | 215 | No response before stop condition NO RESPONSE Record; do not loop forever | AUTOCONT (text) | EXISTS-PARTIAL (reuse/extend) | process rule; enforced via reports/grok/CLAUDE_CONTINUATION_GUIDE.md, docs/canonical/GOVERNANCE.md, .cursor/skills/; reports/grok/OWNER_DIRECTIVE_MISSION_PLAN.m | all |  |
| AD-0277 | 219 | Conflict with charter/code/governance CONFLICTED Apply source hierarchy; do not silently override | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0278 | 242 | The agent must request human help when the missing element is human authority, inaccessible information, or a physical action—not because direct inspection is inconvenient | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0279 | 265 | Every mission must define: | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0280 | 288 | If a target cannot be contacted, record NO CONTACT / CAPABILITY GAP ; do not create a replacement identity or loop indefinitely | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |

### `docs/governance/AGENT_REGISTRY_MODEL.md` — GOVERNANCE/DIRECTIVE, 2026-09-15 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0281 | 67 | Reports must say which plane an AGENT ID belongs to | DAILY (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/reports.py, engine/research_report_bot.py, TELEGRAM_RESEARCH_REPORT | M17 |  |

### `docs/governance/AGENT_TAXONOMY_MAP.md` — GOVERNANCE/DIRECTIVE, 2026-09-28 (6)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0282 | 68 | INV-VETO-DETERMINISTIC AG-09 holds VETO as a deterministic safety veto — never an AI veto | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0283 | 69 | INV-PROMOTE-HUMAN-ONLY AG-23 holds PROMOTE+VETO but only as a documented human gateway — never implementable as software | SELFIMP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0284 | 71 | INV-MATURITY-ADVANCE-GOVERNED The only path from REGISTERED to IMPLEMENTED is AgentRegistry.advance maturity — fail-closed, evidence-mandatory, audit-logged, and never called by any seed or production path. Levels above IMPLEMENTED are not reachable through it | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0285 | 72 | INV-GLOBAL-DENY GLOBAL DENY CAPABILITIES ( trading.live , production.operate , credentials.access , ahos.lane a , telegram.access , n8n.access , …) are never ALLOW | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0286 | 73 | INV-RESEARCH-FORBIDDEN A research context cannot receive IDENTITY MANAGE , APPROVAL ISSUE , KNOWLEDGE PROMOTE , AUTHORITY DELEGATE , EXECUTION , POLICY MODIFY , VERIFICATION RECORD , TASK MANAGE | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0287 | 86 | H — GitHub / Open-Source Intelligence No Slice-1 anchor. AG-25 is PLANNED and engine/oss audit is an orphaned dead module (never imported). The entire Agent-H substrate is dead code behind one manual audit report | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |

### `docs/governance/M4_WAVE_DIRECTIVE_DECLARATION.md` — GOVERNANCE/DIRECTIVE, 2026-09-28 (5)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0288 | 73 | "register Master Directive" (E4/E5) and never completed it | SYNC (text) | EXISTS-PARTIAL (reuse/extend) | scripts/doc_drift.py, docs/CANONICAL_IMPLEMENTATION_MATRIX.md, reports/grok/GROK_HANDOFF.md, d2aa09b (12 stale maps bannered) | all + M14 |  |
| AD-0289 | 128 | Should it be deleted or renamed? NO — not by me. It is operationally governing. Renaming would break 9 referencing files and is a disposition decision requiring owner review ( docs/canonical/GOVERNANCE.md : autonomous deletion prohibited) DECISION REQUIRED | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0290 | 137 | Add W43 to the registry as a version REJECTED. Either breaks max() or demotes v1 to SUPERSEDED — a constitutional change v1's own law forbids and W43 never requested | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0291 | 138 | Add a wave directives key to the registry DEFERRED — DECISION REQUIRED. Cleanest model, but it changes the registry schema (schema 1 → 2), which is constitutional enforcement. Requires owner ratification and an R-series entry | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0292 | 139 | Rename W43 so it cannot be mistaken for doctrine DECISION REQUIRED. Breaks 9 referencing files; disposition of an operationally governing document is owner review under GOVERNANCE.md | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |

### `docs/governance/ORGANIZATIONAL_ARCHITECTURE_BASELINE_v0.1.md` — GOVERNANCE/DIRECTIVE, 2026-09-15 (23)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0293 | 115 | HUMAN ACCEPTED must identify D1, D2, and D3 separately; bundled silence or an unrelated approval is invalid | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0294 | 118 | Rejection, partial acceptance, requested amendment, or deferment must be recorded without rewriting proposal history | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0295 | 142 | AGENT-03 , for example, is not self-resolving; a plane-qualified identity is required | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0296 | 143 | Every declared cross-taxonomy relationship must have a mapping ID, mapping version, source/target plane, relation type, scope, decision reference, effective state, and revocation/supersession state | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0297 | 144 | Ambiguous resolution must fail closed as ROLE IDENTITY AMBIGUOUS | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0298 | 203 | Agent One must not own or exercise: | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0299 | 274 | Cursor must not be treated as: | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0300 | 285 | A future Cursor Federation Bridge must: | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0301 | 334 | Every future organizational identity reference must resolve through a record conceptually containing: | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0302 | 366 | A future command is an authenticated, authorized, scope-bounded instruction processed by the Mission Controller. It must carry, at minimum: | LEDGER (text) | IMPLEMENTED+TESTED | architecture/mission/ledger.py + scripts/mission_ledger.py + tests/test_mission_ledger.py (d1571c4) | M14 extend |  |
| AD-0303 | 408 | The implemented Slice 2B CommandEnvelope is TCB ingress and must not be silently merged with either future envelope | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0304 | 451 | The following are data or presentation only and must never constitute identity, authority, activation, verification, or acceptance: | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0305 | 474 | REQUIRED FUTURE RUNTIME PRIMITIVES | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0306 | 478 | Primitive Why it exists / failure prevented Authority it may own Authority it must not own Dependencies Verification requirement Acceptance requirement | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0307 | 597 | Future implementation must compile these into typed policy/schema/tests without weakening semantics. Adding test code does not by itself advance the decision state | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0308 | 693 | To advance state, the new record must contain decision ID, accepted text/version/hash, scope, human principal identity through an accepted mechanism, timestamp, conditions, objections/amendments, and supersession rules | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0309 | 697 | The rows below trace architectural findings; they do not assert that any agent accepted D1, D2, D3, or this document | GOVBOUND (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0310 | 703 | Agent-05 Epistemic Reasoning evidence/claim/decision distinctions; Agent One must not be truth root I-EPI- ; D2 no promotion/verification/acceptance | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0311 | 708 | Agent-10 Token Security Intelligence Agent-03 and Agent-10 security domains are distinct; findings do not become scam/execution authority D1 no role collapse; D2 no decision/execution | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0312 | 714 | Agent-15 Prompt/Instruction/Delegation prompt is not authority/capability; command differs from request; MC must mediate D2/D3; I-CMD- ; envelope requirements | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0313 | 715 | Agent-16 Independent Verification 251 substrate tests do not prove organizational readiness; no IV dispatch; Dual-19 unresolved acceptance state separation; D1; verification preconditions | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-0314 | 745 | This proposal is immutable as a historical version once reviewed. Amendments produce a new version or explicit amendment record; they do not silently rewrite acceptance history | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0315 | 804 | NO HUMAN ACCEPTANCE SHALL BE IMPLIED FROM THIS DOCUMENT | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |

### `docs/supervision/LATEST_DIRECTIVE_FOR_AHOS_AGENT.md` — GOVERNANCE/DIRECTIVE, 2026-09-13 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0316 | 30 | S20-1 Lane A — DO NOT touch | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |

### `reports/grok/OWNER_DIRECTIVE_MISSION_PLAN.md` — GOVERNANCE/DIRECTIVE, 2026-10-03 (8)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0317 | 6 | PLANNED < PARTIAL < IMPLEMENTED < TESTED < VERIFIED < OPERATIONAL. Never PLANNED=DONE, never CODE EXISTS=OPERATIONAL | TEST (text) | MERGED (source ref on existing row) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all | same requirement as OD-284 (source ref added) |
| AD-0318 | 42 | Human-gated: SKIP and list (never done by agents | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0319 | 66 | Docker/n8n files. Launcher (now M11) must NOT need Docker. Order: M9 truth - M10 de-Docker/de-n8n - M11 one-click launcher - M12 agents | PERSIST (text) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |
| AD-0320 | 104 | De-Docker (M10) is lower-risk than it looks. Postgres was never live on | RISKGOV (text) | EXISTS-PARTIAL (reuse/extend) | architecture/risk/engine.py, paper_trading/risk.py; not independent governor | M13 |  |
| AD-0321 | 146 | HARD RULE — search first, extend, never duplicate (applies to every mission | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |
| AD-0322 | 147 | Before building anything, Claude must search the repo ( rg -i <concept across architecture/, agent org/, ahos org/, | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0323 | 174 | Each mission must tick off its rows. At mission close, update the Status/Evidence cells of the rows whose Mission column names | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0324 | 210 | Existing duplicates (do not extend the duplication; consolidate only in the named mission | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |

### `reports/grok/CLAUDE_CONTINUATION_GUIDE.md` — OWNER INSTRUCTIONS/HANDOFF, 2026-10-03 (14)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0325 | 112 | Local authenticated POST (never print the token): | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0326 | 123 | Invariants you must not break | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0327 | 131 | Refusal, proposal and confirmation texts are locked: true and are never phrased by an LLM | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0328 | 138 | Decision, trading and telegram code must not import it, and it must not import them (static tests pin this | TG (text) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |
| AD-0329 | 151 | Phrased HTML is rebuilt from escaped plain text ( phrasedHtml ); phraser HTML is never trusted | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0330 | 157 | Only the helper processes architecture/ai/gemini phraser.py and architecture/ai/gemini chat.py call get secret ; Node never sees the key. gemini phraser.ts::HELPER MODULES whitelists the spawnable modules | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0331 | 161 | The audit stores hashed ids and the text length/sha only, never raw text | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0332 | 348 | News and replies with links are never phrased | NEWS (text) | EXISTS-PARTIAL (reuse/extend) | architecture/intel/news.py, c62340c narrative RSS into scoring, root news.ts; paid credential gated | M18 |  |
| AD-0333 | 386 | NEW NUMBER : every number must appear in tool output, the user message or earlier assistant turns. Persian and Arabic digits and separators are normalized; rounded and هزار/میلیون/میلیارد/تریلیون scaled forms are accepted; 0–10 is always allowed | TG (text) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend | ; also: reports/grok/GROK_HANDOFF.md:385 |
| AD-0334 | 397 | Telegram user id must be in TELEGRAM ADMIN USER IDS ∪ TELEGRAM ALLOWED CHAT IDS . If both are empty, nobody qualifies | TG (text) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend | ; also: reports/grok/GROK_HANDOFF.md:396 |
| AD-0335 | 456 | To add a command: add it to ActionKind plus PROPOSE TOOLS plus CAPABILITY plus defaultActionDeps (must reuse the dashboard route function), plus selftests for confirm/cancel/expiry/non-owner. It must be PAPER ONLY and needs review | LIVEOFF (text) | IMPLEMENTED+TESTED | PAPER_ONLY markers + tests (12 test files, e.g. tests/test_paper_api_security_gate.py); M9.5 0638643 | keep |  |
| AD-0336 | 481 | Not verified: no live gateway POST this run. A real «دانشگاه رو بساز» → code → «تایید CODE» → queued line round trip is still unverified. A gateway reload loses only pending proposals, never queued missions (on disk | UNI (text) | MISSING→added to plan | docs-only: reports/grok/UNIVERSITY_AND_AGENTS_DISCOVERY.md (3eea757); reuse architecture/cognitive/self_research.py + strategy_lab/ + research_worker/ as the Un | M16 |  |
| AD-0337 | 644 | Each mission must tick off its rows. At close, update the Status/Evidence cells of every row whose Mission column names the | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0338 | 646 | HARD RULE — search first, extend, never duplicate. Before building anything: | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `reports/grok/GROK_HANDOFF.md` — OWNER INSTRUCTIONS/HANDOFF, 2026-10-03 (23)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0339 | 23 | Identity is now server-proven, never claimed (B1/BL-3, M1/MJ-6): isOwner | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0340 | 35 | Secrets never leave the boundary (M2/BL-1/BL-2, m3/m4, MJ-5, MN-5): | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0341 | 280 | NameError , never triggered because the council has never run on a real | COUNCIL (text) | EXISTS-PARTIAL (reuse/extend) | architecture/ai/council_live.py, architecture/ai/debate_council.py, council.ts, tests/test_ai_council_live.py, test_multi_mind_council_anti_echo.py | M15 |  |
| AD-0342 | 343 | Recorded missions are never shown as done; there is deliberately no DONE/COMPLETED status | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0343 | 562 | New stop loss intent (presentation routing only): asks which token, shows only the recorded invalidation condition, never invents a number | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |
| AD-0344 | 606 | The phraser never decides anything and never sees credentials | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0345 | 613 | Independent review is required before enabling | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0346 | 659 | "stop loss", "stoploss", "start-up", "restart", "توقف ضرر" never match | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |
| AD-0347 | 664 | The client channel field is never a grant: it is recorded as channel claimed only | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0348 | 719 | Live E2E: OWNER ACTION REQUIRED . Follow reports/grok/G11 LIVE E2E RUNBOOK.md . Its port override is the bot-session $env:AHOS GATEWAY URL="http://127.0.0.1:3500/api/chat" ; service.py ignores AHOS GATEWAY PORT . .env is unchanged | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0349 | 768 | The four agent taxonomies are referenced, not merged . CURRENT AGENT must be namespaced as engineering: , agent: , AG: , AGENT: , agent.org: or M0: , and a bare "01" is rejected. Every entry carries agent taxonomy ref = docs/governance/agent taxonomy map.json | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0350 | 813 | The interface has no raw getter. SecretValue never prints its value and cannot be pickled | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0351 | 816 | The Persian new-key message tells the owner to use Credential Manager target AHOS/ai/<provider , and never to paste the key in chat, Telegram or .env | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0352 | 873 | GM-02 Telegram offline edge harness IMPLEMENTED VERIFIED (offline/self-test only); live E2E = LIVE E2E UNVERIFIED / OWNER ACTION REQUIRED 552eda | TG (text) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |
| AD-0353 | 875 | GM-05 gateway port single source + diagnosis IMPLEMENTED VERIFIED (self-tests + one real read-only diagnosis run); port choice = OWNER ACTION REQUIRED 06e44e | SELFDIAG (text) | EXISTS-PARTIAL (reuse/extend) | engine/health_manager.py, architecture/runtime/observability_snapshot.py, scripts/gateway_port.py (06e44e6) | M11/M14 |  |
| AD-0354 | 885 | TelegramAuditLog (in-memory, plus an optional append-only JSONL; hashed ids, length and sha of the text, never raw text | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0355 | 904 | Live Telegram E2E (G11) stays LIVE E2E UNVERIFIED / OWNER ACTION REQUIRED . The running bot only picks this up after the owner restarts it; Grok restarted nothing | TG (text) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |
| AD-0356 | 944 | CLI: --json , --url-only , --env-file . It never writes anything | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0357 | 949 | The historical .env persistence of the 3000 default happens only when source = DEFAULT, never for a port override | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0358 | 963 | OWNER ACTION REQUIRED: choose one: | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0359 | 1001 | Gateway port: .env says 3000, the listener is on 3500. OWNER ACTION REQUIRED (restart on 3000, or set AHOS GATEWAY PORT/URL | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0360 | 1002 | G11 live Telegram E2E: LIVE E2E UNVERIFIED / OWNER ACTION REQUIRED | TG (text) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |
| AD-0361 | 1084 | Calibration sufficiency: NOT proven; never report CLOSED | CALIB (text) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |

### `AHOS_ROADMAP_v3.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-18 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0362 | 98 | Any Lane-A need ⇒ governance proposal (freeze regeneration), never a silent edit | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |

### `docs/architecture/F1_RESOLUTION_PLAN.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0363 | 44 | Invariants (must hold at EVERY stage — a breach aborts the stage | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |
| AD-0364 | 48 | I4 Claim honesty: docs never state "trigger-guarded" beyond measured coverage at that stage | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0365 | 54 | S2–S4: PG side is additive; rollback = stop mirroring; SQLite never destroyed (destruction is | PERSIST (text) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |

### `docs/architecture/unified_control_plane.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (6)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0366 | 7 | The operator NEVER manually starts Python agents, stores, routers, red team, n8n, or probes | PERSIST (text) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |
| AD-0367 | 16 | ENTER the runtime; every other agent is REPORTED as REGISTERED/NOT IMPLEMENTED, never pretended | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0368 | 32 | A SAFE HALTed run is NEVER replayed as success: a later START after recovery executes anew | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0369 | 37 | PHASE SKIPPED RESUME events; health is ALWAYS re-measured (never cached truth); activations are | LEDGER (text) | IMPLEMENTED+TESTED | architecture/mission/ledger.py + scripts/mission_ledger.py + tests/test_mission_ledger.py (d1571c4) | M14 extend |  |
| AD-0370 | 54 | BLOCKED NO HOST and every unprobed health is UNKNOWN (test real config boot never fabricates online | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0371 | 55 | The plane never fabricates ONLINE. In this repo reality the deterministic Lane-A core continues | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |

### `docs/mission_v1_1/A_CURRENT_PAL_AUDIT.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0372 | 38 | Ankr public EVM 200 but JSON-RPC error "must authenticate" no longer free-anonymous → reclassify PAID-KEY tier | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |
| AD-0373 | 44 | PAL must be built now as REAL code (STEP 3 prerequisite), not deferred into n8n nodes | PERSIST (text) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |

### `docs/mission_v1_1/B_CURRENT_E01_AUDIT.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0374 | 30 | B.3 What E-01 must NOT become (council red lines | COUNCIL (text) | EXISTS-PARTIAL (reuse/extend) | architecture/ai/council_live.py, architecture/ai/debate_council.py, council.ts, tests/test_ai_council_live.py, test_multi_mind_council_anti_echo.py | M15 |  |
| AD-0375 | 32 | Not a single-run scrape: observations must be replayable with raw payloads retained (integrity like MANIFEST | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0376 | 33 | Not a silent-failure system: every provider error → error state row, never a fabricated NULL-as-pass | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |

### `docs/mission_v1_1/B_DUPLICATE_REDUNDANCY_REPORT.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0377 | 21 | Component marks: report LIVE VERIFIED · uploads deletion UNKNOWN→user decision (never autonomous, Part XXVII | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/mission_v1_1/C_DISCOVERY_DATA_MODEL.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0378 | 9 | Rationale: provider-pair addresses change, token contracts do not; ID must be stable across providers | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0379 | 63 | Provider-reported changes (price change ) stored as-reported for snapshot consistency; recomputed-from-series variants are separate features (D), never overwriting raw fields | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |

### `docs/mission_v1_1/D_FEATURE_STORE_SCHEMA.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0380 | 50 | Tests: synthetic future-injection fixture (observation with retrieved ts as of must never affect output; | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/mission_v1_1/E01_GATE_PROTOCOL_v1.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0381 | 8 | Report. This protocol binds INTERPRETATION only; it never changes the frozen pipeline | DAILY (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/reports.py, engine/research_report_bot.py, TELEGRAM_RESEARCH_REPORT | M17 |  |
| AD-0382 | 27 | Escaping it requires MORE DATA (future windows/cohorts), never edits | ONECLICK (text) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |

### `docs/mission_v1_1/E_FEATURE_EXPANSION_PLAN.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0383 | 10 | HOLDER holder growth (total count), holder survival — MISSING-by-platform: free RPC cannot count holders (getProgramAccounts cost-blocked publicly) → UNKNOWN documented, never faked | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0384 | 23 | Registry ⇄ computed-set equality (D-doc law) · leakage tests per new feature · missing→absent (never 0-fill) · | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |

### `docs/mission_v1_1/E_SECURITY_GATE_DESIGN.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0385 | 29 | SOL tokens meanwhile always get RugCheck (VERIFIED) + UNKNOWN for GoPlus-only checks (never inferred | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0386 | 34 | Gate NEVER upgrades UNKNOWN→PASS silently; re-verification only with fresher evidence (new row, old kept | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0387 | 37 | Veto fixtures: synthetic contracts emulating known patterns (honeypot sim response, mint-active RugCheck payload, LP-unlocked young pool, prior-rug creator) — target 100% veto on fixture set (Phase-3 exit; labeled FIXTURE forever, never "real scam detection rate" | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |

### `docs/mission_v1_1/F12_DECISION_MEMO.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0388 | 1 | F12 — DECISION MEMO: tracked/active-cohort observation starvation (OWNER DECISION REQUIRED | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0389 | 67 | Any approval must name: option, activation time, disclosure ack — and it will be executed as a | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0390 | 89 | DEGRADED (fresh share 0.727; 580 gaps churned in last 24h — must fall as poller cadence serves | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/mission_v1_1/F_PUMP_EVENT_RESEARCH_SPEC.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0391 | 23 | A raw +100% in an illiquid token is NEVER equated to a healthy opportunity (Part III rule embedded as | SELFDIAG (text) | EXISTS-PARTIAL (reuse/extend) | engine/health_manager.py, architecture/runtime/observability_snapshot.py, scripts/gateway_port.py (06e44e6) | M11/M14 |  |

### `docs/mission_v1_1/F_STATE_MACHINE_72H.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0392 | 13 | Any state → REJECTED? — no : candidates are never "rejected" from history; they RESOLVE with outcomes | LEARN (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/prediction_lifecycle.py, 202f8c9 learning bridge | M13 |  |

### `docs/mission_v1_1/G_BASELINE_LIFT_DESIGN.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0393 | 2 | Implemented: research/baseline stats.py (+ tests). Rule: never evaluate a signal without a baseline | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0394 | 9 | Wilson 95% CI for both rates · sample sizes printed ALWAYS · regime stratum = {chain × week} (v | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0395 | 30 | Strata ALWAYS include dead/rugged/flat/security-failed tokens (lifecycle states + veto flags are in-store | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |

### `docs/mission_v1_1/G_PROVIDER_MATRIX.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-20 (4)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0396 | 4 | Cost ceiling: $0/month — Tier-4 (paid) never a hard dependency | RES2ARCH (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0397 | 16 | Paid DEXTools/CMC APIs — 🚫 excluded ($) — — never required | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |
| AD-0398 | 25 | Paid Chainalysis/TRM etc. 🚫 never | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |
| AD-0399 | 73 | Every response → raw payloads (sha256) before normalization; parse failures produce error state, never silent | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |

### `docs/mission_v1_1/H_COUNCIL_15_EXECUTION_MODEL.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0400 | 33 | They never write to the repo, never set numbers, never count as verification. Council-of-record = this | COUNCIL (text) | EXISTS-PARTIAL (reuse/extend) | architecture/ai/council_live.py, architecture/ai/debate_council.py, council.ts, tests/test_ai_council_live.py, test_multi_mind_council_anti_echo.py | M15 |  |
| AD-0401 | 38 | Fabrication incidents: must be 0 · Silent-failure incidents: must be | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/mission_v1_1/H_H14_GENERATION_DESIGN.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0402 | 14 | Minimum cell stats: F §5 (n≥200, positives≥20) else cell = INSUFFICIENT DATA (never mined harder | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |
| AD-0403 | 17 | OOS cohort = strictly LATER calendar weeks (time-split, never random-split here | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |
| AD-0404 | 24 | What auto-generation will NEVER do | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |

### `docs/mission_v1_1/I_HOLDER_WHALE_ARCHITECTURE.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0405 | 31 | WalletReputation is DERIVED, never manual: | CHAINS (text) | EXISTS-PARTIAL (reuse/extend) | architecture/providers/ (pumpfun, dex_pools, coingecko, defillama, chain_explorer), discovery/providers.yaml | M13/M18 |  |

### `docs/mission_v1_1/I_TELEGRAM_PERSIAN_CONTRACT.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0406 | 15 | Parsed-confidence < 0.7 or ambiguous token ⇒ clarifying question (never guess financial records | CALIB (text) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |

### `docs/mission_v1_1/J_IMPLEMENTATION_PLAN.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0407 | 20 | STEP 9 ranking never shows score to user surfaces yet (research gate law); ranks+bullets only | SCORING (text) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |

### `docs/mission_v1_1/J_SOCIAL_NARRATIVE_ARCHITECTURE.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0408 | 24 | Two distinct feature families, never merged upstream: | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |

### `docs/mission_v1_1/K_TELEGRAM_AI_IMPLEMENTATION_PLAN.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0409 | 5 | An LLM output can never mutate a financial record without schema validation + user confirmation | TG (doc) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |
| AD-0410 | 28 | NO AI call is required for system operation (cost-zero + Iran-resilient by construction | TG (doc) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |
| AD-0411 | 31 | Intent schema whitelist (unknown intent ⇒ clarify; never execute-side effects | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/mission_v1_1/L_COUNCIL_WAVE6_DECISION_LOG.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0412 | 2 | Chain: Producer → Critic → Quant → Security → Red-Team → QA → Auditor. Disagreements recorded (never hidden | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0413 | 9 | Security (14) RESERVATION: docs/ISSUES REGISTER.md stub must keep the exact archive path (it does); | SYNC (text) | EXISTS-PARTIAL (reuse/extend) | scripts/doc_drift.py, docs/CANONICAL_IMPLEMENTATION_MATRIX.md, reports/grok/GROK_HANDOFF.md, d2aa09b (12 stale maps bannered) | all + M14 |  |

### `docs/mission_v1_1/W10_ARCHITECTURE_READINESS.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (12)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0414 | 39 | Statuses are re-affirmed, never promoted: 8 EXISTS / 13 PARTIAL / 2 PLANNED / 1 MISSING | SELFIMP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0415 | 77 | /200 ⇒ all cells honest). → Fallback: gated null verdicts. → Boundary: never auto-promotes a | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0416 | 113 | OBSERVE+ANALYZE. Failure: worst-case-first; TRAPPED never guessed from UNKNOWN. Fallback: | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0417 | 130 | UNAVAILABLE NO FEED (live in reports ✓). Fallback: UNAVAILABLE class. Boundary: never promotes | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0418 | 156 | Failure: conflicts recorded, never averaged. Fallback: SINGLE SOURCE label. Boundary: outputs | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0419 | 164 | CHALLENGE + VETO over CLAIMS (never data) ✓. Verdict enum fixed: REJECT/INVALID/ | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0420 | 166 | Boundary: vetoes claims/promotions, never edits. Deps: evidence stores. Missing: runtime | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0421 | 199 | Inputs: AG-16 closes. Authority: ANALYZE+ADVISE. Failure: hypotheses never auto-promote ✓ | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0422 | 215 | Boundary: proposals never touch frozen artifacts. Deps: AG-14, AG-18, human gate. Missing: | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-0423 | 302 | Evidence ids are not resolvable at rest (design limit; runtime must resolve them | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0424 | 315 | F5 MEDIUM authority ambiguity: AG-23 holds PROMOTE (human-only law) without human gate marker; AG-09's deterministic VETO unnamed in W9 §2 text yaml vs W9 doc Amend W9 authority text to recognize deterministic safety vetoes; add human gate: true in v2 spec for AG-23; never implement AG-23 as software | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0425 | 340 | B1 F1 trigger overclaim W10A-02 HIGH pick remediation (a) text-truth or (b) owner-approved migration; P3 ledger must not rest on overstated immutability owner (if b) run-ledger integrity claims would inherit a false premise | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/mission_v1_1/W11_UNIFIED_RUNTIME_ARCHITECTURE.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0426 | 81 | F5 (PROMOTE holder): AG-23 documented as human gateway; NEVER-to-be-software law recorded in ops | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |

### `docs/mission_v1_1/W13_REALITY_AUDIT.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0427 | 37 | DAG acyclic (CI-pinned). Only AG-15/16 hold DECIDE; AG-23 = human gateway (never software); | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |

### `docs/mission_v1_1/W7_B_H14_RESEARCH_PLAN.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0428 | 36 | Time-split OOS only (never random split); multiplicity budget = registry cells (9 total: 2 B1 + 7 B | RESSTD (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |

### `docs/mission_v1_1/W7_C_TELEGRAM_AI_ARCHITECTURE.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0429 | 9 | DETERMINISTIC COMMAND LAYER — routes ONLY on rule hits; UNKNOWN ⇒ clarify, never guess — B Implemented | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0430 | 26 | Degradation ladder (never stops answering — directive § | TG (doc) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |

### `docs/mission_v1_1/W7_F_DOC_HYGIENE_POLICY_V2.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (6)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0431 | 6 | A CANONICAL — current authority. Automation NEVER archives A | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0432 | 8 | C HISTORICAL EVIDENCE — decisions, failures, negative results, probes, audit. NEVER removed | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0433 | 15 | NEVER delete: negative evidence, failed experiments, rejected hypotheses (H1–H13…), audit | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0434 | 19 | Reversibility: E/F-moves are archives (content intact); G-deletions must be REGENERABLE | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |
| AD-0435 | 21 | Ambiguous ⇒ ARCHIVE, never delete. F-class ⇒ no autonomous deletion, ever | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |
| AD-0436 | 27 | Idempotency is a release gate: a second dry run must plan 0 actions | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |

### `docs/mission_v1_1/W7_G_CLEANUP_EXECUTION_REPORT.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0437 | 14 | C HISTORICAL 152 13.40 MB preserve (never auto-removed | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |

### `docs/mission_v1_1/W7_H_CANONICAL_KNOWLEDGE_MAP_V2.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0438 | 27 | Canonical docs reference Tier-2/3 by PATH, never copy content. Duplicate-statements found during | ROADMAP (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/MISSION.md, docs/canonical/ROADMAP.md, AHOS_ROADMAP_v3.md | M9 (done) / all |  |

### `docs/mission_v1_1/W7_I_POSITION_MONITORING_SPEC.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0439 | 16 | — if the token is outside E-01 coverage: state UNKNOWN, never fabricated. Fiat conversion for | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/mission_v1_1/W7_K_COUNCIL_DECISION_LOG.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0440 | 43 | Red Team: verify gluing features+outcomes in one module doesn't violate L2 (feature store must not | LEARN (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/prediction_lifecycle.py, 202f8c9 learning bridge | M13 |  |

### `docs/mission_v1_1/W9_COGNITIVE_ARCHITECTURE.md` — PLAN/ROADMAP/MISSION PLAN, 2026-08-16 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0441 | 9 | DESIGN+isolated code. Lane B must not alter the E-01 execution path; promotion only via | SELFIMP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0442 | 14 | Named persons are intellectual provenance only ( source inspiration ), never authority | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0443 | 21 | Red Team: CHALLENGE + VETO(claims/promotions) — never data/rule edits | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `reports/agi_aci_evolution/BENCHMARK_PLAN.md` — PLAN/ROADMAP/MISSION PLAN, 2026-09-09 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0444 | 4 | Law: Synthetic data must be labeled SYNTHETIC/SIMULATION/TEST. Real soak rows remain distinct. Do not consume soak in a way that changes experimental semantics | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0445 | 24 | External AI/tool baseline only with labeled TEST packets — never as soak truth | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0446 | 37 | B-WM-01 Causal/CF quality — ACI-GAP-002; do not fake | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |

### `reports/agi_aci_evolution/PR93_DOCUMENTATION_RECONCILIATION_PLAN.md` — PLAN/ROADMAP/MISSION PLAN, 2026-09-11 (19)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0447 | 82 | P5 FINAL CLOSURE GATE REVIEW.md 1 + 6 Security-exit decision Historical of the gate SECURITY-EXIT-CANDIDATE n/a NO Living indexes point here ; they do not copy-rewrite it | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |
| AD-0448 | 112 | Untracked next-env.d.ts , reports/PRE SOAK STATUS.txt : not documentation surfaces ; must not be added | DAILY (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/reports.py, engine/research_report_bot.py, TELEGRAM_RESEARCH_REPORT | M17 |  |
| AD-0449 | 118 | MUST NOT rewrite (PROHIBITED). Preserve original test counts, FAIL/C1 findings, and “unimplemented” design-gate language | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0450 | 132 | A historical report that says 28 or 1954 passed, 2 failed is not stale . It is a snapshot. Living indexes must cite later reports rather than “correct” the old ones | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0451 | 182 | Keep the existing 28/195 block underneath, retitled as a snapshot (title tweak of the living file’s new heading is OK; changing the numbers inside the old block is PROHIBITED | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0452 | 253 | The proposed title does represent the PR vs main at professional length. The body must still spell the progression | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0453 | 265 | Tests — scoped counts from §5 (2065 total repo; 308 P5-named collected; do not say “2065 P5 tests” | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0454 | 277 | Rewrite any historical audit/implementation/forensic conclusion PROHIBITED | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0455 | 278 | Change 28, 195, 187, 1954, 2008, 2042, etc. inside historical reports or inside the existing TEST EVIDENCE snapshot block PROHIBITED | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0456 | 279 | Replace “28 tests” with “2065 tests” as if the same scope PROHIBITED | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0457 | 280 | Delete or rename evidence files / JSON PROHIBITED | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0458 | 281 | Close ACI-GAP-002 (charter world model) because evolution P5 advanced PROHIBITED | SELFIMP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0459 | 282 | Edit Lane A, soak, freeze hashes PROHIBITED | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-0460 | 283 | Edit PHASE STATE / ops ROADMAP “P5 Telegram/n8n” to mean ObservationGrant PROHIBITED | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0461 | 284 | Rewrite AHOS COGNITIVE LOOP ARCHITECTURE v1.0.md into a V4-PIN spec PROHIBITED (pointer from truth map instead | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0462 | 285 | Claim merge, Ready, production, live trading, AGI, ACI PROHIBITED | LIVEOFF (text) | IMPLEMENTED+TESTED | PAPER_ONLY markers + tests (12 test files, e.g. tests/test_paper_api_security_gate.py); M9.5 0638643 | keep |  |
| AD-0463 | 286 | Modify production code, tests, architecture, PR title/body in the documentation-index implementation step without a separate explicit metadata task PROHIBITED for the index patch; PR metadata is a later separate step | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0464 | 287 | Implement this plan in the same commit as the plan itself PROHIBITED (this file is plan-only | GIT (text) | EXISTS-PARTIAL (reuse/extend) | CLAUDE_CONTINUATION_GUIDE.md commit rules, .cursor/hooks.json ahos-guard | all |  |
| AD-0465 | 297 | Documentation consistency audit (read-only): living files vs HEAD counts vs “do not imply merge”; confirm historical files unchanged ( git diff should not touch P5 V3 , forensics, records 0008–0010 bodies, JSON | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |

### `reports/grok/_claude_task_10.txt` — PLAN/ROADMAP/MISSION PLAN, untracked (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0466 | 1 | You are continuing AHOS engineering in G:\robat\ahos (branch ahos), driven headless by Grok. Work fully autonomously; do not ask questions | GIT (text) | EXISTS-PARTIAL (reuse/extend) | CLAUDE_CONTINUATION_GUIDE.md commit rules, .cursor/hooks.json ahos-guard | all | ; also: reports/grok/_claude_task_11.txt:1, reports/grok/_claude_task_8.txt:1, reports/grok/_claude_task_9.txt:1, reports/grok/_claude_task_9_5.txt:1 |

### `reports/grok/_claude_task_9_5.txt` — PLAN/ROADMAP/MISSION PLAN, untracked (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0467 | 10 | M1: owner = TELEGRAM ADMIN USER IDS only (not ALLOWED CHAT IDS). If TELEGRAM ADMIN USER IDS is empty, set it in .env from the existing allowed owner id ONLY if unambiguous (exactly one id); it is a config value; never print any other .env value. If ambiguous, leave it, fail closed, and record it as an owner action item | TG (text) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |

### `AHOS_SELF_REPAIR_DESIGN.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0468 | 8 | Never Modify Automatically ❌: Files and databases are NEVER modified automatically without explicit user confirmation ( --repair --confirm | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |

### `architecture/knowledge/EVIDENCE_GRAPH.md` — SUPPLEMENTARY/ANNEX, 2026-09-12 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0469 | 27 | Provider- VERIFIED evidence maps to DERIVED , never OBSERVED | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0470 | 48 | A graph ID is never a canonical token identity | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |

### `architecture/knowledge/FEEDBACK.md` — SUPPLEMENTARY/ANNEX, 2026-09-12 (4)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0471 | 33 | W3 never assigns OBSERVED , FACTUAL , FACTUAL PREMISE , or VERIFIED | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0472 | 37 | Copied authoritative state (decision, security, identity) is never | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0473 | 49 | "Human said X" is never rewritten as market evidence | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0474 | 54 | W3 never calls now() . Feedback time is not event, prediction, observation, | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/ARCHITECTURE_FINAL.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0475 | 23 | P2 Validation Plan-Phase 2/3 backtest + OOS + WF + MC on real data PARTIAL → REBUILD REQUIRED (baseline failed gates on 83d; 3yr data absent | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0476 | 42 | Secrets only in .env (+n8n credential store), never in repo/JSON/logs/telegram | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0477 | 52 | CI gate before any delivery: engine/run all checks.sh (4 checks must be green | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |

### `docs/CANONICAL_COMMAND_REFERENCE.md` — SUPPLEMENTARY/ANNEX, 2026-09-26 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0478 | 27 | Live trading Disabled at every layer. Any command that would enable it is forbidden ( AGENTS.md §Safety | LIVEOFF (text) | IMPLEMENTED+TESTED | PAPER_ONLY markers + tests (12 test files, e.g. tests/test_paper_api_security_gate.py); M9.5 0638643 | keep |  |
| AD-0479 | 198 | Never force-push, never auto-merge, never push to main without review | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0480 | 209 | /home/user/ahos paths in reports/ .json , research/experiments/ .json , docs/mission v1 1/ Historical evidence. These recorded where data lived on the original Linux host. They must not be rewritten — rewriting historical evidence is forbidden. config/paths.py already eliminates the hard-coded dependency at runtime | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/CANONICAL_IMPLEMENTATION_MATRIX.md` — SUPPLEMENTARY/ANNEX, 2026-10-03 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0481 | 49 | Owner action consolidator Ops One OWNER checklist docs/OWNER ACTION REQUIRED.md same — Added 2026-08-27 COMPLETE — — — Owner executes OA | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0482 | 53 | Calibration measurement Learning Score vs outcome Framework COMPLETE architecture/learning/ calibration tests CALIBRATION READY BUT DATA REQUIRED PARTIAL Local pairs High Owner OA-4 Accrue evidence | CALIB (text) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0483 | 81 | Not closable without owner/external: M-GAP-003, 004, 008, 009, 010 residual; M-GAP-007 residual laptop re-probe (agent-host MITIGATED). See docs/OWNER ACTION REQUIRED.md | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |

### `docs/COUNCIL_15_DESIGN.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0484 | 3 | Disagreements recorded (never hidden); unresolved ⇒ artifact stays CANDIDATE | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0485 | 15 | AI/ML Engineer FREE-tier-only advisory layer (narrative summaries); never numeric authority AGENT-02 advisory | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |

### `docs/OPPORTUNITY_SCORE_DESIGN_v0.1.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0486 | 35 | System MUST be able to emit "NO OPPORTUNITY" as a first-class successful output | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/SECURITY_CHECKLIST.md` — SUPPLEMENTARY/ANNEX, 2026-08-27 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0487 | 6 | Current operator actions: docs/OWNER ACTION REQUIRED.md · AHOS GAP REGISTER.md · docs/DOC TRUTH MAP.md | SYNC (text) | EXISTS-PARTIAL (reuse/extend) | scripts/doc_drift.py, docs/CANONICAL_IMPLEMENTATION_MATRIX.md, reports/grok/GROK_HANDOFF.md, d2aa09b (12 stale maps bannered) | all + M14 |  |

### `docs/SECURITY_SCORE_DESIGN_v0.1.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0488 | 21 | Recommendation ceiling: any UNKNOWN hard-veto check ⇒ recommendation ≤ WATCH (never HIGH-RISK-ENTRY | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/STRATEGY_SPEC_v1.0.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0489 | 18 | SL = entry ± 1.5 × ATR14[signal] (fixed at entry; never widened | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0490 | 30 | Leverage: 2x fixed (5x cap absolute; 10x never in micro-capital mode | RISKGOV (text) | EXISTS-PARTIAL (reuse/extend) | architecture/risk/engine.py, paper_trading/risk.py; not independent governor | M13 |  |
| AD-0491 | 38 | Removed rows (bad OHLCV) are registered, never replaced | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |

### `docs/agents/AGENT_ORGANIZATION_README.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (4)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0492 | 109 | [AGENT SUPERVISION PROTOCOL.md](../protocols/AGENT SUPERVISION PROTOCOL.md). Default: human operator. You do not supervise yourself for verification | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0493 | 115 | [AGENT ESCALATION PROTOCOL.md](../protocols/AGENT ESCALATION PROTOCOL.md). Target is never “myself” and not Agent One while it does not exist | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0494 | 140 | Use available authorized tools to inspect technical evidence directly. If required access or capability is unavailable, report CAPABILITY GAP ; do not invent evidence or make the human a routine command relay | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0495 | 144 | Existing implemented pieces (do not mythologize | OBS (text) | EXISTS-PARTIAL (reuse/extend) | engine/health_manager.py, architecture/runtime/observability_snapshot.py, scripts/gateway_port.py (06e44e6) | M11/M14 |  |

### `docs/architecture/AGENT_01_ORGANIZATIONAL_FEDERATION_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (6)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0496 | 141 | Peer collaboration uses OrgRequestEnvelope , never MissionCommandEnvelope | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0497 | 394 | Durable memory entry must preserve: | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0498 | 460 | Failure side states: BLOCKED , FAILED , CANCELLED , TIMED OUT , SUSPENDED , QUARANTINED , RECOVERY REQUIRED | FEDSEC (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0499 | 502 | Current Plane-D runtime capabilities are empty. Architecture reports exercising READ/ANALYZE/PROPOSE do not self-issue runtime grants. Missing commander, charter, capability record, or plane binding blocks activation | DAILY (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/reports.py, engine/research_report_bot.py, TELEGRAM_RESEARCH_REPORT | M17 |  |
| AD-0500 | 604 | The durable audit must answer without Cursor transcript archaeology: | OBS (text) | EXISTS-PARTIAL (reuse/extend) | engine/health_manager.py, architecture/runtime/observability_snapshot.py, scripts/gateway_port.py (06e44e6) | M11/M14 |  |
| AD-0501 | 698 | WHAT MUST NOT BE IMPLEMENTED YET | REALCLASS (text) | EXISTS-PARTIAL (reuse/extend) | ahos_org/registry.py states, reports/grok/REMAINING_REALITY_REGISTER.md | M9 (done) / M12 |  |

### `docs/architecture/AGENT_01_ORGANIZATIONAL_FEDERATION_READINESS_MATRIX.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (4)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0502 | 53 | Organizational frontend Architecture only; trusted backend/projections absent PARTIAL design in Agent-18 NO NO NO NO — MUST NOT IMPLY LIVE STATE | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0503 | 54 | AHOS integration Intentionally absent/protected; no authorization in this mission Boundary defined NO NO NO NO — FORBIDDEN | FEDSEC (doc) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0504 | 55 | Live trading/execution Outside Agent Organization authority and prohibited here Exclusion defined NO NOT APPLICABLE NOT APPLICABLE NO — FORBIDDEN | LIVEOFF (text) | IMPLEMENTED+TESTED | PAPER_ONLY markers + tests (12 test files, e.g. tests/test_paper_api_security_gate.py); M9.5 0638643 | keep |  |
| AD-0505 | 85 | Approve the first authoritative commander relationship; do not infer it from role number | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |

### `docs/architecture/AGENT_05_EPISTEMIC_REASONING_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (39)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0506 | 36 | Agent One: NOT IMPLEMENTED / FUTURE NON AUTHORITY ROOT — must never become epistemic root of truth | GOVBOUND (text) | MERGED (source ref on existing row) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate | same requirement as OD-423 (source ref added) |
| AD-0507 | 139 | L5 AI / human discussion Proposals; never execution authority | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0508 | 140 | L6 Assumption Must be labeled; never promoted silently | SELFIMP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0509 | 153 | [IMPLEMENTED] Slice 2B TCB denies execution-class operations on protected resources. [PROPOSED] Future decision system must consume epistemic objects without inheriting their authority automatically | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0510 | 193 | Meaning: A testable proposition explicitly not established; must remain distinguishable from fact even under agreement | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |
| AD-0511 | 279 | Every path must preserve type boundaries at each hop. Shortcuts may skip stages , not distinctions | ONECLICK (text) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0512 | 334 | Evaluate evidence on independent dimensions ; do not collapse into one score without publishing the vector: | SCORING (text) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0513 | 362 | Architecture rule: confidence (if used) is a reporting annotation tied to explicit epistemic status and cited evidence IDs — never a substitute for VerificationRecord or lifecycle state | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0514 | 364 | Slice 2B assurance is not truth; module docstring: "Stored memory, confidence, recency, and audit inclusion never imply truth." | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0515 | 417 | Future Predictions only; never observations | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0516 | 427 | Stale evidence must not silently support live claims — label [STALE] in reports; TCB transitions to EvidenceState.STALE | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0517 | 476 | Missing SUPPORTED Use SUBMITTED + evidence linkage as "supported" structurally; do not treat submission as verification | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0518 | 485 | Supersession preserves lineage; do not delete rejected claims | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0519 | 509 | A hypothesis must remain distinguishable from a fact even when many agents agree with it | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0520 | 564 | Major organizational requirement: do not hide contradictions to achieve consensus | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0521 | 600 | [DOCUMENTED] Evidence Protocol contradiction block. Known org contradiction (Dual-19) must remain visible | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0522 | 633 | Rule: Confidence must not override epistemic status in gates. Promotion checks lifecycle + verification, not assurance alone | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0523 | 682 | [PROPOSED] Consensus records as Recommendation artifacts, never Knowledge | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-0524 | 745 | Rule: unverified speculation → permanent truth memory is forbidden | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0525 | 845 | Future Agent One NOT IMPLEMENTED ; may synthesize and detect contradictions; may not promote or execute | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0526 | 880 | Adversarial tests the architecture must survive: | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0527 | 914 | Unknown must remain representable. [DOCUMENTED] [UNKNOWN] token | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0528 | 915 | Uncertainty must remain representable. Separate from LOW CONFIDENCE [PROPOSED] | CALIB (text) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0529 | 916 | Contradiction must remain representable. [IMPLEMENTED] ContradictionCase | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0530 | 917 | Knowledge must be scoped and contextual. [PROPOSED] scope fields on candidates | EPIST (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0531 | 1047 | HD-01 Dual-19 resolution: merge, map, dual-run, or retire Plane A vs Plane D HUMAN DECISION REQUIRED | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0532 | 1048 | HD-02 Claim lifecycle vocabulary: adopt SUBMITTED vs add SUPPORTED state HUMAN DECISION REQUIRED | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0533 | 1049 | HD-03 Evidence taxonomy: approve orthogonal dimension model vs minimal enum HUMAN DECISION REQUIRED | TAXO (text) | EXISTS-PARTIAL (reuse/extend) | ahos_org/registry.py, docs/agents/PLANNED_19_AGENT_MAP.md, docs/governance/agent_taxonomy_map.json (e0ac1dd); all 19 at REGISTERED | M12 |  |
| AD-0534 | 1050 | HD-04 Scalar assurance: retain, restrict, or replace with quality vector HUMAN DECISION REQUIRED | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0535 | 1051 | HD-05 Chat agent → TCB artifact bridge: when planned agents may write epistemic objects HUMAN DECISION REQUIRED | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0536 | 1052 | HD-06 AHOS epistemic integration boundary (future): read-only vs mediated write HUMAN DECISION REQUIRED | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0537 | 1053 | HD-07 Contradiction state alignment: extend Slice 2B vs map documentary states HUMAN DECISION REQUIRED | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0538 | 1054 | HD-08 Adoption of this architecture doc as L2 governance text HUMAN DECISION REQUIRED | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate | ; also: docs/architecture/AGENT_06_RESEARCH_METHODOLOGY_ARCHITECTURE.md:1307, docs/architecture/AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md:1720 |
| AD-0539 | 1060 | RECOMMENDED NEXT MISSION = STATE ONLY — DO NOT EXECUTE | EPIST (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all | ; also: docs/architecture/AGENT_06_RESEARCH_METHODOLOGY_ARCHITECTURE.md:1314, docs/architecture/AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md:1726, docs/architecture/AGENT_08_CRYPTO_MARKET_INTELLIGENCE_ARCHITECTURE.md:1562, docs/architecture/AGENT_09_ON_CHAIN_INTELLIGENCE_ARCHITECTURE.md:1635 |
| AD-0540 | 1064 | FUTURE IMPLEMENTATION REQUIRED: Add orthogonal evidence metadata dimensions to Evidence (or sidecar artifacts) without breaking existing tests | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0541 | 1065 | FUTURE IMPLEMENTATION REQUIRED: Correlation cluster ID on evidence and verification for multi-agent deduplication | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0542 | 1066 | FUTURE IMPLEMENTATION REQUIRED: Prediction content-hash immutability at registration | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0543 | 1067 | FUTURE IMPLEMENTATION REQUIRED: Chat-to-TCB adapter for Response Protocol → REGISTER ARTIFACT (gated by epistemic.write | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0544 | 1068 | FUTURE IMPLEMENTATION REQUIRED: Explicit EpistemicStatus on knowledge candidates (KNOWN/UNCERTAIN/UNKNOWN/CONTRADICTORY/NOVEL | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |

### `docs/architecture/AGENT_06_RESEARCH_METHODOLOGY_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (44)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0545 | 45 | Agent One: NOT IMPLEMENTED / FUTURE NON AUTHORITY ROOT — must never become methodological authority or epistemic root | GOVBOUND (text) | MERGED (source ref on existing row) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate | same requirement as OD-423 (source ref added) |
| AD-0546 | 119 | Question must differ from desired answer Required Motivated reasoning often hides desired outcomes in framing | LEARN (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/prediction_lifecycle.py, 202f8c9 learning bridge | M13 |  |
| AD-0547 | 120 | Hypotheses must be explicit Required [IMPLEMENTED] falsification criteria required on Hypothesis in Slice 2B | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0548 | 122 | Assumptions must be explicit Required [PROPOSED] no assumption registry in code today | RESSTD (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0549 | 123 | Evidence must be traceable Required [IMPLEMENTED] provenance on artifacts; chat agents often lack TCB binding | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0550 | 137 | Methodology must preserve uncertainty Required [IMPLEMENTED] research worker emits uncertainty labels | WORKER (text) | EXISTS-PARTIAL (reuse/extend) | research_worker/ + agent_org/research_host/ (process-isolated, 5 test files) | M12 |  |
| AD-0551 | 191 | A research question must not secretly encode the desired answer (e.g., "Why is organic demand the cause of the rise?" presumes causation and desired explanation | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0552 | 218 | Rule: Hypothesis ≠ Fact — even SUPPORTED or TESTING states in Slice 2B do not equate to knowledge ( [IMPLEMENTED] lifecycle; epistemic promotion is separate | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0553 | 239 | Falsification criteria must be observable and prior to seeing results. Criteria like "if wrong, we'd notice eventually" are insufficient | OBS (text) | EXISTS-PARTIAL (reuse/extend) | engine/health_manager.py, architecture/runtime/observability_snapshot.py, scripts/gateway_port.py (06e44e6) | M11/M14 |  |
| AD-0554 | 257 | Where reasonable alternatives exist, researchers must enumerate and discriminate among them — not adopt the first plausible explanation | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0555 | 273 | Research plans must include a competing-hypothesis section with: | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0556 | 313 | Confirmatory research should not execute until method review passes (§31). Exploratory research may proceed with lighter plan but must be labeled | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0557 | 362 | Confounders Common causes of X and Y — must be measured or blocked | RESSTD (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0558 | 367 | Temporal precedence Cause must precede effect in time | RESSTD (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0559 | 495 | Every research report must state: | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0560 | 589 | All multi-source crypto research must document: | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0561 | 597 | Price or volume anomalies require competing hypotheses (§8) before narrative assignment. Methodology must not default to "organic" or "manipulation" without discrimination tests | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0562 | 614 | Evaluation: This scale is appropriate with the caveat that not every question requires Level 5. Research plans must declare target level and achieved level honestly | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0563 | 635 | When replication is required [PROPOSED] | RESSTD (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0564 | 645 | Independent replication must not : | RESSTD (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0565 | 678 | Contradictory finding ContradictionCase ; do not delete prior | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0566 | 755 | Exploratory research is valuable but must not be relabeled confirmatory after seeing results | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0567 | 840 | Do not reduce all priorities to a single opaque score without tradeoff documentation. Multi-criteria framing with explicit tradeoffs is required | SCORING (text) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0568 | 877 | Every research agent report must be able to state: | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0569 | 897 | Research agents must NOT silently claim: | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0570 | 906 | RESEARCH ANALYST AGENT enforces subset via fixed interpreter rules ( [IMPLEMENTED] ): never emits VERIFIED , PROMOTED , AUTHORIZED , etc | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0571 | 936 | Multi-agent studies must document shared sources and adjust independence claims accordingly | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0572 | 1281 | What minimum RQ level is required for each epistemic promotion tier (coordination with Agent 05)? | SELFIMP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0573 | 1298 | HD-01 Dual-19 resolution: impact on methodology role ownership (Plane A vs Plane D) HUMAN DECISION REQUIRED | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-0574 | 1299 | HD-02 Adopt RQ maturity model (§33) as organizational vocabulary HUMAN DECISION REQUIRED | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0575 | 1300 | HD-03 Pre-registration policy: mandatory for confirmatory research or optional HUMAN DECISION REQUIRED | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0576 | 1301 | HD-04 Minimum reproducibility level by research class (exploratory vs confirmatory vs ML) HUMAN DECISION REQUIRED | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0577 | 1302 | HD-05 Method review gate: who performs it (Agent 06 documentary vs Agent 16 vs human) HUMAN DECISION REQUIRED | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0578 | 1303 | HD-06 Failure taxonomy: adopt closed enum in ExperimentRun.failure class HUMAN DECISION REQUIRED | TAXO (text) | EXISTS-PARTIAL (reuse/extend) | ahos_org/registry.py, docs/agents/PLANNED_19_AGENT_MAP.md, docs/governance/agent_taxonomy_map.json (e0ac1dd); all 19 at REGISTERED | M12 |  |
| AD-0579 | 1304 | HD-07 Exploratory→confirmatory transition: require fresh data vs allow held-out split HUMAN DECISION REQUIRED | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0580 | 1305 | HD-08 MethodologyAssessment handoff schema to Agent 05 epistemic evaluation HUMAN DECISION REQUIRED | OBS (text) | EXISTS-PARTIAL (reuse/extend) | engine/health_manager.py, architecture/runtime/observability_snapshot.py, scripts/gateway_port.py (06e44e6) | M11/M14 |  |
| AD-0581 | 1306 | HD-09 Crypto data provider reconciliation hierarchy (when providers disagree) HUMAN DECISION REQUIRED | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0582 | 1308 | HD-11 Resource budget defaults by decision impact tier HUMAN DECISION REQUIRED | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0583 | 1318 | FUTURE IMPLEMENTATION REQUIRED: Add research mode , reproducibility level , and rq level metadata to ResearchMission or sidecar artifacts | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0584 | 1319 | FUTURE IMPLEMENTATION REQUIRED: Pre-registration artifact with content hash and plan binding | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-0585 | 1320 | FUTURE IMPLEMENTATION REQUIRED: Closed failure class enum aligned with §37 taxonomy | TAXO (text) | EXISTS-PARTIAL (reuse/extend) | ahos_org/registry.py, docs/agents/PLANNED_19_AGENT_MAP.md, docs/governance/agent_taxonomy_map.json (e0ac1dd); all 19 at REGISTERED | M12 |  |
| AD-0586 | 1321 | FUTURE IMPLEMENTATION REQUIRED: MethodologyAssessment schema for Agent 05 handoff | OBS (text) | EXISTS-PARTIAL (reuse/extend) | engine/health_manager.py, architecture/runtime/observability_snapshot.py, scripts/gateway_port.py (06e44e6) | M11/M14 |  |
| AD-0587 | 1322 | FUTURE IMPLEMENTATION REQUIRED: Leakage checklist attestation field on ExperimentPlan for ML/backtest studies | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0588 | 1323 | FUTURE IMPLEMENTATION REQUIRED: Negative result registry and audit for missing experiment runs | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |

### `docs/architecture/AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (47)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0589 | 58 | Agent One: NOT IMPLEMENTED / FUTURE NON AUTHORITY ROOT — must never become data authority or truth root | GOVBOUND (text) | MERGED (source ref on existing row) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate | same requirement as OD-423 (source ref added) |
| AD-0590 | 154 | Primary question "How do we move and store data?" "What must be true about data before it may support reasoning?" | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0591 | 170 | SOURCE RELIABILITY = EVIDENCE STRENGTH Reliable stale source may not support live claims | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0592 | 182 | [IMPLEMENTED] Subset encoded in Slice 2B module docstring: "Stored memory, confidence, recency, and audit inclusion never imply truth." | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0593 | 188 | Each object below is classified as conceptual , runtime , or documentary . Not all conceptual objects must become runtime entities | PDQ (doc) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0594 | 229 | Data objects may inform evidence creation but must not collapse into evidence automatically | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0595 | 233 | [PROPOSED] Conversion path (never automatic): | PDQ (doc) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0596 | 274 | One provider may produce many Source registrations; one Source may aggregate multiple provider inputs (must be documented | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0597 | 367 | Supersession edges for restatements (never silent overwrite | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0598 | 512 | Provider restatement (correcting past values) is not schema evolution. Restatements require new artifact version with supersession link, never silent overwrite | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0599 | 597 | Freshness thresholds must be domain-specific and decision-specific : | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0600 | 630 | Completeness metrics must report where incompleteness occurs (time range, entity class, event type), not only a global percentage | DAILY (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/reports.py, engine/research_report_bot.py, TELEGRAM_RESEARCH_REPORT | M17 |  |
| AD-0601 | 650 | Identity keys must be domain-defined (e.g., (chain id, block number, tx hash, log index) for EVM logs). Never deduplicate merely because two records look similar if they may represent distinct real-world events | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0602 | 673 | Critical rule: Missing data must remain distinguishable from zero. Null, absent, and zero are three different states | GIT (text) | EXISTS-PARTIAL (reuse/extend) | CLAUDE_CONTINUATION_GUIDE.md commit rules, .cursor/hooks.json ahos-guard | all |  |
| AD-0603 | 722 | Resolution must consider: | PDQ (doc) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0604 | 729 | Whether conflict is resolvable or must remain UNRESOLVED | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0605 | 822 | Unresolved conflict Preserve all values Downstream must handle UNKNOWN | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0606 | 981 | A tamper-proof pipeline can still ingest semantically wrong data. Semantically perfect data can arrive via insecure channel (must be quarantined until security review | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0607 | 1142 | Downstream consumers must fail closed or explicit bypass with governance approval | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0608 | 1184 | Historical research must remain interpretable after future schema changes — pin versions in research artifacts (Agent-06 reproducibility matrix | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0609 | 1290 | Do not prescribe a single formula without evidence. [PROPOSED] scoring interface must accept quality vector + readiness level as inputs | SCORING (text) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0610 | 1303 | A technically high-quality dataset irrelevant to the decision must not increase confidence | CALIB (text) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0611 | 1416 | Adversarial questions the organization must survive: | PDQ (doc) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0612 | 1531 | Data readiness must be contextual Required — purpose-bound levels | PDQ (doc) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0613 | 1532 | Downstream systems must inherit upstream uncertainty Required — propagation rules | PDQ (doc) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0614 | 1533 | Data correction must remain auditable Required — supersession + incident record | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0615 | 1691 | What minimum provider admission evidence is required before governance approval (Agent 04)? | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0616 | 1709 | HD-01 Dual-19 resolution: Plane A agent.provider-data vs Plane D Agent-07 ownership HUMAN DECISION REQUIRED | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-0617 | 1710 | HD-02 Adopt data readiness levels (§36) as organizational vocabulary HUMAN DECISION REQUIRED | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0618 | 1711 | HD-03 Adopt FIT FOR PURPOSE evaluation model (§35) HUMAN DECISION REQUIRED | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0619 | 1712 | HD-04 Quality representation: retain Evidence assurance scalar vs quality vector vs both HUMAN DECISION REQUIRED | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0620 | 1713 | HD-05 Provider admission process and minimum evidence for approval HUMAN DECISION REQUIRED | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0621 | 1714 | HD-06 Default crypto provider reconciliation strategy when providers disagree HUMAN DECISION REQUIRED | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0622 | 1715 | HD-07 Quarantine override authority and audit requirements HUMAN DECISION REQUIRED | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0623 | 1716 | HD-08 Data retention policy tiers (raw vs derived vs features) HUMAN DECISION REQUIRED | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0624 | 1717 | HD-09 DataIntelligenceAssessment → Evidence packaging handoff schema (with Agent 05) HUMAN DECISION REQUIRED | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0625 | 1718 | HD-10 Research data requirements template adoption (with Agent 06) HUMAN DECISION REQUIRED | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0626 | 1719 | HD-11 When AHOS integration is allowed: read-only mirror vs mediated contract boundary HUMAN DECISION REQUIRED | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0627 | 1730 | FUTURE IMPLEMENTATION REQUIRED: DataQualityAssessment artifact (or sidecar) with multi-dimensional vector | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-0628 | 1731 | FUTURE IMPLEMENTATION REQUIRED: Provider registry with dependency/correlation graph | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0629 | 1732 | FUTURE IMPLEMENTATION REQUIRED: DataContract and SchemaVersion types with compatibility tests | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0630 | 1733 | FUTURE IMPLEMENTATION REQUIRED: DataGap, DataAnomaly, DataConflict artifact types | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-0631 | 1734 | FUTURE IMPLEMENTATION REQUIRED: DataIntelligenceAssessment handoff schema for Agent 05 Evidence eligibility | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0632 | 1735 | FUTURE IMPLEMENTATION REQUIRED: Research data requirements block coordinated with Agent 06 template | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0633 | 1736 | FUTURE IMPLEMENTATION REQUIRED: Readiness level computation from assessments (purpose-bound | PDQ (doc) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0634 | 1737 | FUTURE IMPLEMENTATION REQUIRED: Data artifact quarantine state with downstream propagation rules | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-0635 | 1738 | FUTURE IMPLEMENTATION REQUIRED: Semantic validation layer above JSON schema for crypto identity tuples | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |

### `docs/architecture/AGENT_08_CRYPTO_MARKET_INTELLIGENCE_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (25)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0636 | 69 | Agent One: NOT IMPLEMENTED / FUTURE NON AUTHORITY ROOT — must never become market truth root or execution authority | GOVBOUND (text) | MERGED (source ref on existing row) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate | same requirement as OD-423 (source ref added) |
| AD-0637 | 261 | CMI must never silently imply: | SCORING (doc) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0638 | 322 | If Agent 07 marks data NOT FIT or STALE for purpose → CMI must not emit live-grade signals without explicit degraded-mode labeling | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0639 | 349 | Every metric must declare its tier. INFERRED metrics must cite input observables and transform version | OBS (text) | EXISTS-PARTIAL (reuse/extend) | engine/health_manager.py, architecture/runtime/observability_snapshot.py, scripts/gateway_port.py (06e44e6) | M11/M14 |  |
| AD-0640 | 382 | Agent 08 must not override Agent 07 findings. If data is stale, incomplete, contradictory, corrupted, or semantically ambiguous, CMI propagates that limitation on every downstream artifact | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0641 | 444 | Buy/sell volume INFERRED/OBSERVABLE Often unavailable; tier must be honest | OBS (text) | EXISTS-PARTIAL (reuse/extend) | engine/health_manager.py, architecture/runtime/observability_snapshot.py, scripts/gateway_port.py (06e44e6) | M11/M14 |  |
| AD-0642 | 524 | When order flow is UNKNOWN, CMI must not infer demand from price alone without labeled proxy limitations | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0643 | 652 | CMI must document provider-specific fields in Provider Dependency Matrix (Matrix C | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0644 | 773 | Future dedicated narrative intelligence layer must not collapse into CMI price/volume signals without explicit fusion contract and human L2 approval | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0645 | 794 | Architecture must emit POTENTIAL OPPORTUNITY and POTENTIAL DANGER with equal structural weight. No forced positive-only scoring | SCORING (text) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0646 | 924 | Mapping note: Align with but do not merge silently into Slice 2B HypothesisState , EvidenceState , or Agent 07 readiness enums — explicit compatibility table in § | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0647 | 1058 | Prediction must include: prediction target , prediction time , horizon , information cutoff , expected outcome , falsification criterion , provenance | LEARN (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/prediction_lifecycle.py, 202f8c9 learning bridge | M13 |  |
| AD-0648 | 1066 | Agent 08 may propose Agent 08 must NOT | SCORING (doc) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0649 | 1089 | CMI supplies context (liquidity, vol, threats). Agent 11 owns loss framing, exposure limits, and risk decisions. A bullish momentum signal with thin liquidity must surface as conflict , not net bullish score | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0650 | 1099 | Transfer restriction symptoms in market data → do not interpret as normal vol | SCORING (doc) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0651 | 1101 | Agent 08 must not replace Token Security analysis. Security finding can invalidate market signal actionability without deleting observations | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0652 | 1130 | CMI features fed to backtests must carry leakage annotations and cutoff times | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0653 | 1164 | Adversarial questions CMI architecture must survive: | SCORING (doc) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0654 | 1177 | Agent 19 probes; architecture must fail closed or expose conflicts | SCORING (doc) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0655 | 1379 | CMI-C09 Global deny provider.connect denied Any future market data ingestion Data must come from somewhere Blocks all live CMI until governed exception IMPLEMENTED Human-governed mediated ingest architecture (not direct connect | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0656 | 1569 | FUTURE IMPLEMENTATION REQUIRED: MarketFeatureDefinition registry with formula hashes | SCORING (doc) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0657 | 1570 | FUTURE IMPLEMENTATION REQUIRED: Golden test suite for core metrics (returns, vol, impact | GOLD (text) | MISSING→added to plan | no gold code (only 01/src UI mock text); reuse paper_trading/ + architecture/providers/ + strategy_lab/ - do NOT create a parallel gold engine | M13 gold-paper track → M18 Gold Division |  |
| AD-0658 | 1571 | FUTURE IMPLEMENTATION REQUIRED: CrossVenueAssessment with UNRESOLVED default | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0659 | 1572 | FUTURE IMPLEMENTATION REQUIRED: Regime multi-model disagreement preservation | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0660 | 1573 | FUTURE IMPLEMENTATION REQUIRED: Market incident + signal INVALID propagation | SCORING (doc) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |

### `docs/architecture/AGENT_09_ON_CHAIN_INTELLIGENCE_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (25)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0661 | 65 | [VERIFIED] Slice 1 globally denies provider.connect , trading.live , and AHOS production access ( ahos org/policy.py , [IMPLEMENTED] [TESTED] ). Logical roles agent.provider-data and agent.reality-forensics exist in the registry but cannot connect to chain providers and do not implement OCI | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0662 | 77 | Agent One: NOT IMPLEMENTED / FUTURE NON AUTHORITY ROOT — must never become on-chain truth root or execution authority | GOVBOUND (text) | MERGED (source ref on existing row) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate | same requirement as OD-423 (source ref added) |
| AD-0663 | 176 | Rule: AHOS artifacts inform compatibility analysis only. They do not grant org runtime authority | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0664 | 256 | Observation before interpretation Raw and decoded tiers never silently merge | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0665 | 333 | OCI architecture must support chain profile metadata declaring which levels apply | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0666 | 360 | Same address different chain 0xabc… on ETH and BSC Different entities — never merge | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0667 | 365 | Every observation must record: | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0668 | 439 | Intelligence derived from blocks below organization's finality threshold must carry: | CHAINS (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/providers/ (pumpfun, dex_pools, coingecko, defillama, chain_explorer), discovery/providers.yaml | M13/M18 |  |
| AD-0669 | 567 | EVM indexed topics enable filtering but lose dynamic type detail. Decoders must document what is partial vs complete | CHAINS (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/providers/ (pumpfun, dex_pools, coingecko, defillama, chain_explorer), discovery/providers.yaml | M13/M18 |  |
| AD-0670 | 600 | Rule: Decoders must never silently invent missing fields | CHAINS (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/providers/ (pumpfun, dex_pools, coingecko, defillama, chain_explorer), discovery/providers.yaml | M13/M18 |  |
| AD-0671 | 972 | All intelligence artifacts must declare which timestamp anchors the claim | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0672 | 978 | Future system must answer: | CHAINS (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/providers/ (pumpfun, dex_pools, coingecko, defillama, chain_explorer), discovery/providers.yaml | M13/M18 |  |
| AD-0673 | 1009 | Historical queries use as of block / as of time parameters. Features for Agent 12 must declare block cutoff | CHAINS (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/providers/ (pumpfun, dex_pools, coingecko, defillama, chain_explorer), discovery/providers.yaml | M13/M18 |  |
| AD-0674 | 1077 | Explicit statuses — do not silently merge : | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0675 | 1094 | Mapping to Slice 2B: generic Observation may wrap OCI artifacts but domain status must remain on payload | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0676 | 1158 | Agent 09 may observe Agent 10 must govern | CHAINS (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/providers/ (pumpfun, dex_pools, coingecko, defillama, chain_explorer), discovery/providers.yaml | M13/M18 |  |
| AD-0677 | 1165 | Agent 09 must not independently declare SAFE or SCAM | CHAINS (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/providers/ (pumpfun, dex_pools, coingecko, defillama, chain_explorer), discovery/providers.yaml | M13/M18 |  |
| AD-0678 | 1182 | Agent 08 §36 defines fusion as hypothesis only. Agent 09 symmetrically must not explain price moves from flows alone | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0679 | 1196 | On-chain features for quant use must preserve: | CHAINS (text) | EXISTS-PARTIAL (reuse/extend) | architecture/providers/ (pumpfun, dex_pools, coingecko, defillama, chain_explorer), discovery/providers.yaml | M13/M18 |  |
| AD-0680 | 1211 | ML may consume normalized observations and graph features. ML must not: | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0681 | 1238 | Required adversarial questions (architecture must survive): | CHAINS (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/providers/ (pumpfun, dex_pools, coingecko, defillama, chain_explorer), discovery/providers.yaml | M13/M18 |  |
| AD-0682 | 1459 | Authority Roles, Ownable Mint/freeze/update Miner/validator Security reviews must be chain-aware | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0683 | 1645 | FUTURE IMPLEMENTATION REQUIRED: FinalityAssessment , ReorgEvent , OnChainConflict artifact types | CHAINS (text) | EXISTS-PARTIAL (reuse/extend) | architecture/providers/ (pumpfun, dex_pools, coingecko, defillama, chain_explorer), discovery/providers.yaml | M13/M18 |  |
| AD-0684 | 1646 | FUTURE IMPLEMENTATION REQUIRED: Historical snapshot store with as of block queries | CHAINS (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/providers/ (pumpfun, dex_pools, coingecko, defillama, chain_explorer), discovery/providers.yaml | M13/M18 |  |
| AD-0685 | 1647 | FUTURE IMPLEMENTATION REQUIRED: Decoder registry with version pinning and regression suite | CHAINS (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/providers/ (pumpfun, dex_pools, coingecko, defillama, chain_explorer), discovery/providers.yaml | M13/M18 |  |

### `docs/architecture/AGENT_10_TOKEN_SECURITY_SCAM_INTELLIGENCE_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (13)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0686 | 75 | Agent One: NOT IMPLEMENTED / FUTURE NON AUTHORITY ROOT — must never become security truth root or execution authority | GOVBOUND (text) | MERGED (source ref on existing row) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate | same requirement as OD-423 (source ref added) |
| AD-0687 | 175 | What TSI must answer vs must not answer | SECSTATE (doc) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0688 | 177 | TSI may architect answers to TSI must not auto-answer | SECSTATE (doc) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0689 | 202 | Scam Intelligence is a subset of TSI focused on patterns consistent with fraudulent intent or deceptive economic traps , expressed only through explicit ScamIndicator and ScamHypothesis objects — never as raw observation labels | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0690 | 218 | Provider disagreement is data, not resolution by vote Methodology must be preserved | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0691 | 255 | Scam language is reserved for ScamHypothesis and ScamAssessment lifecycle states ≥ SUPPORTED , never for raw observations | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0692 | 331 | Every transition must preserve: source, timestamp, chain, token/contract identity, provenance, evidence refs, uncertainty, confidence (bounded), schema version, lifecycle status | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0693 | 373 | Upgrade rules: Indirect → Direct requires explicit warrant chain. Speculation never becomes Direct without new evidence tier | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0694 | 398 | Agent 09 produces Agent 10 consumes Agent 10 must not | SECSTATE (doc) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0695 | 406 | Agent 09 §44: Agent 09 must not declare SAFE or SCAM . Agent 10 must not override Agent 09 observations — only interpret via security objects | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0696 | 485 | Chain congestion / gas Tx never included vs revert | SECSTATE (doc) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0697 | 778 | [PROPOSED] TSI readiness levels (mapping only — do not replace Agent 07/08/09 readiness without HD): | SECSTATE (doc) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0698 | 992 | Architecture must fail closed or preserve UNKNOWN/CONFLICT | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/architecture/AGENT_11_RISK_INTELLIGENCE_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (27)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0699 | 73 | Agent One: NOT IMPLEMENTED / FUTURE NON AUTHORITY ROOT — must never become risk authority or decision root | GOVBOUND (text) | MERGED (source ref on existing row) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate | same requirement as OD-423 (source ref added) |
| AD-0700 | 147 | Given what we observe and what we do not know, what adverse outcomes are plausible , how severe could they be , under what assumptions , over what horizon , with what dependencies , and what must remain UNKNOWN ? | LEARN (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/prediction_lifecycle.py, 202f8c9 learning bridge | M13 |  |
| AD-0701 | 157 | A scalar score may exist as a derived summary under strict governance, but it is never the canonical risk representation. The canonical representation is a multidimensional, time-stamped, provenance-linked structure that survives audit, red-team attack, and regime change without hiding tail risk or UNKNOWN dimensions | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0702 | 177 | Scalar risk score Derived summary Optional; never canonical | SCORING (text) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0703 | 198 | [IMPLEMENTED] Slice 2B: "Stored memory, confidence, recency, and audit inclusion never imply truth." Risk Intelligence must treat this as binding on any future risk artifacts stored in or derived from TCB | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0704 | 237 | Nominal TVL, volume, or "high liquidity" labels from Agent 08 do not authorize low exit-risk conclusions. Agent 11 must evaluate: executable depth at size, route diversity, LP control (Agent 09/10), security restrictions (Agent 10), and time-to-exit under stress | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |
| AD-0705 | 251 | Invariant: Agent 10 finding is preserved verbatim . Agent 11 adds exposure × severity × scenario — never rewrites SUPPORTED HONEYPOT HYPOTHESIS into LOW RISK | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0706 | 340 | Architectural rule: Tail risk must never be fully absorbed into a mean-variance or average score without explicit separate representation. A small probability of catastrophic loss must remain visible | SCORING (text) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0707 | 363 | Optional scalar summary index — explicitly labeled derived, with precision policy (§23), never used alone for decisions | RISKGOV (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/risk/engine.py, paper_trading/risk.py; not independent governor | M13 |  |
| AD-0708 | 448 | Rule: Expected value averaging must not erase CATASTROPHIC tail in summary views | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0709 | 471 | N assets sharing: same chain, same stablecoin quote, same LP owner, same indexer, same narrative, same market maker — may have near-unity effective exposure . Agent 11 must compute effective independence via dependency graph, not asset count | RISKGOV (text) | EXISTS-PARTIAL (reuse/extend) | architecture/risk/engine.py, paper_trading/risk.py; not independent governor | M13 |  |
| AD-0710 | 477 | Every assessment must include: | RISKGOV (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/risk/engine.py, paper_trading/risk.py; not independent governor | M13 |  |
| AD-0711 | 528 | Contrast: High severity + minutes lead time ≠ high severity + weeks lead time. Architecture must represent both | RISKGOV (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/risk/engine.py, paper_trading/risk.py; not independent governor | M13 |  |
| AD-0712 | 615 | Architecture must support compound stress — e.g. price shock + liquidity withdrawal + provider outage. Single-factor-only stress tests are insufficient for tail analysis | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0713 | 691 | They may co-occur but must not merge into one object type | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0714 | 721 | Agent 07 flagged Evidence.assurance 0–100 as scalar collapse risk — Risk Intelligence must not replicate this pattern on risk outputs | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0715 | 753 | Architecture must prevent upside attractiveness from suppressing risk dimensions in composite "opportunity scores." | SCORING (text) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0716 | 825 | Invariant: Market interpretation must not silently become risk verdict. CMI supplies inputs ; RI produces loss framing | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0717 | 859 | Risk must not replace epistemology. Future risk artifacts may reference Evidence , Claim , Hypothesis , ContradictionCase — not substitute for them | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0718 | 942 | Propagation MUST STOP before Decision. No automatic edge from RiskAssessment to ALLOW / DENY trade | RISKGOV (text) | EXISTS-PARTIAL (reuse/extend) | architecture/risk/engine.py, paper_trading/risk.py; not independent governor | M13 |  |
| AD-0719 | 1081 | Answer: Apparent agent independence is false . Architecture must track: | RES2ARCH (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0720 | 1087 | [PROPOSED] InformationDependencyGraph — provider/upstream lineage on every risk input. Red Team (Agent 19) must attack "three agents agree" consensus | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-0721 | 1150 | Future risk report must answer: | RISKGOV (text) | EXISTS-PARTIAL (reuse/extend) | architecture/risk/engine.py, paper_trading/risk.py; not independent governor | M13 |  |
| AD-0722 | 1192 | Thresholds for classification and escalation may exist; they must never silently map to BUY/SELL | REALCLASS (text) | EXISTS-PARTIAL (reuse/extend) | ahos_org/registry.py states, reports/grok/REMAINING_REALITY_REGISTER.md | M9 (done) / M12 |  |
| AD-0723 | 1283 | Agent One must not : treat risk score as truth, auto-execute on risk threshold, override risk UNKNOWNs, become risk authority | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0724 | 1344 | Low volatility + hidden structural fragility Stress test reveals tail; do not trust vol alone | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0725 | 1471 | Future Mission Map (STATE ONLY — DO NOT EXECUTE | RISKGOV (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/risk/engine.py, paper_trading/risk.py; not independent governor | M13 |  |

### `docs/architecture/AGENT_12_QUANTITATIVE_INTELLIGENCE_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (13)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0726 | 303 | Delayed events Apply availability ts ; never retroactive signal | PERF (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0727 | 342 | Every object consumed at decision time must prove: | PERF (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0728 | 462 | Status: [HUMAN DECISION REQUIRED] — see § | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0729 | 487 | Rule: A signal must never silently become a decision. Decision-simulation is a separate explicit stage with cost matrix and authority gate | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0730 | 599 | How many strategies must fail before the surviving winner becomes suspicious? | PERF (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0731 | 845 | [PROPOSED] explicit conflict object — do not average contradictory evidence : | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0732 | 870 | Agent Agent-12 receives Agent-12 produces Agent-12 must NOT | PERF (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0733 | 925 | Point-in-time feature compute + L1–L4 MUST HAVE FOR FIRST RUN Already in AHOS; core honesty | PERF (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0734 | 926 | Pre-registered opportunity event study ( baseline stats + search cells) MUST HAVE FOR FIRST RUN Matches product (detection ≠ portfolio | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0735 | 927 | Score ledger + calibration harness (read-only) MUST HAVE FOR FIRST RUN Converts scores to measurable claims | CALIB (text) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0736 | 928 | Negative result registry MUST HAVE FOR FIRST RUN Prevents repeated failure | PERF (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0737 | 935 | Survivorship PIT universe MUST HAVE FOR FIRST RUN (token claims) Gap — blocker for broad token backtest marketing | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0738 | 1024 | Cross-agent boundary violations Agent 19 Attempt quant→decision shortcut; must fail closed | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |

### `docs/architecture/AGENT_13_AI_ML_INTELLIGENCE_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (28)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0739 | 213 | Strategy lab rejected registry Yes Negative-result memory; do not re-train on failures without lineage | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0740 | 219 | What must NOT be consumed until validated | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-0741 | 287 | Model output never auto-promotes to Knowledge | SELFIMP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0742 | 370 | Every training/eval dataset must declare: | MODELREG (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/ai/provider_status.py (b4e67be), architecture/ai/router.py, config/ai_provider_registry.yaml, tests/test_ai_provider_status.py; no ModelRegistry/pe | M14 |  |
| AD-0743 | 400 | Synthetic/test rows never enter production model training without explicit quarantine flag | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0744 | 401 | Label corrections create new label version — never silently rewrite historical training rows | MODELREG (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/ai/provider_status.py (b4e67be), architecture/ai/router.py, config/ai_provider_registry.yaml, tests/test_ai_provider_status.py; no ModelRegistry/pe | M14 |  |
| AD-0745 | 402 | Class imbalance must be declared before metric selection (§ | OBS (text) | EXISTS-PARTIAL (reuse/extend) | engine/health_manager.py, architecture/runtime/observability_snapshot.py, scripts/gateway_port.py (06e44e6) | M11/M14 |  |
| AD-0746 | 409 | For inference at time T , every input must satisfy: | MODELREG (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/ai/provider_status.py (b4e67be), architecture/ai/router.py, config/ai_provider_registry.yaml, tests/test_ai_provider_status.py; no ModelRegistry/pe | M14 |  |
| AD-0747 | 422 | L1 future observations Feature store ML must not bypass store with ad-hoc joins | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0748 | 423 | L2 outcome in features Architecture test ML feature pipelines must not import label tables | LEARN (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/prediction_lifecycle.py, 202f8c9 learning bridge | M13 |  |
| AD-0749 | 424 | L3 availability DB CHECK Model serving must respect availability ts | PERSIST (text) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |
| AD-0750 | 425 | L4 research joins Join policy Train/test splits must use PIT feature rows only | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0751 | 598 | CognitivePanel Lenses return ABSTAIN — never guess | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0752 | 797 | Retrieved document status must include: STALE SUPERSEDED WRONG UNVERIFIED CONTRADICTORY | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0753 | 799 | Every LLM factual claim requires evidence path — numeric claims must bind to AHOS observation IDs or CAPABILITY GAP | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0754 | 1023 | Each world-model element must declare: | MODELREG (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/ai/provider_status.py (b4e67be), architecture/ai/router.py, config/ai_provider_registry.yaml, tests/test_ai_provider_status.py; no ModelRegistry/pe | M14 |  |
| AD-0755 | 1087 | ML must not emit SCAM/SAFE — security domain owns binary verdict | MODELREG (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/ai/provider_status.py (b4e67be), architecture/ai/router.py, config/ai_provider_registry.yaml, tests/test_ai_provider_status.py; no ModelRegistry/pe | M14 |  |
| AD-0756 | 1090 | Every model eval must include data quality/freshness/missingness/provenance/drift census | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0757 | 1120 | Self-fulfilling signals: backtest performance may not equal post-deployment performance when AHOS attention is material | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0758 | 1223 | Deterministic scorer + breakdown MUST HAVE FOR LAUNCH Already core; beats unvalidated ML | SCORING (text) | IMPLEMENTED+TESTED | 88f3484 scoring contract, architecture/intel/ (market_structure, tokenomics, catalyst 4fd818c), 39 test files | keep |  |
| AD-0759 | 1224 | Read-only calibration accrual MUST HAVE FOR LAUNCH Makes intelligence measurable | CALIB (text) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0760 | 1225 | Abstention contract (unified) MUST HAVE FOR LAUNCH Correct "I don't know" | MODELREG (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/ai/provider_status.py (b4e67be), architecture/ai/router.py, config/ai_provider_registry.yaml, tests/test_ai_provider_status.py; no ModelRegistry/pe | M14 |  |
| AD-0761 | 1228 | ModelInference + Registry schema (docs/contracts) MUST HAVE BEFORE ANY ML Gate for future models | MODELREG (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/ai/provider_status.py (b4e67be), architecture/ai/router.py, config/ai_provider_registry.yaml, tests/test_ai_provider_status.py; no ModelRegistry/pe | M14 |  |
| AD-0762 | 1285 | Not sequential gates — but Phase 0 must precede any production ML | MODELREG (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/ai/provider_status.py (b4e67be), architecture/ai/router.py, config/ai_provider_registry.yaml, tests/test_ai_provider_status.py; no ModelRegistry/pe | M14 |  |
| AD-0763 | 1305 | Online learning FORBIDDEN — — — N/A | LEARN (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/prediction_lifecycle.py, 202f8c9 learning bridge | M13 |  |
| AD-0764 | 1429 | AHOS online learning [FORBIDDEN] by design | LEARN (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/prediction_lifecycle.py, 202f8c9 learning bridge | M13 |  |
| AD-0765 | 1471 | ML must not emit SCAM/SAFE Security boundary 10, 13 Confirm ANOMALY vs VERDICT split Agent-10 boundary amendment | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0766 | 1502 | Every ML model must beat: | MODELREG (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/ai/provider_status.py (b4e67be), architecture/ai/router.py, config/ai_provider_registry.yaml, tests/test_ai_provider_status.py; no ModelRegistry/pe | M14 |  |

### `docs/architecture/AGENT_14_AGENT_RUNTIME_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (20)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0767 | 85 | [VERIFIED] Zero cross-repo references exist. AHOS has 25 product agents ( AG-01 … AG-25 ); org has separate registries. AHOS orchestrated=0/25 ; AG-01 missing by design. Org must not assume AHOS runtime capabilities | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0768 | 109 | Three implemented control planes (do not invent a fourth | REALCLASS (text) | EXISTS-PARTIAL (reuse/extend) | ahos_org/registry.py states, reports/grok/REMAINING_REALITY_REGISTER.md | M9 (done) / M12 |  |
| AD-0769 | 246 | Each arrow is a separate trust concern . Components that must not collapse: | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0770 | 276 | Current authority (do not invent | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0771 | 313 | Recommendation [PROPOSED] : Commander, Supervisor, Verifier, Knowledge Owner, and Executor should be separate roles . Initially, Supervisor can be audit-query-only; Verifier must be a different principal from builder | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0772 | 326 | Knowledge exchange must NOT imply authority, command rights, verification rights, or promotion rights | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0773 | 343 | Promotion requests via mesh (must be CommandEnvelope → TCB | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0774 | 448 | Completed mission never silently resumes New mission id required | LEDGER (text) | IMPLEMENTED+TESTED | architecture/mission/ledger.py + scripts/mission_ledger.py + tests/test_mission_ledger.py (d1571c4) | M14 extend |  |
| AD-0775 | 452 | Slice 1 TaskState and Slice 2B GovernedTask cover task lifecycle, not agent lifecycle. Agent lifecycle is [PLANNED] . MC must unify: | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0776 | 499 | Two envelope families (never merge | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0777 | 585 | Runtime must operate safely while unresolved: | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0778 | 647 | Specialists never receive raw grant objects — only session-bound capability tokens | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0779 | 655 | Before ACTIVE, agent must receive: | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0780 | 925 | Questions the org must eventually answer | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0781 | 1131 | DISCOVERY ID DISCOVERY AFFECTED REQUIRED ACTION PRIORITY | AUTOCONT (text) | EXISTS-PARTIAL (reuse/extend) | process rule; enforced via reports/grok/CLAUDE_CONTINUATION_GUIDE.md, docs/canonical/GOVERNANCE.md, .cursor/skills/; reports/grok/OWNER_DIRECTIVE_MISSION_PLAN.m | all |  |
| AD-0782 | 1137 | DISC-14-005 REQUIRES REVIEW not hard-blocked at all callers (Agent-04) 03, 04, 14 MC must treat REQUIRES REVIEW as BLOCKED for activation HIGH | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0783 | 1223 | Recommended next implementation mission (STATE ONLY — DO NOT EXECUTE | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0784 | 1247 | Agent One must not automatically become: source of truth, verifier, governance authority, production executor, knowledge promoter, policy modifier, trading executor | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0785 | 1265 | Reports must declare plane for every AGENT ID | DAILY (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/reports.py, engine/research_report_bot.py, TELEGRAM_RESEARCH_REPORT | M17 |  |
| AD-0786 | 1341 | Runtime must preserve Slice 2B types — never flatten to message.content | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |

### `docs/architecture/AGENT_14_RUNTIME_FOUNDATION_RECONCILIATION_AND_MVOR_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (19)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0787 | 102 | These four Agent One statements remain simultaneously true and must not be collapsed | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0788 | 176 | P0-01 Cursor collapse YES No federation code; L5 unbound Cursor must become CLIENT not ROOT All org claims unenforceable Federation bridge + MC | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0789 | 178 | P0-03 COMMAND≠REQUEST documentary YES 0 py envelope validators MC must type all downward/lateral traffic Prose commands work today MissionCommandEnvelope at MC | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0790 | 225 | Mission status MC projection Authoritative — never invented by Cursor | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0791 | 272 | MISSION mission. IDs plane-agnostic but agent refs must be plane-tagged Mission targets must specify plane | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0792 | 280 | All reports and envelopes must include identity plane field | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0793 | 295 | Contradiction surfacing (never silent merge | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0794 | 299 | Agent One MUST NOT directly own | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0795 | 331 | Agent One monolith prevention (S-14): Agent One process must not host TCB, verifier sessions, or acceptance signing keys | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0796 | 395 | What context is valid? context snapshot ref hash must match gate | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0797 | 444 | Three envelope families — never merge : | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0798 | 469 | TCB validates: only CommandEnvelope — never MissionCommandEnvelope directly | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0799 | 611 | Bus never decides ALLOW/DENY — only delivers MC-authorized envelopes | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0800 | 670 | SELF CHECK identity only (explicitly labeled — never for promotion | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-0801 | 711 | Every slot typed — never flat blob : | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0802 | 759 | Cursor never directly mutates protected state | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0803 | 802 | Reactivation requires new mission — completed mission never silently resumes | LEDGER (text) | IMPLEMENTED+TESTED | architecture/mission/ledger.py + scripts/mission_ledger.py + tests/test_mission_ledger.py (d1571c4) | M14 extend |  |
| AD-0804 | 860 | Org runtime must NOT inherit: AHOS execution, credentials, Telegram, n8n, live providers, production DB | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0805 | 972 | DO NOT IMPLEMENT — sequencing for future missions only | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |

### `docs/architecture/AGENT_15_PROMPT_INSTRUCTION_DELEGATION_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (36)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0806 | 123 | Authority ceiling Coordination + mission creation (via MC) + synthesis + recommendation — never truth, governance, verification, acceptance, execution, promotion | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0807 | 137 | Agent One must not become (even if capable in a single LLM): | AGCOMM (doc) | MISSING→added to plan | no agent message protocol; extend contracts/agent_contract_v1.json + agent_org/research_host/contracts.py | M12 |  |
| AD-0808 | 171 | Three names, three planes — do not merge silently : | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0809 | 179 | [PROPOSED] Federation mapping table (Human L2): Agent One runtime principal may project into chief-orchestrator inspect/plan/propose scope — never the reverse | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0810 | 195 | Phase 7 "Agent One orchestration" deferred Agent One instruction architecture must be designed now ; runtime build follows Agent-14 Phase 1 substrate | AGCOMM (doc) | MISSING→added to plan | no agent message protocol; extend contracts/agent_contract_v1.json + agent_org/research_host/contracts.py | M12 |  |
| AD-0811 | 261 | Peer lateral communication is never command unless the peer is the registered direct commander | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0812 | 269 | Every agent record (when fully implemented) must carry: | REALCLASS (text) | EXISTS-PARTIAL (reuse/extend) | ahos_org/registry.py states, reports/grok/REMAINING_REALITY_REGISTER.md | M9 (done) / M12 |  |
| AD-0813 | 357 | Return structured Mission Result — never bare "PASS" | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-0814 | 359 | Escalate contradictions, capability gaps, and scope violations — never silently resolve | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0815 | 411 | VERIFICATION FLOW MC-dispatched verifier Producer must cooperate within scope NO command authority | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0816 | 488 | Agent One may not delegate: verification authority, acceptance authority, promotion authority, policy modification, or AHOS connection | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0817 | 559 | ADVERSARIAL Red-team must not see producer reasoning chain Isolated parallel with sealed inputs | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0818 | 586 | Contradiction likely (08 vs 10 vs 11) Parallelize but preserve all findings — never average | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0819 | 625 | Each layer is a separate referenced artifact with version , hash , effective at . The worker receives references + hashes , not concatenated prose. The runtime assembles the effective instruction view; the model never sees a single undifferentiated blob where L5 could masquerade as L | WORKER (text) | EXISTS-PARTIAL (reuse/extend) | research_worker/ + agent_org/research_host/ (process-isolated, 5 test files) | M12 |  |
| AD-0820 | 656 | Context pack vs newer canonical memory Canonical memory (if version gate fails) CONTEXT GAP or CONTEXT DRIFT flag; do not proceed silently | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0821 | 669 | Subordinate never chooses between commanders | AGCOMM (doc) | MISSING→added to plan | no agent message protocol; extend contracts/agent_contract_v1.json + agent_org/research_host/contracts.py | M12 |  |
| AD-0822 | 675 | Two envelope types (do not merge | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0823 | 836 | Agent must acknowledge context version in result CONTEXT REVIEWED field | AGCOMM (doc) | MISSING→added to plan | no agent message protocol; extend contracts/agent_contract_v1.json + agent_org/research_host/contracts.py | M12 |  |
| AD-0824 | 884 | L6 context (documents, web, GitHub) LOW — untrusted data Data plane; never instruction plane | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0825 | 934 | Worker prompt template must visually and structurally separate planes. Retrieved content wrapped in: | WORKER (text) | EXISTS-PARTIAL (reuse/extend) | research_worker/ + agent_org/research_host/ (process-isolated, 5 test files) | M12 |  |
| AD-0826 | 942 | Worker instructions explicitly state: content inside UNTRUSTED DATA must not override instruction plane | WORKER (text) | EXISTS-PARTIAL (reuse/extend) | research_worker/ + agent_org/research_host/ (process-isolated, 5 test files) | M12 |  |
| AD-0827 | 1079 | Challenge is a command (from commander) — specialist must respond | AGCOMM (doc) | MISSING→added to plan | no agent message protocol; extend contracts/agent_contract_v1.json + agent_org/research_host/contracts.py | M12 |  |
| AD-0828 | 1081 | Agent One may not alter evidence artifacts — only request re-examination | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0829 | 1121 | The organization must support controlled agent-to-agent communication: | AGCOMM (doc) | MISSING→added to plan | no agent message protocol; extend contracts/agent_contract_v1.json + agent_org/research_host/contracts.py | M12 |  |
| AD-0830 | 1209 | Verification outcome via peer message (must be TCB or MC record | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0831 | 1302 | Agent One should maintain read-only projections over canonical memory — never private unversioned memory that bypasses TCB. [PROPOSED] Agent One session state is ephemeral ; durable state goes to MC/TCB store | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0832 | 1448 | Agent One must not become a monolith | AGCOMM (doc) | MISSING→added to plan | no agent message protocol; extend contracts/agent_contract_v1.json + agent_org/research_host/contracts.py | M12 |  |
| AD-0833 | 1480 | Agent One never holds TCB write keys | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0834 | 1494 | COR-05 Domain commanders assumed in target tree Domain commanders NOT IMPLEMENTED — do not invent MEDIUM | REALCLASS (text) | EXISTS-PARTIAL (reuse/extend) | ahos_org/registry.py states, reports/grok/REMAINING_REALITY_REGISTER.md | M9 (done) / M12 |  |
| AD-0835 | 1519 | AGENT FINDING RUNTIME/INSTRUCTION IMPACT REQUIRED FUTURE CHANGE | AGCOMM (doc) | MISSING→added to plan | no agent message protocol; extend contracts/agent_contract_v1.json + agent_org/research_host/contracts.py | M12 |  |
| AD-0836 | 1521 | Security Authority collapse is primary threat; MO/Agent One monolith risk Agent One must be rules+API bounded; separate critique/verify Implement trust boundary matrix in MC | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0837 | 1522 | Governance Commander model documented; lifecycle activation rules MissionCommandEnvelope must enforce commander chain Federation + commander registry in MC | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0838 | 1523 | Epistemic Chat → TCB bridge undecided; claim lifecycle gaps Result contract must preserve epistemic types; bus carries refs not flattened content HD-05: chat agent TCB write policy | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0839 | 1525 | Data DataIntelligenceAssessment handoff to 05/12 undefined Context pack must include data readiness refs for quant missions HD-09: assessment handoff schema | AGCOMM (doc) | MISSING→added to plan | no agent message protocol; extend contracts/agent_contract_v1.json + agent_org/research_host/contracts.py | M12 |  |
| AD-0840 | 1526 | Market Domain findings contradict 10/11 possible Contradiction workflow mandatory — never average signals Parallel branch preservation in MC | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0841 | 1531 | AI/ML Model output ≠ evidence (05 alignment) Instruction plane must label ML output UNTRUSTED AGENT-05 → AGENT-13 REQUEST pattern in mesh | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/architecture/AGENT_17_HUMAN_AGENT_ORGANIZATION_UX_AND_PRODUCT_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (33)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0842 | 33 | Is Persian-first required? YES (product requirement) — AHOS already treats FA/EN as first-class; org UX must inherit that posture | TG (text) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |
| AD-0843 | 34 | AHOS product UX = Org UX? NO — separate products; must not merge prematurely | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0844 | 127 | AGENT ONE STATUS code marker Historical wording; organizational intent superseded per mission correction CONFIRMED — CORRECTION REQUIRED IN CODE COMMENT ONLY (future governance mission | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0845 | 134 | Slice 1 TaskState ≠ mission UX states — task FSM lacks VERIFICATION , ACCEPTANCE , WAITING phases needed for human mental model; UX must compose orthogonal status dimensions | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0846 | 135 | Agent-05 §1 still says Agent One "must never become epistemic root" — correct for epistemic authority, but easily misread as "Agent One is not organizational root"; UX must disambiguate interface root vs truth root | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0847 | 186 | No fake live org PLANNED capabilities labeled PLANNED — never animated as if running | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0848 | 204 | Level 0 must never require Level 2+ to answer a status question | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0849 | 222 | G. Ask for evidence "Show me what proves this." Drill to Level 3–6; never prose-only EVIDENCE REQUEST | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0850 | 313 | Semantic classes (must be visually and linguistically distinct | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0851 | 376 | Slice 1 TaskState ( PROPOSED , AUTHORIZED , RUNNING , BLOCKED , COMPLETED , FAILED , CANCELLED , REJECTED ) maps to mission lifecycle partially — UX must add Verification and Acceptance explicitly | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0852 | 432 | Slice 1 seeds all 19 roles at MaturityLevel.REGISTERED (0) — below execution threshold. UX must show registered logical role distinctly from active specialist worker | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0853 | 532 | Slice 2B assurance (0–100) on Evidence/Memory is warrant strength metadata , not user-facing confidence score. If shown, label "Assurance (internal warrant)" and never animate | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0854 | 540 | User must always be able to answer: | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0855 | 564 | Distinct trust tokens (never collapse in UI | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0856 | 572 | Consensus ≠ truth. Correlated LLM agreement must display "Correlated agreement — independence not established" | RES2ARCH (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0857 | 587 | Contradictions are first-class , never averaged, never hidden | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0858 | 611 | Known standing contradiction (must remain visible | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0859 | 651 | Same Cursor session verification today = [UNVERIFIED independence] — UX must warn if producer and verifier principals match | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0860 | 673 | When requested capability does not exist, never hallucinate organizational ability | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0861 | 688 | Known capability gaps (UX must be able to display | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0862 | 701 | Any surface showing future inter-agent messages, bus traffic, or Agent One auto-delegation must carry: | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0863 | 711 | Failures must be typed , not generic | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0864 | 776 | When planes disagree, show both with plane labels — never silent pick | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0865 | 1059 | Color never sole channel — icon + text for status | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0866 | 1095 | Alert fatigue → ignore Noise notifications NO ACTION REQUIRED state; dedup | ALERT:System Failure (text) | EXISTS-PARTIAL (reuse/extend) | architecture/alerts/engine.py, telegram_ai/alerts.py, telegram_ai/pump_alert.py, tests/test_alert_engine.py, test_proactive_alert_delivery.py | M17/M18 |  |
| AD-0867 | 1186 | Preview mock must be watermarked SIMULATION | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0868 | 1219 | P19 Mode Honesty CURRENT vs FUTURE never blurred | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0869 | 1278 | What human must stop micromanaging (design target | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0870 | 1288 | UX must reflect architectural boundaries even when conversation feels unified | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0871 | 1290 | Agent One does NOT personally (UX must not imply | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0872 | 1401 | Verifier independence: Can LLM verify LLM output (HD-16-07)? UX must reflect decision | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-0873 | 1473 | STATE ONLY — DO NOT EXECUTE | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 | ; also: docs/architecture/AGENT_18_FRONTEND_VISUALIZATION_AND_TRUST_INTERFACE_ARCHITECTURE.md:2472, docs/governance/AGENT_01_GOVERNANCE_PROPAGATION_ADOPTION_REPORT.md:375, docs/security/AGENT_19_RED_TEAM_AND_ADVERSARIAL_ORGANIZATIONAL_SECURITY_ARCHITECTURE.md:1066, docs/verification/AGENT_16_INDEPENDENT_VERIFICATION_AND_ORGANIZATIONAL_FORENSICS.md:919 |
| AD-0874 | 1494 | What Agent-18 must build later (NOT now | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |

### `docs/architecture/AGENT_18_FRONTEND_VISUALIZATION_AND_TRUST_INTERFACE_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (38)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0875 | 31 | Should frontend create organizational truth? NEVER — hard invariant | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0876 | 32 | Should UI imply live agents when runtime absent? NEVER — no-fake-live-system policy | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0877 | 166 | Agent-17 gaps Agent-18 must fill | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0878 | 181 | Code marker AGENT ONE STATUS = FUTURE NON AUTHORITY ROOT [CONFIRMED] — organizational vs runtime conflation Frontend labels must separate role from runtime ; code comment fix is governance mission | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0879 | 186 | AGENT 17 CORRECTIONS REQUIRED = NONE IN THIS DOCUMENT — governance/code missions remain | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0880 | 190 | ReadOnlyProjections is the seed of an honest read-model API — frontend should never bypass it to mutate stores | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0881 | 191 | AHOS "ROOTS LIVE" pulsing indicator is an anti-pattern for org UI — [VERIFIED] in AHOS app-shell.tsx ; org frontend must not copy uncritically | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0882 | 192 | Evidence assurance field (0–100) must never become a user-facing confidence meter — [VERIFIED] in epistemic.py ; internal warrant only | CALIB (text) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |
| AD-0883 | 193 | Slice 2B VerificationKind.INDEPENDENT enforces producer ≠ verifier in code — UI must surface this distinction; backend already validates | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-0884 | 202 | The frontend never creates organizational truth | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0885 | 211 | The frontend must never independently decide or visually imply: | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0886 | 245 | Epistemic and lifecycle states must be visually and semantically non-interchangeable . Color alone is forbidden as the sole channel | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0887 | 283 | UNKNOWN No evidence or UNVERIFIED Prominent UNKNOWN — never empty silence | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0888 | 289 | Frontend DTOs must map 1:1 to repository enums — no UI-only aliases that collapse meaning: | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0889 | 348 | UI renders five separate badges + freshness clock — never a single "75% complete" bar unless sub-steps have defensible semantics | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0890 | 371 | Slice 1 seeds all 19 roles at MaturityLevel.REGISTERED (0) — below MINIMUM MATURITY FOR ALLOW (2). UI must show maturity explicitly | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0891 | 382 | Overlay dimensions (not in TaskState — must be separate): | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0892 | 466 | AHOS product surfaces — separate app shell; never merged nav without HD | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0893 | 473 | Approval modal Multi-step WHAT/WHY/WHO/IMPACT/RISK — never one-click confirm | RISKGOV (text) | EXISTS-PARTIAL (reuse/extend) | architecture/risk/engine.py, paper_trading/risk.py; not independent governor | M13 |  |
| AD-0894 | 544 | Level 0 must never require Level 2+ for a status question | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0895 | 586 | Frontend hides action buttons based on authoritative capability projection — never client-side authorization alone. Read paths may be wider than write paths. Expert mode may require explicit toggle + session flag | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0896 | 893 | At-least-once delivery — client must dedupe by event id | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0897 | 968 | Event conflicts with projection Prefer snapshot; flag conflict; never silently merge | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0898 | 1014 | Audit events append-only Events never "stale" — timestamps always shown | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0899 | 1050 | Intent while offline Queue locally with QUEUED OFFLINE — do not show as executed | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0900 | 1064 | Cache is display cache only — never authoritative | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0901 | 1203 | EXECUTE Runtime activation Separate confirm after APPROVE — never merged | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0902 | 1229 | Button labels must use action class vocabulary — Persian: پیشنهاد , درخواست , تایید , اجرا , مشاهده | TG (text) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |
| AD-0903 | 1262 | Expired approval: visually distinct from never-requested | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0904 | 1300 | NO ACTION REQUIRED (valid empty state — prominent | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0905 | 1420 | Surface backend rule from Evidence.is eligible positive support() result — do not recompute trust client-side as authority | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0906 | 1794 | Frontend must not directly mutate AHOS. Status: [NOT IMPLEMENTED] | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0907 | 1802 | What org UI must never assume from AHOS | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0908 | 1859 | Critical information remains 2D, precise, accessible, textual . Any 3D is decorative, disable-able, and never sole channel | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0909 | 1906 | AHOS app-shell.tsx shows pulsing green "ROOTS LIVE" — [VERIFIED] . Org frontend must not copy this pattern without live backend subscription | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0910 | 1918 | StatusBadge Single orthogonal dimension value Requires dimension prop; never generic "status" | DASH (doc) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-0911 | 2100 | Backend-driven flags for: SIMULATION mode, expert graph, AHOS adapter — never client-only enable of authority features | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0912 | 2310 | Agent One must not rely on frontend for authority decisions — only for intent collection and projection display | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |

### `docs/architecture/AGENT_ORGANIZATION_SECURITY_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (7)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0913 | 176 | Cursor Control-Plane persistence: Even after runtime exists, human-facing coordination via Cursor should remain an explicit layer — the runtime must not silently absorb human decision authority | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0914 | 267 | ACTIVE → ACTIVE FORBIDDEN — — Must deactivate first — Silent mission continuation | SECSTATE (doc) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0915 | 285 | Four questions must never collapse: | SECSTATE (doc) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0916 | 342 | The Master Orchestrator must not become: | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-0917 | 350 | Function Orchestrator may Orchestrator must not | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-0918 | 545 | Credentials Globally denied Forbidden authority keys Vault with injection, never in context | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0919 | 755 | RECOMMENDED NEXT MISSION [PLANNED] — STATE ONLY; DO NOT EXECUTE | SECSTATE (doc) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |

### `docs/architecture/AHOS_COGNITIVE_BENCHMARK_ARCHITECTURE_v1.0.md` — SUPPLEMENTARY/ANNEX, 2026-09-09 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0920 | 30 | Denominator 0 → NOT MEASURED (never PASS | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-0921 | 36 | GOVERNANCE invariants (leakage, unsupported SUPPORTED, nondeterminism, contradiction false-resolution) are floors that must not be lowered to hide failures | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |

### `docs/architecture/AHOS_COGNITIVE_LOOP_ARCHITECTURE_v1.0.md` — SUPPLEMENTARY/ANNEX, 2026-09-09 (5)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0922 | 23 | Finance is a proving domain, not the definition of cognition. The loop must not import | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0923 | 92 | Buckets (never collapsed into one bag): | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0924 | 118 | P3 never silently upgrades OPINION/PREDICTION/SIMULATION/HYPOTHESIS to FACT | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0925 | 183 | It must not write OBSERVED FACT unless an adapter/source is a real observation | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0926 | 250 | P4 candidates must be chosen from measured gaps, not the original roadmap | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |

### `docs/architecture/AHOS_COGNITIVE_MEMORY_ARCHITECTURE_v1.0.md` — SUPPLEMENTARY/ANNEX, 2026-09-09 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0927 | 5 | DB: data/ahos cognitive memory.sqlite (gitignored; never soak DBs | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0928 | 33 | AGENT Per-namespace lessons Default queries do not leak other namespaces | LEARN (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/prediction_lifecycle.py, 202f8c9 learning bridge | M13 |  |

### `docs/architecture/AHOS_RUNTIME_ARCHITECTURE_v1.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0929 | 66 | DETERMINISTIC LANE-A CORE (CRITICAL floor — NEVER depends on any AI/network target): | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-0930 | 186 | Human Gate ── never software; AI never approver (contract-pinned | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |

### `docs/architecture/OSS_CAPABILITY_DISCOVERY.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0931 | 6 | GitHub Repository = CANDIDATE — never truth, never dependency | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |

### `docs/architecture/PRODUCTION_SCHEDULER_SPEC.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (5)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0932 | 5 | To transition from experimental gate mode to 24/7 continuous opportunity intelligence, a production-grade durable scheduler is required | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0933 | 8 | No Silent Backfilling: Missed observation windows must be logged as missed:<slot in gap register . Future coverage improves through continuous execution, not revisionism | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0934 | 10 | Idempotency & Deduplication: Concurrent or repeated execution of a snapshot task within its tolerance window ($\pm \text{tol}$) must be safe and idempotent ( INSERT OR IGNORE / ON CONFLICT DO UPDATE | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-0935 | 11 | Lease & Distributed Locking: Any multi-worker or cloud deployment must enforce atomic lease acquisitions ( scheduler locks ) with expiration timeouts to prevent split-brain observation recording | WORKER (text) | EXISTS-PARTIAL (reuse/extend) | research_worker/ + agent_org/research_host/ (process-isolated, 5 test files) | M12 |  |
| AD-0936 | 12 | Fail-Closed & Drift Bounds: If system clock drift exceeds 5.0 seconds vs monotonic reference, scheduled tasks must abort to protect scientific causal ordering | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |

### `docs/architecture/RESEARCH_ANALYST_AGENT.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (7)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0937 | 81 | Evidence keeps its provenance reference and is never converted into a claim | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0938 | 82 | Claims stay claims and are never converted into evidence | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0939 | 83 | Hypotheses must be labeled HYPOTHESIS | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0940 | 84 | Predictions must be labeled PREDICTION | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0941 | 85 | Missing provenance becomes UNKNOWN / UNVERIFIED , never SAFE | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0942 | 91 | The agent never emits VERIFIED , PROMOTED , AUTHORIZED , EXECUTABLE , | SELFIMP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0943 | 165 | Duplicate JSON keys are rejected ( DUPLICATE JSON KEY ). Operation names must | RESSTD (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |

### `docs/architecture/SELF_EVOLUTION_LOOP.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0944 | 5 | Supreme law: AI → directly modify AHOS is FORBIDDEN — contract law sentence: "AI may | SELFIMP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0945 | 33 | GitHub/GitLab candidates never enter this loop directly: AG-25 (DISCOVERY→ANALYSIS→PROPOSAL | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0946 | 37 | NO INTEGRATION recorded (both are kept evidence, never deleted | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/architecture/SLICE_2A_EPISTEMIC_CORE_AND_TCB_SPEC.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (23)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0947 | 20 | Implementation must be checked against this document . Any deviation must be recorded explicitly (see docs/architecture/SLICE 2B REMEDIATION 01 IMPLEMENTATION VS SPEC.md | EPIST (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0948 | 46 | These equalities are forbidden . The corresponding objects, commands, and states must remain distinct: | EPIST (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0949 | 88 | Arbitrary strings must not masquerade as registered artifacts. IDs used as references must resolve to stored objects of the expected type | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0950 | 111 | Direct mutation of governed state by untrusted callers is forbidden . Naming, comments, and developer discipline are not enforcement. Structural bounds that Python actually permits (frozen envelopes, permit-gated store, single public submit , import-boundary tests) are required | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0951 | 156 | An agent must not establish those properties by payload fields | EPIST (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0952 | 176 | AuthorityContext is derived by the TCB , never accepted from the caller | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0953 | 185 | Command envelopes must carry a sentinel such as DERIVE AT TCB . Any caller-supplied authority blob is a construction failure | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0954 | 213 | Cognitive authority must not imply execution authority | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0955 | 252 | Effective authority is computed inside submit from registered grants. Handlers must not trust envelope fields that claim authorization. Policy mapping from command type to (capability, operation, resource, task required) is fixed. Callers cannot substitute a more powerful tuple onto a weaker command | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0956 | 298 | Claim is an interpretation of evidence. It is not a fact. Lifecycle includes draft/submitted/challenged/verified/rejected/superseded. Verification of a claim requires an independent verification record. Claims must not collapse into KnowledgeCandidate or Outcome | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-0957 | 345 | Contradictory evidence must not disappear; there is no delete of governed artifacts in this slice | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0958 | 346 | Automatic selection of a winner is forbidden | EPIST (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0959 | 373 | SELF CHECK may exist and must not satisfy promotion; | SELFIMP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0960 | 384 | Approval is an artifact, never human approved=true | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-0961 | 412 | Generic command CommandType.TRANSITION ARTIFACT must deny any request whose target denotes that promotion state | SELFIMP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-0962 | 413 | Generic lifecycle map must not list PROMOTED as a legal TRANSITION ARTIFACT edge | LIFE (text) | MISSING→added to plan | only docs (docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md); c7ed457 REGISTERED->IMPLEMENTED path in ahos_org/registry.py -> extend it, no new lifecycl | M12 |  |
| AD-0963 | 445 | Assurance is a bounded numeric annotation on evidence/memory. It is not authority, not truth, and not a substitute for verification, contradiction handling, or approval. Scalar scores must not create capabilities | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0964 | 455 | Memory requires evidence references, provenance, and a lifecycle that can be challenged. Memory must never automatically become TCB-authoritative knowledge. Autonomous learning is out of scope | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-0965 | 471 | Untrusted callers may read copied views of agents, tasks, epistemic objects, research missions, audit events, and capability/delegation status. Projections have no mutators and must not expose secrets (this slice stores none). Write-through via returned objects is forbidden | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0966 | 477 | Untrusted/future-plugin modules must not import governed-store mutators, TCB internals, governance internals, authority internals, or the audit ledger. Static inspection is the Slice 2A/2B control. Runtime import firewalls and process isolation are deferred | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0967 | 483 | In scope (must deny or contain): | EPIST (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0968 | 523 | Production human authentication, passwords, WebAuthn, IdP federation, workload identity for agents, and credential storage are deferred . They must exist before any sensitive integration | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-0969 | 543 | Legacy Slice 1 ( ahos org ) remains a separate governance scaffold. It is not authoritative for Slice 2A/2B governed state. Wrap-and-harden: do not silently preserve bypass APIs into the new store. Do not wire Slice 1 mutators to future runtimes | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |

### `docs/architecture/SLICE_2B_DEFERRED_DECISIONS_ADR.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0970 | 32 | CREATE TASK ) do not scope to a task. Because child grants must narrow to a | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/architecture/SLICE_2B_IMPLEMENTATION_REPORT.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (5)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0971 | 81 | Slice 2B; process isolation or a stronger language/runtime boundary is required | WORKER (text) | EXISTS-PARTIAL (reuse/extend) | research_worker/ + agent_org/research_host/ (process-isolated, 5 test files) | M12 |  |
| AD-0972 | 92 | Delegated authority must be time-, policy-, capability-, operation-, | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0973 | 102 | Evidence must be current, non-revoked, valid, and independently PASS-verified | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0974 | 207 | Child task authority gain: task scopes must be subsets of parent scopes; | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0975 | 250 | They must not be wired to future runtime adapters. A future migration should | PERSIST (text) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |

### `docs/architecture/SLICE_2B_REMEDIATION_01_IMPLEMENTATION_VS_SPEC.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0976 | 75 | D-18 LOW "Projection staging" is a failure-injection trip, not a staged store SPEC CONFORMANT BY DESIGN Spec §28 requires copied views ; snapshot for projection deep-copies under lock. No staged projection store is required by spec | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0977 | 186 | Some task required=False commands cannot be usefully delegated because child grants must narrow to a task. Not changed | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/architecture/agent_matrix_v2.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0978 | 4 | Laws honored: no agent exists by declaration alone (PART J) — MISSING/PARTIAL/PLANNED never | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/architecture/ai_council_architecture.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0979 | 7 | AI is ADVISORY ONLY. The council is not a decision authority and can never become one: | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-0980 | 10 | AI output may never become authoritative evidence, market data, numeric truth, financial | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0981 | 56 | INSUFFICIENT EVIDENCE/NEEDS MORE DATA. Red team vetoes CLAIMS/promotions — never rewrites | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/architecture/cognitive_agent_fabric.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0982 | 5 | Agent existence is earned, never declared | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0983 | 21 | UNKNOWN health never becomes READY (no-evidence law applies to liveness | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/architecture/cognitive_agent_mapping_w10.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (10)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0984 | 59 | Nazarov oracle integrity; never one feed → ≥2 sources or confidence-capped single-source — uncorroborated flip capped — SOURCE DISAGREEMENT PROBE — per-source availability matrix — providers.yaml chains exist; disagreement probe DEFINED MAPPED CRYPTO-05 (probe DEFINED ⇒ F-adjacent honesty | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-0985 | 67 | Larsen settlement/finality semantics must be explicit → distinguish observed/executable/settled states in every value claim — unpriced settlement forbidden (PT-X3-v2 law) — FINALITY SEMANTICS CHECK — state fields separate obs vs settled — position state event + settle guards exist DRAFT-W | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-0986 | 73 | Poulsen (journalistic/security verification) claims about systems must be independently reproduced → auditor ≠ producer; reproduction before acceptance — self-certified claim REJECT — REPRODUCTION CHECK — second-run parity — run all checks replay culture MAPPED SEC-01/MATH-09 area | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0987 | 96 | Ramanujan pattern is hypothesis, never proof MAPPED MATH | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0988 | 97 | André Weil structural correspondences must be total → every bridge between representations (SQLite⇄PG, raw⇄normalized) is a total, tested function — partial mapping = defect list — BRIDGE TOTALITY CHECK — unmapped cases enumerated — PG parity audit (33/33 drift) is the honest exemplar DRAFT-W | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-0989 | 124 | Einstein thought experiments must land as testable consequences; humility about what is proven — untestable speculation marked PERSPECTIVE, not claim — TESTABILITY LINT — every vision doc ends in probes — phased architecture behind evidence gates DRAFT-W10 (HUM-03 extended | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0990 | 125 | Jules Verne disciplined imagination: scenarios as labeled fiction that generate requirements → FUTURE SCENARIO tag; a scenario is never evidence — scenario text quarantined from evidence — SCENARIO QUARANTINE LINT — tag-present check — roadmap docs as labeled scenarios DRAFT-W | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-0991 | 174 | May NEVER generate authoritative numbers every AI-form agent (AG-11/AG-12 + any future AI) contract note exists; runtime enforcement pending (F | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-0992 | 175 | May NEVER alter frozen governance all except the human via AG-23 path AG-23 holds PROMOTE — acceptable ONLY as documented human gateway (F5); require human gate: true marker in a future contract version | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-0993 | 185 | Circular invocation AG-11↔AG-13 dependency cycle (W10A-07) none — registry does not validate acyclicity F2: must be resolved before any runtime | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |

### `docs/architecture/cognitive_principle_matrix.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0994 | 21 | Nazarov (oracle integrity, never one feed) · Adams (liquidity = truth of markets | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-0995 | 36 | CRITICAL LAW: pattern alone never proves; AI confidence is not evidence | CALIB (text) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |

### `docs/architecture/orchestration_comparison.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0996 | 37 | Temporal must not become a hidden single point of failure: if Temporal is DOWN and Lane-A | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |

### `docs/architecture/pg_parity_audit_w9.md` — SUPPLEMENTARY/ANNEX, 2026-08-20 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0997 | 27 | Destruction rule: SQLite evidence is NEVER deleted by migration | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/architecture/runtime_dependency_graph.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0998 | 38 | OPTIONAL (never affects status): redis, event bus (both NOT JUSTIFIED by evidence | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/architecture/single_start_runtime.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (5)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-0999 | 9 | Tomorrow (host exists): the same surface wraps docker compose + Temporal; the operator NEVER | PERSIST (text) | SUPERSEDED | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 | Owner update 2026-10-02 18:49 (remove Docker/n8n) + M10 Stage-1 decision d80b5b7 (embedded PGlite, verified to parity 7ace415); Docker volumes kept for rollback |
| AD-1000 | 16 | /8. optional Redis/bus health (never affects status) → 9. config verification → | SELFDIAG (text) | EXISTS-PARTIAL (reuse/extend) | engine/health_manager.py, architecture/runtime/observability_snapshot.py, scripts/gateway_port.py (06e44e6) | M11/M14 |  |
| AD-1001 | 24 | SAFE HALT run NEVER replays as a later success (new attempt executes | ONECLICK (doc) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-1002 | 35 | START (full chain, honest verdict) YES (Python engine) test one start system online + test real config boot never fabricates online | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1003 | 40 | Boot actual containers/Temporal workers NO — NO HOST BLOCKED NO HOST, never claimed | WORKER (text) | EXISTS-PARTIAL (reuse/extend) | research_worker/ + agent_org/research_host/ (process-isolated, 5 test files) | M12 |  |

### `docs/canonical/AGENT_COUNCIL.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1004 | 18 | External AI opinions (ChatGPT/Claude/Gemini/local) = optional review text; never repo writes, never numbers | COUNCIL (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/ai/council_live.py, architecture/ai/debate_council.py, council.ts, tests/test_ai_council_live.py, test_multi_mind_council_anti_echo.py | M15 |  |

### `docs/canonical/DATA_MODEL.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1005 | 20 | NULL=UNKNOWN (never fabricated) · dual timestamps everywhere · raw payload sha256 before normalization · | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/canonical/EXECUTION_STATE.md` — SUPPLEMENTARY/ANNEX, 2026-09-28 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1006 | 21 | That logging had never been mechanised. The five verification steps existed only in | OBS (text) | EXISTS-PARTIAL (reuse/extend) | engine/health_manager.py, architecture/runtime/observability_snapshot.py, scripts/gateway_port.py (06e44e6) | M11/M14 |  |
| AD-1007 | 76 | Missing persistence stores read NO DATA — the honest state of a host that has never | PRINC (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/canonical/KNOWLEDGE_MAP.md` — SUPPLEMENTARY/ANNEX, 2026-08-28 (12)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1008 | 2 | This is THE entry point. Read order below; everything else is referenced, never duplicated | PRINC (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1009 | 84 | PART J closed: engine/agent matrix v2.py (deterministic generator, never hand-edited) → | PRINC (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1010 | 125 | PRE FIX = retrieved ts < 1786595433.489443 · POST FIX = ≥ (owner-mandated split; never merge | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-1011 | 167 | Laws enforced & proven: expired windows never attempted · no backfill · true retrieved ts · | ONECLICK (text) | EXISTS-PARTIAL (reuse/extend) | start_ahos.bat/.ps1, AHOS_WINDOWS_OPS.bat, AHOS_PRE_SOAK_NOW.bat, AHOS_MAIN_FIRST.bat (4 parallel launchers); config/control_plane.yaml ControlPlane test-only | M11 (consolidate) |  |
| AD-1012 | 172 | F12 = MITIGATION DEPLOYED (never SOLVED; VERIFIED only after several real windowed cycles | PRINC (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1013 | 364 | Fewer than 10 pre-prediction observations ⇒ UNKNOWN bucket (never a default | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1014 | 384 | UNKNOWN with value None — the signal's False-on-missing default never | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1015 | 403 | OLLAMA BASE URL documented but never read (code reads OLLAMA API URL); | PRINC (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1016 | 448 | UNKNOWN/NO DATA are explicit, never a fake numeric score; derived after the | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1017 | 461 | GOVERNANCE REQUIRED (any regression or failed test ⇒ REGRESSION DETECTED; | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1018 | 559 | COMPARES — never implements/approves/merges | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-1019 | 597 | Measured-and-rejected (recorded in the experiment ledger, never re-proposed): | RESSTD (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |

### `docs/canonical/PROVIDERS.md` — SUPPLEMENTARY/ANNEX, 2026-08-20 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1020 | 19 | NO KEY/AUTH REQUIRED/RATE LIMIT/DOWN/ERROR/UNSUPPORTED vocabulary (M-GAP | PROVIDER (text) | IMPLEMENTED+TESTED | architecture/providers/registry.py + adapters, tests/test_provider_abstraction.py, test_provider_failure_resilience.py, 1a0d141 ProviderHealth | M13 extend |  |
| AD-1021 | 24 | Free-first ordered chains per capability; paid tier never a hard dependency; envelope contract | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-1022 | 29 | Rate/breaker sync law (Month 2): architecture adapters/breakers must never be | PRINC (doc) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/canonical/RESEARCH.md` — SUPPLEMENTARY/ANNEX, 2026-08-16 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1023 | 18 | Small n ⇒ verdict INSUFFICIENT DATA (never over-read | RESSTD (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |

### `docs/engineering/ALERTS_WEB_BANNER.md` — SUPPLEMENTARY/ANNEX, 2026-09-09 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1024 | 7 | PHASE0 recorded /api/alerts as unwired: the route existed; Command Center never fetched it | ALERT:System Failure (text) | EXISTS-PARTIAL (reuse/extend) | architecture/alerts/engine.py, telegram_ai/alerts.py, telegram_ai/pump_alert.py, tests/test_alert_engine.py, test_proactive_alert_delivery.py | M17/M18 |  |

### `docs/engineering/PHASE0_MASTER_AUDIT_AND_FOUNDATION.md` — SUPPLEMENTARY/ANNEX, 2026-09-09 (7)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1025 | 54 | Lane B identity resolution overlay 1 Wrap frozen token id ; do not edit identity.py | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-1026 | 77 | Lane A security gate vs Lane B architecture/security vs TS fetchSecurity Three verdict vocabularies Compose; do not add a fourth | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-1027 | 109 | Phase 5 may be prototyped after Phase 3 but must not emit paper/alerts before Phase 6 gates | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |
| AD-1028 | 123 | Empty VM DB filed as soak High AGENTS.md + start.sh never init stores | PERSIST (text) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |
| AD-1029 | 150 | EXACT FILES THAT MUST REMAIN FROZEN | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-1030 | 162 | Also do not mutate: docs/canonical/MASTER DIRECTIVE v1.md , existing reports/ evidence, operator .env , SQLite stores under data/ | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1031 | 186 | Worktree + environment scripts exist and do not init DBs or drizzle-push | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |

### `docs/engineering/PHASE2_SECURITY_GATE.md` — SUPPLEMENTARY/ANNEX, 2026-09-09 (6)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1032 | 50 | CRITICAL vs HIGH (do not confuse the registry | SECSTATE (doc) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-1033 | 62 | HIGH (not veto; overlay must not invent a veto): | SECSTATE (doc) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-1034 | 84 | SIGNAL CRITICAL PROJECTION must equal the live CRITICAL set | SECSTATE (doc) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-1035 | 115 | UNKNOWN critical evidence is never treated as safe | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1036 | 211 | Lane A paper trading frozen Lane A evaluate entry treats PASS WITH UNKNOWN as QUALIFIED ENTRY FROZEN LANE-A LIMITATION do not edit this phase | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-1037 | 216 | SQLite pair created ts drop persistence missing age → overlay INCOMPLETE No (fail-closed) do not redesign this phase | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |

### `docs/engineering/PHASE3_CANONICAL_DECISION.md` — SUPPLEMENTARY/ANNEX, 2026-09-09 (5)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1038 | 7 | Lane A freeze: must remain 36 files — verify with python3 -B scripts/freeze lane a.py | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-1039 | 81 | Telegram service Still must not import OpportunityScorer or instantiate a second authority | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1040 | 84 | Command Center Reads Python JSON via /api/canonical + snapshot overlay. Missing/stale ⇒ UNAVAILABLE/STALE, never invented BUY | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1041 | 126 | GET /api/canonical returns the fail-closed loader, never a live BUY on a STALE file | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1042 | 130 | Phase dependency (do not auto-merge | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |

### `docs/protocols/AGENT_COMMUNICATION_PROTOCOL.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (5)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1043 | 18 | Existing related artifacts (do not treat as this protocol): | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-1044 | 51 | SENDER AGENT / RECIPIENT AGENT must be known identity strings (Slice 1 id, research id, planned agent.org. , or human. ). Unknown recipient → BLOCKED , do not invent a listener | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1045 | 52 | CONSTRAINTS must include Constitution non-overrides and any FORBIDDEN CAPABILITIES | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1046 | 79 | CONTRADICTION REPORT must include the contradiction block from [AGENT EVIDENCE PROTOCOL.md](AGENT EVIDENCE PROTOCOL.md | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-1047 | 80 | RESULT bodies must follow [AGENT RESPONSE PROTOCOL.md](AGENT RESPONSE PROTOCOL.md | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/protocols/AGENT_ESCALATION_PROTOCOL.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1048 | 17 | CONTEXT STATUS = INSUFFICIENT and missing context is required for the asked conclusion; | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1049 | 71 | ESCALATION TARGET must not be the same agent. Agent One is not a valid target while unimplemented | REALCLASS (text) | EXISTS-PARTIAL (reuse/extend) | ahos_org/registry.py states, reports/grok/REMAINING_REALITY_REGISTER.md | M9 (done) / M12 |  |

### `docs/protocols/AGENT_EVIDENCE_PROTOCOL.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1050 | 61 | If two sources disagree, do not silently pick one | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-1051 | 75 | Known current organization contradiction (must remain visible): | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-1052 | 92 | Evidence older than the files it cites, or citing L4 docs as current architecture, must be labeled [STALE] | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `docs/protocols/AGENT_RESPONSE_PROTOCOL.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1053 | 43 | TASK TASK ID or human task statement; do not invent IDs | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-1054 | 54 | OPEN QUESTIONS Unresolved; do not fill with guesses | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1055 | 57 | CONFIDENCE Qualitative; never a fake numeric score without a defined method | CALIB (text) | EXISTS-PARTIAL (reuse/extend) | architecture/learning/calibration.py, score_ledger.py, tests/test_score_ledger_calibration.py, test_calibration_*.py; no outcome data | M13 |  |

### `docs/protocols/AGENT_SUPERVISION_PROTOCOL.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (7)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1056 | 22 | Each agent charter must name, as identities not as “the model”: | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1057 | 40 | Challenge Human; planned agent 19 (Red Team); Slice 1 agent.red-team is a different logical role — do not treat as the same instance | GIT (text) | EXISTS-PARTIAL (reuse/extend) | CLAUDE_CONTINUATION_GUIDE.md commit rules, .cursor/hooks.json ahos-guard | all |  |
| AD-1058 | 41 | Verify Independent agent or human; never solely the producing agent | GATEDOPS (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-1059 | 44 | Change authority Human governance + code change in the relevant plane; never the agent | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-1060 | 46 | Agent One (unimplemented) may request work and collect results. It may not verify itself, approve, or change another agent’s authority | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-1061 | 50 | Repository reality (do not over-claim | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1062 | 69 | Agents must not treat a passed unit test of their own package as independent verification of a new claim | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |

### `docs/security/AGENT_19_RED_TEAM_AND_ADVERSARIAL_ORGANIZATIONAL_SECURITY_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-15 (12)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1063 | 102 | These statements remain distinct. Agent One must never become sole truth source, verifier, governance authority, execution engine, or self-modifying monolith — yet the current Cursor workflow already approximates that collapse | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1064 | 174 | Org must not disturb AHOS soak — this mission had AHOS IMPACT = NONE | SECSTATE (doc) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-1065 | 264 | RT-003 Command Specialist active in Cursor Agent-07 sends "Agent-12 must execute X" in chat Peer prose = command Protocol says COMMAND≠REQUEST; no enforcement DOCUMENTARY HIGH Unauthorized activation P0 LOW None HIGH MC command typing + envelope VERIFIED | TCB (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, identity.py, governance.py, research_worker/protocol.py (22 test files) | M12 |  |
| AD-1066 | 359 | Gap: No automated enforcement that verifier must access L0/L1 artifacts | INDVER (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/tcb.py, agent_org/epistemic.py, agent_org/research_host/host.py (11 test files); independent verifier agent not live | M12/M15 |  |
| AD-1067 | 493 | Agent-07 → Agent-01: "Agent-12 must execute X" — may succeed if human treats as command | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-1068 | 535 | Forged CommandEnvelope authority context ref DENY — must be DERIVE AUTHORITY AT TCB [TESTED] | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1069 | 623 | AHOS [VERIFIED] anti-pattern: pulsing "ROOTS LIVE" in app-shell.tsx — org UI must not replicate | DASH (text) | EXISTS-PARTIAL (reuse/extend) | CommandCenter.tsx, app/, canonical_read_model.ts, AHOS_WEB_COMMAND_CENTER.md | M17 |  |
| AD-1070 | 638 | False state composition: Agent state T1 + Mission T2 + Verification T3 + UI T4 — can produce state that never existed if UI joins without snapshot ID | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |
| AD-1071 | 756 | AGENT A CLAIM A AGENT B CLAIM B REPOSITORY EVIDENCE CLASS SEVERITY DO NOT ASSUME | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1072 | 866 | ID WHY IT MATTERS ATTACK PATH CURRENT GAP MINIMUM SAFE CONTROL DEPENDENCIES DO NOT IMPLEMENT YET IF | RES2ARCH (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/evolution_gate.py, architecture/evolution/engine.py, strategy_lab/hypothesis_engine.py, contracts/improvement_proposal_contract_v1.json,  | M14/M16 |  |
| AD-1073 | 932 | HD-19-07: Cursor federation trust level — what L5 may and may not trigger | SECSTATE (doc) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-1074 | 1024 | Persian/RTL REQUIRED Semantic inversion risk | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |

### `docs/supervision/SUPERVISION_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-12 (5)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1075 | 71 | Scope (delta-first — never full rescan without cause | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1076 | 87 | FIX BEFORE CONTINUE Build agent must fix before more work | AUTOCONT (text) | EXISTS-PARTIAL (reuse/extend) | process rule; enforced via reports/grok/CLAUDE_CONTINUATION_GUIDE.md, docs/canonical/GOVERNANCE.md, .cursor/skills/; reports/grok/OWNER_DIRECTIVE_MISSION_PLAN.m | all |  |
| AD-1077 | 177 | Fail-closed: insufficient evidence = UNKNOWN , never upgrade | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1078 | 183 | ALLOW · MONITOR · DO · DO NOT · FIX BEFORE CONTINUE · FIX BEFORE MERGE · BLOCK · STOP · ESCALATE TO HUMAN | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-1079 | 201 | Every recommendation must pass: | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |

### `reports/agi_aci_evolution/ARCHITECTURE_MAP.md` — SUPPLEMENTARY/ANNEX, 2026-09-13 (2)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1080 | 39 | Intelligence → execution (must remain | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1081 | 49 | Kill switch must not require Cognitive Core cooperation (n8n/telegram sketches exist; not upgraded here | TG (text) | IMPLEMENTED+TESTED | telegram_ai/ + chat.ts/chat_agent.ts (71fe160, 231e7ac), GM-02 552eda7, W57 82dcfb7, tests/test_telegram_*.py, scripts/chat_agent_selftest.ts | M17 extend |  |

### `reports/agi_aci_evolution/MEMORY_ARCHITECTURE_AUDIT.md` — SUPPLEMENTARY/ANNEX, 2026-09-09 (1)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1082 | 12 | Episodic (soak observations) PARTIAL Lane-A sqlite — must not be this store | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |

### `reports/agi_aci_evolution/P5_EPISODE_POLARITY_ARCHITECTURE_REPORT.md` — SUPPLEMENTARY/ANNEX, 2026-09-10 (6)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1083 | 68 | METACOGNITIVE lexical inventory counted, never cited as support | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1084 | 76 | Orchestrator uses that helper, not verdict == "WEAKLY SUPPORTED" . Episode rows may still be written; LESSON / HYPOTHESIS / reusable INFERENCE may not | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-1085 | 188 | P5 STATUS recorded there FIX REQUIRED | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1086 | 191 | The original document is the historical failure record. Passing tests on this SHA do not rewrite it | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-1087 | 217 | Assumptions are recorded ( ASM-000001 ) and do not enter EvidenceBinding lists. They do not constrain WEAKLY inference beyond critic rules that almost never fire on P5 (SUPPORTED is stripped). They must not be treated as evidence; they are also not a working assumption engine | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1088 | 218 | TEMP CURRENT is never assigned. ACTIVE + observed at is DATED . A timestamp is not freshness proof. This layer does not invent an age-from-clock current-state model | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `reports/agi_aci_evolution/P5_HYBRID_D_V3_REMEDIATION_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-11 (18)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1089 | 25 | Hybrid-D’s consumption boundary is working. HMAC verification against the latest store row is PROVEN . Ordinary remember , SQLite INSERT without a process MAC, revision inheritance, generic ingest, world-model FACT mint, and DERIVED FACT grant reuse do not yield FACTUAL PREMISE | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-1090 | 44 | Time: factual valid until / future observed at checks use episode authority time supplied by the orchestrator/runtime clock ( time.time() by default, already the CognitiveOrchestrator.run ts ). CognitiveTask.created at remains task metadata and MUST NOT be read for grant validity | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1091 | 262 | Existing AHOS sources (reuse, do not invent | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1092 | 273 | Eval seeders in architecture/cognitive/benchmark/ and loop/benchmark.py must not import a production mint function. They receive an optional injected port from the test/eval composition root; default None means ungranted data (not FACTUAL PREMISE | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |
| AD-1093 | 283 | Ordinary IngestPort() / missing-authority persist: fail closed (raise or persist without grant — never process-mint | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1094 | 289 | A nested def persist acquired closed over the secret, never assigned to a module global | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-1095 | 341 | TestAcquisitionAdapter.persist(statement=…) is allowed in tests/ because Level 3 tests are proving the trusted path, not the untrusted caller. Level 4 tests must not import it | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-1096 | 357 | ProductionScheduler.check clock drift wall vs monotonic for scheduler abort do not import into cognitive loop; different subsystem | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1097 | 364 | Conceptual contract (do not implement in this task): | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1098 | 376 | EvidenceBinding stores authority now=ts (not as a trust flag). live grant ok() uses authority now , never task.created at | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1099 | 403 | E Malformed task.created at must not control grant; fail-closed or ignore | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1100 | 432 | Orchestrator is the supplier of trusted now on the production path. Tests that call bind context directly must pass the test episode clock explicitly (Level | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-1101 | 440 | V3 MUST NOT redesign these PROVEN controls: | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |
| AD-1102 | 469 | Temporal tests freeze time via CognitiveTask.created at / fixture NOW , which is the production grant clock. They do not prove expiry against an orchestrator clock | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-1103 | 473 | Future tests must split levels. Do not modify tests in this task | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-1104 | 533 | Delete process authority() as a live-issuer getter. Verify must not require calling mint | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1105 | 557 | L/M Serialize/deserialize capability BLOCKED (must not pickle secret; grant JSON is data, still needs verify | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-1106 | 662 | Level 4 must not use fixtures that mint | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |

### `reports/agi_aci_evolution/P5_MEMORY_AUTHORIZATION_BOUNDARY_ARCHITECTURE_DESIGN.md` — SUPPLEMENTARY/ANNEX, 2026-09-10 (33)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1107 | 76 | These five must not be equated | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1108 | 81 | B. Retrieval May retrieve this object MemoryRetriever anchors (exact id, lexical, P4.3 rejects) Unchanged. Retrieval must not become the fact-authorization gate. P4.3 FAILURE-intent reject is not authorization ( PROVEN requested evidence still anchors | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-1109 | 95 | FACTUAL PREMISE remains a reasoning role , never a stored kind ( PROVEN EpistemicKind has no FACTUAL PREMISE; test remember rejects factual premise kind | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1110 | 123 | Acquisition path REQUIRED FOR AUTHORITY as source location + producer Distinguishes adapter vs raw remember | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1111 | 156 | OBSERVED FACT / DERIVED FACT (Z3 candidate) FORBIDDEN at grant issue. UNKNOWN ≠ fabricated evidence | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1112 | 173 | Bind temporal from parts Uses status + observed at only . ACTIVE + observed at → DATED , never CURRENT. CURRENT is reserved and unused by this layer | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1113 | 181 | Minimum invariant (do not redesign decay | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1114 | 183 | An object whose valid until (or expires at ) is already ≤ now must not receive FACTUAL PREMISE merely because status is still ACTIVE | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1115 | 207 | Matching source id MUST NEVER mean the claim is true | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1116 | 221 | Write Optional payload fingerprints if the adapter already knows a component id — OPTIONAL METADATA, never sufficient for FACTUAL PREMISE | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1117 | 238 | Existing P5 principle remains: stored metadata must never manufacture authority when the statement contradicts it. Live recompute stays. The new write grant authorizes kind persistence , not support class | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-1118 | 268 | → OBSERVED FACT FORBIDDEN | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1119 | 271 | LESSON → OBSERVED FACT FORBIDDEN / UNREACHABLE via accept | LEARN (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/prediction_lifecycle.py, 202f8c9 learning bridge | M13 |  |
| AD-1120 | 276 | Minimum OBSERVED FACT design: do not change accept() . Follow-on (not this minimum): bind accepted kind to proposed kind ; require existing derived from ; treat requires human as real (out of scope unless a human-attestation grant exists | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-1121 | 282 | Legend: DIRECT = happens by storing/consuming that kind as-is. AUTHORIZED TRANSFORMATION = only via an explicit grant/orchestrator policy. CONDITIONALLY ALLOWED = allowed if other gates pass. FORBIDDEN = code veto or consumption forbid. UNREACHABLE = no path | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-1122 | 291 | HYPOTHESIS FORBIDDEN FORBIDDEN FORBIDDEN as fact FORBIDDEN alone DIRECT label; write-back extra FORBIDDEN without facts | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1123 | 292 | LESSON FORBIDDEN FORBIDDEN FORBIDDEN FORBIDDEN alone same | LEARN (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/lessons.py, architecture/learning/prediction_lifecycle.py, 202f8c9 learning bridge | M13 |  |
| AD-1124 | 293 | INFERENCE FORBIDDEN FORBIDDEN FORBIDDEN FORBIDDEN alone same | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1125 | 295 | EPISODIC + INFERENCE FORBIDDEN retype FORBIDDEN FORBIDDEN DIRECT strength FORBIDDEN alone episode log DIRECT; reusable extra FORBIDDEN | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-1126 | 296 | PREDICTION FORBIDDEN FORBIDDEN FORBIDDEN FORBIDDEN FORBIDDEN extra | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1127 | 297 | OPINION FORBIDDEN FORBIDDEN FORBIDDEN FORBIDDEN FORBIDDEN extra | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1128 | 298 | SIMULATION FORBIDDEN FORBIDDEN FORBIDDEN FORBIDDEN FORBIDDEN extra | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1129 | 299 | ASSUMPTION (not a kind) UNREACHABLE FORBIDDEN FORBIDDEN FORBIDDEN FORBIDDEN | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1130 | 300 | CONTRADICTORY pair of facts each remains OBSERVED FACT mixed: FORBIDDEN positive both may classify SUPPORT/CONTRA FORBIDDEN WEAKLY SUPPORTED FORBIDDEN reusable | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-1131 | 301 | STALE OBSERVED FACT stays OBSERVED FACT FORBIDDEN FORBIDDEN FACTUAL PREMISE FORBIDDEN FORBIDDEN | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1132 | 303 | Critical invariant (design): No epistemically weaker or non-factual artifact may silently gain factual authority. Consumption already enforces this for non-OBSERVED FACT. Write must enforce it for minting OBSERVED FACT | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1133 | 305 | UNKNOWN row: future FORBIDDEN to mint OBSERVED FACT with UNKNOWN provenance. UNKNOWN AGE (missing observed at) stays FORBIDDEN as FACTUAL PREMISE | PRINC (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1134 | 391 | Backward compatibility Adapters, corpus, tests, record failure must obtain grants (synthetic issuer for SYNTHETIC TEST DATA | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-1135 | 395 | New bypass risk Grant constructor public without HMAC = A in disguise — must HMAC or sealed mint | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-1136 | 415 | Lane A Must not open soak DBs ( PROVEN FORBIDDEN DB NAMES | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-1137 | 484 | Test design (must exist before implementation is complete | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-1138 | 530 | Future implementation specification (do not implement | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1139 | 612 | Whether DERIVED FACT must require a grant: not the proven bypass (roles forbid FACTUAL PREMISE). Spec still includes FACT KINDS to avoid a second door. Alternative minimum is OBSERVED FACT-only grants; UNRESOLVED which is smaller vs safer — recommendation: both FACT KINDS | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |

### `reports/agi_aci_evolution/P5_V3_FINAL_REFINEMENT_ARCHITECTURE.md` — SUPPLEMENTARY/ANNEX, 2026-09-11 (21)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1140 | 26 | Public orchestrator stays input-only. Do not add ingest= , verifier= , secret= , or grant key= to CognitiveOrchestrator. init or run . A matching issuer/verifier pair must not be a public constructor combination | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-1141 | 27 | Verify is a pure function of (grant, fields, now, key) . Bind supplies key from an internally owned verify context, never from CognitiveTask and never from a public kwarg | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1142 | 28 | Mint is not an orchestrator attribute. The orchestrator must not hold BoundIngestPort / mint as a reachable persist API. Ordinary orch.run(task) cannot sign | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-1143 | 33 | This is VALID AFTER REFINEMENT . It does not replace Hybrid-D. Python still cannot stop ACE/ gc /reading grant secret . Ordinary application APIs must not recreate mint | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-1144 | 127 | It must not accept as an authority request: | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1145 | 149 | Until a Lane-B provider adapter is wired, do not mint from architecture/collector into cognitive memory (discovery DB / Lane A freeze). Production mint = zero adapters. remember remains data | LANEA (text) | IMPLEMENTED+TESTED | app/api/canonical/route.ts, docs/engineering/PHASE3_CANONICAL_DECISION.md, Lane A tests (42 files) | keep (gate on change) |  |
| AD-1146 | 156 | Default IngestPort() must not mint (raise or persist without grant). Remove persist observed acquisition as a minting function | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-1147 | 190 | Production packages must not import tests/ | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-1148 | 191 | Test vector key must not appear in architecture/ , config/ , or env ( AHOS TEST GRANT KEY forbidden | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-1149 | 193 | Production ObservationAuthority() / runtime must refuse the published test-vector key bytes (denylist of the committed vector) so a mis-wired runtime cannot treat test material as production | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1150 | 194 | Layer-4 test modules must not import the test compose/adapter | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-1151 | 205 | Layer 2/4: construct CognitiveOrchestrator exactly as production public API . Those instances get an internal verify-only random key and no mint . Remember/sqlite/forged grants fail. Tests never receive a matching ingest port | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-1152 | 222 | Production bind never uses the test key | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-1153 | 223 | Public orchestrator never accepts that key | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-1154 | 269 | Not a production public capability: tests/compose test cognitive runtime.py . Production architecture/ must not import it. Layer 4 must not import it | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1155 | 282 | Grant validity MUST NOT MUST | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1156 | 328 | Conceptual (do not implement in this task): | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1157 | 392 | Layer 2/4 use only public orchestrator/store/adapter APIs and do not import test compose | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-1158 | 405 | Per this design-only mission: do not implement now. IMPLEMENTATION AUTHORIZED = NO | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1159 | 411 | MUST CHANGE / MUST NOT CHANGE (future implementation | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1160 | 421 | CognitiveOrchestrator. init public signature unchanged except it must not grow grant kwargs | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |

### `reports/agi_aci_evolution/P5_V4_FINAL_SECRET_BOUNDARY_DESIGN.md` — SUPPLEMENTARY/ANNEX, 2026-09-11 (31)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1161 | 27 | Layer 3 — K O exists only as O instance state and is read only inside O ’s own verification method. It never enters ContextVar, GrantVerifyContext , bindings, tasks, retrieved items, retriever/memory arguments, logs, or CognitiveResult | ORGMEM (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/memory/ (store, consolidation, self_query); ahos_cognitive_memory.sqlite 0 bytes; no org-memory store | M14/M16 |  |
| AD-1162 | 39 | IMPLEMENTATION AUTHORIZED = NO . Independent review of this report is required before any implementation turn | DAILY (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/reports.py, engine/research_report_bot.py, TELEGRAM_RESEARCH_REPORT | M17 |  |
| AD-1163 | 182 | K O first becomes available at O. init . It first becomes available to verification at O. permits observation grant . It is never an argument to retrieve , assemble context , remember , or public reason / bind item | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1164 | 184 | Public module reason / bind item / bind context remain fail-closed: they must not consult ContextVar keys and must set grant ok=False . Production O.run must not call them to assign FACTUAL PREMISE | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1165 | 216 | ContextVar FORBIDDEN (present) FORBIDDEN — | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1166 | 217 | GrantVerifyContext FORBIDDEN (present) FORBIDDEN for keys/issuers-as-authority — | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1167 | 219 | RetrievedItem / CognitiveTask / CognitiveResult / ReasoningTrace no key FORBIDDEN — | AGILOOP (text) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1168 | 223 | Logging / exceptions / repr default object repr; no log of secret FORBIDDEN to log/repr K O ; do not put it in ValueError text — | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-1169 | 224 | Thread-local / async task-local ContextVar (task-local) FORBIDDEN for K O — | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1170 | 227 | Public current grant verify context() returns .key must not return K O ; production run must not set it — | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1171 | 229 | If K O must be stored on a collaborator-visible object, reject the design . It does not | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1172 | 246 | Manipulate ContextVars? YES YES — must not matter to O. permits | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1173 | 277 | What it carries key , issuer id , trusted now must not carry secret, issuer-as-authority, verifier, grant context | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-1174 | 338 | Production code in architecture/ must not mint under K O via any function whose parameters include statement= , AcquisitionRecord , or a caller-built “typed result” | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-1175 | 339 | Until a poll/fetch adapter is separately authorized, production mint stays 0 . Then FACTUAL PREMISE never occurs in production O.run — fail-closed, not a bypass | SECSTATE (text) | IMPLEMENTED+TESTED | architecture/security/gate.py, discovery/security_gate.py, tests/test_canonical_security_gate.py, test_security_intelligence.py | keep |  |
| AD-1176 | 340 | Future adapter public API: poll() / fetch() with no result argument . Provider I/O stays inside the adapter object owned by the composition root. That object must not be handed to ordinary run() callers as a statement= RPC | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |
| AD-1177 | 355 | Required: Grant(O1) is not automatically valid for O2 . No transfer mechanism exists; do not add one | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1178 | 390 | Production K O is per-instance urandom, never imported by tests. Reading orch. grant verify secret on an orchestrator a test constructed is that instance’s key, not a shared production secret file. Keep it out of Layer 4 mint proofs | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-1179 | 398 | Stops ContextVar join / retriever rekey yes if K O never in ContextVar yes | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1180 | 411 | An implementer must not invent a fourth place to put K O . Exact contract: | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1181 | 424 | CognitiveOrchestrator. init (memory, hypotheses, ledger path, retriever=None) — do not add secret , verifier , ingest , authority , issuer , grant verify context , permits | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-1182 | 426 | CognitiveOrchestrator.run(task, budget=None, now=None, use memory=True) — do not add those either | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-1183 | 428 | Public reason / bind item / bind context — do not add key= , secret= , verifier= , permits factual= , grant ok= | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-1184 | 434 | O. permits observation grant(...) verify observation grant(..., key=self. grant verify secret, expected issuer id=self. verify issuer id, now=ts) ; never reads ContextVar | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-1185 | 439 | EvidenceBinding.live grant ok return frozen grant ok ; do not HMAC via ContextVar | DISTINCT (text) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1186 | 441 | O.run do not call current grant verify context / push grant verify context / GrantVerifyContext | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1187 | 449 | Must not carry K O , production issuer authority, verifier, or authority-bearing grant context. Production run should not set the grant ContextVar. If the ContextVar remains for unused clock fallback, production bind must ignore it for keys and issuers | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1188 | 453 | TestCognitiveOrchestrator in tests/ as in §16. Production must not import it. Layer 4 C1 replay stays non-FACTUAL | AG01 (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/ (tcb, authority, governance), agent_org/research_host/; Agent-01 runtime not live | M12 |  |
| AD-1189 | 464 | If an engineer cannot implement this without putting K O in ContextVar or adding key= to public reason , they must stop and re-read this section — not improvise | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1190 | 487 | Three layers (do not collapse | AGILOOP (doc) | EXISTS-PARTIAL (reuse/extend) | architecture/cognitive/loop/ (orchestrator, reason, metacognition, inference), architecture/cognitive/reasoning.py, tests (4+) | M14/M16 |  |
| AD-1191 | 578 | No implementation. No production/test/schema/Lane A/soak changes. No merge. Not ready for review. Independent review of this design is required before any implementation authorization | PUSHGATE (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |

### `reports/grok/GROK_SESSION_2026-10-02_REALITY_INSPECTION.md` — SUPPLEMENTARY/ANNEX, 2026-10-02 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1192 | 8 | Status vocabulary: IMPLEMENTED VERIFIED / IMPLEMENTED UNVERIFIED / DESIGN ONLY / OWNER ACTION REQUIRED / WALL CLOCK BLOCKED / BLOCKED / REJECTED / UNKNOWN; claim checks VERIFIED / CONTRADICTED / UNVERIFIABLE | CONTRA (text) | EXISTS-PARTIAL (reuse/extend) | architecture/knowledge/anti_echo.py, architecture/knowledge/evidence_graph.py, research_worker/analyst.py | M15 |  |
| AD-1193 | 57 | Telegram live E2E OWNER ACTION REQUIRED G11 NOT VERIFIED; credential present (CREDENTIAL PRESENT BUT REDACTED | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-1194 | 104 | Safety-architecture inventory (preserve, never modify | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |

### `AHOS_PHASE19_RELEASE_GATE.md` — UPDATE/CHANGE, 2026-08-20 (3)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1195 | 97 | The "do not touch architecture/ " rule was the Phase 18 scope grant, and | PRINC (default) | SUPERSEDED | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all | Phase-specific scope grants expired with their phase; current scope = OWNER_DIRECTIVE_MISSION_PLAN.md mission definitions |
| AD-1196 | 284 | The launchers have never been executed. This is a Linux sandbox with no | WORKER (text) | EXISTS-PARTIAL (reuse/extend) | research_worker/ + agent_org/research_host/ (process-isolated, 5 test files) | M12 |  |
| AD-1197 | 295 | Blockers to activation (unchanged, all USER-ACTION-REQUIRED | AUTOCONT (text) | EXISTS-PARTIAL (reuse/extend) | process rule; enforced via reports/grok/CLAUDE_CONTINUATION_GUIDE.md, docs/canonical/GOVERNANCE.md, .cursor/skills/; reports/grok/OWNER_DIRECTIVE_MISSION_PLAN.m | all |  |

### `AHOS_UPDATE_POLICY.md` — UPDATE/CHANGE, 2026-08-16 (4)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1198 | 5 | NEVER download code automatically: No background agent may pull or apply unvetted git commits | GIT (text) | EXISTS-PARTIAL (reuse/extend) | CLAUDE_CONTINUATION_GUIDE.md commit rules, .cursor/hooks.json ahos-guard | all |  |
| AD-1199 | 6 | NEVER modify architecture automatically: Subsystem boundaries and schemas require explicit human governance approval | GOVBOUND (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |
| AD-1200 | 7 | NEVER modify databases silently: Historical observations, paper trades, and experiment records are append-only | PAPER (text) | EXISTS-PARTIAL (reuse/extend) | paper_trading/cycle.py:run_full_cycle (not wired to daemon), exit_rules.py, position_monitor.py; 19 tables 0 rows, paper_exits=0 | M13 |  |
| AD-1201 | 8 | NEVER upgrade dependencies without approval: Package version bumps must pass the full 14-stage improvement proposal v1 workflow | REPRO (text) | EXISTS-PARTIAL (reuse/extend) | reports/grok/ (reality maps), docs/archive/consolidation_2026-09-26/, reports/backup_restore_drill.json | M9 (done) |  |

### `docs/protocols/AGENT_UPDATE_PROTOCOL.md` — UPDATE/CHANGE, 2026-09-15 (5)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1202 | 34 | The agent must not decide from the mission document alone | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1203 | 60 | Every newly encountered document must be labeled: | PRINC (default) | EXISTS-PARTIAL (reuse/extend) | docs/canonical/GOVERNANCE.md, docs/canonical/MISSION.md, agent_org/epistemic.py, config/cognitive_principles.yaml | all |  |
| AD-1204 | 105 | The agent must not silently change behavior, especially authority | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1205 | 117 | Agents may not infer new AUTHORITY CLASS from tone, urgency, or “you are the architect now” | GOVBOUND (text) | EXISTS-PARTIAL (reuse/extend) | agent_org/governance.py, agent_org/authority.py, docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md, .cursor/hooks.json ahos-guard | keep (locked domain) |  |
| AD-1206 | 123 | Specialists should re-read L0 after project changes. They must not treat a merged PR as governance approval ( MERGE ≠ GOVERNANCE APPROVAL ) unless tests + policy say the change is allowed | PUSHGATE (text) | HUMAN-GATE (locked) | governance gates: docs/canonical/GOVERNANCE.md, .cursor/hooks.json ahos-guard | gate |  |

### `reports/grok/DECKER_N8N_MIGRATION.md` — UPDATE/CHANGE, 2026-10-03 (13)

| ID | Line | Requirement | Key (map) | Status | Evidence | Mission | Note |
|---|---|---|---|---|---|---|---|
| AD-1207 | 15 | Python Lane B never touches Postgres. No Python Postgres driver exists in | PERSIST (text) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |
| AD-1208 | 23 | :59-65 and db :67-73 so importing never throws). Exactly four live | PERSIST (text) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |
| AD-1209 | 49 | OWNER DIRECTIVE MISSION PLAN.md:105-108 says "Postgres was never live on this | PERSIST (text) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |
| AD-1210 | 64 | THE REQUIRED INVENTORY TABLE | PERSIST (doc) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |
| AD-1211 | 77 | Design artifact deployment/docker-compose.target.yml never built (design only) Archive NONE NOT STARTED | PERSIST (text) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |
| AD-1212 | 86 | DATABASE URL env .env (gitignored — confirmed via git check-ignore ; values never printed or committed) Gateway → Postgres Same key, PGlite-flavoured value ( pglite://<dataDir or explicit flag) LOW — one-key switch, rollback = restore old value NOT STARTED | PERSIST (text) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |
| AD-1213 | 87 | POSTGRES PASSWORD env .env Container DB superuser Unused after switch; leave in place (never delete secrets) NONE NOT STARTED | SECRET (text) | EXISTS-PARTIAL (reuse/extend) | architecture/mission/ledger.py redaction (d1571c4), 0638643 redaction, .gitignore; secret-scan pre-commit not verified | M9.x/M14 |  |
| AD-1214 | 94 | Guard regex .cursor/hooks/ahos-guard.py:45-46 Blocks docker compose up in this repo Keep (defense-in-depth; also blocks accidental re-launch) NONE — do not touch .cursor/hooks.json overlay (binding) UNCHANGED (human-gated, § | PERSIST (text) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |
| AD-1215 | 108 | Route behaviour app/api/command/route.ts:20-23 (200 on failure), app/api/chat/route.ts:19-24 + :91-115 (retry + 500 w/ hint) Honest degradation contract Preserve exactly — this is the acceptance criterion for the smoke test LOW NOT STARTED (must be asserted by a test | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-1216 | 136 | Broad grep hits tests/test ahos.py , tests/test boundaries.py , tests/test operator validation gate.py , tests/test runtime w11.py Incidental compose/n8n string references Verify each still passes post-switch; do not bulk-edit LOW | TEST (text) | EXISTS-PARTIAL (reuse/extend) | tests/ (186 files, 466 total per 3004e8f), tests2b/, .github CI 8857929, docs/security/AGENT_19_RED_TEAM... | all |  |
| AD-1217 | 236 | Package config package.json , next.config.ts @electric-sql/pglite@^0.5.8 added; serverExternalPackages keeps the WASM module out of the webpack server bundle (it must resolve at runtime, not be bundled | IDENT (text) | IMPLEMENTED+TESTED | architecture/identity/ (fusion, resolution, gates), discovery/identity.py, tests/test_canonical_identity.py, test_identity_fusion.py | keep |  |
| AD-1218 | 268 | WHAT MUST NOT CHANGE (safety surface | PERSIST (doc) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |
| AD-1219 | 310 | Rollback path (will be documented in Stage 4, stated here so it is never | PERSIST (doc) | EXISTS-PARTIAL (reuse/extend) | SQLite canonical (config/paths.py); Postgres via M10 native portable PG (pg_dump/restore + parity tests) | M10 |  |

