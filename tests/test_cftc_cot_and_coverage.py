import csv
import io
import math

from architecture.markets.cftc_cot import (
    COT_CONTRACTS,
    COT_SCALE,
    cftc_cot_signal,
    parse_cot_row,
    positioning_score,
)
from architecture.markets.family_coverage import family_coverage
from architecture.markets.paper_trade_gates import (
    MIN_AGREEING_FAMILIES,
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
)
from architecture.markets import signal_brain as sb


def _line(name: str, oi: int, mm_long: int, mm_short: int) -> str:
    fields = [""] * 15
    fields[0] = name
    fields[2] = "2026-10-20"
    fields[7] = str(oi)
    fields[13] = str(mm_long)
    fields[14] = str(mm_short)
    buf = io.StringIO()
    csv.writer(buf).writerow(fields)
    return buf.getvalue()


def test_brent_score_uses_the_public_columns_not_a_fixture():
    assert COT_SCALE == 0.05
    name = COT_CONTRACTS[("OIL", "BRENT")]
    row = parse_cot_row(_line(name, 230693, 4307, 1458), name)
    expected = round(math.tanh((4307 - 1458) / 230693 / 0.05), 4)
    assert row is not None
    assert row["score"] == expected
    assert row["as_of"] == "2026-10-20"
    assert positioning_score(0, 1, 0) is None


def test_unmapped_desk_does_not_invent_a_whale_signal(tmp_path):
    assert cftc_cot_signal(tmp_path, "FOREX", "EURUSD", text="ignored") is None
    assert cftc_cot_signal(tmp_path, "PB_TOKEN", "PEPE", text="ignored") is None


def test_mapped_contract_missing_from_file_is_unavailable_not_flat(tmp_path):
    sig = cftc_cot_signal(tmp_path, "OIL", "BRENT", text="NOT A COT FILE\n")
    assert sig is not None
    assert sig["available"] is False
    assert sig["evidence"]["reason"] == "CONTRACT_ROW_MISSING"
    assert sb.combine([sig], dict(sb.DEFAULT_WEIGHTS))["composite"] == 0.0


def test_coverage_marks_missing_whale_desks_absent_and_keeps_gates():
    doc = family_coverage()
    assert doc["gates_unchanged"]["min_agreeing_families"] == 2
    assert doc["gates_unchanged"]["min_expected_profit_to_fee_ratio"] == 2.0
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0
    rows = {(r["desk"], r["family"]): r for r in doc["rows"]}
    assert rows[("OIL", "whales")]["status"] == "CFTC_COT"
    assert "BRENT LAST DAY" in rows[("OIL", "whales")]["contracts"]["BRENT"]
    assert rows[("GOLD", "whales")]["status"] == "CFTC_COT"
    assert rows[("FOREX", "whales")]["status"] == "ABSENT_BY_DESIGN"
    assert rows[("PB_TOKEN", "whales")]["status"] == "ABSENT_BY_DESIGN"
    assert rows[("US_EQUITIES", "whales")]["status"] == "ABSENT_BY_DESIGN"
    assert rows[("CRYPTO", "whales")]["status"] == "LIVE_FEEDS"
    assert rows[("OIL", "research")]["status"] == "ADVISORY_VOTE"
    assert rows[("OIL", "research")]["composite_weight"].startswith("0 unless")
    blob = str(doc)
    assert "103.85" not in blob
    assert "cot_oil_net_percentile" not in blob
