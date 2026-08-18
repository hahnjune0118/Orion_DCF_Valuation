from pathlib import Path

from orion_dcf import run_orion_dcf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"


def test_business_scenario_direction():
    base_case = run_orion_dcf(EXCEL_PATH)

    upside_case = run_orion_dcf(
        EXCEL_PATH,
        revenue_growth_adjustment=0.01,
        ebit_margin_adjustment=0.01,
        wacc_adjustment=-0.005,
        terminal_growth_adjustment=0.005,
    )

    downside_case = run_orion_dcf(
        EXCEL_PATH,
        revenue_growth_adjustment=-0.01,
        ebit_margin_adjustment=-0.01,
        wacc_adjustment=0.005,
        terminal_growth_adjustment=-0.005,
    )

    base_value = base_case[
        "지분가치"
    ]["주당 내재가치"]

    upside_value = upside_case[
        "지분가치"
    ]["주당 내재가치"]

    downside_value = downside_case[
        "지분가치"
    ]["주당 내재가치"]

    assert upside_value > base_value
    assert base_value > downside_value

    assert (
        upside_case["전망"][-1]["매출액"]
        > base_case["전망"][-1]["매출액"]
        > downside_case["전망"][-1]["매출액"]
    )

    assert (
        upside_case["전망"][-1]["영업이익률"]
        > base_case["전망"][-1]["영업이익률"]
        > downside_case["전망"][-1]["영업이익률"]
    )

    assert (
        upside_case["WACC"]["WACC"]
        < base_case["WACC"]["WACC"]
        < downside_case["WACC"]["WACC"]
    )