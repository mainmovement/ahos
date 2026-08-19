#!/usr/bin/env python3
"""Executable opinions for the 19 team members who previously had none.

Wave-31. `config/council_teams.yaml` organises the 100-registry into seven
operational teams, each answering one question that must be settled before
money moves. Nineteen of those members had a named duty and no way to perform
it -- which is the same decoration this project has been removing all along,
just with a job title attached.

Each function below reads real measured fields and applies one published
principle from the member's own card in `lenses_teams.py`. Where the evidence
is absent the lens ABSTAINS: silence lowers panel coverage honestly, while a
manufactured vote would corrupt the verdict it feeds.

Signature contract, identical to the pilot lenses:
    (candidate, ctx) -> LensOpinion
`ctx` carries score_report, exitability, virality, whale, narrative, now.
"""
from __future__ import annotations

from .panel import LensOpinion, _op, _f, _m, _s, register_lenses as _register
# The sizing lens uses the same pre-registered pay-off geometry as the paper
# exit rules. Importing the immutable policy avoids restoring the older,
# competing evolution/calibration implementation found in a source patch.
from paper_trading.exit_rules import EXIT_V1

TAKE_PROFIT_PCT = float(EXIT_V1["take_profit_pct"])
STOP_LOSS_PCT = float(EXIT_V1["stop_loss_pct"])


# ============================================================== SURVIVAL ====

def lens_poincare_sensitivity(cand, ctx) -> LensOpinion:
    """Sensitive dependence: does the verdict rest on a knife edge?

    A candidate whose liquidity sits a few dollars above the minimum, or whose
    realizable fraction is a hair above the trap threshold, is not "passing" in
    any meaningful sense -- it is one small measurement error from failing. The
    lens measures the margin, not the pass.
    """
    liq = _m(cand, "liquidity_usd")
    ex = ctx.get("exitability")
    frac = _f(getattr(ex, "realizable_fraction", None)) if ex is not None else None
    if liq is None and frac is None:
        return _op("LENS-POINCARE", "CHAOS-01", "ABSTAIN",
                   "بدون نقدینگی و کسر قابل بازیافت، حساسیت قابل سنجش نیست")

    fragile: list[str] = []
    # Margins are expressed relative to the thresholds other lenses enforce.
    if liq is not None and 10_000 <= liq < 12_000:
        fragile.append(f"نقدینگی ${liq:,.0f} تنها اندکی بالای کف ۱۰ هزار دلار")
    if frac is not None and 0.75 <= frac < 0.80:
        fragile.append(f"کسر قابل بازیافت {frac:.0%} درست روی مرز")
    tax = _f(_s(cand, "sell_tax_pct"))
    if tax is not None and 20.0 <= tax < 25.0:
        fragile.append(f"مالیات فروش {tax:.0f}٪ نزدیک آستانه وتوی ۲۵٪")
    top10 = _f(_s(cand, "top10_holder_concentration_pct"))
    if top10 is not None and 45.0 <= top10 < 50.0:
        fragile.append(f"تمرکز مالکیت {top10:.0f}٪ درست زیر آستانه")

    if len(fragile) >= 2:
        return _op("LENS-POINCARE", "CHAOS-01", "VETO",
                   "چند شاخص هم‌زمان روی لبه تصمیم‌اند — کوچک‌ترین خطای اندازه‌گیری "
                   "حکم را برمی‌گرداند: " + "، ".join(fragile[:2]),
                   metric=float(len(fragile)), severity=3)
    if fragile:
        return _op("LENS-POINCARE", "CHAOS-01", "CAUTION",
                   "حاشیه اطمینان باریک است: " + fragile[0],
                   metric=1.0, severity=2)
    return _op("LENS-POINCARE", "CHAOS-01", "APPROVE",
               "شاخص‌ها با فاصله روشن از آستانه‌ها قرار دارند")


def lens_box_model_validity(cand, ctx) -> LensOpinion:
    """All models are wrong: state where ours stops being useful.

    The opportunity score was built for tokens with observable depth and trade
    flow. Applied to a pair with almost no liquidity or almost no trades it
    still returns a confident-looking number, and that number is the model
    operating outside the range it was ever meaningful in.
    """
    report = ctx.get("score_report")
    score = _f(getattr(report, "opportunity_score", None)) if report else None
    liq = _m(cand, "liquidity_usd")
    buys = _m(cand, "txns_1h_buys")
    sells = _m(cand, "txns_1h_sells")
    trades = (buys or 0) + (sells or 0) if (buys is not None or sells is not None) else None

    if score is None:
        return _op("LENS-BOX", "BOX-01", "ABSTAIN",
                   "بدون امتیاز، اعتبار مدل قابل ارزیابی نیست")
    if liq is None and trades is None:
        return _op("LENS-BOX", "BOX-01", "ABSTAIN",
                   "بدون نقدینگی و تعداد معاملات، دامنه اعتبار مدل نامعلوم است")

    out_of_range: list[str] = []
    if liq is not None and liq < 5_000:
        out_of_range.append(f"نقدینگی ${liq:,.0f}")
    if trades is not None and trades < 20:
        out_of_range.append(f"{trades:.0f} معامله در ساعت")

    if out_of_range and score >= 60.0:
        # The dangerous combination: a high score produced from inputs the
        # model was never calibrated on. The score is not wrong so much as
        # meaningless, and a meaningless 85 reads exactly like a real one.
        return _op("LENS-BOX", "BOX-01", "VETO",
                   f"امتیاز {score:.0f} خارج از دامنه اعتبار مدل تولید شده است ("
                   + "، ".join(out_of_range) + ") — عدد بی‌معناست، نه خوش‌بینانه",
                   metric=score, severity=3)
    if out_of_range:
        return _op("LENS-BOX", "BOX-01", "CAUTION",
                   "ورودی‌ها خارج از دامنه کالibration مدل‌اند: "
                   + "، ".join(out_of_range), severity=2)
    return _op("LENS-BOX", "BOX-01", "APPROVE",
               "ورودی‌ها در دامنه‌ای هستند که مدل برای آن ساخته شده است",
               metric=score)


# ============================================================= ADVERSARY ====

def lens_anderson_incentives(cand, ctx) -> LensOpinion:
    """Who profits from this exact structure?

    Anderson's contribution was noticing that security fails where the party
    who can prevent a loss is not the party who suffers it. A token where the
    deployer keeps every lever and the holders carry every risk is that
    misalignment in its purest form -- regardless of whether the code is clean.
    """
    levers = []
    if _s(cand, "has_mint_authority") is True:
        levers.append("ضرب نامحدود")
    if _s(cand, "has_freeze_authority") is True:
        levers.append("انجماد دارایی")
    if _s(cand, "is_ownership_renounced") is False:
        levers.append("مالکیت قرارداد")
    locked = _f(_s(cand, "liquidity_locked_pct"))
    burned = _f(_s(cand, "liquidity_burned_pct"))
    secured = max([v for v in (locked, burned) if v is not None], default=None)
    liq = _m(cand, "liquidity_usd")

    probes = [_s(cand, "has_mint_authority"), _s(cand, "has_freeze_authority"),
              _s(cand, "is_ownership_renounced"), secured]
    if all(p is None for p in probes):
        return _op("LENS-ANDERSON", "ECON-SEC-01", "ABSTAIN",
                   "بدون داده اختیارات و قفل، توازن انگیزه‌ها قابل تحلیل نیست")

    # Quantify the asymmetry: what the deployer can take vs what they risk.
    extractable = None
    if liq is not None and secured is not None:
        extractable = liq * (1.0 - min(secured, 100.0) / 100.0)

    if levers and extractable is not None and extractable > 20_000:
        return _op("LENS-ANDERSON", "ECON-SEC-01", "VETO",
                   f"سازنده هم اختیار ({'، '.join(levers[:2])}) دارد و هم "
                   f"${extractable:,.0f} قابل برداشت — کسی که می‌تواند ضرر را "
                   f"جلوگیری کند، متحمل آن نمی‌شود",
                   metric=extractable, severity=3)
    if len(levers) >= 2:
        return _op("LENS-ANDERSON", "ECON-SEC-01", "VETO",
                   "چند اهرم کنترلی نزد سازنده باقی مانده: " + "، ".join(levers),
                   metric=float(len(levers)), severity=3)
    if levers:
        return _op("LENS-ANDERSON", "ECON-SEC-01", "CAUTION",
                   "ناترازی انگیزه: " + "، ".join(levers), severity=2)
    return _op("LENS-ANDERSON", "ECON-SEC-01", "APPROVE",
               "سازنده اهرمی برای انتقال ضرر به دارندگان ندارد")


def lens_krebs_deployer_history(cand, ctx) -> LensOpinion:
    """Prior offence is the strongest single predictor available.

    The honest half of this lens is its blind spot: a clean record on a fresh
    wallet is not evidence of good faith, it is absence of evidence. The lens
    says so explicitly rather than converting silence into approval.
    """
    rugs = _f(_s(cand, "deployer_past_rug_count"))
    deployer = _s(cand, "deployer_address")

    if rugs is None:
        if deployer is None:
            return _op("LENS-KREBS", "KREBS-01", "ABSTAIN",
                       "آدرس سازنده ثبت نشده — سابقه قابل استعلام نیست")
        return _op("LENS-KREBS", "KREBS-01", "ABSTAIN",
                   "سابقه سازنده استعلام نشده است — نبودِ سابقه، پاکی نیست")
    if rugs >= 2:
        return _op("LENS-KREBS", "KREBS-01", "VETO",
                   f"سازنده {rugs:.0f} بار پیش‌تر نقدینگی را برداشته است — "
                   f"زیرساخت کلاهبرداری بازاستفاده می‌شود",
                   metric=rugs, severity=3)
    if rugs == 1:
        return _op("LENS-KREBS", "KREBS-01", "VETO",
                   "سازنده سابقه یک رگ‌پول دارد", metric=rugs, severity=3)
    return _op("LENS-KREBS", "KREBS-01", "APPROVE",
               "سابقه رگ‌پولی برای این سازنده ثبت نشده است", metric=0.0)


def lens_mitnick_manufactured_hype(cand, ctx) -> LensOpinion:
    """Urgency and social proof bypass deliberation.

    A coordinated promotion leaves a characteristic fingerprint: buy pressure
    far beyond anything organic, on a pair too young to have earned it. The
    lens cannot read Telegram, so it reads the shape the promotion leaves in
    the trade flow.
    """
    buys = _m(cand, "txns_1h_buys")
    sells = _m(cand, "txns_1h_sells")
    chg_1h = _m(cand, "price_change_1h")
    virality = ctx.get("virality")
    viral_score = _f(getattr(virality, "score", None)) if virality is not None else None

    if buys is None or sells is None:
        return _op("LENS-MITNICK", "SOCENG-01", "ABSTAIN",
                   "بدون تفکیک خرید و فروش، الگوی تبلیغ هماهنگ قابل تشخیص نیست")

    total = buys + sells
    if total < 30:
        return _op("LENS-MITNICK", "SOCENG-01", "ABSTAIN",
                   f"تنها {total:.0f} معامله — الگوی رفتاری قابل استخراج نیست")

    buy_ratio = buys / total
    # A market with essentially no sellers is not "leaning bullish", it is not
    # a market. At 97%+ the only way to get that print is coordination, and
    # this lens must reach that verdict on its OWN evidence rather than
    # relying on some other lens to supply a second caution -- which is
    # exactly what used to happen: Fisher cautioned on the same trade counts,
    # convergence tripped, and the trap was caught for the wrong reason.
    if buy_ratio >= 0.97:
        return _op("LENS-MITNICK", "SOCENG-01", "VETO",
                   f"{buy_ratio:.0%} معاملات خرید از {total:.0f} معامله — "
                   f"عملاً هیچ فروشنده‌ای وجود ندارد؛ این الگو تنها با "
                   f"هماهنگی ساخته می‌شود",
                   metric=buy_ratio, severity=3, evidence=("trade_flow",))

    signs: list[str] = []
    if buy_ratio > 0.92:
        signs.append(f"{buy_ratio:.0%} معاملات خرید — فروشنده‌ای وجود ندارد")
    if chg_1h is not None and chg_1h > 150.0:
        signs.append(f"جهش {chg_1h:.0f}٪ در یک ساعت")
    if viral_score is not None and viral_score > 80.0 and buy_ratio > 0.85:
        signs.append("هم‌زمانی اوج وایرال با فشار خرید یک‌طرفه")

    if len(signs) >= 2:
        return _op("LENS-MITNICK", "SOCENG-01", "VETO",
                   "الگوی تبلیغ هماهنگ: " + "، ".join(signs[:2])
                   + " — فوریت مصنوعی، تصمیم را دور می‌زند",
                   metric=buy_ratio, severity=3)
    if signs:
        return _op("LENS-MITNICK", "SOCENG-01", "CAUTION",
                   "نشانه هیجان مصنوعی: " + signs[0],
                   metric=buy_ratio, severity=2)
    return _op("LENS-MITNICK", "SOCENG-01", "APPROVE",
               f"توزیع خرید/فروش طبیعی است ({buy_ratio:.0%} خرید)",
               metric=buy_ratio)


# ============================================================= LIQUIDITY ====

def lens_adams_slippage(cand, ctx) -> LensOpinion:
    """Constant-product slippage for the position actually being proposed.

    x*y=k means price impact is dx/(x+dx). Round-tripping a position costs
    roughly twice that. This is arithmetic, not estimation -- given pool depth
    and order size the answer is exact for a single v2-style pool.
    """
    liq = _m(cand, "liquidity_usd")
    if liq is None or liq <= 0:
        return _op("LENS-ADAMS", "AMM-01", "ABSTAIN",
                   "بدون عمق استخر، لغزش قابل محاسبه نیست")

    # Size the probe the way the advisor does: 1% of pool, capped by bankroll.
    position = min(liq * 0.01, 20.0)
    dx = position / liq
    one_way = dx / (1 + dx)
    round_trip_pct = one_way * 2 * 100.0

    if round_trip_pct > 5.0:
        return _op("LENS-ADAMS", "AMM-01", "VETO",
                   f"لغزش رفت‌وبرگشت {round_trip_pct:.1f}٪ برای پوزیشن "
                   f"${position:,.2f} — هزینه ورود و خروج سود را می‌بلعد",
                   metric=round_trip_pct, severity=3)
    if round_trip_pct > 2.0:
        return _op("LENS-ADAMS", "AMM-01", "CAUTION",
                   f"لغزش رفت‌وبرگشت {round_trip_pct:.1f}٪ قابل توجه است",
                   metric=round_trip_pct, severity=2)
    return _op("LENS-ADAMS", "AMM-01", "APPROVE",
               f"لغزش رفت‌وبرگشت تنها {round_trip_pct:.2f}٪ برای پوزیشن هدف",
               metric=round_trip_pct)


def lens_keynes_liquidity_preference(cand, ctx) -> LensOpinion:
    """The premium demanded for holding something you may not be able to sell.

    Depth in isolation says little; depth relative to how much actually trades
    says whether you are one of many sellers or the only one.
    """
    liq = _m(cand, "liquidity_usd")
    vol_24h = _m(cand, "volume_24h")
    if liq is None or vol_24h is None or liq <= 0:
        return _op("LENS-KEYNES", "LIQPREF-01", "ABSTAIN",
                   "بدون نقدینگی و حجم روزانه، ترجیح نقدشوندگی سنجیده نمی‌شود")

    daily_turnover = vol_24h / liq
    if daily_turnover < 0.10:
        return _op("LENS-KEYNES", "LIQPREF-01", "CAUTION",
                   f"گردش روزانه تنها {daily_turnover:.1%} عمق استخر — "
                   f"خریدار کافی برای خروج شما وجود ندارد",
                   metric=daily_turnover, severity=2)
    # Upper bound set from the healthy distribution, not intuition: over 600
    # healthy candidates the p99 daily turnover was ~27x, so 20x was flagging
    # the top decile of perfectly ordinary tokens. 40x sits clear of the
    # healthy range while still catching genuine churn.
    # A pool turning over 100x a day recycles its entire depth every ~15
    # minutes. Real two-sided demand does not do that; wash trading does, and
    # the inflated volume is precisely the number a buyer would mistake for
    # interest. Treated as fatal on this lens's own evidence rather than
    # waiting for a second opinion to converge with.
    if daily_turnover > 100.0:
        return _op("LENS-KEYNES", "LIQPREF-01", "VETO",
                   f"گردش روزانه {daily_turnover:.0f} برابر عمق استخر — "
                   f"این حجم با تقاضای واقعی سازگار نیست و نشانه معامله صوری است",
                   metric=daily_turnover, severity=3, evidence=("turnover",))
    if daily_turnover > 40.0:
        return _op("LENS-KEYNES", "LIQPREF-01", "CAUTION",
                   f"گردش روزانه {daily_turnover:.0f} برابر عمق — "
                   f"سرمایه ناپایدار و زودگذر است",
                   metric=daily_turnover, severity=2, evidence=("turnover",))
    return _op("LENS-KEYNES", "LIQPREF-01", "APPROVE",
               f"گردش روزانه {daily_turnover:.1f} برابر عمق — بازار دوطرفه فعال است",
               metric=daily_turnover)


# ============================================================== EVIDENCE ====

def lens_neyman_error_asymmetry(cand, ctx) -> LensOpinion:
    """The two errors do not cost the same, so the bar cannot be symmetric.

    Missing a good token costs the opportunity. Accepting a scam costs the
    capital, and capital lost cannot take the next trade. Neyman's point is
    that this ratio is a choice which must be stated, not discovered -- so the
    lens states it: near the decision boundary, refuse.
    """
    report = ctx.get("score_report")
    score = _f(getattr(report, "opportunity_score", None)) if report else None
    confidence = getattr(report, "confidence_level", None) if report else None
    if score is None:
        return _op("LENS-NEYMAN", "NEYMAN-01", "ABSTAIN",
                   "بدون امتیاز، توازن خطا قابل ارزیابی نیست")

    if confidence == "LOW" and score >= 70.0:
        return _op("LENS-NEYMAN", "NEYMAN-01", "VETO",
                   f"امتیاز بالای {score:.0f} با اعتماد پایین به داده — "
                   f"هزینه پذیرش اشتباه بسیار بیشتر از هزینه رد اشتباه است",
                   metric=score, severity=3)
    if 68.0 <= score <= 74.0:
        return _op("LENS-NEYMAN", "NEYMAN-01", "CAUTION",
                   f"امتیاز {score:.0f} در ناحیه مرزی آستانه ۷۰ — "
                   f"عدم تقارن هزینه خطا رد کردن را توصیه می‌کند",
                   metric=score, severity=2)
    return _op("LENS-NEYMAN", "NEYMAN-01", "APPROVE",
               f"امتیاز {score:.0f} با فاصله روشن از مرز تصمیم", metric=score)


def lens_tao_sparse_evidence(cand, ctx) -> LensOpinion:
    """How few observations can still support a claim?

    Sparse recovery works when sparsity actually holds. Here the analogue is:
    a small number of well-populated fields can support an inference, but only
    if the fields that matter are among them. Counting populated fields is the
    measurement; whether they are the right ones is the judgement.
    """
    decisive = {
        "liquidity_usd": _m(cand, "liquidity_usd"),
        "volume_1h": _m(cand, "volume_1h"),
        "txns_1h_buys": _m(cand, "txns_1h_buys"),
        "price_change_1h": _m(cand, "price_change_1h"),
        "is_honeypot": _s(cand, "is_honeypot"),
        "sell_tax_pct": _s(cand, "sell_tax_pct"),
        "liquidity_locked_pct": _s(cand, "liquidity_locked_pct"),
        "top10_holder_concentration_pct": _s(cand, "top10_holder_concentration_pct"),
    }
    present = [k for k, v in decisive.items() if v is not None]
    ratio = len(present) / len(decisive)

    if ratio < 0.4:
        return _op("LENS-TAO", "SPARSE-01", "VETO",
                   f"تنها {len(present)} میدان تعیین‌کننده از {len(decisive)} "
                   f"موجود است — بازیابی سیگنال از این تُنُکی ممکن نیست",
                   metric=ratio, severity=3)
    if ratio < 0.7:
        return _op("LENS-TAO", "SPARSE-01", "CAUTION",
                   f"پوشش میدان‌های تعیین‌کننده {ratio:.0%} — استنتاج شکننده است",
                   metric=ratio, severity=2)
    return _op("LENS-TAO", "SPARSE-01", "APPROVE",
               f"{len(present)} میدان تعیین‌کننده در دسترس است ({ratio:.0%})",
               metric=ratio)


# ================================================================ TIMING ====

def lens_riemann_joint_surface(cand, ctx) -> LensOpinion:
    """Judge the axes together, not one at a time.

    A token can be acceptable on depth, acceptable on momentum and acceptable
    on concentration, while the combination -- shallow pool plus violent
    momentum plus concentrated ownership -- is a structure no single axis
    flags. Marginal checks miss joint structure by construction.
    """
    liq = _m(cand, "liquidity_usd")
    chg_1h = _m(cand, "price_change_1h")
    top10 = _f(_s(cand, "top10_holder_concentration_pct"))
    if liq is None or chg_1h is None or top10 is None:
        return _op("LENS-RIEMANN", "RIEMANN-01", "ABSTAIN",
                   "برای سنجش سطح ریسک، هر سه محور عمق، شتاب و تمرکز لازم است")

    # Each axis individually tolerable, jointly not.
    shallow = liq < 100_000
    violent = chg_1h > 50.0
    concentrated = top10 > 30.0
    combined = sum((shallow, violent, concentrated))

    if combined == 3:
        return _op("LENS-RIEMANN", "RIEMANN-01", "VETO",
                   f"ترکیب سه‌محوره خطرناک: عمق ${liq:,.0f}، جهش {chg_1h:.0f}٪، "
                   f"تمرکز {top10:.0f}٪ — هر محور به‌تنهایی قابل قبول، "
                   f"ولی هندسه مشترک نیست",
                   metric=float(combined), severity=3)
    if combined == 2:
        return _op("LENS-RIEMANN", "RIEMANN-01", "CAUTION",
                   f"دو محور هم‌زمان نامساعدند (عمق ${liq:,.0f}، "
                   f"شتاب {chg_1h:.0f}٪، تمرکز {top10:.0f}٪)",
                   metric=float(combined), severity=2)
    return _op("LENS-RIEMANN", "RIEMANN-01", "APPROVE",
               "سطح مشترک عمق، شتاب و تمرکز پایدار است",
               metric=float(combined))


def lens_tversky_anchoring(cand, ctx) -> LensOpinion:
    """Do not let one number anchor the whole judgement.

    Anchoring is our bias, not the token's. The operational form here: when a
    single headline figure -- a spectacular 24h gain -- dwarfs everything else
    on the card, it will dominate the reader's judgement regardless of what
    the other fields say. The lens names the anchor so it stops working
    silently.
    """
    chg_24h = _m(cand, "price_change_24h")
    chg_1h = _m(cand, "price_change_1h")
    if chg_24h is None:
        return _op("LENS-TVERSKY", "ANCHOR-01", "ABSTAIN",
                   "بدون تغییر قیمت ۲۴ ساعته، اثر لنگر قابل سنجش نیست")

    if chg_24h > 200.0:
        detail = f"رشد {chg_24h:.0f}٪ در ۲۴ ساعت"
        if chg_1h is not None and chg_1h < 0:
            # The headline is already stale: the last hour is negative.
            return _op("LENS-TVERSKY", "ANCHOR-01", "VETO",
                       f"{detail} لنگر ذهنی می‌سازد در حالی که ساعت اخیر "
                       f"{chg_1h:.0f}٪ منفی است — عدد بزرگ متعلق به گذشته است",
                       metric=chg_24h, severity=3)
        return _op("LENS-TVERSKY", "ANCHOR-01", "CAUTION",
                   f"{detail} — تصمیم نباید بر پایه این عدد گرفته شود",
                   metric=chg_24h, severity=2)
    return _op("LENS-TVERSKY", "ANCHOR-01", "APPROVE",
               "هیچ عدد منفردی بر تصویر کلی غالب نیست", metric=chg_24h)


def lens_simon_satisficing(cand, ctx) -> LensOpinion:
    """Stop optimising when the data cannot support the precision.

    Ranking candidates to the decimal point when the underlying observations
    are coarse is false precision. Simon's answer is to seek adequacy: if the
    evidence only supports "good enough", say that instead of manufacturing a
    ranking the data cannot justify.
    """
    report = ctx.get("score_report")
    score = _f(getattr(report, "opportunity_score", None)) if report else None
    unknowns = getattr(cand, "unknown_fields", None) or []
    if score is None:
        return _op("LENS-SIMON", "SATISFICE-01", "ABSTAIN",
                   "بدون امتیاز، کفایت قابل ارزیابی نیست")

    # Counting raw unknown_fields was wrong: a healthy DexScreener candidate
    # always lacks ~11 optional fields (5m windows, socials, market cap), so
    # the test fired on everything. Only decision-critical gaps make a precise
    # score unsupportable.
    critical_missing = [name for name, value in (
        ("liquidity_usd", _m(cand, "liquidity_usd")),
        ("volume_1h", _m(cand, "volume_1h")),
        ("sell_tax_pct", _s(cand, "sell_tax_pct")),
        ("liquidity_locked_pct", _s(cand, "liquidity_locked_pct")),
        ("top10_concentration", _s(cand, "top10_holder_concentration_pct")),
    ) if value is None]

    if critical_missing and score >= 85.0:
        return _op("LENS-SIMON", "SATISFICE-01", "CAUTION",
                   f"امتیاز {score:.0f} در حالی که "
                   + "، ".join(critical_missing[:2])
                   + " نامعلوم است — دقت ادعاشده بیش از پشتیبانی داده است",
                   metric=score, severity=2)
    return _op("LENS-SIMON", "SATISFICE-01", "APPROVE",
               f"امتیاز {score:.0f} با سطح جزئیات داده سازگار است", metric=score)


def lens_hayek_price_knowledge(cand, ctx) -> LensOpinion:
    """Price aggregates knowledge only when there is a crowd to aggregate.

    With thousands of independent participants a price carries information no
    one holds alone. With eleven wallets it carries the intentions of eleven
    wallets. The distinction decides whether the price signal means anything.
    """
    buys = _m(cand, "txns_1h_buys")
    sells = _m(cand, "txns_1h_sells")
    top10 = _f(_s(cand, "top10_holder_concentration_pct"))
    if buys is None or sells is None:
        return _op("LENS-HAYEK", "HAYEK-01", "ABSTAIN",
                   "بدون تعداد معاملات، توان تجمیع دانش بازار سنجیده نمی‌شود")

    participants = buys + sells
    if participants < 50:
        return _op("LENS-HAYEK", "HAYEK-01", "CAUTION",
                   f"تنها {participants:.0f} معامله — قیمت، دانش جمعی را "
                   f"تجمیع نمی‌کند بلکه نظر چند نفر است",
                   metric=participants, severity=2)
    if top10 is not None and top10 > 60.0:
        return _op("LENS-HAYEK", "HAYEK-01", "VETO",
                   f"{top10:.0f}٪ عرضه نزد ده کیف پول — قیمت، دانش پراکنده "
                   f"نیست بلکه اراده چند مالک است",
                   metric=top10, severity=3)
    return _op("LENS-HAYEK", "HAYEK-01", "APPROVE",
               f"{participants:.0f} معامله از مشارکت‌کنندگان متعدد — "
               f"قیمت اطلاعات جمعی را بازتاب می‌دهد", metric=participants)


def lens_newton_momentum_decay(cand, ctx) -> LensOpinion:
    """Velocity versus acceleration: is momentum still building, or fading?

    A token up 80% over 24h but flat in the last hour has already made its
    move. Comparing windows gives the second derivative -- crude, but the
    difference between arriving early and arriving last.
    """
    chg_1h = _m(cand, "price_change_1h")
    chg_24h = _m(cand, "price_change_24h")
    if chg_1h is None or chg_24h is None:
        return _op("LENS-NEWTON", "NEWTON-01", "ABSTAIN",
                   "برای سنجش شتاب، تغییر قیمت ۱ ساعته و ۲۴ ساعته لازم است")

    # Hourly rate implied by the 24h move, against the actual last hour.
    implied_hourly = chg_24h / 24.0
    if chg_24h > 30.0 and chg_1h < 0:
        return _op("LENS-NEWTON", "NEWTON-01", "VETO",
                   f"شتاب منفی شده است: {chg_24h:.0f}٪ در روز اما "
                   f"{chg_1h:.0f}٪ در ساعت اخیر — حرکت تمام شده است",
                   metric=chg_1h, severity=3)
    if chg_24h > 50.0 and 0 <= chg_1h < implied_hourly * 0.3:
        return _op("LENS-NEWTON", "NEWTON-01", "CAUTION",
                   f"شتاب در حال کاهش: نرخ ساعتی {chg_1h:.1f}٪ در برابر "
                   f"میانگین {implied_hourly:.1f}٪",
                   metric=chg_1h, severity=2)
    return _op("LENS-NEWTON", "NEWTON-01", "APPROVE",
               f"آهنگ حرکت پایدار است (ساعتی {chg_1h:.1f}٪)", metric=chg_1h)


# ================================================================ SIZING ====

def lens_thorp_kelly(cand, ctx) -> LensOpinion:
    """Kelly sizing -- and an honest refusal when it cannot be computed.

    f* = (bp - q)/b needs a win probability. Without a calibrated one, Kelly
    is not merely imprecise, it is undefined; and full Kelly on an overstated
    p is the classic route to ruin, which is why the fractional form is the
    only one used here.
    """
    report = ctx.get("score_report")
    score = _f(getattr(report, "opportunity_score", None)) if report else None
    ex = ctx.get("exitability")
    frac = _f(getattr(ex, "realizable_fraction", None)) if ex is not None else None

    if score is None or frac is None:
        return _op("LENS-THORP", "KELLY-01", "ABSTAIN",
                   "بدون امتیاز و کسر قابل بازیافت، معیار کِلی تعریف نشده است")

    # Kelly needs a WIN PROBABILITY. The opportunity score is an ordinal
    # quality signal, not a probability, and inventing a mapping from one to
    # the other is precisely the self-deception Feynman's lens objects to.
    #
    # A first attempt here mapped p = score/200, which turned a score of 90
    # into a 45% win rate and produced a near-zero Kelly fraction for every
    # candidate -- a lens that always says the same thing carries no
    # information. The honest position: the calibrator in
    # `architecture/learning/calibration.py` derives descriptive rates from real
    # outcomes, and until a pre-registered band clears its guards there IS no p.
    calibrated = (ctx or {}).get("calibration")
    p = None
    p_hat = None
    p_low = None
    if calibrated is not None and getattr(calibrated, "is_usable", False):
        result = calibrated.probability_for_score(score)
        if result is not None:
            p_hat, interval = result
            # The calibrator returns a Wilson interval alongside the point
            # estimate, precisely because a rate measured on a handful of
            # outcomes is not the rate. This lens used to take result[0] and
            # discard the interval -- betting the point estimate as though it
            # were certain, which is the "overstated p" route to ruin this
            # docstring warns about, committed by the lens that warns about it.
            #
            # The canonical calibration layer already refuses bands below its
            # strict sample/positive guards. Even after those guards clear,
            # Kelly uses the LOWER Wilson bound rather than the point estimate.
            # Uncertainty therefore shrinks
            # the position instead of being silently rounded away, and the
            # recommendation converges on the point estimate as evidence
            # accumulates and the interval tightens.
            p_low = interval[0] if interval else p_hat
            p = p_low

    if p is None:
        return _op("LENS-THORP", "KELLY-01", "ABSTAIN",
                   "احتمال برد هنوز کالیبره نشده است — معیار کِلی بدون احتمال "
                   "واقعی محاسبه نمی‌شود و حدس زدن آن، اندازه پوزیشن را "
                   "بر پایه توهم می‌گذارد")

    # Kelly's `b` is NET ODDS -- the profit per unit staked on a win, not the
    # gross multiple. This line previously read `b = 1.5`, taking EXIT_V1's
    # 1.5x take-profit as the odds. That is a unit error: exiting at +50% pays
    # 0.50 per unit staked, so b = 0.50.
    #
    # It also assumed a losing trade loses the whole stake, when EXIT_V1 stops
    # out at -35%. Both sides were wrong in opposite directions, and they did
    # not cancel: break-even landed at p=0.400 instead of the true p=0.412, so
    # in that band the lens called a losing bet profitable, and above it every
    # fraction was understated by roughly 2.5x.
    #
    # For a win of +a and a loss of -c, the growth-optimal fraction is
    #     f* = p/c - (1-p)/a
    # which reduces to the familiar (bp-q)/b when c = 1 (total loss).
    a, c = TAKE_PROFIT_PCT, STOP_LOSS_PCT
    kelly = p / c - (1.0 - p) / a
    kelly_hat = (p_hat / c - (1.0 - p_hat) / a) if p_hat is not None else kelly

    # Two different failures, and collapsing them would be its own bug.
    #
    # A negative POINT estimate means the measured rate itself is a losing
    # bet: no amount of further sampling makes the observed edge positive, so
    # the verdict is fatal.
    #
    # A negative LOWER BOUND with a positive point estimate means something
    # milder -- the edge looks real but five outcomes cannot prove it. That is
    # recoverable by construction: it resolves as the bin fills. A genuinely
    # profitable 60% strategy has a negative lower bound until roughly n=40,
    # so vetoing on it would block every real edge for its first forty trades.
    # VETO is reserved for the unrecoverable; this is CAUTION.
    if kelly_hat <= 0:
        return _op("LENS-THORP", "KELLY-01", "VETO",
                   f"کِلی منفی است (p={p_hat:.0%}، سود {a:.0%} در برابر زیان "
                   f"{c:.0%}) — هیچ اندازه‌ای از این شرط سودآور نیست",
                   metric=kelly_hat, severity=3, evidence=("calibrated_edge",))
    if kelly <= 0:
        return _op("LENS-THORP", "KELLY-01", "CAUTION",
                   f"برآورد نقطه‌ای p={p_hat:.0%} لبه مثبت نشان می‌دهد اما کف "
                   f"بازه اطمینان ({p:.0%}) هنوز زیان را رد نمی‌کند — "
                   f"شواهد برای اندازه‌گیری پوزیشن کافی نیست",
                   metric=kelly, severity=2, evidence=("calibrated_edge",))

    # Quarter-Kelly: full Kelly is brutally sensitive to an overstated p, and
    # scaled by realizable fraction because an un-exitable edge is not an edge.
    #
    # Capped at 1.0 before scaling. With a -35% stop rather than a total loss,
    # f* legitimately exceeds 1 (p=0.60 gives 0.91, p=0.75 gives 1.64) because
    # the formula is implicitly sizing against the stop distance, not the whole
    # stake. Reporting "164% of capital" would be arithmetically faithful and
    # practically absurd on a $20 bankroll, and the deterministic sizing rules
    # in the advisor -- 1% of pool, 10% of bankroll -- bind far below it anyway.
    quarter = min(kelly, 1.0) * 0.25 * frac
    if quarter < 0.02:
        return _op("LENS-THORP", "KELLY-01", "CAUTION",
                   f"کسر کِلی توصیه‌شده تنها {quarter:.1%} سرمایه است — "
                   f"لبه بسیار نازک", metric=quarter, severity=2,
                   evidence=("calibrated_edge",))
    basis = (f"p={p:.0%}" if p_hat is None or abs(p_hat - p) < 1e-9
             else f"محافظه‌کارانه بر کف بازه p={p:.0%} (برآورد {p_hat:.0%})")
    return _op("LENS-THORP", "KELLY-01", "APPROVE",
               f"یک‌چهارم کِلی: {quarter:.1%} از سرمایه — {basis}",
               metric=quarter, evidence=("calibrated_edge",))


def lens_einstein_reference_frame(cand, ctx) -> LensOpinion:
    """A number without its frame is not a measurement.

    $20 is trivial against a $100k bankroll and the entire stake against $20.
    The system's bankroll is $20, so any position must be judged in that frame
    -- and the pool must be deep enough that our own order is not the event.
    """
    liq = _m(cand, "liquidity_usd")
    if liq is None or liq <= 0:
        return _op("LENS-EINSTEIN", "FRAME-01", "ABSTAIN",
                   "بدون عمق استخر، چارچوب مرجع قابل تعیین نیست")

    bankroll = 20.0            # BANKROLL_START_USD
    our_share = bankroll / liq
    if our_share > 0.01:
        return _op("LENS-EINSTEIN", "FRAME-01", "VETO",
                   f"کل سرمایه ما ${bankroll:.0f} معادل {our_share:.1%} استخر "
                   f"است — در این چارچوب، خودِ ما رویداد بازار می‌شویم",
                   metric=our_share, severity=3)
    if our_share > 0.002:
        return _op("LENS-EINSTEIN", "FRAME-01", "CAUTION",
                   f"سهم ما از استخر {our_share:.2%} — اثر خودمان قابل اغماض نیست",
                   metric=our_share, severity=2)
    return _op("LENS-EINSTEIN", "FRAME-01", "APPROVE",
               f"در چارچوب سرمایه ${bankroll:.0f}، سهم ما {our_share:.3%} "
               f"استخر است و بی‌اثر", metric=our_share)


def lens_feynman_first_principles(cand, ctx) -> LensOpinion:
    """You must not fool yourself, and you are the easiest person to fool.

    Every figure driving a decision must trace to a measured input. The most
    common way this system could fool itself is a default that looks like a
    measurement: a field left at its initial value and then reasoned over as
    though a provider had reported it.
    """
    suspicious: list[str] = []
    # A provider genuinely reporting these exact values is possible but rare;
    # in combination they indicate defaults rather than observations.
    if _m(cand, "price_change_1h") == 0.0 and _m(cand, "price_change_24h") == 0.0:
        suspicious.append("تغییر قیمت ۱ و ۲۴ ساعته دقیقاً صفر")
    if _m(cand, "volume_1h") == 0.0 and _m(cand, "liquidity_usd"):
        suspicious.append("حجم صفر با نقدینگی غیرصفر")
    buys, sells = _m(cand, "txns_1h_buys"), _m(cand, "txns_1h_sells")
    if buys == 0 and sells == 0 and _m(cand, "volume_1h"):
        suspicious.append("حجم ثبت‌شده بدون هیچ تراکنشی")

    provider = getattr(cand, "source_provider", None)
    if not provider or provider == "unknown":
        suspicious.append("منبع داده نامشخص")

    if len(suspicious) >= 2:
        return _op("LENS-FEYNMAN", "FEYNMAN-01", "VETO",
                   "داده‌ها با مقادیر پیش‌فرض سازگارترند تا با مشاهده واقعی: "
                   + "، ".join(suspicious[:2]),
                   metric=float(len(suspicious)), severity=3)
    if suspicious:
        return _op("LENS-FEYNMAN", "FEYNMAN-01", "CAUTION",
                   "احتمال مقدار پیش‌فرض به‌جای مشاهده: " + suspicious[0],
                   severity=2)
    return _op("LENS-FEYNMAN", "FEYNMAN-01", "APPROVE",
               f"ارقام از مشاهده واقعی منبع «{provider}» می‌آیند")


# ============================================================== LEARNING ====

def lens_deming_process_control(cand, ctx) -> LensOpinion:
    """Common cause or special cause? Reacting wrongly makes it worse.

    Applied per-candidate: is this token's profile an ordinary member of the
    population we routinely see, or a genuine outlier? Treating every outlier
    as a signal is precisely the tampering Deming warned about.
    """
    report = ctx.get("score_report")
    score = _f(getattr(report, "opportunity_score", None)) if report else None
    if score is None:
        return _op("LENS-DEMING", "SPC-01", "ABSTAIN",
                   "بدون امتیاز، تفکیک علت عام از خاص ممکن نیست")

    # Deming's actual warning is against tampering: treating ordinary
    # variation as a special cause. Measured against 600 healthy candidates,
    # 47% score 100 -- a perfect score is the COMMON case for this scorer, so
    # flagging it was itself the tampering the principle forbids.
    #
    # The genuine special cause is a score that disagrees with its own
    # evidence: a high number resting on an admittedly incomplete picture.
    confidence = getattr(report, "confidence_level", None)
    # Deliberately keyed on the provider's own confidence grade rather than on
    # the unknown-field count. Simon already inspects missing critical fields,
    # and two lenses reading the same input are not two independent opinions --
    # counting them as such is how a healthy token collected a CONVERGENT
    # veto from what was really one observation.
    if score >= 90.0 and confidence == "LOW":
        return _op("LENS-DEMING", "SPC-01", "CAUTION",
                   f"امتیاز {score:.0f} با اعتماد پایین به داده — "
                   f"این نوسان علت خاص دارد، نه عام",
                   metric=score, severity=2)
    return _op("LENS-DEMING", "SPC-01", "APPROVE",
               f"امتیاز {score:.0f} با کیفیت شواهد سازگار است", metric=score)


def lens_drucker_measurement(cand, ctx) -> LensOpinion:
    """An objective without a measurement is an intention.

    This lens audits the panel's own output: how many of the opinions formed
    about this candidate actually carry a number. A council of qualitative
    assertions is a debating society.
    """
    report = ctx.get("score_report")
    measurable = 0
    total = 0
    for field in ("liquidity_usd", "volume_1h", "price_usd"):
        total += 1
        measurable += _m(cand, field) is not None
    for field in ("sell_tax_pct", "liquidity_locked_pct",
                  "top10_holder_concentration_pct"):
        total += 1
        measurable += _s(cand, field) is not None
    total += 1
    measurable += report is not None

    ratio = measurable / total if total else 0.0
    if ratio < 0.5:
        return _op("LENS-DRUCKER", "DRUCKER-01", "VETO",
                   f"تنها {measurable} سنجه از {total} قابل اندازه‌گیری است — "
                   f"آنچه اندازه‌گیری نشود، مدیریت نمی‌شود",
                   metric=ratio, severity=3)
    if ratio < 0.8:
        return _op("LENS-DRUCKER", "DRUCKER-01", "CAUTION",
                   f"پوشش سنجه‌ها {ratio:.0%} — بخشی از حکم بر برآورد استوار است",
                   metric=ratio, severity=2)
    return _op("LENS-DRUCKER", "DRUCKER-01", "APPROVE",
               f"{measurable} سنجه از {total} با عدد پشتیبانی می‌شوند",
               metric=ratio)


# ------------------------------------------- Wave-33c: previously ADVISORY --

def lens_mises_calculation(cand, ctx) -> LensOpinion:
    """A valuation nobody could actually cash out is not a price.

    `fdv_usd` is collected from both providers and stored on every candidate,
    and until now NO lens and not even the scorer read it. That left the panel
    blind to the most ordinary memecoin trap there is: a headline valuation
    resting on a pool far too thin to honour it. A token showing "$50M" backed
    by a $250k pool is asking holders to believe in a number that only 0.5% of
    them could ever realise.

    Mises' calculation problem is exactly this: prices that do not arise from
    real exchange convey no information. The ratio is deliberately generous --
    fully diluted valuation legitimately exceeds pool depth by a wide margin
    on healthy tokens -- so only the range where the notional becomes fiction
    is flagged.
    """
    fdv = _m(cand, "fdv_usd")
    liq = _m(cand, "liquidity_usd")
    if fdv is None or liq is None or liq <= 0 or fdv <= 0:
        return _op("LENS-MISES", "CALC-01", "ABSTAIN",
                   "بدون ارزش‌گذاری کامل و عمق استخر، محاسبه اقتصادی ممکن نیست")

    ratio = fdv / liq
    # Absorbable share: the fraction of the notional the pool could actually pay.
    absorbable = 1.0 / ratio

    if ratio > 400.0:
        return _op("LENS-MISES", "CALC-01", "VETO",
                   f"ارزش‌گذاری اعلام‌شده {ratio:.0f} برابر عمق استخر است — "
                   f"استخر تنها {absorbable:.2%} این ارزش را می‌تواند پرداخت کند؛ "
                   f"این عدد از معامله واقعی نیامده است",
                   metric=ratio, severity=3, evidence=("fdv_backing",))
    if ratio > 120.0:
        return _op("LENS-MISES", "CALC-01", "CAUTION",
                   f"ارزش‌گذاری {ratio:.0f} برابر عمق استخر — "
                   f"تنها {absorbable:.1%} آن قابل نقد شدن است",
                   metric=ratio, severity=2, evidence=("fdv_backing",))
    return _op("LENS-MISES", "CALC-01", "APPROVE",
               f"نسبت ارزش‌گذاری به عمق استخر {ratio:.0f} برابر — در محدوده معقول",
               metric=ratio, evidence=("fdv_backing",))


def lens_archimedes_load(cand, ctx) -> LensOpinion:
    """What must the price do before the position merely breaks even?

    Adams computes round-trip SLIPPAGE and stops there; the taxes are never
    added in, and `buy_tax_pct` is read by no lens at all. So a token charging
    24% to buy and 24% to sell passed every tax check -- each sits below the
    25% sell-tax veto -- while quietly requiring a +161% move to net the +50%
    the exit rules take profit at.

    Archimedes' lever states the load against the fulcrum that must bear it.
    Here the load is the total friction and the fulcrum is the take-profit the
    system actually trades:

        needed = (1 + TP) / ((1 - buy_tax)(1 - sell_tax)) - 1 + slippage
    """
    buy_tax = _f(_s(cand, "buy_tax_pct"))
    sell_tax = _f(_s(cand, "sell_tax_pct"))
    liq = _m(cand, "liquidity_usd")
    if buy_tax is None and sell_tax is None:
        return _op("LENS-ARCHIMEDES", "LEVER-01", "ABSTAIN",
                   "بدون مالیات خرید و فروش، بار کل معامله محاسبه نمی‌شود")

    b = (buy_tax or 0.0) / 100.0
    s_ = (sell_tax or 0.0) / 100.0
    if b >= 1.0 or s_ >= 1.0:
        return _op("LENS-ARCHIMEDES", "LEVER-01", "VETO",
                   "مالیات معامله ۱۰۰٪ یا بیشتر است — خروج غیرممکن است",
                   metric=100.0, severity=3, evidence=("round_trip_cost",))

    slip = 0.0
    if liq and liq > 0:
        dx = min(liq * 0.01, 20.0) / liq
        slip = (dx / (1 + dx)) * 2

    # The move required to net the take-profit the exit rules actually use.
    needed = ((1.0 + TAKE_PROFIT_PCT) / ((1.0 - b) * (1.0 - s_)) - 1.0 + slip) * 100.0
    target = TAKE_PROFIT_PCT * 100.0
    overhead = needed - target

    if overhead > 60.0:
        return _op("LENS-ARCHIMEDES", "LEVER-01", "VETO",
                   f"برای رسیدن به سود {target:.0f}٪ خالص، قیمت باید "
                   f"{needed:.0f}٪ رشد کند (مالیات خرید {b:.0%}، فروش {s_:.0%}) — "
                   f"اهرم معامله زیر بار خودش می‌شکند",
                   metric=needed, severity=3, evidence=("round_trip_cost",))
    if overhead > 20.0:
        return _op("LENS-ARCHIMEDES", "LEVER-01", "CAUTION",
                   f"هزینه رفت‌وبرگشت، حد سود را از {target:.0f}٪ به "
                   f"{needed:.0f}٪ حرکت لازم می‌رساند",
                   metric=needed, severity=2, evidence=("round_trip_cost",))
    return _op("LENS-ARCHIMEDES", "LEVER-01", "APPROVE",
               f"هزینه کل رفت‌وبرگشت اندک است — {needed:.0f}٪ حرکت برای سود "
               f"{target:.0f}٪ خالص کافی است",
               metric=needed, evidence=("round_trip_cost",))


def lens_noether_supply_invariant(cand, ctx) -> LensOpinion:
    """What a holder assumes is fixed, and is not: their share of supply.

    `market_cap_usd` was the other collected-but-unread field. Market cap
    counts circulating supply; FDV counts all of it. The gap is the overhang
    -- tokens that can still be issued against the same pool.

    A buyer at 10% circulating owns a claim that nine times as much supply can
    be printed against. Nothing about price or liquidity reveals this; the two
    numbers must be read together, which is why neither alone was enough and
    why the field sat unused.

    Noether's theorem identifies the quantity a system conserves under its
    symmetries. Here the invariant a holder implicitly assumes -- my fraction
    of the supply -- is exactly the one that is not conserved.

    Deliberately generous: legitimate projects vest over time, so only the
    range where circulating supply is a small minority is treated as a
    finding, and it is never fatal on its own. An unlock is a schedule, not a
    honeypot: it is a reason to size down, not to refuse.
    """
    mcap = _m(cand, "market_cap_usd")
    fdv = _m(cand, "fdv_usd")
    if mcap is None or fdv is None or fdv <= 0 or mcap <= 0:
        return _op("LENS-NOETHER", "INVAR-01", "ABSTAIN",
                   "بدون ارزش بازار در گردش و ارزش کامل، رقیق‌شدگی محاسبه نمی‌شود")

    circulating = mcap / fdv
    if circulating > 1.01:
        # Not a dilution finding -- an accounting one. Circulating supply
        # cannot exceed total supply, so one of the two numbers is wrong and
        # neither should be trusted.
        return _op("LENS-NOETHER", "INVAR-01", "CAUTION",
                   f"ارزش بازار از ارزش کامل بیشتر است ({circulating:.2f}) — "
                   f"داده‌های عرضه ناسازگارند و قابل اتکا نیستند",
                   metric=circulating, severity=2, evidence=("supply_overhang",))

    overhang = 1.0 - circulating
    if circulating < 0.20:
        return _op("LENS-NOETHER", "INVAR-01", "CAUTION",
                   f"تنها {circulating:.0%} عرضه در گردش است — "
                   f"{overhang:.0%} باقی‌مانده می‌تواند روی همان استخر آزاد شود "
                   f"و سهم دارنده را رقیق کند",
                   metric=circulating, severity=2, evidence=("supply_overhang",))
    if circulating < 0.50:
        return _op("LENS-NOETHER", "INVAR-01", "CAUTION",
                   f"{circulating:.0%} عرضه در گردش — آزادسازی {overhang:.0%} "
                   f"باقی‌مانده فشار فروش بالقوه است",
                   metric=circulating, severity=1, evidence=("supply_overhang",))
    return _op("LENS-NOETHER", "INVAR-01", "APPROVE",
               f"{circulating:.0%} عرضه در گردش — رقیق‌شدگی آتی محدود است",
               metric=circulating, evidence=("supply_overhang",))


# The team bench, in team order. Grouped so the panel output reads as seven
# teams reporting rather than one undifferentiated wall of opinions.
TEAM_PANEL_LENSES: list[tuple[str, object]] = [
    # SURVIVAL
    ("LENS-POINCARE", lens_poincare_sensitivity),
    ("LENS-BOX", lens_box_model_validity),
    # ADVERSARY
    ("LENS-ANDERSON", lens_anderson_incentives),
    ("LENS-KREBS", lens_krebs_deployer_history),
    ("LENS-MITNICK", lens_mitnick_manufactured_hype),
    # LIQUIDITY
    ("LENS-ADAMS", lens_adams_slippage),
    ("LENS-MISES", lens_mises_calculation),
    ("LENS-ARCHIMEDES", lens_archimedes_load),
    ("LENS-NOETHER", lens_noether_supply_invariant),
    ("LENS-KEYNES", lens_keynes_liquidity_preference),
    # EVIDENCE
    ("LENS-NEYMAN", lens_neyman_error_asymmetry),
    ("LENS-TAO", lens_tao_sparse_evidence),
    # TIMING
    ("LENS-RIEMANN", lens_riemann_joint_surface),
    ("LENS-TVERSKY", lens_tversky_anchoring),
    ("LENS-SIMON", lens_simon_satisficing),
    ("LENS-HAYEK", lens_hayek_price_knowledge),
    ("LENS-NEWTON", lens_newton_momentum_decay),
    # SIZING
    ("LENS-THORP", lens_thorp_kelly),
    ("LENS-EINSTEIN", lens_einstein_reference_frame),
    ("LENS-FEYNMAN", lens_feynman_first_principles),
    # LEARNING
    ("LENS-DEMING", lens_deming_process_control),
    ("LENS-DRUCKER", lens_drucker_measurement),
]

# Push the bench onto the panel from this side too. When panel.py is imported
# first it pulls the bench in itself; when THIS module is imported first, that
# pull happens while this file is still executing and finds no
# TEAM_PANEL_LENSES yet. Registering here closes the second case, and
# `register_lenses` deduplicates so exactly one of the two ever takes effect.
_register(TEAM_PANEL_LENSES)
