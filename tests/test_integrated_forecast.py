from pathlib import Path

import pytest
from openpyxl import load_workbook

from cash_flow_model import (
    calculate_capex_and_depreciation,
    calculate_nwc,
)
from fcff_model import calculate_fcff
from forecast_model import (
    calculate_operating_profit,
    forecast_segment_revenue,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"

FORECAST_COLUMNS = ["F", "G", "H", "I", "J"]
DCF_COLUMNS = ["C", "D", "E", "F", "G"]

SEGMENTS = [
    # 과거재무제표 행, 성장률 가정 행
    (71, 7),  # 한국
    (72, 8),  # 중국
    (73, 9),  # 기타 국가
]


@pytest.fixture(scope="module")
def workbook():
    return load_workbook(
        EXCEL_PATH,
        data_only=True,
        read_only=True,
    )


def test_integrated_fcff_forecast(workbook):
    historical = workbook["과거재무제표"]
    assumptions = workbook["가정"]

    # 2025년 공시자료로부터 기초 NWC를 직접 계산
    previous_nwc = (
        historical["F39"].value
        + historical["F40"].value
        + historical["F41"].value
        - historical["F56"].value
        - historical["F57"].value
        - historical["F58"].value
    )

    # 지역별 매출액 전망
    segment_forecasts = []

    for historical_row, assumption_row in SEGMENTS:
        base_revenue = historical[
            f"F{historical_row}"
        ].value

        growth_rates = [
            assumptions[f"{col}{assumption_row}"].value
            for col in FORECAST_COLUMNS
        ]

        segment_forecasts.append(
            forecast_segment_revenue(
                base_revenue=base_revenue,
                growth_rates=growth_rates,
            )
        )

    # 2026~2030년 통합 계산
    for index, (schedule_col, dcf_col) in enumerate(
        zip(FORECAST_COLUMNS, DCF_COLUMNS)
    ):
        year = 2026 + index

        revenue = sum(
            segment[index]
            for segment in segment_forecasts
        )

        operating_result = calculate_operating_profit(
            revenue=revenue,
            cost_of_sales_ratio=assumptions[
                f"{schedule_col}13"
            ].value,
            selling_expense_ratio=assumptions[
                f"{schedule_col}14"
            ].value,
            administrative_expense_ratio=assumptions[
                f"{schedule_col}15"
            ].value,
        )

        cost_of_sales_positive = (
            -operating_result["매출원가"]
        )

        nwc_result = calculate_nwc(
            revenue=revenue,
            cost_of_sales=cost_of_sales_positive,
            dso=assumptions[
                f"{schedule_col}22"
            ].value,
            inventory_days=assumptions[
                f"{schedule_col}23"
            ].value,
            dpo=assumptions[
                f"{schedule_col}24"
            ].value,
            other_operating_asset_ratio=assumptions[
                f"{schedule_col}25"
            ].value,
            other_operating_liability_ratio=assumptions[
                f"{schedule_col}26"
            ].value,
        )

        current_nwc = nwc_result["NWC"]
        change_in_nwc = current_nwc - previous_nwc

        investment_result = (
            calculate_capex_and_depreciation(
                revenue=revenue,
                depreciation_ratio=assumptions[
                    f"{schedule_col}17"
                ].value,
                maintenance_capex_ratio=assumptions[
                    f"{schedule_col}18"
                ].value,
                growth_capex=assumptions[
                    f"{schedule_col}19"
                ].value,
            )
        )

        fcff_result = calculate_fcff(
            ebit=operating_result["EBIT"],
            tax_rate=assumptions[
                f"{schedule_col}16"
            ].value,
            depreciation=investment_result["D&A"],
            capex=investment_result["총 Capex"],
            change_in_nwc=change_in_nwc,
        )

        # Excel 결과값은 검증 목적으로만 사용
        excel_nwc = workbook[
            "NWC"
        ][f"{schedule_col}19"].value

        excel_change_in_nwc = workbook[
            "NWC"
        ][f"{schedule_col}21"].value

        excel_depreciation = workbook[
            "Capex_D&A"
        ][f"{schedule_col}8"].value

        excel_capex = workbook[
            "Capex_D&A"
        ][f"{schedule_col}15"].value

        excel_fcff = workbook[
            "DCF"
        ][f"{dcf_col}15"].value

        tolerance = 0.000001

        assert abs(
            current_nwc - excel_nwc
        ) < tolerance, f"{year}년 NWC 대사 실패"

        assert abs(
            change_in_nwc - excel_change_in_nwc
        ) < tolerance, f"{year}년 NWC 증감 대사 실패"

        assert abs(
            investment_result["D&A"]
            - excel_depreciation
        ) < tolerance, f"{year}년 D&A 대사 실패"

        assert abs(
            investment_result["총 Capex"]
            - excel_capex
        ) < tolerance, f"{year}년 Capex 대사 실패"

        assert abs(
            fcff_result["FCFF"]
            - excel_fcff
        ) < tolerance, (
            f"{year}년 FCFF 대사 실패: "
            f"Python={fcff_result['FCFF']:,.6f}, "
            f"Excel={excel_fcff:,.6f}"
        )

        previous_nwc = current_nwc