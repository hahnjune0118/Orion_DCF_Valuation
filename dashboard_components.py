"""Reusable, testable components for the Orion valuation dashboard.

The core valuation model stores monetary amounts in KRW millions.  Dashboard
figures may convert those amounts for presentation, but this module never
changes the source model values.
"""

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite

import plotly.graph_objects as go


MODEL_UNIT = "백만원"
DISPLAY_UNIT = "십억원"
MODEL_TO_DISPLAY_DIVISOR = 1_000.0
FCFF_RECONCILIATION_TOLERANCE = 1e-6
SUPPORTED_FORECAST_YEARS = frozenset(range(2026, 2031))

REQUIRED_FCFF_FIELDS = (
    "연도",
    "EBIT",
    "NOPAT",
    "D&A",
    "Capex",
    "NWC 증감",
    "FCFF",
)


def _finite_number(row: Mapping[str, object], field: str) -> float:
    value = row[field]
    if isinstance(value, bool):
        raise TypeError(f"{field}은(는) 숫자여야 합니다.")

    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{field}은(는) 숫자여야 합니다.") from exc

    if not isfinite(numeric_value):
        raise ValueError(f"{field}은(는) 유한한 숫자여야 합니다.")
    return numeric_value


def prepare_fcff_waterfall_data(
    forecast_row: Mapping[str, object],
) -> dict[str, object]:
    """Prepare one forecast year for the EBIT-to-FCFF waterfall.

    Data contract
    -------------
    * Source monetary amounts are KRW millions.
    * Operating tax = EBIT - NOPAT.
    * Recalculated FCFF = NOPAT + D&A - Capex - change in NWC.
    * A positive change in NWC is a cash outflow; a negative change is a
      cash inflow.  Therefore its waterfall cash-flow effect is ``-change``.

    The supplied mapping is read only and is never mutated.
    """

    if not isinstance(forecast_row, Mapping):
        raise TypeError("forecast_row는 열 이름을 키로 갖는 매핑이어야 합니다.")

    missing_fields = [
        field for field in REQUIRED_FCFF_FIELDS if field not in forecast_row
    ]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise KeyError(f"FCFF Waterfall 필수 열 누락: {missing}")

    year_value = _finite_number(forecast_row, "연도")
    if not year_value.is_integer():
        raise ValueError("연도는 정수여야 합니다.")
    year = int(year_value)
    if year not in SUPPORTED_FORECAST_YEARS:
        raise ValueError(
            "지원하지 않는 전망 연도입니다: "
            f"{year}. 지원 범위는 2026~2030년입니다."
        )

    ebit = _finite_number(forecast_row, "EBIT")
    nopat = _finite_number(forecast_row, "NOPAT")
    depreciation = _finite_number(forecast_row, "D&A")
    capex = _finite_number(forecast_row, "Capex")
    change_in_nwc = _finite_number(forecast_row, "NWC 증감")
    model_fcff = _finite_number(forecast_row, "FCFF")

    operating_tax = ebit - nopat
    nwc_cash_flow_effect = -change_in_nwc
    recalculated_fcff = (
        nopat + depreciation - capex - change_in_nwc
    )
    reconciliation_difference = recalculated_fcff - model_fcff

    if abs(reconciliation_difference) > FCFF_RECONCILIATION_TOLERANCE:
        raise ValueError(
            "FCFF 대사 실패: "
            f"재계산={recalculated_fcff:,.6f}{MODEL_UNIT}, "
            f"모델={model_fcff:,.6f}{MODEL_UNIT}, "
            f"차이={reconciliation_difference:,.6f}{MODEL_UNIT}"
        )

    waterfall_effects = {
        "EBIT": ebit,
        "영업관련 법인세": -operating_tax,
        "NOPAT": nopat,
        "D&A": depreciation,
        "Capex": -capex,
        "NWC 증감": nwc_cash_flow_effect,
        "FCFF": model_fcff,
    }

    return {
        "연도": year,
        "모델 단위": MODEL_UNIT,
        "표시 단위": DISPLAY_UNIT,
        "EBIT": ebit,
        "영업관련 법인세": operating_tax,
        "NOPAT": nopat,
        "D&A": depreciation,
        "Capex": capex,
        "NWC 증감": change_in_nwc,
        "NWC 현금흐름 효과": nwc_cash_flow_effect,
        "FCFF": model_fcff,
        "재계산 FCFF": recalculated_fcff,
        "대사 차이": reconciliation_difference,
        "Waterfall 효과": waterfall_effects,
    }


def _signed_amount(value: float) -> str:
    if value > 0:
        return f"+{value:,.1f}"
    return f"{value:,.1f}"


def build_fcff_waterfall_figure(
    waterfall_data: Mapping[str, object],
) -> go.Figure:
    """Build a Plotly EBIT-to-FCFF waterfall in KRW billions."""

    required_fields = (
        "연도",
        "표시 단위",
        "EBIT",
        "영업관련 법인세",
        "NOPAT",
        "D&A",
        "Capex",
        "NWC 현금흐름 효과",
        "FCFF",
        "Waterfall 효과",
    )
    missing_fields = [
        field for field in required_fields if field not in waterfall_data
    ]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise KeyError(f"Waterfall 시각화 필수 항목 누락: {missing}")

    year = int(_finite_number(waterfall_data, "연도"))
    if year not in SUPPORTED_FORECAST_YEARS:
        raise ValueError(
            f"지원하지 않는 전망 연도입니다: {year}. "
            "지원 범위는 2026~2030년입니다."
        )

    effects = waterfall_data["Waterfall 효과"]
    if not isinstance(effects, Mapping):
        raise TypeError("Waterfall 효과는 항목별 금액을 담은 매핑이어야 합니다.")

    labels = [
        "EBIT",
        "영업관련<br>법인세",
        "NOPAT",
        "D&A",
        "Capex",
        "NWC<br>증감",
        "FCFF",
    ]
    effect_keys = [
        "EBIT",
        "영업관련 법인세",
        "NOPAT",
        "D&A",
        "Capex",
        "NWC 증감",
        "FCFF",
    ]
    display_effects = [
        _finite_number(effects, key) / MODEL_TO_DISPLAY_DIVISOR
        for key in effect_keys
    ]

    # Plotly calculates subtotal and total bars from preceding relative bars;
    # the visible NOPAT and FCFF amounts are carried separately in customdata.
    plot_values = [
        display_effects[0],
        display_effects[1],
        0.0,
        display_effects[3],
        display_effects[4],
        display_effects[5],
        0.0,
    ]
    displayed_amounts = [
        display_effects[0],
        display_effects[1],
        _finite_number(waterfall_data, "NOPAT")
        / MODEL_TO_DISPLAY_DIVISOR,
        display_effects[3],
        display_effects[4],
        display_effects[5],
        _finite_number(waterfall_data, "FCFF")
        / MODEL_TO_DISPLAY_DIVISOR,
    ]
    text = [_signed_amount(value) for value in displayed_amounts]
    text[0] = f"{displayed_amounts[0]:,.1f}"
    text[2] = f"{displayed_amounts[2]:,.1f}"
    text[6] = f"{displayed_amounts[6]:,.1f}"

    figure = go.Figure(
        go.Waterfall(
            x=labels,
            y=plot_values,
            measure=[
                "absolute",
                "relative",
                "total",
                "relative",
                "relative",
                "relative",
                "total",
            ],
            customdata=displayed_amounts,
            text=text,
            textposition="outside",
            connector=dict(
                line=dict(color="#D9E2EC", width=1)
            ),
            increasing=dict(
                marker=dict(color="#247B7B")
            ),
            decreasing=dict(
                marker=dict(color="#D97732")
            ),
            totals=dict(
                marker=dict(color="#102A43")
            ),
            hovertemplate=(
                "%{x}<br>"
                "금액 %{customdata:,.1f}십억원"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title=(
            f"<b>{year}E EBIT에서 FCFF로의 전환</b>"
            "<br><sup>세후 영업이익 및 재투자 조정 · 십억원</sup>"
        ),
        height=390,
        margin=dict(l=45, r=35, t=75, b=55),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        showlegend=False,
        font=dict(
            family="Arial, Pretendard, sans-serif",
            color="#243B53",
            size=12,
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#D9E2EC",
            font_color="#243B53",
        ),
    )
    figure.update_xaxes(
        showgrid=False,
        linecolor="#D9E2EC",
        tickfont=dict(color="#64748B"),
    )
    figure.update_yaxes(
        title="십억원",
        gridcolor="#E9EEF3",
        zeroline=False,
        linecolor="#D9E2EC",
        tickfont=dict(color="#64748B"),
    )

    return figure
