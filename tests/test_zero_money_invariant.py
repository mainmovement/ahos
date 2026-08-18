"""The load-bearing safety invariant: this system CANNOT spend money.

Everything else in AHOS is a judgement call that reasonable engineers could
argue about. This is not. The user runs it on a personal laptop, single-user,
under sanctions, with no budget -- and the whole design rests on the promise
that no code path can sign a transaction or move funds.

Promises decay. Features get added, an LLM gets asked to "make it trade", a
dependency quietly ships a wallet helper. So the promise is enforced here as a
repo-wide scan rather than as documentation, and it fails the build the moment
a signing primitive appears anywhere in the source tree.

This is deliberately the strictest test in the suite.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Directories that hold executable product code. Tests are scanned too (a
# "temporary" signing helper in a test file is still a signing helper), but
# this file is excluded because it necessarily names the forbidden patterns.
SCANNED_DIRS = ("architecture", "telegram_ai", "paper_trading", "discovery",
                "engine", "scripts", "config", "strategy_lab")

EXCLUDED_FILES = {"test_zero_money_invariant.py", "security.py", "hygiene.py"}

# Primitives that can move real funds. Matched case-insensitively against
# source text with comments and docstrings stripped, so that a comment saying
# "we never sign transactions" does not trip the alarm.
FORBIDDEN_PATTERNS = [
    (r"\bKeypair\b", "Solana/EVM keypair construction"),
    (r"\bfrom_secret_key\b", "loading a secret key"),
    (r"\bfrom_private_key\b", "loading a private key"),
    (r"\bsign_transaction\b", "transaction signing"),
    (r"\bsignTransaction\b", "transaction signing"),
    (r"\bsend_transaction\b", "transaction broadcast"),
    (r"\bsendTransaction\b", "transaction broadcast"),
    (r"\bsend_raw_transaction\b", "raw transaction broadcast"),
    (r"\bsendRawTransaction\b", "raw transaction broadcast"),
    (r"\beth_sendTransaction\b", "EVM transaction broadcast"),
    (r"\beth_signTransaction\b", "EVM transaction signing"),
    (r"\bpersonal_sign\b", "wallet signing"),
    (r"\bcreate_order\b", "exchange order placement"),
    (r"\bplace_order\b", "exchange order placement"),
    (r"\bcreate_market_buy\b", "exchange market order"),
    (r"\bcreate_market_sell\b", "exchange market order"),
]

# Wallet / exchange / trading SDKs. Importing one is not proof of intent, but
# it is exactly the dependency that would make real execution one line away.
FORBIDDEN_IMPORTS = {
    "ccxt", "web3", "eth_account", "solana", "solders", "anchorpy",
    "solana_agent_kit", "binance", "python-binance", "krakenex",
    "metaplex", "raydium",
}


def _python_files():
    for d in SCANNED_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if p.name not in EXCLUDED_FILES:
                yield p
    for p in ROOT.glob("*.py"):
        if p.name not in EXCLUDED_FILES:
            yield p
    for p in (ROOT / "tests").glob("*.py"):
        if p.name not in EXCLUDED_FILES:
            yield p


def _strip_comments_and_docstrings(src: str) -> str:
    """Remove comments and string literals so prose cannot trigger a match."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return src
    spans: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.end_lineno is not None:
                spans.append((node.lineno, node.end_lineno))
    lines = src.splitlines()
    drop = set()
    for a, b in spans:
        drop.update(range(a - 1, b))
    kept = [("" if i in drop else re.sub(r"#.*$", "", ln))
            for i, ln in enumerate(lines)]
    return "\n".join(kept)


@pytest.mark.parametrize("pattern,description", FORBIDDEN_PATTERNS)
def test_no_transaction_signing_primitive_exists_anywhere(pattern, description):
    rx = re.compile(pattern, re.IGNORECASE)
    offenders = []
    for path in _python_files():
        code = _strip_comments_and_docstrings(
            path.read_text(encoding="utf-8", errors="ignore"))
        for i, line in enumerate(code.splitlines(), 1):
            if rx.search(line):
                offenders.append(f"{path.relative_to(ROOT)}:{i}")
    assert not offenders, (
        f"ZERO-MONEY INVARIANT BROKEN — {description} found at: {offenders}. "
        f"AHOS must never be able to move real funds.")


def test_no_wallet_or_exchange_sdk_is_imported():
    offenders = []
    for path in _python_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module]
            for m in mods:
                if m.split(".")[0].lower() in FORBIDDEN_IMPORTS:
                    offenders.append(f"{path.relative_to(ROOT)}: import {m}")
    assert not offenders, (
        f"ZERO-MONEY INVARIANT AT RISK — trading/wallet SDK imported: {offenders}")


def test_requirements_declare_no_trading_sdk():
    """The dependency list is the other way real execution could arrive."""
    for name in ("requirements.txt", "requirements-optional.txt"):
        f = ROOT / name
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith(("#", "-r")):
                continue
            pkg = re.split(r"[<>=\[;!]", line)[0].strip().lower()
            assert pkg not in FORBIDDEN_IMPORTS, (
                f"{name} declares trading/wallet SDK '{pkg}'")


def test_ledger_mutation_stays_confined_to_one_intent():
    """Only an explicit human report of a purchase may touch the ledger.

    No AI, council, panel or advisory path may ever be on a write path.
    """
    import telegram_ai.intent as I
    assert I.LEDGER_MUTATING_INTENTS == {"BUY_LOG"}


def test_paper_trading_declares_itself_paper_only():
    from architecture.runtime import observability_snapshot as obs
    src = Path(obs.__file__).read_text(encoding="utf-8")
    assert "PAPER" in src.upper()


def test_advisor_never_emits_an_execution_action():
    """The advice vocabulary is closed and contains no executable verb."""
    from architecture.decision.advisor import ACTIONS
    assert set(ACTIONS) == {"ENTER", "WAIT", "AVOID", "HOLD", "REDUCE", "EXIT"}
    for forbidden in ("BUY", "SELL", "SWAP", "EXECUTE", "TRADE", "ORDER"):
        assert forbidden not in ACTIONS
