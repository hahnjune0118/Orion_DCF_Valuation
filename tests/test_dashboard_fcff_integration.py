from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest

from dashboard_components import (
    build_fcff_waterfall_figure,
    build_fcff_waterfall_insight,
    calculate_fcff_waterfall_kpis,
    prepare_fcff_waterfall_data,
    select_forecast_row,
)
from orion_dcf import run_orion_dcf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"


@pytest.fixture(scope="module")
def forecast_df():
    model = run_orion_dcf(EXCEL_PATH)
    return pd.DataFrame(model["전망"])


@pytest.mark.parametrize("year", range(2026, 2031))
def test_each_dropdown_year_selects_one_copied_row(forecast_df, year):
    original = forecast_df.copy(deep=True)

    selected = select_forecast_row(forecast_df, year)

    assert selected["연도"] == year
    assert isinstance(selected, dict)
    pd.testing.assert_frame_equal(forecast_df, original)


def test_missing_and_duplicate_years_are_rejected(forecast_df):
    with pytest.raises(ValueError, match="현재 0개"):
        select_forecast_row(forecast_df.iloc[:-1], 2030)

    duplicated = pd.concat(
        [forecast_df, forecast_df.loc[forecast_df["연도"] == 2026]],
        ignore_index=True,
    )
    with pytest.raises(ValueError, match="현재 2개"):
        select_forecast_row(duplicated, 2026)


@pytest.mark.parametrize("year", range(2026, 2031))
def test_selected_year_matches_figure_title_and_kpis(forecast_df, year):
    selected = select_forecast_row(forecast_df, year)
    data = prepare_fcff_waterfall_data(selected)
    kpis = calculate_fcff_waterfall_kpis(data)
    figure = build_fcff_waterfall_figure(data)

    assert f"{year}E EBIT" in figure.layout.title.text
    assert kpis["연도"] == year
    assert kpis["EBIT"] == pytest.approx(selected["EBIT"] / 1_000)
    assert kpis["NOPAT"] == pytest.approx(selected["NOPAT"] / 1_000)
    assert kpis["FCFF"] == pytest.approx(selected["FCFF"] / 1_000)
    assert kpis["현금전환율"] == pytest.approx(
        selected["FCFF"] / selected["EBIT"]
    )
    assert data["재계산 FCFF"] == pytest.approx(
        selected["FCFF"], abs=1e-6
    )


def test_2026_nwc_is_cash_outflow_in_data_and_insight(forecast_df):
    selected = select_forecast_row(forecast_df, 2026)
    data = prepare_fcff_waterfall_data(selected)
    kpis = calculate_fcff_waterfall_kpis(data)
    insight = build_fcff_waterfall_insight(data, kpis)

    assert data["NWC 증감"] > 0
    assert data["NWC 현금흐름 효과"] < 0
    assert "현금유출로 작용" in insight


@pytest.mark.parametrize("year", [2028, 2030])
def test_nwc_release_is_cash_inflow_in_data_and_insight(
    forecast_df,
    year,
):
    selected = select_forecast_row(forecast_df, year)
    data = prepare_fcff_waterfall_data(selected)
    kpis = calculate_fcff_waterfall_kpis(data)
    insight = build_fcff_waterfall_insight(data, kpis)

    assert data["NWC 증감"] < 0
    assert data["NWC 현금흐름 효과"] > 0
    assert "운전자본 회수가 현금유입으로 작용" in insight


def test_integration_helpers_do_not_mutate_inputs(forecast_df):
    selected = select_forecast_row(forecast_df, 2027)
    original = deepcopy(selected)
    data = prepare_fcff_waterfall_data(selected)
    original_data = deepcopy(data)

    kpis = calculate_fcff_waterfall_kpis(data)
    build_fcff_waterfall_insight(data, kpis)
    build_fcff_waterfall_figure(data)

    assert selected == original
    assert data == original_data
