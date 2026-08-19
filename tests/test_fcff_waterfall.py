from copy import deepcopy
from pathlib import Path

import pytest

from dashboard_components import (
    DISPLAY_UNIT,
    FCFF_RECONCILIATION_TOLERANCE,
    MODEL_UNIT,
    build_fcff_waterfall_figure,
    prepare_fcff_waterfall_data,
)
from orion_dcf import run_orion_dcf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"


@pytest.fixture(scope="module")
def forecast_rows():
    return run_orion_dcf(EXCEL_PATH)["전망"]


@pytest.mark.parametrize("year", range(2026, 2031))
def test_all_forecast_years_reconcile_to_model_fcff(forecast_rows, year):
    row = next(item for item in forecast_rows if item["연도"] == year)

    result = prepare_fcff_waterfall_data(row)

    expected_fcff = (
        row["NOPAT"]
        + row["D&A"]
        - row["Capex"]
        - row["NWC 증감"]
    )
    assert result["연도"] == year
    assert result["영업관련 법인세"] == pytest.approx(
        row["EBIT"] - row["NOPAT"], abs=1e-6
    )
    assert result["재계산 FCFF"] == pytest.approx(
        expected_fcff, abs=FCFF_RECONCILIATION_TOLERANCE
    )
    assert result["FCFF"] == pytest.approx(
        row["FCFF"], abs=FCFF_RECONCILIATION_TOLERANCE
    )
    assert abs(result["대사 차이"]) <= FCFF_RECONCILIATION_TOLERANCE


def test_units_are_explicit_and_source_amounts_remain_in_millions(
    forecast_rows,
):
    row = forecast_rows[0]
    result = prepare_fcff_waterfall_data(row)

    assert result["모델 단위"] == MODEL_UNIT == "백만원"
    assert result["표시 단위"] == DISPLAY_UNIT == "십억원"
    assert result["EBIT"] == row["EBIT"]


def test_capex_and_positive_nwc_change_are_cash_outflows(forecast_rows):
    row_2026 = next(
        item for item in forecast_rows if item["연도"] == 2026
    )
    result = prepare_fcff_waterfall_data(row_2026)
    effects = result["Waterfall 효과"]

    assert row_2026["NWC 증감"] > 0
    assert effects["Capex"] == -row_2026["Capex"]
    assert effects["NWC 증감"] == -row_2026["NWC 증감"]
    assert effects["Capex"] < 0
    assert effects["NWC 증감"] < 0


@pytest.mark.parametrize("year", [2028, 2030])
def test_negative_nwc_change_is_a_cash_inflow(forecast_rows, year):
    row = next(item for item in forecast_rows if item["연도"] == year)
    result = prepare_fcff_waterfall_data(row)

    assert row["NWC 증감"] < 0
    assert result["NWC 현금흐름 효과"] == -row["NWC 증감"]
    assert result["Waterfall 효과"]["NWC 증감"] > 0


@pytest.mark.parametrize(
    "field",
    ["EBIT", "NOPAT", "D&A", "Capex", "NWC 증감", "FCFF"],
)
def test_missing_required_field_is_rejected(forecast_rows, field):
    row = dict(forecast_rows[0])
    del row[field]

    with pytest.raises(KeyError, match="필수 열 누락"):
        prepare_fcff_waterfall_data(row)


@pytest.mark.parametrize("year", [2025, 2031, 2026.5])
def test_invalid_or_unsupported_year_is_rejected(forecast_rows, year):
    row = dict(forecast_rows[0])
    row["연도"] = year

    with pytest.raises(ValueError, match="연도"):
        prepare_fcff_waterfall_data(row)


@pytest.mark.parametrize("invalid_value", [None, "not-a-number", float("nan")])
def test_invalid_financial_value_is_rejected(forecast_rows, invalid_value):
    row = dict(forecast_rows[0])
    row["EBIT"] = invalid_value

    with pytest.raises((TypeError, ValueError), match="EBIT"):
        prepare_fcff_waterfall_data(row)


def test_input_row_is_not_mutated(forecast_rows):
    row = deepcopy(forecast_rows[0])
    original = deepcopy(row)

    prepare_fcff_waterfall_data(row)

    assert row == original


def test_reconciliation_failure_is_rejected(forecast_rows):
    row = dict(forecast_rows[0])
    row["FCFF"] += 1.0

    with pytest.raises(ValueError, match="FCFF 대사 실패"):
        prepare_fcff_waterfall_data(row)


def test_waterfall_figure_uses_expected_order_signs_and_unit(forecast_rows):
    result = prepare_fcff_waterfall_data(forecast_rows[0])
    original = deepcopy(result)

    figure = build_fcff_waterfall_figure(result)
    trace = figure.data[0]

    assert list(trace.measure) == [
        "absolute",
        "relative",
        "total",
        "relative",
        "relative",
        "relative",
        "total",
    ]
    assert list(trace.x) == [
        "EBIT",
        "영업관련<br>법인세",
        "NOPAT",
        "D&A",
        "Capex",
        "NWC<br>증감",
        "FCFF",
    ]
    assert trace.y[1] < 0
    assert trace.y[3] > 0
    assert trace.y[4] < 0
    assert trace.y[5] < 0
    assert figure.layout.yaxis.title.text == "십억원"
    assert result == original
