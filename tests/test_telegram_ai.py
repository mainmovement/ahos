#!/usr/bin/env python3
"""Wave-7 Telegram AI tests — Persian intent law, AI-PAL fallback law, ledger law, alert WHY-law.
Every natural-language example mandated by the Wave-7 directive (§12 + Part XVI) is pinned here."""
import sys, json
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from telegram_ai import intent as I
from telegram_ai import positions as P
from telegram_ai import alerts as A
from telegram_ai.providers import AIPAL  # noqa: E402

EVM = "0x" + "ab" * 20
SOL = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"


# ---------------------------------------------------------- directive-mandated examples (§12)
@pytest.mark.parametrize("text,expected", [
    ("این توکن رو بررسی کن", "CHECK_TOKEN"),
    ("به نظرت شرایطش چطوره؟", "TOKEN_STATUS"),
    ("من ۵ میلیون از این خریدم", "BUY_LOG"),
    ("الان چند درصد سود دارم؟", "PNL_QUERY"),
    ("اگر شرایط خراب شد بهم خبر بده", "ALERT_SET"),
    ("چرا این توکن رو رد کردی؟", "WHY_REJECTED"),
    ("بهترین فرصت‌های امروز رو نشون بده", "TOP_OPPORTUNITIES"),
    ("فقط توکن‌هایی که ریسک امنیتی پایین دارن", "LOW_RISK_FILTER"),
    # Part XVI mandated examples
    ("من ۵ میلیون تومان این توکن خریدم", "BUY_LOG"),
    ("از این ۲ اتریوم خریدم", "BUY_LOG"),
    ("این توکن رو زیر نظر بگیر", "WATCH_TOKEN"),
    ("نصفش رو بفروشم؟", "SELL_ADVICE_QUERY"),
    ("سیو سود کنم؟", "TAKE_PROFIT_QUERY"),
    ("همه رو بفروشم؟", "SELL_ADVICE_QUERY"),
    ("الان وضعیتش چطوره؟", "TOKEN_STATUS"),
])
def test_directive_examples_parse(text, expected):
    r = I.parse(text)
    assert r.intent == expected, f"{text} -> {r.intent} (rule {r.rule_id})"
    assert r.confidence == "HIGH"


def test_amount_normalization_persian_digits():
    r = I.parse("من ۵ میلیون تومان این توکن خریدم")
    assert r.slots["amount"] == 5_000_000 and r.slots["currency"] == "IRT"
    r2 = I.parse("از این ۲ اتریوم خریدم")
    assert r2.slots["amount"] == 2.0 and r2.slots["currency"] == "ETH"
    r3 = I.parse("من ۵ میلیون از این خریدم")          # no unit -> currency honestly None
    assert r3.slots["amount"] == 5_000_000 and r3.slots["currency"] is None


def test_portions_and_alert_condition():
    assert I.parse("نصفش رو بفروشم؟").slots["portion"] == 0.5
    assert I.parse("همه رو بفروشم؟").slots["portion"] == 1.0
    assert I.parse("اگر شرایط خراب شد بهم خبر بده").slots["condition"] == "CONDITIONS_DETERIORATE"
    assert I.parse("بهترین فرصت‌های امروز رو نشون بده").slots["timeframe"] == "today"


def test_address_extraction_and_anaphora():
    r = I.parse(f"این رو بررسی کن {EVM}")
    assert r.intent == "CHECK_TOKEN" and r.slots["token"] == {"address": EVM.lower(), "chain": "evm"}
    r2 = I.parse(f"وضعیت {SOL} چطوره؟")
    assert r2.slots["token"] == {"address": SOL, "chain": "solana"}
    r3 = I.parse("این توکن رو بررسی کن")
    assert r3.needs_context is True and r3.slots.get("token") is None
    ctx = {"address": EVM.lower(), "chain": "evm"}
    r4 = I.parse("این توکن رو بررسی کن", context_token=ctx)
    assert r4.slots["token"] == ctx and r4.needs_context is False


def test_unknown_never_guessed():
    for junk in ["سلام خوبی؟", "حتماً پامپ میشه نه؟", "asdkjh qwerty", "قیمت طلا چنده"]:
        assert I.parse(junk).intent == "UNKNOWN"


def test_info_only_and_mutation_law():
    assert {"SELL_ADVICE_QUERY", "TAKE_PROFIT_QUERY"} <= I.INFO_ONLY_INTENTS
    assert I.LEDGER_MUTATING_INTENTS == {"BUY_LOG"}      # AI can never be on this path
    assert "SELL_ADVICE_QUERY" not in I.LEDGER_MUTATING_INTENTS


# ---------------------------------------------------------- AI-PAL fallback (mocked transport)
class _Resp:
    def __init__(self, body): self._b = body
    def __enter__(self): self.status = 200; return self
    def __exit__(self, *a): return False
    def read(self): return self._b


def _registry(tmp_path, keyless_ok):
    y = tmp_path / "ai.yaml"
    ok_body = json.dumps({"choices": [{"message": {"content": "OK"}}]}).encode()
    y.write_text(f"""
version: 1
capabilities:
  persian_parse: {{chain: [keyed_first, keyless_second]}}
providers:
  keyed_first:
    {{kind: openai_compatible, base_url: "https://x.example", model: m, key_env: AHOS_TEST_KEY_MISSING, timeout_sec: 1}}
  keyless_second:
    {{kind: openai_compatible, base_url: "https://y.example", model: m, key_env: null, timeout_sec: 1}}
""")
    def transport(req, timeout=None):
        if not keyless_ok:
            raise ConnectionError("blocked")
        return _Resp(ok_body)
    return y, transport


def test_aipal_fallback_to_keyless_and_degraded_mode(tmp_path):
    y, transport = _registry(tmp_path, keyless_ok=True)
    pal = AIPAL(y, transport=transport)
    env = pal.chat("persian_parse", [{"role": "user", "content": "سلام"}])
    assert env["mode"] == "AI_ASSISTED" and env["provider_id"] == "keyless_second"
    assert env["attempts"][0]["error"] == "no_key"          # keyed skipped without a key, chain continued
    y2, transport2 = _registry(tmp_path, keyless_ok=False)
    env2 = AIPAL(y2, transport=transport2).chat("persian_parse", [{"role": "user", "content": "x"}])
    assert env2["mode"] == "DETERMINISTIC_ONLY" and env2["availability"] == "DEGRADED"


# ---------------------------------------------------------- position ledger law
def test_ledger_refuses_unresolved_and_invalid(tmp_path):
    conn = P.open_ledger(tmp_path / "pos.sqlite")
    assert P.log_buy(conn, token=None, amount_value=5e6, amount_currency="IRT",
                     intent_rule="R-BUY-01", raw_text="x", now=1.0) is None
    assert P.log_buy(conn, token={"address": EVM, "chain": "evm"}, amount_value=-3,
                     amount_currency="IRT", intent_rule="R-BUY-01", raw_text="x", now=1.0) is None
    n = conn.execute("SELECT COUNT(*) c FROM position_ledger").fetchone()["c"]
    assert n == 0                                          # nothing junk ever stored
    conn.close()


def test_ledger_append_and_lookup(tmp_path):
    conn = P.open_ledger(tmp_path / "pos.sqlite")
    eid = P.log_buy(conn, token={"address": EVM, "chain": "evm"}, amount_value=5_000_000,
                    amount_currency="IRT", intent_rule="R-BUY-01",
                    raw_text=I.normalize("من ۵ میلیون تومان این توکن خریدم"), now=1_756_000_000.0)
    assert eid
    rows = P.positions_for_token(conn, "evm", EVM)
    assert len(rows) == 1 and rows[0]["amount_value"] == 5_000_000
    assert rows[0]["created_utc"].startswith("2025")       # deterministic ts
    assert not hasattr(P, "update_entry") and not hasattr(P, "delete_entry")  # append-only by construction
    conn.close()


# ---------------------------------------------------------- alert WHY-law
def test_alert_requires_why_and_evidence():
    with pytest.raises(ValueError):
        A.build("OPPORTUNITY", "ABC", reasons=[], evidence=["obs:1"])
    with pytest.raises(ValueError):
        A.build("OPPORTUNITY", "ABC", reasons=["دلیل"], evidence=[])
    with pytest.raises(ValueError):
        A.build("NOT_A_CLASS", "ABC", reasons=["x"], evidence=["y"])


def test_alert_render_footer_and_body():
    a = A.build("RISK_INCREASING", "ABC", reasons=["افت نقدشوندگی ۴۰٪"],
                evidence=["obs:abc123", "probe:PRB-20260811-003"], severity="HIGH",
                data_state="STALE")
    txt = A.render_fa(a)
    assert "🟠" in txt and "افزایش ریسک" in txt and "افت نقدشوندگی ۴۰٪" in txt
    assert "obs:abc123" in txt and A.FOOTER in txt          # decisional -> footer mandated
    assert "STALE" in txt                                    # staleness never hidden
    b = A.build("ABNORMAL_MOVEMENT", "XYZ", reasons=["شتاب حجم ×۳"],
                evidence=["fv:volume_acceleration=3.1"], data_state="LIVE")
    assert A.FOOTER not in A.render_fa(b)                    # non-decisional -> no footer
