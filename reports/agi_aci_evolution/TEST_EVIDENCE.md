# TEST_EVIDENCE

**Environment:** Cursor Cloud Linux `/workspace` (not `G:\robat\ahos`).  
**Interpreter for tests/validate:** `/tmp/ahos-test-venv` (ephemeral; not committed). System `python3` lacks pytest (PEP 668).  
**Soak daemon:** not started. Cloud sqlite: not treated as soak.

## P4.3 (lookalike discrimination)

**Base SHA:** `eb1dbcf883bf3cba94e18881c9bea9a5252a88af`  
See `P4_3_LOOKALIKE_DISCRIMINATION_AUDIT.md` and `P4_3_RETRIEVAL_BENCHMARK_REPORT.md`. Targeted pytest: 167 passed. Freeze 36/36. validate_imports PASS. Reproducibility equal. Precision 0.9091 / F1 0.9524 / recall 1.0 on the P4.1 cases.

```text
python3 -B scripts/freeze_lane_a.py
# result: Lane-A integrity OK (36 files pinned)  exit 0

/tmp/ahos-test-venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_retrieval_lookalike.py tests/test_retrieval_relevance.py \
  tests/test_cognitive_benchmark.py tests/test_cognitive_loop.py \
  tests/test_cognitive_memory.py tests/test_cognitive_core.py \
  tests/test_self_evolution_engine.py tests/test_multi_mind_council_anti_echo.py \
  tests/test_evolution_validate.py tests/test_cognitive_panel.py
# result: 167 passed  exit 0
```

## P4.2 (retrieval relevance)

**Base SHA:** `6e65f1573dea8c2fe91d6a181b25a20015e76fe1`  
See `P4_2_RETRIEVAL_RELEVANCE_AUDIT.md` and `P4_2_RETRIEVAL_BENCHMARK_REPORT.md`. Targeted pytest: 148 passed (relevance + benchmark + loop + memory + core + evolution + council). Freeze 36/36. validate_imports PASS. Reproducibility equal. Precision/F1 still FAIL vs provisional floors; recall 1.0 protected.

```text
python3 -B scripts/freeze_lane_a.py
# result: Lane-A integrity OK (36 files pinned)  exit 0

/tmp/ahos-test-venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_retrieval_relevance.py \
  tests/test_cognitive_benchmark.py \
  tests/test_cognitive_loop.py \
  tests/test_cognitive_memory.py \
  tests/test_cognitive_core.py \
  tests/test_self_evolution_engine.py \
  tests/test_multi_mind_council_anti_echo.py \
  tests/test_evolution_validate.py \
  tests/test_cognitive_panel.py
# result: 148 passed  exit 0

/tmp/ahos-test-venv/bin/python scripts/validate_imports.py
# result: VALIDATION PASSED (after rm -rf .pytest_cache; restore reports/*.json side effects)
```

## P4.1 (cognitive benchmark)

**Base SHA:** `6862c6fc20050622f6125853671f885b0e36b16a`  
**Implementation commit:** `525443d9ed182d4f464ce260ee4d8b7a4bfffab5`  
See `P4_1_COGNITIVE_BENCHMARK_REPORT.md` and `p4_1_cognitive_benchmark_latest.json`. Targeted pytest: 61 passed (benchmark+loop+memory+core+evolution+council). Freeze 36/36. Several metrics FAIL honestly.

## P3 (cognitive loop)

**Base SHA:** `606b6f282318d48e287873aaf0f3ad4c9def4321`  
See `COGNITIVE_LOOP_IMPLEMENTATION_EVIDENCE.md` for the command log. Targeted pytest: loop + memory + cognitive core + evolution + council.

## P1 (contracts) — historical

**Base SHA:** `f273feb5875c24b9fbccdc552445d82175a6597c`  
**Implementation commit:** `aa0519a`

## Commands

```text
python3 -B scripts/freeze_lane_a.py
# result: Lane-A integrity OK (36 files pinned)  exit 0
# classification: PASS

python3 -m pytest -q -p no:cacheprovider tests/test_cognitive_core.py
# result: /usr/bin/python3: No module named pytest  exit 1
# classification: ENVIRONMENT_FAILURE (system Python; not a code failure)

python3 -m venv /tmp/ahos-test-venv
/tmp/ahos-test-venv/bin/pip install pytest pytest-timeout pyyaml
/tmp/ahos-test-venv/bin/python -m pytest -q -p no:cacheprovider tests/test_cognitive_core.py
# result: 13 passed in 0.15s  exit 0
# classification: PASS

# First validate_imports in venv without numpy/pandas:
# ARTIFACTS FAIL .pytest_cache/ (removed, not committed)
# IMPORTS FAIL ModuleNotFoundError numpy/pandas on pre-existing modules
# EVIDENCE-BOUNDARY: 31 files scanned, no forbidden-lane FAIL
# LANE-A FREEZE OK
# classification of numpy/pandas FAILs: ENVIRONMENT_FAILURE (pre-existing deps)
# classification of evidence-boundary: PASS for this change

/tmp/ahos-test-venv/bin/pip install numpy pandas
rm -rf .pytest_cache
/tmp/ahos-test-venv/bin/python scripts/validate_imports.py
# result: VALIDATION PASSED — repository wiring is clean.
# 197 modules imported; 31 evidence-surface files scanned; Lane-A OK; secrets 2977 files
# orphan WARN (pre-existing 12 modules): UNRELATED / PRE-EXISTING
# classification: PASS

/tmp/ahos-test-venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_cognitive_core.py \
  tests/test_self_evolution_engine.py \
  tests/test_multi_mind_council_anti_echo.py
# result: 21 passed in 0.28s  exit 0
# classification: PASS
```

## Interpretation

Cognitive contracts are fail-closed under TEST data. Lane A freeze unchanged. Cognitive package is on the evidence-surface import ban (no `discovery` / `paper_trading` / `telegram_ai` / `engine`). Broader pytest of the full suite was not run in this pass.

No test was converted to PASS by documentation. No fabricated intelligence metric was recorded.
