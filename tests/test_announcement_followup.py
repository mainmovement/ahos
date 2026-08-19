"""The bot announces a token; the user replies «خریدم». That must work.

Why this file exists
--------------------
Three defects sat on the single most likely path through the product -- the
bot pushes an alert, the user acts on it, the user tells the bot.

1. The announcement did not repeat the contract address next to the verdict.
   Symbols are not unique; anyone can deploy a second token called PEPE. The
   address was buried further up the analysis card.

2. Replying «۵ میلیون تومان خریدم» failed with "token unknown". The intent
   parser only consulted context when the sentence contained «این», «اون» or a
   trailing «ـش», and the natural reply has none of them. Worse, the context
   store was written only by *user-initiated* questions, so a token the
   pipeline announced on its own was never recorded anywhere at all, and the
   in-memory dict was lost on restart -- guaranteed for a laptop that sleeps.

3. Messages go out with parse_mode="HTML" while carrying Markdown `**bold**`,
   and token names were interpolated unescaped. A token named `Bull & Bear`
   makes Telegram reject the whole send with 400 "can't parse entities", and
   the pipeline's send guard swallows the exception -- the alert silently
   never arrives. Token names are attacker-controlled by construction.

The through-line: every one of these passed its own unit tests. They only
appear when you follow one user through one realistic sequence.
"""
from __future__ import annotations

import re
import time

import pytest

from telegram_ai.announced import (
    record_announcement, last_announced, recent_announcements, context_token,
    MAX_REMEMBERED, STALE_AFTER_SEC)
from telegram_ai.intent import parse
from telegram_ai.response_contract import format_opportunity_response, esc

SOL = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
SOL2 = "So11111111111111111111111111111111111111112"
NOW = time.time()


@pytest.fixture
def store(tmp_path):
    return tmp_path / "announced.json"


# ------------------------------------------------------- the memory itself --

def test_an_announcement_survives_a_restart(store):
    """In-memory context is empty exactly when it is needed: the pipeline may
    announce at 3am and the user answer at 9am after a reboot."""
    record_announcement(SOL, "solana", "CLEAN", "Clean", now=NOW, path=store)
    assert last_announced(now=NOW, path=store)["address"] == SOL
    # A fresh process reads the same file; nothing is cached in memory.
    assert context_token(now=NOW, path=store) == {"address": SOL, "chain": "solana"}


def test_a_stale_announcement_is_not_a_referent(store):
    """Resolving a two-day-old alert would log a position against a token the
    user never meant -- worse than admitting we don't know."""
    record_announcement(SOL, "solana", "OLD", "Old",
                        now=NOW - STALE_AFTER_SEC - 60, path=store)
    assert last_announced(now=NOW, path=store) is None
    assert context_token(now=NOW, path=store) is None


def test_the_newest_announcement_wins(store):
    record_announcement(SOL, "solana", "FIRST", "First", now=NOW - 7200, path=store)
    record_announcement(SOL2, "solana", "SECOND", "Second", now=NOW - 60, path=store)
    assert last_announced(now=NOW, path=store)["symbol"] == "SECOND"


def test_re_announcing_a_token_does_not_duplicate_it(store):
    record_announcement(SOL, "solana", "CLEAN", "Clean", now=NOW - 3600, path=store)
    record_announcement(SOL, "solana", "CLEAN", "Clean", now=NOW, path=store)
    assert len(recent_announcements(now=NOW, path=store)) == 1


def test_history_is_bounded(store):
    for i in range(MAX_REMEMBERED + 4):
        record_announcement(f"addr{i}", "solana", f"T{i}", "", now=NOW - i, path=store)
    assert len(recent_announcements(limit=99, now=NOW, path=store)) == MAX_REMEMBERED


def test_a_corrupt_store_does_not_crash_the_bot(store):
    store.write_text("{ this is not json", encoding="utf-8")
    assert last_announced(now=NOW, path=store) is None
    record_announcement(SOL, "solana", "CLEAN", "", now=NOW, path=store)
    assert last_announced(now=NOW, path=store)["address"] == SOL


def test_a_missing_store_is_not_an_error(tmp_path):
    assert last_announced(now=NOW, path=tmp_path / "nope.json") is None


# ------------------------------------------------- resolving the follow-up --

@pytest.mark.parametrize("text", [
    "۵ میلیون تومان خریدم",
    "۲ میلیون خریدم",
    "100 دلار خریدم",
])
def test_bought_it_resolves_without_a_pronoun(text):
    """The natural reply to an alert contains no «این»/«اون»/«ـش»."""
    result = parse(text, context_token={"address": SOL, "chain": "solana"})
    assert result.intent == "BUY_LOG"
    assert result.slots.get("token", {}).get("address") == SOL, \
        "the commonest reply in the product still cannot resolve its token"
    assert result.token_inferred is True


def test_an_explicit_address_beats_the_context():
    """If the user names a token, that is the token -- never the remembered one."""
    result = parse(f"۵ میلیون تومان از {SOL2} خریدم",
                   context_token={"address": SOL, "chain": "solana"})
    assert result.slots["token"]["address"] == SOL2
    assert result.token_inferred is False


def test_nothing_is_invented_when_there_is_no_context():
    result = parse("۵ میلیون تومان خریدم", context_token=None)
    assert result.slots.get("token") is None
    assert result.token_inferred is False


@pytest.mark.parametrize("text,intent", [
    ("بهترین فرصت‌های امروز", "TOP_OPPORTUNITIES"),
    ("امروز چه خبر از کریپتو", "NEWS_DIGEST"),
    ("چی بخرم", "WHAT_TO_BUY"),
])
def test_discovery_intents_never_borrow_a_subject(text, intent):
    """Guessing a subject for "what should I buy?" would be fabrication, not
    resolution. The fallback is restricted to position-centric intents."""
    result = parse(text, context_token={"address": SOL, "chain": "solana"})
    assert result.intent == intent
    assert result.slots.get("token") is None, \
        f"{intent} silently attached a token the user never mentioned"


@pytest.mark.parametrize("text", [
    "کی بفروشم", "چقدر سود دارم", "الان وضعیتش چطوره",
])
def test_position_intents_do_resolve_from_context(text):
    result = parse(text, context_token={"address": SOL, "chain": "solana"})
    assert result.slots.get("token", {}).get("address") == SOL


# ----------------------------------------------------- HTML render safety --

def _telegram_would_reject(text: str) -> list[str]:
    """Telegram returns 400 on an unescaped `&` or unbalanced tags."""
    problems = []
    if re.search(r"&(?!amp;|lt;|gt;|quot;|#\d+;)", text):
        problems.append("unescaped &")
    from collections import Counter
    opened = Counter(re.findall(r"<([a-zA-Z-]+)[^>/]*>", text))
    closed = Counter(re.findall(r"</([a-zA-Z-]+)>", text))
    for tag in set(opened) | set(closed):
        if opened[tag] != closed[tag]:
            problems.append(f"unbalanced <{tag}>")
    return problems


def _card(name: str, symbol: str = "PUMP") -> str:
    from architecture.providers.contracts import (
        NormalizedTokenCandidate, MarketMetrics, SecuritySignals)
    from architecture.scoring.engine import OpportunityScorer
    cand = NormalizedTokenCandidate(
        chain="solana", address=SOL, symbol=symbol, name=name,
        metrics=MarketMetrics(
            price_usd=1.0, liquidity_usd=200_000.0, volume_1h=120_000.0,
            volume_24h=1_500_000.0, txns_1h_buys=1_400, txns_1h_sells=300,
            price_change_1h=45.0, price_change_24h=90.0, fdv_usd=3_000_000.0),
        security=SecuritySignals(
            is_honeypot=False, sell_tax_pct=1.0, buy_tax_pct=1.0,
            liquidity_locked_pct=95.0, has_mint_authority=False,
            has_freeze_authority=False, is_contract_verified=True,
            is_ownership_renounced=True, top10_holder_concentration_pct=12.0,
            deployer_past_rug_count=0),
        source_provider="dexscreener", retrieved_ts=NOW)
    cand.identify_unknowns()
    return format_opportunity_response(OpportunityScorer().evaluate(cand, now=NOW), cand)


@pytest.mark.parametrize("name", [
    "Bull & Bear",          # the ampersand that broke the send outright
    "<b>Safe</b> Token",    # injected markup
    "Moon <3",              # stray angle bracket
    "Tom & Jerry & Co",     # several
    'Say "hi"',
])
def test_hostile_token_names_still_produce_a_sendable_message(name):
    """Whoever deploys a token picks its name. A name must never be able to
    stop the alert from arriving."""
    problems = _telegram_would_reject(_card(name))
    assert not problems, f"name {name!r} breaks the send: {problems}"


def test_the_address_survives_a_hostile_name():
    """A stray `<` used to be able to swallow the rest of the card."""
    assert SOL in _card("Evil <b Token")


def test_esc_leaves_ordinary_persian_text_alone():
    assert esc("نقدینگی بالا") == "نقدینگی بالا"
    assert esc("Bull & Bear") == "Bull &amp; Bear"


def test_no_markdown_bold_is_emitted_under_html_parse_mode():
    """`**bold**` renders as literal asterisks in HTML mode."""
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "architecture" / "pipeline"
           / "orchestrator.py").read_text(encoding="utf-8")
    for line in src.splitlines():
        if line.lstrip().startswith("#"):
            continue
        assert "**" not in line, f"Markdown bold sent under HTML mode: {line.strip()}"


# ================================================================ end-to-end ==
#
# The tests above prove each piece. The bug was that the pieces were never
# connected, so the only convincing evidence is the whole sequence: the
# pipeline announces, the process restarts, the user replies, a position is
# recorded against the right token.

def test_the_full_alert_then_bought_it_sequence(tmp_path, monkeypatch):
    monkeypatch.setenv("AHOS_DATA_DIR", str(tmp_path))
    import importlib
    import config.paths
    importlib.reload(config.paths)
    import telegram_ai.announced as announced
    importlib.reload(announced)

    from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
    from architecture.providers.contracts import (
        NormalizedTokenCandidate, MarketMetrics, SecuritySignals)
    from architecture.collector.engine import CollectedObservationRecord
    from telegram_ai.adapter import MockTelegramAdapter

    cand = NormalizedTokenCandidate(
        chain="solana", address=SOL, symbol="CLEAN", name="Clean Token",
        metrics=MarketMetrics(
            price_usd=1.0, liquidity_usd=200_000.0, volume_1h=120_000.0,
            volume_24h=1_500_000.0, txns_1h_buys=1_400, txns_1h_sells=300,
            price_change_1h=45.0, price_change_24h=90.0, fdv_usd=3_000_000.0),
        security=SecuritySignals(
            is_honeypot=False, sell_tax_pct=1.0, buy_tax_pct=1.0,
            liquidity_locked_pct=95.0, has_mint_authority=False,
            has_freeze_authority=False, is_contract_verified=True,
            is_ownership_renounced=True, top10_holder_concentration_pct=12.0,
            deployer_past_rug_count=0),
        source_provider="dexscreener", retrieved_ts=NOW)
    cand.identify_unknowns()

    class _Collector:
        def collect_candidates(self, chain="solana", limit=10, now=None):
            return [CollectedObservationRecord(
                obs_id="o1", token_address=SOL, chain="solana", symbol="CLEAN",
                name="Clean Token", provider_source="dexscreener",
                retrieved_ts=NOW, raw_evidence_hash="0" * 64,
                confidence_level="HIGH", metrics=dict(vars(cand.metrics)),
                security=dict(vars(cand.security)), unknown_fields=[])]

    # 1. the autonomous cycle announces
    adapter = MockTelegramAdapter()
    OpportunityPipelineOrchestrator(
        collector=_Collector(), telegram_adapter=adapter,
        target_chat_id="1").run_pipeline(now=NOW)

    alert = next((m["text"] for m in adapter.sent_messages
                  if "فرصت ویژه" in m["text"]), None)
    assert alert is not None, "nothing was announced"
    assert SOL in alert, "the announcement omitted the contract address"
    assert "آدرس قرارداد" in alert, \
        "the address was not labelled for copying into a trade"

    # 2. the laptop restarts: a brand-new runner with empty memory
    from telegram_ai.bot import TelegramBotRunner
    importlib.reload(importlib.import_module("telegram_ai.bot"))
    from telegram_ai.bot import TelegramBotRunner as FreshRunner

    adapter2 = MockTelegramAdapter()
    bot = FreshRunner(adapter=adapter2)
    assert bot.user_contexts == {}, "fixture is not simulating a cold start"

    # 3. the user replies to the alert
    result = bot.process_update(
        adapter2.inject_update(chat_id="1", text="۵ میلیون تومان خریدم"))

    assert result.get("intent") == "BUY_LOG"
    reply = adapter2.sent_messages[-1]["text"]
    assert "ثبت" in reply and "ناموفق" not in reply, \
        f"replying to an alert still fails: {reply}"
    assert SOL in reply, "recorded a position without confirming which token"
    assert "آخرین اعلام" in reply, \
        "the token was inferred silently; a wrong inference must be visible"


def test_market_overview_escapes_an_attacker_controlled_symbol():
    from types import SimpleNamespace
    from telegram_ai.response_contract import format_market_overview
    hostile = SimpleNamespace(
        token_symbol="Bull & <Fake>", opportunity_score=88.0, risk_level="LOW")
    text = format_market_overview(1, 0, 0, [hostile])
    assert "Bull &amp; &lt;Fake&gt;" in text
    assert "Bull & <Fake>" not in text
