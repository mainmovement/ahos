#!/usr/bin/env python3
"""Phase 4 — TS canonical identity is byte-parity with the Python authority.

Runs the real TypeScript ``canonical_identity.ts`` under Node (type-stripping)
and compares its output to ``architecture.canonical.identity.canonical_token_id``
for a matrix of fixtures. There must be exactly ONE identity representation.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.canonical.identity import canonical_token_id

FIXTURES = [
    ("ethereum", "0xABCdef0000000000000000000000000000001234"),  # EVM casing
    ("ethereum", "0xabcdef0000000000000000000000000000001234"),  # lower
    ("eth", "0xABCdef0000000000000000000000000000001234"),        # chain alias
    ("bnb", "0xDeAd000000000000000000000000000000009999"),        # alias → bsc
    ("solana", "So11111111111111111111111111111111111111112"),    # case preserved
    ("solana", "so11111111111111111111111111111111111111112"),    # different case → different id
    ("robinhood", "SomeToken123"),
    ("not-a-chain", "0xabc"),                                      # fail-closed
    ("ethereum", ""),                                              # fail-closed
    ("", "0xabc"),                                                 # fail-closed
]

_RUNNER = """
import { canonicalTokenId } from "%s/canonical_identity.ts";
const fx = JSON.parse(process.argv[2]);
console.log(JSON.stringify(fx.map(([c, a]) => canonicalTokenId(c, a))));
"""


def _node_available() -> bool:
    return shutil.which("node") is not None


@pytest.mark.skipif(not _node_available(), reason="node not available")
def test_ts_identity_matches_python(tmp_path):
    runner = tmp_path / "run.mjs"
    runner.write_text(_RUNNER % ROOT.as_posix(), encoding="utf-8")
    payload = json.dumps(FIXTURES)
    proc = subprocess.run(
        ["node", "--experimental-strip-types", str(runner), payload],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, f"node failed: {proc.stderr}"
    ts_ids = json.loads(proc.stdout.strip().splitlines()[-1])

    py_ids = [canonical_token_id(c, a) for c, a in FIXTURES]
    # Normalize JS null → Python None for comparison.
    ts_ids = [None if x is None else x for x in ts_ids]

    assert ts_ids == py_ids, f"identity divergence:\nTS={ts_ids}\nPY={py_ids}"
    # sanity: valid fixtures produced 32-hex ids; invalid produced None
    assert py_ids[0] == py_ids[1] == py_ids[2]  # casing + alias converge
    assert py_ids[4] != py_ids[5]               # solana case-sensitive
    assert py_ids[7] is None and py_ids[8] is None and py_ids[9] is None
