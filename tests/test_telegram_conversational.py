"""Wave-25: free-form Persian conversation layer.

These tests pin the behaviour the user asked for: talk to the bot like you talk
to ChatGPT, in Persian, and get a real answer -- while the safety laws that make
the answer trustworthy stay bolted down.

Two invariants dominate this file:
  1. No conversational path may ever mutate the ledger or emit an order.
  2. Missing data must surface as UNKNOWN with an honest explanation, never as
     silence and never as a reassuring default.
"""
from __future__ import annotations

import pytest

import telegram_ai.intent as I
from telegram_ai.service import TelegramDomainService, TOKEN_SCOPED_INTENTS
from telegram_ai.response_contract import FOOTER_MANDATED

SOL = "So11111111111111111111111111111111111111112"
CTX = {"current_token": {"address": SOL, "chain": "solana"}}


@pytest.fixture(scope="module")
def svc():
    return TelegramDomainService()


# ----------------------------------------------------------------- routing --

@pytest.mark.parametrize("text,intent", [
    ("سلام", "GREETING"),
    ("درود", "GREETING"),
    ("چطوری", "GREETING"),
    ("امروز چه خبر؟", "NEWS_DIGEST"),
    ("اخبار کریپتو رو بگو", "NEWS_DIGEST"),
    ("چی بخرم؟", "WHAT_TO_BUY"),
    ("کدوم توکن رو بخرم", "WHAT_TO_BUY"),
    ("کی وارد بشم؟", "ENTRY_TIMING"),
    ("نقدشوندگی این چطوره؟", "EXITABILITY_QUERY"),
    ("نهنگ ها چیکار میکنن؟", "WHALE_QUERY"),
    ("این وایرال شده؟", "VIRALITY_QUERY"),
    ("نظر هوش مصنوعی ها چیه؟", "COUNCIL_OPINION"),
    ("اشتباهاتت رو مرور کن", "SELF_REVIEW"),
    ("عملکرد گذشته چطور بوده؟", "SELF_REVIEW"),
    ("چه درسی گرفتی؟", "SELF_REVIEW"),
])
def test_conversational_intents_route(text, intent):
    assert I.parse(text).intent == intent


def test_existing_intents_are_not_shadowed():
    """The new rules must not steal traffic from the deterministic command layer."""
    assert I.parse("۵ میلیون تومان خریدم").intent == "BUY_LOG"
    assert I.parse("کی بفروشم؟").intent == "SELL_ADVICE_QUERY"
    assert I.parse("چند درصد سود دارم؟").intent == "PNL_QUERY"
    assert I.parse("وضعیت سیستم چطوره؟").intent == "SYSTEM_HEALTH"
    assert I.parse("بهترین فرصت های امروز").intent == "TOP_OPPORTUNITIES"


def test_leading_question_is_not_answered_as_data_query():
    """«حتماً پامپ میشه نه؟» seeks agreement. Agreeing would be the whole failure."""
    assert I.parse("حتماً پامپ میشه نه؟").intent == "UNKNOWN"
    assert I.parse("قطعا ترند میشه؟").intent == "UNKNOWN"


# -------------------------------------------------------------------- laws --

def test_all_conversational_intents_are_info_only():
    convo = {"NEWS_DIGEST", "WHAT_TO_BUY", "ENTRY_TIMING", "EXITABILITY_QUERY",
             "WHALE_QUERY", "VIRALITY_QUERY", "COUNCIL_OPINION", "GREETING",
             "SELF_REVIEW"}
    assert convo <= I.INFO_ONLY_INTENTS
    assert not (convo & I.LEDGER_MUTATING_INTENTS)


def test_ledger_mutation_remains_a_single_deterministic_intent():
    """Conversation expanded; the write surface did not."""
    assert I.LEDGER_MUTATING_INTENTS == {"BUY_LOG"}


@pytest.mark.parametrize("text", [
    "سلام", "امروز چه خبر؟", "چی بخرم؟", "راهنما",
])
def test_every_reply_carries_the_mandated_footer(svc, text):
    assert FOOTER_MANDATED in svc.handle_message(text)["text"]


@pytest.mark.parametrize("text", [
    "نقدشوندگی این چطوره؟", "نهنگ ها چیکار میکنن؟",
    "این وایرال شده؟", "نظر هوش مصنوعی ها چیه؟",
])
def test_token_scoped_replies_carry_the_footer(svc, text):
    assert FOOTER_MANDATED in svc.handle_message(text, user_context=CTX)["text"]


# ------------------------------------------------------- conversational UX --

def test_greeting_is_answered_and_advertises_capability(svc):
    r = svc.handle_message("سلام")
    assert r["intent"] == "GREETING" and r["status"] == "OK"
    # A greeting should teach the user what to ask next.
    assert "؟" in r["text"]
    # ...and must restate that this is not a trading bot.
    assert "معامله‌گر" in r["text"]


def test_token_scope_is_inherited_across_turns(svc):
    """«نهنگ‌ها چیکار می‌کنن؟» has no pointing word but clearly means *this* token."""
    for text in ("نهنگ ها چیکار میکنن؟", "نظر هوش مصنوعی ها چیه؟"):
        r = svc.handle_message(text, user_context=CTX)
        assert r["status"] == "OK", f"{text} failed to inherit session token"


def test_token_scoped_query_without_context_asks_rather_than_guesses(svc):
    r = svc.handle_message("نهنگ ها چیکار میکنن؟")
    assert r["status"] == "NEEDS_CONTEXT"
    assert "آدرس" in r["text"]


def test_inheritance_is_limited_to_token_scoped_intents():
    """A session token must not silently narrow market-wide questions."""
    assert "NEWS_DIGEST" not in TOKEN_SCOPED_INTENTS
    assert "WHAT_TO_BUY" not in TOKEN_SCOPED_INTENTS
    assert "GREETING" not in TOKEN_SCOPED_INTENTS


# ------------------------------------------------------- honest degradation --

def test_unreachable_news_feeds_are_reported_not_hidden(svc):
    """Under filtering this is the normal path -- it must be legible, not empty."""
    r = svc.handle_message("امروز چه خبر؟")
    assert r["intent"] == "NEWS_DIGEST"
    if r["status"] == "UNKNOWN":
        assert "در دسترس" in r["text"]
        # Must not let the user read "no news" as "nothing is happening".
        assert "فیلترینگ" in r["text"] or "شبکه" in r["text"]


def test_empty_database_explains_the_next_step(svc):
    r = svc.handle_message("چی بخرم؟")
    if r["status"] == "EMPTY":
        assert "single-cycle" in r["text"]


def test_missing_holder_data_is_unknown_not_safe(svc):
    """Free RPC exposes no holder list. Absence of evidence != evidence of safety."""
    r = svc.handle_message("نهنگ ها چیکار میکنن؟", user_context=CTX)
    txt = r["text"]
    if "UNKNOWN" in txt:
        assert "امن" in txt  # the reply explicitly refuses to call it safe
        assert "🟢" not in txt


def test_offline_council_falls_back_to_deterministic_engine(svc):
    """No AI reachable is a survivable state, not an outage."""
    r = svc.handle_message("نظر هوش مصنوعی ها چیه؟", user_context=CTX)
    assert r["status"] == "OK"
    v = r["council"]
    assert v.advisory_only is True
    if v.council_status in ("OFFLINE", "DETERMINISTIC_ONLY"):
        assert "موتور قطعی" in r["text"]


def test_council_reply_states_it_cannot_override_the_math(svc):
    r = svc.handle_message("نظر هوش مصنوعی ها چیه؟", user_context=CTX)
    assert "مشورتی" in r["text"]


def test_virality_reply_discloses_its_measurement_basis(svc):
    """We measure attention on-chain; the user must know social media is not scraped."""
    r = svc.handle_message("این وایرال شده؟", user_context=CTX)
    assert "شبکه‌های اجتماعی" in r["text"]


def test_exitability_reply_is_produced_for_a_session_token(svc):
    r = svc.handle_message("نقدشوندگی این چطوره؟", user_context=CTX)
    assert r["status"] == "OK"
    assert r["exitability"].verdict in ("EXITABLE", "DEGRADED", "TRAPPED", "UNKNOWN")


def test_help_covers_the_new_conversational_surface(svc):
    txt = svc.handle_message("راهنما")["text"]
    for probe in ["چه خبر", "چی بخرم", "نهنگ", "وایرال", "نقدشوندگی"]:
        assert probe in txt, f"help text never mentions {probe}"


def test_unrecognised_input_still_refuses_to_guess(svc):
    r = svc.handle_message("asdkjh qwerty")
    assert r["status"] == "UNRECOGNIZED"


def test_self_review_is_available_on_demand_and_labelled(svc):
    """The learning loop must be inspectable by the user, not a black box."""
    r = svc.handle_message("اشتباهاتت رو مرور کن")
    assert r["intent"] == "SELF_REVIEW" and r["status"] == "OK"
    # Hindsight may judge, never justify -- the label must reach the user.
    assert "OUT_OF_SAMPLE_REVIEW" in r["text"]
    assert FOOTER_MANDATED in r["text"]


def test_help_mentions_the_self_review_capability(svc):
    assert "مرور" in svc.handle_message("راهنما")["text"]
