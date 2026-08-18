from pathlib import Path

from openpyxl import load_workbook

from orion_dcf import run_orion_dcf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"


def test_end_to_end_dcf_reconciles():
    model = run_orion_dcf(EXCEL_PATH)

    workbook = load_workbook(
        EXCEL_PATH,
        data_only=True,
        read_only=True,
    )

    excel_wacc = workbook["WACC"]["C20"].value
    excel_enterprise_value = workbook["DCF"]["C29"].value
    excel_equity_value = workbook[
        "기업가치_지분가치"
    ]["C27"].value
    excel_value_per_share = workbook[
        "기업가치_지분가치"
    ]["C29"].value

    tolerance = 0.001

    assert len(model["전망"]) == 5

    assert model["전망"][0]["연도"] == 2026
    assert model["전망"][-1]["연도"] == 2030

    assert abs(
        model["WACC"]["WACC"] - excel_wacc
    ) < 0.000000000001

    assert abs(
        model["DCF"]["기업가치"]
        - excel_enterprise_value
    ) < tolerance

    assert abs(
        model["지분가치"]["지분가치"]
        - excel_equity_value
    ) < tolerance

    assert abs(
        model["지분가치"]["주당 내재가치"]
        - excel_value_per_share
    ) < 0.001

    assert round(
        model["지분가치"]["주당 내재가치"]
    ) == 244_708