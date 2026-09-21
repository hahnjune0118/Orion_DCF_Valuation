from pathlib import Path

import pytest

from fcff_model import calculate_fcff
from orion_dcf import run_orion_dcf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"


@pytest.mark.parametrize(
    "ebit,tax_rate,depreciation,capex,change_in_nwc",
    [
        (100.0, 0.25, 10.0, 20.0, 5.0),
        (100.0, 0.25, 10.0, 20.0, -5.0),
        (0.0, 0.25, 0.0, 0.0, 0.0),
    ],
)
def test_fcff_formula_is_correct(
    ebit,
    tax_rate,
    depreciation,
    capex,
    change_in_nwc,
):
    result = calculate_fcff(
        ebit=ebit,
        tax_rate=tax_rate,
        depreciation=depreciation,
        capex=capex,
        change_in_nwc=change_in_nwc,
    )
    expected_nopat = ebit * (1 - tax_rate)
    expected_fcff = expected_nopat + depreciation - capex - change_in_nwc

    assert result["NOPAT"] == pytest.approx(expected_nopat)
    assert result["FCFF"] == pytest.approx(expected_fcff)


def test_working_capital_release_increases_fcff():
    outflow = calculate_fcff(100.0, 0.25, 10.0, 20.0, 5.0)["FCFF"]
    release = calculate_fcff(100.0, 0.25, 10.0, 20.0, -5.0)["FCFF"]
    assert release > outflow


def test_current_model_fcff_is_fdd_adjusted_and_reconciled():
    model = run_orion_dcf(EXCEL_PATH)
    expected = {
        2026: 269_051.075,
        2027: 318_693.548,
        2028: 532_375.101,
        2029: 535_014.336,
        2030: 562_920.607,
    }
    for row in model["전망"]:
        assert row["FCFF"] == pytest.approx(expected[row["연도"]], abs=0.001)
        assert row["FCFF"] == pytest.approx(row["FDD 조정 FCFF"], abs=1e-6)


def test_2028_working_capital_release_is_preserved_after_fdd_adjustment():
    model = run_orion_dcf(EXCEL_PATH)
    row_2028 = next(row for row in model["전망"] if row["연도"] == 2028)
    assert row_2028["NWC 증감"] < 0
