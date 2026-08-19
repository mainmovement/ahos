# AHOS canonicalization deletion / relocation manifest

Created before cleanup on 2026-08-19 and updated after execution. “Relocated”
means Git preserved the content under a classified path. No broad recursive
source/document deletion was authorized or performed.

| Original path | Executed action | Reason / uniqueness proof | Replacement / preservation path |
|---|---|---|---|
| `config/paths.yaml` | Removed tracked generated file | Machine-specific `/home/user/ahos`; values are deterministically regenerated and contained no historical observations | `config/paths.example.yaml`; local `config/paths.yaml` is ignored |
| `01a00f79-b48c-7afb-87e7-3850b1bc66f5 (1).md` | Relocated, content preserved | 90 patch sections inspected; SHA-256 `fc5a1e74a8e8cf6818f3bfe58c9a3f39900a04c6d9014b00203e226322b07877` | `docs/history/source-patches/01a00f79-b48c-7afb-87e7-3850b1bc66f5.patch` |
| `01a01560-4c5e-7430-a0dd-8558799869d4.md` | Relocated, content preserved | 41 sections inspected; SHA-256 `1c735682932b962a1aa061a62580f1468398b8ff83a55096703fd7d971f20f07` | `docs/history/source-patches/01a01560-4c5e-7430-a0dd-8558799869d4.patch` |
| `01a015c9-a9ed-7bac-9220-3ad2d8321825.md` | Relocated, content preserved | 45 sections inspected; SHA-256 `4900d7c08326e18f7d419fc90bbb3cbfcb172ea3e0abe181fa1e828ff1eed3c2` | `docs/history/source-patches/01a015c9-a9ed-7bac-9220-3ad2d8321825.patch` |
| 25 root `ahos_snap_w*_after.txt` files | Relocated individually, filenames/content preserved | Unique phase file-list evidence; aggregate digest of the sorted SHA-256 listing is `235ad474acd86dc146bb2653de9b311bcc91c22c78150d4a3e254c7f35e32c46` | `docs/history/snapshots/` |
| `reports/reliability_matrix_20260818T164613Z.json` | Removed exact duplicate alias | SHA-256 `c6a61cc5970152e66a45e3aa5531b2819bc11bce0f305cf8b5d171a7932b4c4e`, byte-identical to retained file | `reports/reliability_matrix.json` |
| Generated `__pycache__/`, `.pytest_cache/`, `.venv/`, local `data/` | Kept out of Git; no historical data deleted | Reproducible machine state; no historical SQLite existed at audit start | `.gitignore`, schemas, bootstrap, and dependency files |

No additional unique source, dataset, research report, or historical document was
deleted. Older readiness reports remain present but are classified as historical
in `docs/DOCUMENT_CLASSIFICATION.md`.
