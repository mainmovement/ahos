# DOCUMENT HYGIENE POLICY v2 (Deliverable F) — 2026-08-11
# Permanent system. Engine: engine/doc_hygiene.py (inventory→classify→plan→execute, all manifested).
# Supersedes wave-6 ad-hoc hygiene; wave-6 results remain valid evidence (D_CLEANUP_MANIFEST.md).

## 1. Classes (directive §7, binding)
A CANONICAL — current authority. Automation NEVER archives A.
B ACTIVE IMPLEMENTATION — code, schemas, governed data, current references (incl. redirect stubs).
C HISTORICAL EVIDENCE — decisions, failures, negative results, probes, audit. **NEVER removed.**
D SUPERSEDED — replaced by newer authority; lives in archive dirs WITH redirect stubs.
E EXACT DUPLICATE — byte-identical (sha256 group). Council-autonomous: ARCHIVE (not delete).
F REDUNDANT/LOW-VALUE — fully represented elsewhere. FLAG-ONLY; action needs council sign-off.
G TEMPORARY — regenerable (caches, bytecode, throwaway runtimes). Council-autonomous: DELETE.

## 2. Cleanup law (directive §8–§10, binding)
1. NEVER delete: negative evidence, failed experiments, rejected hypotheses (H1–H13…), audit
   evidence, security findings, probe failures, decision logs, provenance.
2. Every mutation: pre-sha256 → move/remove → post-verify → manifest record (machine-enforced in
   doc_hygiene.execute_plan; sha mismatch aborts that step).
3. Reversibility: E/F-moves are archives (content intact); G-deletions must be REGENERABLE
   (recorded regeneration recipe in the manifest).
4. Ambiguous ⇒ ARCHIVE, never delete. F-class ⇒ no autonomous deletion, ever.
5. User-file pool (uploads/) gets the same rules; wave-7 archived ONLY exact byte-dupes.

## 3. Cadence & ownership
- Each wave: engine/doc_hygiene.py (dry) → council review table → --execute → manifest.
- The inventory JSON is the period-over-period audit (added/removed/changed vs previous baseline).
- Idempotency is a release gate: a second dry run must plan 0 actions.

## 4. Wave-7 machine rules (engine reference)
A-globs, B-globs, C-default(conservative!), D-prefix (docs/archive/, *_archive_*), E-sha-groups,
G-patterns are enforced in code — see doc_hygiene.classify(). Any rule change = council decision
log entry + version bump here.
