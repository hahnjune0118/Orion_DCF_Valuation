from pathlib import Path

import pytest
from openpyxl import load_workbook

from equity_bridge import calculate_equity_bridge


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"


@pytest.fixture(scope="module")
def workbook():
    return load_workbook(
        EXCEL_PATH,
        data_only=True,
        read_only=True,
    )


def test_equity_bridge_reconciles(workbook):
    historical = workbook["과거재무제표"]
    assumptions = workbook["가정"]
    bridge = workbook["기업가치_지분가치"]

    result = calculate_equity_bridge(
        enterprise_value=workbook["DCF"]["C29"].value,
        cash_and_cash_equivalents=historical["F35"].value,
        revenue=historical["F7"].value,
        required_operating_cash_ratio=assumptions["C39"].value,
        short_term_financial_instruments=historical[
            "F36"
        ].value,
        current_fvtpl_financial_assets=historical[
            "F37"
        ].value,
        ligachem_market_value=historical["F50"].value,
        other_associates_and_jvs=(
            historical["F48"].value
            - historical["F49"].value
        ),
        non_current_fvoci_financial_assets=historical[
            "F51"
        ].value,
        investment_property_fair_value=historical[
            "F46"
        ].value,
        financial_debt=historical["F53"].value,
        lease_liabilities=(
            historical["F54"].value
            + historical["F55"].value
        ),
        non_controlling_interests=historical[
            "F59"
        ].value,
        shares_outstanding_millions=(
            historical["F67"].value / 1_000_000
        ),
        current_share_price=historical["F68"].value,
    )

    tolerance = 0.001

    assert abs(
        result["필요 영업현금"]
        - abs(bridge["C9"].value)
    ) < tolerance

    assert abs(
        result["초과현금"]
        - bridge["C10"].value
    ) < tolerance

    assert abs(
        result["비영업자산 합계"]
        - bridge["C17"].value
    ) < tolerance

    assert abs(
        -result["차감항목 합계"]
        - bridge["C23"].value
    ) < tolerance

    assert abs(
        result["순비영업 조정액"]
        - bridge["C26"].value
    ) < tolerance

    assert abs(
        result["지분가치"]
        - bridge["C27"].value
    ) < tolerance

    assert abs(
        result["주당 내재가치"]
        - bridge["C29"].value
    ) < 0.001

    assert abs(
        result["내재 상승여력"]
        - bridge["C31"].value
    ) < 0.000001


def test_share_count_must_be_positive():
    with pytest.raises(
        ValueError,
        match="유통주식수는 0보다 커야 합니다",
    ):
        calculate_equity_bridge(
            enterprise_value=1_000,
            cash_and_cash_equivalents=100,
            revenue=1_000,
            required_operating_cash_ratio=0.02,
            short_term_financial_instruments=0,
            current_fvtpl_financial_assets=0,
            ligachem_market_value=0,
            other_associates_and_jvs=0,
            non_current_fvoci_financial_assets=0,
            investment_property_fair_value=0,
            financial_debt=0,
            lease_liabilities=0,
            non_controlling_interests=0,
            shares_outstanding_millions=0,
        )