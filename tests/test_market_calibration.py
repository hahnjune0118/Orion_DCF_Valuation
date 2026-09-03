from pathlib import Path

import pytest

from market_calibration import (
    calculate_historical_multiple_ranges,
    calculate_relevered_beta,
    calculate_trading_comps_ranges,
    calculate_unlevered_beta,
    load_market_calibration_data,
    prepare_beta_calibration,
    prepare_football_field_ranges,
    reverse_dcf_value_per_share,
    solve_reverse_dcf_growth,
)
from orion_dcf import run_orion_dcf


ROOT = Path(__file__).resolve().parents[1]
MODEL = run_orion_dcf(ROOT / "data" / "raw" / "orion_dcf.xlsx")
PEERS = load_market_calibration_data(
    ROOT / "data" / "metadata" / "market_calibration.csv"
)


def test_peer_snapshot_has_required_population_and_source_metadata():
    assert 5 <= len(PEERS) <= 8
    assert len({peer["ticker"] for peer in PEERS}) == len(PEERS)
    for peer in PEERS:
        assert str(peer["multiple_source"]).startswith("https://")
        assert peer["reference_date"]
        assert peer["ev_ebitda"] > 0
        assert peer["ev_ebit"] > 0
        assert peer["pe"] > 0


def test_hamada_unlever_and_relever_round_trip():
    levered = 0.82
    debt_to_equity = 0.40
    tax_rate = 0.25
    unlevered = calculate_unlevered_beta(
        levered, debt_to_equity, tax_rate
    )
    assert calculate_relevered_beta(
        unlevered, debt_to_equity, tax_rate
    ) == pytest.approx(levered)


def test_beta_calibration_uses_peer_median_and_target_structure():
    result = prepare_beta_calibration(PEERS, 0.05 / 0.95, 0.255)
    assert result["relevered_beta"] > 0
    assert len(result["peers"]) == len(PEERS)
    assert all(peer["unlevered_beta"] > 0 for peer in result["peers"])


def test_trading_and_historical_ranges_are_ordered():
    trading = calculate_trading_comps_ranges(MODEL, PEERS)
    historical = calculate_historical_multiple_ranges(MODEL)
    for ranges in (trading, historical):
        assert set(ranges) == {"EV/EBITDA", "EV/EBIT", "P/E"}
        for result in ranges.values():
            assert result["low"] <= result["mid"] <= result["high"]
            assert result["low_multiple"] <= result["median_multiple"]
            assert result["median_multiple"] <= result["high_multiple"]


def test_football_field_contains_dcf_comps_history_and_market():
    trading = calculate_trading_comps_ranges(MODEL, PEERS)
    historical = calculate_historical_multiple_ranges(MODEL)
    rows = prepare_football_field_ranges(
        [180_000, 220_000, 260_000, 300_000],
        trading,
        historical,
        125_000,
    )
    assert {row["group"] for row in rows} == {
        "DCF",
        "Trading Comps",
        "Historical",
        "Market",
    }
    assert all(row["low"] <= row["mid"] <= row["high"] for row in rows)


def test_reverse_dcf_solver_reconciles_to_market_price():
    result = solve_reverse_dcf_growth(
        MODEL,
        current_price=125_000,
        terminal_ebit_margin=0.162,
        non_operating_asset_realization=0.0,
    )
    recalculated = reverse_dcf_value_per_share(
        MODEL,
        result["revenue_cagr"],
        result["terminal_ebit_margin"],
        result["non_operating_asset_realization"],
    )
    assert recalculated == pytest.approx(125_000, abs=0.50)
    assert result["difference"] == pytest.approx(0, abs=0.50)
    assert result["reconciliation_status"] == "RECONCILED"
    assert result["wacc"] == pytest.approx(MODEL["WACC"]["WACC"])
    assert result["perpetual_growth"] == pytest.approx(
        MODEL["DCF"]["영구성장률"]
    )
    assert result["baseline_revenue_cagr"] > 0
    assert result["baseline_terminal_ebit_margin"] == pytest.approx(
        MODEL["전망"][-1]["영업이익률"]
    )


def test_reverse_dcf_exposes_non_operating_asset_credit_effect():
    no_credit = solve_reverse_dcf_growth(MODEL, 125_000, 0.162, 0.0)
    full_credit = solve_reverse_dcf_growth(MODEL, 125_000, 0.162, 1.0)
    assert full_credit["revenue_cagr"] < no_credit["revenue_cagr"]
