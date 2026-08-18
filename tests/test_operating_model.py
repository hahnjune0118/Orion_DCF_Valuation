from pathlib import Path

import pytest
from openpyxl import load_workbook

from forecast_model import (
    calculate_operating_profit,
    forecast_segment_revenue,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"

FORECAST_COLUMNS = ["F", "G", "H", "I", "J"]


@pytest.fixture(scope="module")
def workbook():
    return load_workbook(
        EXCEL_PATH,
        data_only=True,
        read_only=True,
    )


segment_cases = [
    # 구분, 과거재무제표 2025년 행, 가정 행, 매출액추정 행
    ("한국", 71, 7, 7),
    ("중국", 72, 8, 9),
    ("기타 국가", 73, 9, 11),
]


@pytest.mark.parametrize(
    "segment,historical_row,assumption_row,output_row",
    segment_cases,
)
def test_segment_revenue_forecast(
    workbook,
    segment,
    historical_row,
    assumption_row,
    output_row,
):
    base_revenue = workbook[
        "과거재무제표"
    ][f"F{historical_row}"].value

    growth_rates = [
        workbook["가정"][f"{col}{assumption_row}"].value
        for col in FORECAST_COLUMNS
    ]

    python_forecast = forecast_segment_revenue(
        base_revenue=base_revenue,
        growth_rates=growth_rates,
    )

    excel_forecast = [
        workbook["매출액추정"][f"{col}{output_row}"].value
        for col in FORECAST_COLUMNS
    ]

    for year, python_value, excel_value in zip(
        range(2026, 2031),
        python_forecast,
        excel_forecast,
    ):
        difference = python_value - excel_value

        assert abs(difference) < 0.000001, (
            f"{segment} {year}년 매출액 대사 실패: "
            f"Python={python_value:,.6f}, "
            f"Excel={excel_value:,.6f}, "
            f"차이={difference:,.10f}"
        )


def test_ebit_forecast(workbook):
    segment_forecasts = []

    for _, historical_row, assumption_row, _ in segment_cases:
        base_revenue = workbook[
            "과거재무제표"
        ][f"F{historical_row}"].value

        growth_rates = [
            workbook["가정"][f"{col}{assumption_row}"].value
            for col in FORECAST_COLUMNS
        ]

        segment_forecasts.append(
            forecast_segment_revenue(
                base_revenue=base_revenue,
                growth_rates=growth_rates,
            )
        )

    for index, col in enumerate(FORECAST_COLUMNS):
        year = 2026 + index

        consolidated_revenue = sum(
            segment[index]
            for segment in segment_forecasts
        )

        cost_of_sales_ratio = workbook["가정"][f"{col}13"].value
        selling_expense_ratio = workbook["가정"][f"{col}14"].value
        administrative_expense_ratio = workbook[
            "가정"
        ][f"{col}15"].value

        python_result = calculate_operating_profit(
            revenue=consolidated_revenue,
            cost_of_sales_ratio=cost_of_sales_ratio,
            selling_expense_ratio=selling_expense_ratio,
            administrative_expense_ratio=(
                administrative_expense_ratio
            ),
        )

        excel_revenue = workbook[
            "영업실적추정"
        ][f"{col}7"].value

        excel_ebit = workbook[
            "영업실적추정"
        ][f"{col}17"].value

        assert abs(
            python_result["매출액"] - excel_revenue
        ) < 0.000001, (
            f"{year}년 연결 매출액 대사 실패"
        )

        assert abs(
            python_result["EBIT"] - excel_ebit
        ) < 0.000001, (
            f"{year}년 EBIT 대사 실패: "
            f"Python={python_result['EBIT']:,.6f}, "
            f"Excel={excel_ebit:,.6f}"
        )

        assert 0 < python_result["영업이익률"] < 1