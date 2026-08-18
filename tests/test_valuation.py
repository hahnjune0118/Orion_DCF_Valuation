from pathlib import Path

import pytest
from openpyxl import load_workbook

from valuation_model import (
    calculate_dcf,
    calculate_wacc,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"


@pytest.fixture(scope="module")
def workbook():
    return load_workbook(
        EXCEL_PATH,
        data_only=True,
        read_only=True,
    )


def test_wacc_reconciles(workbook):
    assumptions = workbook["가정"]

    result = calculate_wacc(
        risk_free_rate=assumptions["C30"].value,
        equity_risk_premium=assumptions["C31"].value,
        beta=assumptions["C32"].value,
        country_risk_premium=assumptions["C33"].value,
        pre_tax_cost_of_debt=assumptions["C34"].value,
        tax_rate=assumptions["F16"].value,
        equity_weight=assumptions["C35"].value,
        debt_weight=assumptions["C36"].value,
    )

    excel_wacc = workbook["WACC"]["C20"].value

    assert abs(
        result["WACC"] - excel_wacc
    ) < 0.000000000001

    assert abs(
        result["자본구조 비중 합계"] - 1
    ) < 0.000001


def test_dcf_reconciles(workbook):
    dcf_sheet = workbook["DCF"]
    assumptions = workbook["가정"]

    fcff_forecast = [
        dcf_sheet[f"{col}15"].value
        for col in ["C", "D", "E", "F", "G"]
    ]

    wacc_result = calculate_wacc(
        risk_free_rate=assumptions["C30"].value,
        equity_risk_premium=assumptions["C31"].value,
        beta=assumptions["C32"].value,
        country_risk_premium=assumptions["C33"].value,
        pre_tax_cost_of_debt=assumptions["C34"].value,
        tax_rate=assumptions["F16"].value,
        equity_weight=assumptions["C35"].value,
        debt_weight=assumptions["C36"].value,
    )

    result = calculate_dcf(
        fcff_forecast=fcff_forecast,
        wacc=wacc_result["WACC"],
        terminal_growth_rate=assumptions["C37"].value,
    )

    tolerance = 0.001

    assert abs(
        result["추정기간 FCFF 현재가치"]
        - dcf_sheet["C28"].value
    ) < tolerance

    assert abs(
        result["계속기업가치"]
        - dcf_sheet["C26"].value
    ) < tolerance

    assert abs(
        result["계속기업가치 현재가치"]
        - dcf_sheet["C27"].value
    ) < tolerance

    assert abs(
        result["기업가치"]
        - dcf_sheet["C29"].value
    ) < tolerance

    assert abs(
        result["계속기업가치 비중"]
        - dcf_sheet["C30"].value
    ) < 0.000001


def test_wacc_must_exceed_terminal_growth():
    with pytest.raises(
        ValueError,
        match="WACC는 영구성장률보다 커야 합니다",
    ):
        calculate_dcf(
            fcff_forecast=[100, 105, 110],
            wacc=0.02,
            terminal_growth_rate=0.02,
        )