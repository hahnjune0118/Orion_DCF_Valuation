from pathlib import Path

import pytest
from openpyxl import load_workbook

from fcff_model import calculate_fcff


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"


@pytest.fixture(scope="module")
def workbook():
    return load_workbook(
        EXCEL_PATH,
        data_only=True,
        read_only=True,
    )


forecast_periods = [
    (2026, "F", "C"),
    (2027, "G", "D"),
    (2028, "H", "E"),
    (2029, "I", "F"),
    (2030, "J", "G"),
]


@pytest.mark.parametrize(
    "year,schedule_col,dcf_col",
    forecast_periods,
)
def test_fcff_reconciles(
    workbook,
    year,
    schedule_col,
    dcf_col,
):
    ebit = workbook["영업실적추정"][f"{schedule_col}17"].value
    tax_rate = workbook["DCF"][f"{dcf_col}9"].value
    depreciation = workbook["Capex_D&A"][f"{schedule_col}8"].value
    capex = workbook["Capex_D&A"][f"{schedule_col}15"].value
    change_in_nwc = workbook["NWC"][f"{schedule_col}21"].value

    excel_fcff = workbook["DCF"][f"{dcf_col}15"].value

    result = calculate_fcff(
        ebit=ebit,
        tax_rate=tax_rate,
        depreciation=depreciation,
        capex=capex,
        change_in_nwc=change_in_nwc,
    )

    python_fcff = result["FCFF"]
    difference = python_fcff - excel_fcff

    assert abs(difference) < 0.000001, (
        f"{year}년 FCFF 대사 실패: "
        f"Python={python_fcff:,.6f}, "
        f"Excel={excel_fcff:,.6f}, "
        f"차이={difference:,.10f}"
    )

    assert 0 <= tax_rate <= 1
    assert result["NOPAT"] <= ebit


def test_2028_working_capital_release(workbook):
    change_in_nwc_2028 = workbook["NWC"]["H21"].value

    assert change_in_nwc_2028 < 0, (
        "2028년에는 NWC 감소에 따른 현금 회수가 예상되어야 합니다."
    )