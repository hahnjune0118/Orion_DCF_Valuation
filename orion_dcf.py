from pathlib import Path

from openpyxl import load_workbook

from cash_flow_model import (
    calculate_capex_and_depreciation,
    calculate_nwc,
)
from equity_bridge import calculate_equity_bridge
from fcff_model import calculate_fcff
from forecast_model import (
    calculate_operating_profit,
    forecast_segment_revenue,
)
from valuation_model import (
    calculate_dcf,
    calculate_wacc,
)


FORECAST_COLUMNS = ["F", "G", "H", "I", "J"]

SEGMENTS = {
    "한국": {
        "historical_row": 71,
        "assumption_row": 7,
    },
    "중국": {
        "historical_row": 72,
        "assumption_row": 8,
    },
    "기타 국가": {
        "historical_row": 73,
        "assumption_row": 9,
    },
}


def run_orion_dcf(
    excel_path,
    revenue_growth_adjustment=0.0,
    ebit_margin_adjustment=0.0,
    wacc_adjustment=0.0,
    terminal_growth_adjustment=0.0,
):
    workbook = load_workbook(
        excel_path,
        data_only=True,
        read_only=True,
    )

    historical = workbook["과거재무제표"]
    assumptions = workbook["가정"]

    # 1. 지역별 매출액 전망
    segment_forecasts = {}

    for segment, settings in SEGMENTS.items():
        base_revenue = historical[
            f"F{settings['historical_row']}"
        ].value

        growth_rates = [
            (
                assumptions[
                    f"{col}{settings['assumption_row']}"
                ].value
                + revenue_growth_adjustment
            )
            for col in FORECAST_COLUMNS
        ]

        segment_forecasts[segment] = (
            forecast_segment_revenue(
                base_revenue=base_revenue,
                growth_rates=growth_rates,
            )
        )

    # 2. 2025년 기초 NWC
    previous_nwc = (
        historical["F39"].value
        + historical["F40"].value
        + historical["F41"].value
        - historical["F56"].value
        - historical["F57"].value
        - historical["F58"].value
    )

    forecast_results = []

    # 3. 영업실적 및 FCFF 전망
    for index, col in enumerate(FORECAST_COLUMNS):
        year = 2026 + index

        segment_revenue = {
            segment: values[index]
            for segment, values
            in segment_forecasts.items()
        }

        revenue = sum(segment_revenue.values())

        operating_result = calculate_operating_profit(
            revenue=revenue,
            cost_of_sales_ratio=assumptions[
                f"{col}13"
            ].value,
            selling_expense_ratio=assumptions[
                f"{col}14"
            ].value,
            administrative_expense_ratio=assumptions[
                f"{col}15"
            ].value,
        )

        operating_result["EBIT"] = (
            operating_result["EBIT"]
            + revenue * ebit_margin_adjustment
        )

        operating_result["영업이익률"] = (
            operating_result["영업이익률"]
            + ebit_margin_adjustment
        )

        nwc_result = calculate_nwc(
            revenue=revenue,
            cost_of_sales=(
                -operating_result["매출원가"]
            ),
            dso=assumptions[f"{col}22"].value,
            inventory_days=assumptions[
                f"{col}23"
            ].value,
            dpo=assumptions[f"{col}24"].value,
            other_operating_asset_ratio=assumptions[
                f"{col}25"
            ].value,
            other_operating_liability_ratio=assumptions[
                f"{col}26"
            ].value,
        )

        current_nwc = nwc_result["NWC"]
        change_in_nwc = current_nwc - previous_nwc

        investment_result = (
            calculate_capex_and_depreciation(
                revenue=revenue,
                depreciation_ratio=assumptions[
                    f"{col}17"
                ].value,
                maintenance_capex_ratio=assumptions[
                    f"{col}18"
                ].value,
                growth_capex=assumptions[
                    f"{col}19"
                ].value,
            )
        )

        fcff_result = calculate_fcff(
            ebit=operating_result["EBIT"],
            tax_rate=assumptions[
                f"{col}16"
            ].value,
            depreciation=investment_result["D&A"],
            capex=investment_result["총 Capex"],
            change_in_nwc=change_in_nwc,
        )

        forecast_results.append(
            {
                "연도": year,
                "한국 매출액": segment_revenue["한국"],
                "중국 매출액": segment_revenue["중국"],
                "기타 국가 매출액": (
                    segment_revenue["기타 국가"]
                ),
                "매출액": revenue,
                "EBIT": operating_result["EBIT"],
                "영업이익률": operating_result[
                    "영업이익률"
                ],
                "NWC": current_nwc,
                "NWC 증감": change_in_nwc,
                "D&A": investment_result["D&A"],
                "Capex": investment_result["총 Capex"],
                "NOPAT": fcff_result["NOPAT"],
                "FCFF": fcff_result["FCFF"],
            }
        )

        previous_nwc = current_nwc

    # 4. WACC
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

    base_wacc = wacc_result["WACC"]

    wacc_result["기준 WACC"] = base_wacc

    # Preserve the inputs already used above so downstream review tools can
    # reproduce the WACC calculation without reopening or mutating Excel.
    wacc_result["구성요소"] = {
        "무위험수익률": assumptions["C30"].value,
        "주식시장위험프리미엄": assumptions["C31"].value,
        "베타": assumptions["C32"].value,
        "국가위험프리미엄": assumptions["C33"].value,
        "세전 타인자본비용": assumptions["C34"].value,
        "법인세율": assumptions["F16"].value,
        "자기자본 비중": assumptions["C35"].value,
        "타인자본 비중": assumptions["C36"].value,
        "WACC 조정": wacc_adjustment,
    }

    wacc_result["WACC"] = (
        base_wacc + wacc_adjustment
    )

    # 5. DCF 기업가치
    base_terminal_growth_rate = assumptions[
        "C37"
    ].value

    scenario_terminal_growth_rate = (
        base_terminal_growth_rate
        + terminal_growth_adjustment
    )

    dcf_result = calculate_dcf(
        fcff_forecast=[
            result["FCFF"]
            for result in forecast_results
        ],
        wacc=wacc_result["WACC"],
        terminal_growth_rate=(
            scenario_terminal_growth_rate
        ),
    )
    dcf_result["영구성장률"] = scenario_terminal_growth_rate
    dcf_result["명시적 전망기간"] = len(forecast_results)

    # 6. 기업가치에서 지분가치로 조정
    equity_result = calculate_equity_bridge(
        enterprise_value=dcf_result["기업가치"],
        cash_and_cash_equivalents=historical[
            "F35"
        ].value,
        revenue=historical["F7"].value,
        required_operating_cash_ratio=assumptions[
            "C39"
        ].value,
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
    equity_result["기준주가"] = historical["F68"].value

    return {
        "기준연도": {
            "연도": 2025,
            "매출액": historical["F7"].value,
            "EBIT": historical["F12"].value,
            "D&A": historical["F27"].value,
        },
        "지역별 매출액": segment_forecasts,
        "전망": forecast_results,
        "WACC": wacc_result,
        "DCF": dcf_result,
        "지분가치": equity_result,
    }


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    excel_path = (
        project_root
        / "data"
        / "raw"
        / "orion_dcf.xlsx"
    )

    model = run_orion_dcf(excel_path)

    print("\n[오리온 DCF 전망]")
    print(
        f"{'연도':<6}"
        f"{'매출액':>16}"
        f"{'EBIT':>16}"
        f"{'FCFF':>16}"
    )

    for result in model["전망"]:
        print(
            f"{result['연도']:<6}"
            f"{result['매출액']:>16,.0f}"
            f"{result['EBIT']:>16,.0f}"
            f"{result['FCFF']:>16,.0f}"
        )

    print("\n[가치평가 결과]")
    print(
        f"WACC: "
        f"{model['WACC']['WACC']:.2%}"
    )
    print(
        f"기업가치: "
        f"{model['DCF']['기업가치']:,.0f}백만원"
    )
    print(
        f"지분가치: "
        f"{model['지분가치']['지분가치']:,.0f}백만원"
    )
    print(
        f"주당 내재가치: "
        f"{model['지분가치']['주당 내재가치']:,.0f}원"
    )
