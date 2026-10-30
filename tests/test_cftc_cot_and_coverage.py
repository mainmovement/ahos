import math

from architecture.markets.cftc_cot import (
    GOLD_CODE,
    ICE_BRENT_CODE,
    NYMEX_BRENT_CODE,
    WTI_CODE,
    cftc_cot_signal,
    rows_from_cftc_text,
    rows_from_ice_text,
    select_contract,
    tanh_z_score,
)
from architecture.markets.family_coverage import family_coverage
from architecture.markets.paper_trade_gates import (
    MIN_AGREEING_FAMILIES,
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
)
from architecture.markets import signal_brain as sb


def _cftc(code: str, name: str, oi: int, mm_long: int, mm_short: int, as_of: str = "2026-10-20") -> str:
    fields = [""] * 15
    fields[0] = name
    fields[2] = as_of
    fields[3] = code
    fields[7] = str(oi)
    fields[13] = str(mm_long)
    fields[14] = str(mm_short)
    return ",".join(f'"{field}"' if "," in field or " " in field else field for field in fields)


def _centered(frac: float, start: str = "2025-01-07") -> list[tuple[str, float]]:
    points = []
    year, month, day = 2025, 1, 7
    for i in range(52):
        sign = -1 if i % 2 else 1
        points.append((f"{year:04d}-{month:02d}-{day:02d}", frac + sign * 0.01))
        day += 7
        if day > 28:
            day = 7
            month += 1
            if month > 12:
                month = 1
                year += 1
    return points


def test_wti_and_gold_select_by_code_not_by_name():
    text = "\n".join(
        [
            _cftc("067411", "CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE", 9_000_000, 1, 0),
            _cftc(WTI_CODE, "WTI-PHYSICAL - NEW YORK MERCANTILE EXCHANGE", 1_835_144, 163413, 127226),
            _cftc("088692", "MICRO GOLD - COMMODITY EXCHANGE INC.", 9_000_000, 1, 0),
            _cftc(GOLD_CODE, "GOLD - COMMODITY EXCHANGE INC.", 402279, 120970, 16764),
        ]
    )
    rows = rows_from_cftc_text(text)
    wti = select_contract("OIL", "WTI", rows)
    gold = select_contract("GOLD", "XAU", rows)
    assert wti is not None and wti["chosen_code"] == "067651"
    assert wti["open_interest"] == 1_835_144
    assert "LIGHT SWEET" not in wti["market_name"]
    assert gold is not None and gold["chosen_code"] == "088691"
    assert gold["market_name"] == "GOLD - COMMODITY EXCHANGE INC."


def test_brent_picks_the_higher_open_interest_code_and_ignores_name_matches():
    ice = "\n".join(
        [
            "Market_and_Exchange_Names,As_of_Date_In_Form_YYMMDD,As_of_Date_Form_MM/DD/YYYY,CFTC_Contract_Market_Code,CFTC_Market_Code,CFTC_Region_Code,CFTC_Commodity_Code,Open_Interest_All,Prod_Merc_Positions_Long_All,Prod_Merc_Positions_Short_All,Swap_Positions_Long_All,Swap_Positions_Short_All,Swap_Positions_Spread_All,M_Money_Positions_Long_All,M_Money_Positions_Short_All,FutOnly_or_Combined",
            "ICE Brent Crude Futures and Options - ICE Futures Europe,102026,10/20/2026,,ICEU,0,B,9000000,0,0,0,0,0,1,1,Combined",
            "ICE Brent Crude Futures - ICE Futures Europe,102026,10/20/2026,,ICEU,0,B,2608506,0,0,0,0,0,328285,106941,FutOnly",
            "USGC HSFO-PLATTS/BRENT 1ST LN,102026,10/20/2026,,ICEU,0,X,9000000,0,0,0,0,0,1,1,FutOnly",
        ]
    )
    rows = rows_from_ice_text(ice)
    rows.append(
        {
            "code": NYMEX_BRENT_CODE,
            "market_name": "BRENT LAST DAY - NEW YORK MERCANTILE EXCHANGE",
            "as_of": "2026-10-20",
            "open_interest": 230693.0,
            "managed_money_long": 4307.0,
            "managed_money_short": 1458.0,
            "net_oi": (4307 - 1458) / 230693,
            "source": "cftc",
        }
    )
    chosen = select_contract("OIL", "BRENT", rows)
    assert chosen is not None
    assert chosen["chosen_code"] == ICE_BRENT_CODE
    assert {item["code"] for item in chosen["candidates"]} == {ICE_BRENT_CODE, NYMEX_BRENT_CODE}
    assert all(item["code"] != "02141R" for item in chosen["candidates"])


def test_z_score_does_not_saturate_a_normal_gold_net_and_refuses_a_short_history(tmp_path):
    frac = (120970 - 16764) / 402279
    old_scale = math.tanh(frac / 0.05)
    assert old_scale > 0.99
    score, detail = tanh_z_score(frac, [frac + (0.01 if i % 2 else -0.01) for i in range(52)])
    assert score == 0.0
    assert detail["scale"] == "tanh(z/2)"
    assert detail["history_weeks"] == 52
    gold = {
        "code": GOLD_CODE,
        "market_name": "GOLD - COMMODITY EXCHANGE INC.",
        "as_of": "2026-10-20",
        "open_interest": 402279.0,
        "managed_money_long": 120970.0,
        "managed_money_short": 16764.0,
        "net_oi": frac,
        "source": "cftc",
    }
    short = cftc_cot_signal(tmp_path, "GOLD", "XAU", rows=[gold], history={GOLD_CODE: _centered(frac)[:10]})
    assert short is not None and short["available"] is False
    assert short["evidence"]["reason"] == "HISTORY_SHORT"
    assert short["evidence"]["chosen_code"] == GOLD_CODE
    full = cftc_cot_signal(tmp_path, "GOLD", "XAU", rows=[gold], history={GOLD_CODE: _centered(frac)})
    assert full is not None and full["available"] is True
    assert abs(full["score"]) < 0.05
    assert full["evidence"]["composite_weight"] == 0.0
    assert sb.DEFAULT_WEIGHTS["cftc_cot"] == 0.0
    base = [{"name": "news", "score": 0.4, "available": True}]
    assert sb.combine(base + [full], dict(sb.DEFAULT_WEIGHTS))["composite"] == sb.combine(base, dict(sb.DEFAULT_WEIGHTS))["composite"]


def test_current_week_is_not_part_of_its_own_history(tmp_path):
    frac = 0.08
    points = _centered(frac)
    points.append(("2026-10-20", 0.5))
    row = {
        "code": WTI_CODE,
        "market_name": "WTI-PHYSICAL - NEW YORK MERCANTILE EXCHANGE",
        "as_of": "2026-10-20",
        "open_interest": 100.0,
        "managed_money_long": 54.0,
        "managed_money_short": 46.0,
        "net_oi": frac,
        "source": "cftc",
    }
    sig = cftc_cot_signal(tmp_path, "OIL", "WTI", rows=[row], history={WTI_CODE: points})
    assert sig is not None and sig["available"] is True
    assert sig["evidence"]["history_weeks"] == 52
    assert abs(sig["score"]) < 0.05


def test_unmapped_desk_does_not_invent_a_whale_signal(tmp_path):
    assert cftc_cot_signal(tmp_path, "FOREX", "EURUSD", rows=[]) is None
    assert cftc_cot_signal(tmp_path, "PB_TOKEN", "PEPE", rows=[]) is None


def test_mapped_contract_missing_from_file_is_unavailable_not_flat(tmp_path):
    sig = cftc_cot_signal(tmp_path, "OIL", "WTI", rows=[])
    assert sig is not None
    assert sig["available"] is False
    assert sig["evidence"]["reason"] == "CONTRACT_ROW_MISSING"
    assert sb.combine([sig], dict(sb.DEFAULT_WEIGHTS))["composite"] == 0.0


def test_coverage_marks_codes_and_keeps_gates():
    doc = family_coverage()
    assert doc["gates_unchanged"]["min_agreeing_families"] == 2
    assert doc["gates_unchanged"]["min_expected_profit_to_fee_ratio"] == 2.0
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0
    rows = {(r["desk"], r["family"]): r for r in doc["rows"]}
    oil = rows[("OIL", "whales")]
    assert oil["status"] == "CFTC_COT"
    assert oil["contracts"]["WTI"]["cftc_contract_market_code"] == "067651"
    assert oil["contracts"]["BRENT"]["codes"] == [ICE_BRENT_CODE, NYMEX_BRENT_CODE]
    assert rows[("GOLD", "whales")]["contracts"]["XAU"]["cftc_contract_market_code"] == "088691"
    assert rows[("FOREX", "whales")]["status"] == "ABSENT_BY_DESIGN"
    assert rows[("PB_TOKEN", "whales")]["status"] == "ABSENT_BY_DESIGN"
    assert rows[("US_EQUITIES", "whales")]["status"] == "ABSENT_BY_DESIGN"
    assert rows[("CRYPTO", "whales")]["status"] == "LIVE_FEEDS"
    blob = str(doc)
    assert "067411" not in blob
    assert "103.85" not in blob
    assert "cot_oil_net_percentile" not in blob
