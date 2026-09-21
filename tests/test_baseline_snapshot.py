import hashlib
from pathlib import Path

import pytest

from orion_dcf import run_orion_dcf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"

# Phase 1 validated FDD workbook copied into data/raw/orion_dcf.xlsx.
EXPECTED_WORKBOOK_SHA256 = (
    "f4015e03f47c116c04d51b032d1f1021c7a7186492bac56b4130713303b0251d"
)
EXPECTED_WACC = 0.09477625
EXPECTED_FCFF = {
    2026: 269_051.075,
    2027: 318_693.548,
    2028: 532_375.101,
    2029: 535_014.336,
    2030: 562_920.607,
}
EXPECTED_DCF = {
    "추정기간 FCFF 현재가치": 1_647_790.600,
    "기업가치": 6_530_454.168,
}
EXPECTED_EQUITY_VALUE = 9_415_024.166
EXPECTED_VALUE_PER_SHARE = 238_181.453


@pytest.fixture(scope="module")
def current_model():
    return run_orion_dcf(EXCEL_PATH)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_fdd_baseline_input_fingerprint_is_current():
    assert _sha256(EXCEL_PATH) == EXPECTED_WORKBOOK_SHA256
    assert EXCEL_PATH.stat().st_size > 0


def test_fdd_baseline_forecast_is_current(current_model):
    rows = current_model["전망"]
    assert [row["연도"] for row in rows] == [2026, 2027, 2028, 2029, 2030]

    fdd_required_keys = {
        "FDD 조정 EBIT",
        "FDD 조정 D&A",
        "FDD 조정 Capex",
        "FDD 조정 NWC",
        "FDD 조정 NWC 증감",
        "FDD 조정 FCFF",
        "FDD EBIT 조정액",
        "FDD D&A 조정액",
        "Lease capex",
    }
    for row in rows:
        year = row["연도"]
        assert fdd_required_keys <= row.keys()
        assert row["FCFF"] == pytest.approx(EXPECTED_FCFF[year], abs=0.001)
        assert row["FCFF"] == pytest.approx(row["FDD 조정 FCFF"], abs=1e-6)


def test_fdd_baseline_valuation_is_current(current_model):
    assert current_model["WACC"]["WACC"] == pytest.approx(
        EXPECTED_WACC, abs=1e-12
    )
    assert current_model["DCF"]["추정기간 FCFF 현재가치"] == pytest.approx(
        EXPECTED_DCF["추정기간 FCFF 현재가치"], abs=0.001
    )
    assert current_model["DCF"]["기업가치"] == pytest.approx(
        EXPECTED_DCF["기업가치"], abs=0.001
    )
    assert current_model["지분가치"]["지분가치"] == pytest.approx(
        EXPECTED_EQUITY_VALUE, abs=0.001
    )
    assert current_model["지분가치"]["주당 내재가치"] == pytest.approx(
        EXPECTED_VALUE_PER_SHARE, abs=0.001
    )
