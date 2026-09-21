from pathlib import Path

import pytest
from openpyxl import load_workbook

from orion_dcf import run_orion_dcf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"
FORECAST_COLUMNS = ["F", "G", "H", "I", "J"]
DCF_COLUMNS = ["C", "D", "E", "F", "G"]


@pytest.fixture(scope="module")
def workbook():
    return load_workbook(EXCEL_PATH, data_only=True, read_only=True)


@pytest.fixture(scope="module")
def model():
    return run_orion_dcf(EXCEL_PATH)


def test_integrated_fdd_adjusted_forecast_reconciles(model, workbook):
    qoe = model["FDD"]["qoe"]

    for index, (schedule_col, dcf_col) in enumerate(
        zip(FORECAST_COLUMNS, DCF_COLUMNS, strict=True)
    ):
        year = 2026 + index
        row = model["전망"][index]

        raw_ebit = workbook["영업실적추정"][f"{schedule_col}17"].value
        raw_da = workbook["Capex_D&A"][f"{schedule_col}8"].value
        excel_capex = workbook["Capex_D&A"][f"{schedule_col}15"].value
        excel_nwc = workbook["NWC"][f"{schedule_col}19"].value
        excel_change_in_nwc = workbook["NWC"][f"{schedule_col}21"].value
        excel_fcff = workbook["DCF"][f"{dcf_col}15"].value

        assert row["연도"] == year
        assert row["EBIT"] == pytest.approx(
            raw_ebit + qoe["forecast_ebit_adjustment"][year], abs=1e-6
        )
        assert row["D&A"] == pytest.approx(
            raw_da + qoe["forecast_da_adjustment"][year], abs=1e-6
        )
        assert row["Capex"] == pytest.approx(excel_capex, abs=1e-6)
        assert row["NWC"] == pytest.approx(excel_nwc, abs=1e-6)
        assert row["NWC 증감"] == pytest.approx(excel_change_in_nwc, abs=1e-6)
        assert row["FCFF"] == pytest.approx(excel_fcff, abs=1e-6)
        assert row["FCFF"] == pytest.approx(
            row["NOPAT"] + row["D&A"] - row["Capex"] - row["NWC 증감"],
            abs=1e-6,
        )


def test_2026_nwc_reclassification_is_explicit(model):
    nwc = model["FDD"]["nwc"]
    assert nwc["capex_payable_reclassification"] == pytest.approx(13_687.0)
    assert nwc["applied_nwc_price_adjustment"] == pytest.approx(0.0)
