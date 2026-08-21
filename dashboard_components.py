"""Reusable, testable components for the Orion valuation dashboard.

The core valuation model stores monetary amounts in KRW millions.  Dashboard
figures may convert those amounts for presentation, but this module never
changes the source model values.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from math import isfinite

import plotly.graph_objects as go


MODEL_UNIT = "백만원"
DISPLAY_UNIT = "십억원"
MODEL_TO_DISPLAY_DIVISOR = 1_000.0
WATERFALL_TOTAL_COLOR = "#3478B8"
WATERFALL_INCREASE_COLOR = "#2A9D8F"
WATERFALL_DECREASE_COLOR = "#E07A5F"
FCFF_RECONCILIATION_TOLERANCE = 1e-6
SUPPORTED_FORECAST_YEARS = frozenset(range(2026, 2031))
FORMULA_RECONCILIATION_TOLERANCE = 1e-6
SUPPORTED_FORMULA_STAGES = (
    "매출액",
    "EBIT",
    "FCFF",
    "WACC",
    "DCF",
    "지분가치",
    "주당 내재가치",
)
CHALLENGE_ASSUMPTION_KEYS = (
    "revenue_growth_adjustment",
    "ebit_margin_adjustment",
    "wacc_adjustment",
    "terminal_growth_adjustment",
)
MANAGEMENT_ASSERTION_CASE = "경영진 주장"
AUDITOR_PROFESSIONAL_JUDGMENT_CASE = "감사인의 전문가적 판단"
AUDITOR_RANGE_LOWER_CASE = "감사인 범위 하단"
AUDITOR_RANGE_UPPER_CASE = "감사인 범위 상단"
DEFAULT_SENSITIVITY_WACC_OFFSETS = (
    -0.010,
    -0.005,
    0.000,
    0.005,
    0.010,
)
DEFAULT_SENSITIVITY_GROWTH_OFFSETS = (
    -0.0050,
    -0.0025,
    0.0000,
    0.0025,
    0.0050,
)

REQUIRED_FCFF_FIELDS = (
    "연도",
    "EBIT",
    "NOPAT",
    "D&A",
    "Capex",
    "NWC 증감",
    "FCFF",
)


def _validated_year(value: object) -> int:
    try:
        numeric_year = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError("연도는 숫자여야 합니다.") from exc

    if not isfinite(numeric_year) or not numeric_year.is_integer():
        raise ValueError("연도는 정수여야 합니다.")

    year = int(numeric_year)
    if year not in SUPPORTED_FORECAST_YEARS:
        raise ValueError(
            "지원하지 않는 전망 연도입니다: "
            f"{year}. 지원 범위는 2026~2030년입니다."
        )
    return year


def select_forecast_row(
    forecast_data: object,
    year: object,
) -> dict[str, object]:
    """Return a copied, unique forecast row for a supported year.

    ``forecast_data`` may be a pandas DataFrame or a sequence of mappings.
    The function deliberately returns a new ``dict`` so the dashboard cannot
    mutate the model output while formatting a selected year.
    """

    selected_year = _validated_year(year)

    if hasattr(forecast_data, "to_dict"):
        try:
            records = forecast_data.to_dict(orient="records")
        except TypeError as exc:
            raise TypeError(
                "forecast_data를 행 단위 레코드로 변환할 수 없습니다."
            ) from exc
    elif isinstance(forecast_data, Sequence) and not isinstance(
        forecast_data, (str, bytes)
    ):
        records = list(forecast_data)
    else:
        raise TypeError(
            "forecast_data는 DataFrame 또는 행 매핑의 시퀀스여야 합니다."
        )

    matches = []
    for record in records:
        if not isinstance(record, Mapping):
            raise TypeError("전망 데이터의 각 행은 매핑이어야 합니다.")
        if "연도" not in record:
            raise KeyError("전망 데이터에 연도 열이 없습니다.")
        record_year = _finite_number(record, "연도")
        if record_year == selected_year:
            matches.append(record)

    if len(matches) != 1:
        raise ValueError(
            f"{selected_year}년 전망 행은 정확히 1개여야 합니다. "
            f"현재 {len(matches)}개입니다."
        )
    return dict(matches[0])


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

    year = _validated_year(forecast_row["연도"])

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


def calculate_fcff_waterfall_kpis(
    waterfall_data: Mapping[str, object],
) -> dict[str, float | int | str]:
    """Calculate display KPIs without modifying the prepared data."""

    required_fields = ("연도", "EBIT", "NOPAT", "FCFF")
    missing_fields = [
        field for field in required_fields if field not in waterfall_data
    ]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise KeyError(f"FCFF KPI 필수 항목 누락: {missing}")

    year = _validated_year(waterfall_data["연도"])
    ebit = _finite_number(waterfall_data, "EBIT")
    nopat = _finite_number(waterfall_data, "NOPAT")
    fcff = _finite_number(waterfall_data, "FCFF")

    if ebit == 0:
        raise ValueError("현금전환율 계산을 위한 EBIT가 0입니다.")

    return {
        "연도": year,
        "표시 단위": DISPLAY_UNIT,
        "EBIT": ebit / MODEL_TO_DISPLAY_DIVISOR,
        "NOPAT": nopat / MODEL_TO_DISPLAY_DIVISOR,
        "FCFF": fcff / MODEL_TO_DISPLAY_DIVISOR,
        "현금전환율": fcff / ebit,
    }


def build_fcff_waterfall_insight(
    waterfall_data: Mapping[str, object],
    kpis: Mapping[str, object],
) -> str:
    """Create a factual, non-speculative interpretation of one FCFF bridge."""

    year = _validated_year(waterfall_data["연도"])
    fcff = _finite_number(kpis, "FCFF")
    cash_conversion = _finite_number(kpis, "현금전환율")
    operating_tax = _finite_number(waterfall_data, "영업관련 법인세")
    capex = _finite_number(waterfall_data, "Capex")
    change_in_nwc = _finite_number(waterfall_data, "NWC 증감")

    cash_outflows = {
        "영업관련 법인세": operating_tax,
        "Capex": capex,
    }
    if change_in_nwc > 0:
        cash_outflows["NWC 증가"] = change_in_nwc

    largest_outflow_name, largest_outflow_amount = max(
        cash_outflows.items(), key=lambda item: item[1]
    )
    largest_outflow_display = (
        largest_outflow_amount / MODEL_TO_DISPLAY_DIVISOR
    )

    if change_in_nwc > 0:
        nwc_sentence = (
            f"NWC가 {change_in_nwc / MODEL_TO_DISPLAY_DIVISOR:,.1f}십억원 "
            "증가하여 현금유출로 작용했습니다."
        )
    elif change_in_nwc < 0:
        nwc_sentence = (
            f"NWC가 {-change_in_nwc / MODEL_TO_DISPLAY_DIVISOR:,.1f}십억원 "
            "감소하여 운전자본 회수가 현금유입으로 작용했습니다."
        )
    else:
        nwc_sentence = "NWC 증감에 따른 현금흐름 영향은 없습니다."

    return (
        f"{year}E FCFF는 {fcff:,.1f}십억원이며, EBIT 대비 "
        f"현금전환율은 {cash_conversion:.1%}입니다. 가장 큰 "
        f"현금유출 항목은 {largest_outflow_name} "
        f"{largest_outflow_display:,.1f}십억원입니다. {nwc_sentence}"
    )


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
    cumulative_points = [displayed_amounts[0], displayed_amounts[2]]
    running_value = displayed_amounts[2]
    for effect in display_effects[3:6]:
        running_value += effect
        cumulative_points.append(running_value)
    cumulative_points.append(displayed_amounts[6])
    axis_minimum = min(0.0, min(cumulative_points))
    axis_maximum = max(cumulative_points)
    axis_span = max(axis_maximum - axis_minimum, 1.0)
    axis_upper = axis_maximum + axis_span * 0.16
    axis_lower = (
        axis_minimum - axis_span * 0.08
        if axis_minimum < 0
        else 0.0
    )

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
                marker=dict(color=WATERFALL_INCREASE_COLOR)
            ),
            decreasing=dict(
                marker=dict(color=WATERFALL_DECREASE_COLOR)
            ),
            totals=dict(
                marker=dict(color=WATERFALL_TOTAL_COLOR)
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
        range=[axis_lower, axis_upper],
        gridcolor="#E9EEF3",
        zeroline=False,
        linecolor="#D9E2EC",
        tickfont=dict(color="#64748B"),
    )

    return figure


def build_valuation_formula_catalog() -> dict[str, dict[str, object]]:
    """Return the formulas actually implemented by the Orion model.

    The catalog is presentation metadata only.  Every call returns a deep
    copy so callers cannot mutate the shared definitions.
    """

    catalog = {
        "매출액": {
            "경제적 의미": "지역별 매출액 전망을 합산한 연결 매출액",
            "기호 수식": r"Revenue_t = \sum_s Revenue_{s,t}",
            "부호규칙": "지역별 매출액과 연결 매출액은 양수로 표시",
            "데이터 출처 또는 모델 경로": (
                "model['전망'][연도]; 가정!F7:J9; 과거재무제표!F71:F73"
            ),
        },
        "EBIT": {
            "경제적 의미": "매출액에서 매출원가·판매비·관리비를 차감한 영업이익",
            "기호 수식": r"EBIT_t = Revenue_t \times EBIT\ Margin_t",
            "부호규칙": "영업이익은 이익 발생 시 양수",
            "데이터 출처 또는 모델 경로": (
                "model['전망'][연도]; 가정!F13:J15"
            ),
        },
        "FCFF": {
            "경제적 의미": "자본구조와 무관하게 자본제공자에게 귀속되는 잉여현금흐름",
            "기호 수식": (
                r"FCFF_t = NOPAT_t + D\&A_t - Capex_t - \Delta NWC_t"
            ),
            "부호규칙": (
                "Capex는 차감; NWC 증가는 현금유출, NWC 감소는 운전자본 "
                "회수에 따른 현금유입"
            ),
            "데이터 출처 또는 모델 경로": (
                "model['전망'][연도]; 가정!F16:J26"
            ),
        },
        "WACC": {
            "경제적 의미": "자기자본과 타인자본 제공자의 가중평균 요구수익률",
            "기호 수식": (
                r"WACC = K_e w_E + K_d(1-T)w_D + Adjustment"
            ),
            "부호규칙": "자본비용과 자본구조 비중은 양수; 비중 합계는 100%",
            "데이터 출처 또는 모델 경로": (
                "model['WACC']; 가정!C30:C36; 법인세율 가정!F16"
            ),
        },
        "DCF": {
            "경제적 의미": "명시적 전망 FCFF와 계속기업가치를 기준일 현재가치로 환산한 기업가치",
            "기호 수식": (
                r"EV = \sum_{t=1}^{n}\frac{FCFF_t}{(1+WACC)^t} + "
                r"\frac{FCFF_n(1+g)}{(WACC-g)(1+WACC)^n}"
            ),
            "부호규칙": "WACC는 영구성장률보다 커야 함",
            "데이터 출처 또는 모델 경로": (
                "model['전망']; model['WACC']; model['DCF']; 가정!C37"
            ),
        },
        "지분가치": {
            "경제적 의미": "기업가치에 순비영업 조정액을 반영한 지배기업 보통주주 귀속 가치",
            "기호 수식": r"Equity\ Value = EV + Net\ Nonoperating\ Adjustment",
            "부호규칙": (
                "비영업자산은 가산; 금융부채·리스부채·비지배지분은 차감"
            ),
            "데이터 출처 또는 모델 경로": (
                "model['DCF']['기업가치']; model['지분가치']"
            ),
        },
        "주당 내재가치": {
            "경제적 의미": "지분가치를 유통주식수로 나눈 보통주 1주당 가치",
            "기호 수식": (
                r"Value\ per\ Share = \frac{Equity\ Value}{Shares\ Outstanding}"
            ),
            "부호규칙": "유통주식수는 0보다 커야 함",
            "데이터 출처 또는 모델 경로": (
                "model['지분가치']; 과거재무제표!F67:F68"
            ),
        },
    }
    return deepcopy(catalog)


def _require_mapping(
    value: object,
    name: str,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name}은(는) 매핑이어야 합니다.")
    return value


def _required_value(
    mapping: Mapping[str, object],
    key: str,
    path: str,
) -> float:
    if key not in mapping:
        raise KeyError(f"Formula Explorer 필수 입력 누락: {path}['{key}']")
    return _finite_number(mapping, key)


def _display_mapping(
    raw_inputs: Mapping[str, object],
    divisor: float,
) -> dict[str, object]:
    displayed: dict[str, object] = {}
    for key, value in raw_inputs.items():
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            displayed[key] = [float(item) / divisor for item in value]
        else:
            displayed[key] = float(value) / divisor
    return displayed


def reconcile_formula_result(
    formula_result: Mapping[str, object],
) -> dict[str, object]:
    """Return a copied formula result with a deterministic reconciliation."""

    if not isinstance(formula_result, Mapping):
        raise TypeError("formula_result는 매핑이어야 합니다.")
    required = ("재계산값", "모델값", "허용오차")
    missing = [key for key in required if key not in formula_result]
    if missing:
        raise KeyError(
            "Formula Explorer 대사 필수 항목 누락: " + ", ".join(missing)
        )

    result = deepcopy(dict(formula_result))
    recalculated = _required_value(result, "재계산값", "formula_result")
    model_value = _required_value(result, "모델값", "formula_result")
    tolerance = _required_value(result, "허용오차", "formula_result")
    if tolerance < 0:
        raise ValueError("허용오차는 음수일 수 없습니다.")

    difference = recalculated - model_value
    result["차이"] = difference
    result["대사상태"] = "PASS" if abs(difference) <= tolerance else "FAIL"
    return result


def _formula_result(
    *,
    stage: str,
    year: int | None,
    display_formula: str,
    raw_inputs: Mapping[str, object],
    display_inputs: Mapping[str, object],
    recalculated: float,
    model_value: float,
    model_unit: str,
    display_unit: str,
    details: Mapping[str, object] | None = None,
) -> dict[str, object]:
    metadata = build_valuation_formula_catalog()[stage]
    result: dict[str, object] = {
        "단계": stage,
        "연도": year,
        "경제적 의미": metadata["경제적 의미"],
        "기호 수식": metadata["기호 수식"],
        "표시 수식": display_formula,
        "원본 입력값": deepcopy(dict(raw_inputs)),
        "표시 입력값": deepcopy(dict(display_inputs)),
        "재계산값": recalculated,
        "모델값": model_value,
        "차이": recalculated - model_value,
        "허용오차": FORMULA_RECONCILIATION_TOLERANCE,
        "대사상태": "",
        "원본 단위": model_unit,
        "표시 단위": display_unit,
        "부호규칙": metadata["부호규칙"],
        "데이터 출처 또는 모델 경로": metadata[
            "데이터 출처 또는 모델 경로"
        ],
    }
    if details is not None:
        result["계산 세부"] = deepcopy(dict(details))
    return reconcile_formula_result(result)


def prepare_formula_explorer_data(
    model: Mapping[str, object],
    stage: str,
    year: object | None = None,
) -> dict[str, object]:
    """Recalculate one supported valuation stage from immutable model output."""

    model_mapping = _require_mapping(model, "model")
    if stage not in SUPPORTED_FORMULA_STAGES:
        raise ValueError(
            f"지원하지 않는 가치평가 단계입니다: {stage}. "
            f"지원 단계: {', '.join(SUPPORTED_FORMULA_STAGES)}"
        )

    forecast = model_mapping.get("전망")
    if stage in {"매출액", "EBIT", "FCFF"}:
        if year is None:
            raise ValueError(f"{stage} 단계에는 분석 연도가 필요합니다.")
        row = select_forecast_row(forecast, year)
        selected_year = _validated_year(year)

        if stage == "매출액":
            keys = ("한국 매출액", "중국 매출액", "기타 국가 매출액")
            raw = {
                key: _required_value(row, key, "model['전망'][연도]")
                for key in keys
            }
            model_value = _required_value(row, "매출액", "model['전망'][연도]")
            recalculated = sum(raw.values())
            displayed = _display_mapping(raw, MODEL_TO_DISPLAY_DIVISOR)
            formula = " + ".join(f"{displayed[key]:,.1f}" for key in keys)
            formula += f" = {model_value / MODEL_TO_DISPLAY_DIVISOR:,.1f}십억원"
            return _formula_result(
                stage=stage,
                year=selected_year,
                display_formula=formula,
                raw_inputs=raw,
                display_inputs=displayed,
                recalculated=recalculated,
                model_value=model_value,
                model_unit=MODEL_UNIT,
                display_unit=DISPLAY_UNIT,
            )

        if stage == "EBIT":
            revenue = _required_value(row, "매출액", "model['전망'][연도]")
            margin = _required_value(row, "영업이익률", "model['전망'][연도]")
            model_value = _required_value(row, "EBIT", "model['전망'][연도]")
            recalculated = revenue * margin
            raw = {"매출액": revenue, "영업이익률": margin}
            displayed = {
                "매출액": revenue / MODEL_TO_DISPLAY_DIVISOR,
                "영업이익률": margin,
            }
            formula = (
                f"{displayed['매출액']:,.1f}십억원 × "
                f"{margin:.1%} = {model_value / MODEL_TO_DISPLAY_DIVISOR:,.1f}십억원"
            )
            return _formula_result(
                stage=stage,
                year=selected_year,
                display_formula=formula,
                raw_inputs=raw,
                display_inputs=displayed,
                recalculated=recalculated,
                model_value=model_value,
                model_unit=MODEL_UNIT,
                display_unit=DISPLAY_UNIT,
            )

        nopat = _required_value(row, "NOPAT", "model['전망'][연도]")
        depreciation = _required_value(row, "D&A", "model['전망'][연도]")
        capex = _required_value(row, "Capex", "model['전망'][연도]")
        change_in_nwc = _required_value(row, "NWC 증감", "model['전망'][연도]")
        ebit = _required_value(row, "EBIT", "model['전망'][연도]")
        model_value = _required_value(row, "FCFF", "model['전망'][연도]")
        recalculated = nopat + depreciation - capex - change_in_nwc
        raw = {
            "EBIT": ebit,
            "영업관련 법인세": ebit - nopat,
            "NOPAT": nopat,
            "D&A": depreciation,
            "Capex": capex,
            "NWC 증감": change_in_nwc,
        }
        displayed = _display_mapping(raw, MODEL_TO_DISPLAY_DIVISOR)
        formula = (
            f"{displayed['NOPAT']:,.1f} + {displayed['D&A']:,.1f} - "
            f"{displayed['Capex']:,.1f} - ({displayed['NWC 증감']:,.1f}) "
            f"= {model_value / MODEL_TO_DISPLAY_DIVISOR:,.1f}십억원"
        )
        return _formula_result(
            stage=stage,
            year=selected_year,
            display_formula=formula,
            raw_inputs=raw,
            display_inputs=displayed,
            recalculated=recalculated,
            model_value=model_value,
            model_unit=MODEL_UNIT,
            display_unit=DISPLAY_UNIT,
            details={"영업관련 법인세": ebit - nopat},
        )

    wacc = _require_mapping(model_mapping.get("WACC"), "model['WACC']")
    if stage == "WACC":
        components = _require_mapping(wacc.get("구성요소"), "model['WACC']['구성요소']")
        rf = _required_value(components, "무위험수익률", "model['WACC']['구성요소']")
        erp = _required_value(components, "주식시장위험프리미엄", "model['WACC']['구성요소']")
        beta = _required_value(components, "베타", "model['WACC']['구성요소']")
        crp = _required_value(components, "국가위험프리미엄", "model['WACC']['구성요소']")
        pre_tax_kd = _required_value(components, "세전 타인자본비용", "model['WACC']['구성요소']")
        tax_rate = _required_value(components, "법인세율", "model['WACC']['구성요소']")
        equity_weight = _required_value(components, "자기자본 비중", "model['WACC']['구성요소']")
        debt_weight = _required_value(components, "타인자본 비중", "model['WACC']['구성요소']")
        adjustment = _required_value(components, "WACC 조정", "model['WACC']['구성요소']")
        cost_of_equity = rf + beta * erp + crp
        after_tax_debt_cost = pre_tax_kd * (1 - tax_rate)
        recalculated = (
            cost_of_equity * equity_weight
            + after_tax_debt_cost * debt_weight
            + adjustment
        )
        model_value = _required_value(wacc, "WACC", "model['WACC']")
        raw = dict(components)
        displayed = {key: float(value) for key, value in raw.items()}
        formula = (
            f"{cost_of_equity:.2%} × {equity_weight:.1%} + "
            f"{after_tax_debt_cost:.2%} × {debt_weight:.1%} + "
            f"{adjustment:.2%} = {model_value:.2%}"
        )
        return _formula_result(
            stage=stage,
            year=None,
            display_formula=formula,
            raw_inputs=raw,
            display_inputs=displayed,
            recalculated=recalculated,
            model_value=model_value,
            model_unit="비율",
            display_unit="%",
            details={
                "자기자본비용": cost_of_equity,
                "세후 타인자본비용": after_tax_debt_cost,
                "자본구조 비중 합계": equity_weight + debt_weight,
            },
        )

    dcf = _require_mapping(model_mapping.get("DCF"), "model['DCF']")
    if stage == "DCF":
        forecast_rows = forecast
        if not isinstance(forecast_rows, Sequence) or isinstance(
            forecast_rows, (str, bytes)
        ):
            raise TypeError("model['전망']은 행 매핑의 시퀀스여야 합니다.")
        fcff_values = [
            _required_value(
                _require_mapping(row, "model['전망'] 행"),
                "FCFF",
                "model['전망'] 행",
            )
            for row in forecast_rows
        ]
        if not fcff_values:
            raise ValueError("DCF 계산을 위한 FCFF 전망값이 없습니다.")
        wacc_value = _required_value(wacc, "WACC", "model['WACC']")
        growth = _required_value(dcf, "영구성장률", "model['DCF']")
        if wacc_value <= growth:
            raise ValueError("WACC는 영구성장률보다 커야 합니다.")
        discount_factors = [
            1 / (1 + wacc_value) ** period
            for period in range(1, len(fcff_values) + 1)
        ]
        present_values = [
            fcff * factor
            for fcff, factor in zip(fcff_values, discount_factors, strict=True)
        ]
        forecast_pv = sum(present_values)
        terminal_value = (
            fcff_values[-1] * (1 + growth) / (wacc_value - growth)
        )
        terminal_pv = terminal_value * discount_factors[-1]
        recalculated = forecast_pv + terminal_pv
        model_value = _required_value(dcf, "기업가치", "model['DCF']")
        raw = {
            "FCFF 전망": fcff_values,
            "WACC": wacc_value,
            "영구성장률": growth,
        }
        displayed = {
            "FCFF 전망": [value / 1_000_000 for value in fcff_values],
            "WACC": wacc_value,
            "영구성장률": growth,
        }
        formula = (
            f"명시적 전망 {forecast_pv / 1_000_000:,.2f}조원 + "
            f"계속기업가치 {terminal_pv / 1_000_000:,.2f}조원 "
            f"= {model_value / 1_000_000:,.2f}조원"
        )
        return _formula_result(
            stage=stage,
            year=None,
            display_formula=formula,
            raw_inputs=raw,
            display_inputs=displayed,
            recalculated=recalculated,
            model_value=model_value,
            model_unit=MODEL_UNIT,
            display_unit="조원",
            details={
                "할인계수": discount_factors,
                "FCFF 현재가치": present_values,
                "추정기간 FCFF 현재가치": forecast_pv,
                "계속기업가치": terminal_value,
                "계속기업가치 현재가치": terminal_pv,
                "계속기업가치 비중": terminal_pv / recalculated,
            },
        )

    equity = _require_mapping(model_mapping.get("지분가치"), "model['지분가치']")
    if stage == "지분가치":
        enterprise_value = _required_value(dcf, "기업가치", "model['DCF']")
        adjustment = _required_value(
            equity, "순비영업 조정액", "model['지분가치']"
        )
        model_value = _required_value(equity, "지분가치", "model['지분가치']")
        recalculated = enterprise_value + adjustment
        raw = {"기업가치": enterprise_value, "순비영업 조정액": adjustment}
        displayed = _display_mapping(raw, 1_000_000.0)
        formula = (
            f"{displayed['기업가치']:,.2f}조원 + "
            f"{displayed['순비영업 조정액']:,.2f}조원 "
            f"= {model_value / 1_000_000:,.2f}조원"
        )
        return _formula_result(
            stage=stage,
            year=None,
            display_formula=formula,
            raw_inputs=raw,
            display_inputs=displayed,
            recalculated=recalculated,
            model_value=model_value,
            model_unit=MODEL_UNIT,
            display_unit="조원",
            details={
                "비영업자산 합계": _required_value(
                    equity, "비영업자산 합계", "model['지분가치']"
                ),
                "리스부채": _required_value(
                    equity, "리스부채", "model['지분가치']"
                ),
                "금융기관차입금": _required_value(
                    equity, "금융기관차입금", "model['지분가치']"
                ),
                "비지배지분": _required_value(
                    equity, "비지배지분", "model['지분가치']"
                ),
            },
        )

    equity_value = _required_value(equity, "지분가치", "model['지분가치']")
    shares = _required_value(
        equity, "유통주식수(백만주)", "model['지분가치']"
    )
    if shares <= 0:
        raise ValueError("유통주식수는 0보다 커야 합니다.")
    recalculated = equity_value / shares
    model_value = _required_value(
        equity, "주당 내재가치", "model['지분가치']"
    )
    current_price = _required_value(equity, "기준주가", "model['지분가치']")
    upside = recalculated / current_price - 1
    model_upside = _required_value(
        equity, "내재 상승여력", "model['지분가치']"
    )
    raw = {
        "지분가치": equity_value,
        "유통주식수(백만주)": shares,
        "기준주가": current_price,
    }
    displayed = {
        "지분가치": equity_value / 1_000_000,
        "유통주식수(백만주)": shares,
        "기준주가": current_price,
    }
    formula = (
        f"{displayed['지분가치']:,.2f}조원 ÷ "
        f"{shares:,.3f}백만주 = {model_value:,.0f}원"
    )
    return _formula_result(
        stage=stage,
        year=None,
        display_formula=formula,
        raw_inputs=raw,
        display_inputs=displayed,
        recalculated=recalculated,
        model_value=model_value,
        model_unit="원/주",
        display_unit="원/주",
        details={
            "재계산 내재 상승여력": upside,
            "모델 내재 상승여력": model_upside,
            "내재 상승여력 차이": upside - model_upside,
        },
    )


def build_formula_explorer_insight(
    formula_result: Mapping[str, object],
) -> str:
    """Create a factual interpretation without inferring business causes."""

    reconciled = reconcile_formula_result(formula_result)
    stage = str(reconciled.get("단계", ""))
    status = str(reconciled["대사상태"])
    difference = _required_value(reconciled, "차이", "formula_result")
    year = reconciled.get("연도")
    period = f"{int(year)}E " if year is not None else ""
    base = (
        f"{period}{stage} 재계산 결과는 모델값과 "
        f"{abs(difference):,.6f}{reconciled.get('원본 단위', '')} 차이로 "
        f"{status}입니다."
    )
    if stage == "FCFF":
        raw = _require_mapping(reconciled.get("원본 입력값"), "원본 입력값")
        change_in_nwc = _required_value(raw, "NWC 증감", "원본 입력값")
        if change_in_nwc > 0:
            return base + " NWC 증가는 현금유출로 반영됩니다."
        if change_in_nwc < 0:
            return base + " NWC 감소는 운전자본 회수에 따른 현금유입으로 반영됩니다."
        return base + " NWC 증감에 따른 현금흐름 영향은 없습니다."
    if stage == "DCF":
        details = _require_mapping(reconciled.get("계산 세부"), "계산 세부")
        terminal_pv = _required_value(details, "계속기업가치 현재가치", "계산 세부")
        enterprise_value = _required_value(reconciled, "모델값", "formula_result")
        return base + f" 계속기업가치 현재가치 비중은 {terminal_pv / enterprise_value:.1%}입니다."
    return base


def _validated_adjustments(
    adjustments: Mapping[str, object],
) -> dict[str, float]:
    if not isinstance(adjustments, Mapping):
        raise TypeError("Challenge 가정은 매핑이어야 합니다.")

    missing = [
        key for key in CHALLENGE_ASSUMPTION_KEYS if key not in adjustments
    ]
    if missing:
        raise KeyError(
            "Challenge 가정 누락: " + ", ".join(missing)
        )

    validated = {}
    for key in CHALLENGE_ASSUMPTION_KEYS:
        value = adjustments[key]
        if isinstance(value, bool):
            raise TypeError(f"{key}은(는) 숫자여야 합니다.")
        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise TypeError(f"{key}은(는) 숫자여야 합니다.") from exc
        if not isfinite(numeric_value):
            raise ValueError(f"{key}은(는) 유한한 숫자여야 합니다.")
        validated[key] = numeric_value
    return validated


def _challenge_case_snapshot(
    model: Mapping[str, object],
    case_name: str,
    adjustments: Mapping[str, object],
    current_price: float,
) -> dict[str, object]:
    if not isinstance(model, Mapping):
        raise TypeError("Case 모델은 매핑이어야 합니다.")

    forecast_rows = model.get("전망")
    if not isinstance(forecast_rows, Sequence) or isinstance(
        forecast_rows, (str, bytes)
    ):
        raise TypeError("Case 모델의 전망은 행 시퀀스여야 합니다.")
    if len(forecast_rows) < 2:
        raise ValueError("매출 CAGR 계산에는 최소 2개 전망연도가 필요합니다.")

    revenues = []
    margins = []
    for row in forecast_rows:
        if not isinstance(row, Mapping):
            raise TypeError("전망 데이터의 각 행은 매핑이어야 합니다.")
        revenues.append(_required_value(row, "매출액", "Challenge 전망"))
        margins.append(
            _required_value(row, "영업이익률", "Challenge 전망")
        )

    if revenues[0] <= 0 or revenues[-1] <= 0:
        raise ValueError("매출 CAGR 계산을 위한 매출액은 양수여야 합니다.")

    wacc_data = _require_mapping(model.get("WACC"), "Case 모델['WACC']")
    dcf_data = _require_mapping(model.get("DCF"), "Case 모델['DCF']")
    equity_data = _require_mapping(
        model.get("지분가치"),
        "Case 모델['지분가치']",
    )
    per_share = _required_value(
        equity_data,
        "주당 내재가치",
        "Case 지분가치",
    )
    price = float(current_price)
    if not isfinite(price) or price <= 0:
        raise ValueError("기준주가는 양의 유한한 숫자여야 합니다.")

    return {
        "Case": str(case_name),
        "매출 CAGR": (
            revenues[-1] / revenues[0]
        ) ** (1 / (len(revenues) - 1)) - 1,
        "평균 EBIT Margin": sum(margins) / len(margins),
        "WACC": _required_value(wacc_data, "WACC", "Case WACC"),
        "영구성장률": _required_value(
            dcf_data,
            "영구성장률",
            "Case DCF",
        ),
        "기업가치": _required_value(
            dcf_data,
            "기업가치",
            "Case DCF",
        ),
        "지분가치": _required_value(
            equity_data,
            "지분가치",
            "Case 지분가치",
        ),
        "주당 내재가치": per_share,
        "상승여력": per_share / price - 1,
        "조정 가정": _validated_adjustments(adjustments),
    }


def prepare_challenge_case_comparison(
    management_model: Mapping[str, object],
    reviewer_model: Mapping[str, object],
    reviewer_adjustments: Mapping[str, object],
    current_price: float,
) -> dict[str, object]:
    """Compare management's assertion with the auditor's judgment case.

    The function reads already-calculated models and never mutates them.  It
    deliberately separates model production from reviewer judgment so the
    dashboard can evidence both the asserted case and the challenged case.
    """

    management_adjustments = {
        key: 0.0 for key in CHALLENGE_ASSUMPTION_KEYS
    }
    management = _challenge_case_snapshot(
        management_model,
        MANAGEMENT_ASSERTION_CASE,
        management_adjustments,
        current_price,
    )
    reviewer = _challenge_case_snapshot(
        reviewer_model,
        AUDITOR_PROFESSIONAL_JUDGMENT_CASE,
        reviewer_adjustments,
        current_price,
    )

    metric_names = (
        "매출 CAGR",
        "평균 EBIT Margin",
        "WACC",
        "영구성장률",
        "기업가치",
        "지분가치",
        "주당 내재가치",
        "상승여력",
    )
    deltas = {
        metric: float(reviewer[metric]) - float(management[metric])
        for metric in metric_names
    }
    value_gap_ratio = (
        float(reviewer["주당 내재가치"])
        / float(management["주당 내재가치"])
        - 1
    )

    return {
        "Cases": [management, reviewer],
        MANAGEMENT_ASSERTION_CASE: management,
        AUDITOR_PROFESSIONAL_JUDGMENT_CASE: reviewer,
        "차이": deltas,
        "주당가치 차이율": value_gap_ratio,
        "검토상태": (
            "CHALLENGED"
            if abs(value_gap_ratio) >= 0.05
            else "CORROBORATED"
        ),
    }


def prepare_auditor_range_comparison(
    management_model: Mapping[str, object],
    auditor_lower_model: Mapping[str, object],
    auditor_upper_model: Mapping[str, object],
    lower_adjustments: Mapping[str, object],
    upper_adjustments: Mapping[str, object],
    current_price: float,
) -> dict[str, object]:
    """Compare management's assertion with an auditor-developed range.

    The lower endpoint applies the assumptions that produce the lower value;
    consequently its WACC adjustment must be greater than or equal to the
    upper endpoint's WACC adjustment.  The other three adjustments follow
    their ordinary numeric ordering.
    """

    validated_lower = _validated_adjustments(lower_adjustments)
    validated_upper = _validated_adjustments(upper_adjustments)
    increasing_keys = (
        "revenue_growth_adjustment",
        "ebit_margin_adjustment",
        "terminal_growth_adjustment",
    )
    if any(
        validated_lower[key] > validated_upper[key]
        for key in increasing_keys
    ):
        raise ValueError("범위 하단 가정은 범위 상단 가정보다 클 수 없습니다.")
    if (
        validated_lower["wacc_adjustment"]
        < validated_upper["wacc_adjustment"]
    ):
        raise ValueError(
            "범위 하단의 WACC 조정은 범위 상단보다 작을 수 없습니다."
        )

    management_adjustments = {
        key: 0.0 for key in CHALLENGE_ASSUMPTION_KEYS
    }
    management = _challenge_case_snapshot(
        management_model,
        MANAGEMENT_ASSERTION_CASE,
        management_adjustments,
        current_price,
    )
    lower = _challenge_case_snapshot(
        auditor_lower_model,
        AUDITOR_RANGE_LOWER_CASE,
        validated_lower,
        current_price,
    )
    upper = _challenge_case_snapshot(
        auditor_upper_model,
        AUDITOR_RANGE_UPPER_CASE,
        validated_upper,
        current_price,
    )

    lower_value = float(lower["주당 내재가치"])
    upper_value = float(upper["주당 내재가치"])
    if lower_value > upper_value:
        raise ValueError(
            "계산된 감사인 범위 하단은 범위 상단보다 클 수 없습니다."
        )
    midpoint = (lower_value + upper_value) / 2
    width = upper_value - lower_value
    management_value = float(management["주당 내재가치"])
    includes_management = lower_value <= management_value <= upper_value
    if management_value < lower_value:
        nearest_range_value = lower_value
        misstatement_direction = "과소"
    elif management_value > upper_value:
        nearest_range_value = upper_value
        misstatement_direction = "과대"
    else:
        nearest_range_value = management_value
        misstatement_direction = "범위 내"
    misstatement_amount = abs(management_value - nearest_range_value)

    return {
        "Cases": [management, lower, upper],
        MANAGEMENT_ASSERTION_CASE: management,
        AUDITOR_RANGE_LOWER_CASE: lower,
        AUDITOR_RANGE_UPPER_CASE: upper,
        "감사인 범위 중앙값": midpoint,
        "범위폭": width,
        "범위폭 비율": width / midpoint if midpoint else 0.0,
        "경영진 주장 포함 여부": includes_management,
        "가장 가까운 범위 금액": nearest_range_value,
        "왜곡표시 금액": misstatement_amount,
        "왜곡표시 방향": misstatement_direction,
        "검토상태": "WITHIN_RANGE" if includes_management else "OUTSIDE_RANGE",
    }


def prepare_challenge_sensitivity_data(
    model: Mapping[str, object],
    wacc_offsets: Sequence[float] = DEFAULT_SENSITIVITY_WACC_OFFSETS,
    growth_offsets: Sequence[float] = DEFAULT_SENSITIVITY_GROWTH_OFFSETS,
) -> dict[str, object]:
    """Revalue one completed case over a WACC/g grid without reopening Excel."""

    if not isinstance(model, Mapping):
        raise TypeError("민감도 분석 모델은 매핑이어야 합니다.")

    forecast_rows = model.get("전망")
    if not isinstance(forecast_rows, Sequence) or isinstance(
        forecast_rows, (str, bytes)
    ) or not forecast_rows:
        raise TypeError("민감도 분석 모델의 전망은 비어 있지 않은 행 시퀀스여야 합니다.")

    fcff_forecast = []
    for row in forecast_rows:
        if not isinstance(row, Mapping):
            raise TypeError("전망 데이터의 각 행은 매핑이어야 합니다.")
        fcff_forecast.append(
            _required_value(row, "FCFF", "민감도 전망")
        )

    wacc_data = _require_mapping(
        model.get("WACC"),
        "민감도 모델['WACC']",
    )
    dcf_data = _require_mapping(
        model.get("DCF"),
        "민감도 모델['DCF']",
    )
    equity_data = _require_mapping(
        model.get("지분가치"),
        "민감도 모델['지분가치']",
    )
    base_wacc = _required_value(wacc_data, "WACC", "민감도 WACC")
    base_growth = _required_value(
        dcf_data,
        "영구성장률",
        "민감도 DCF",
    )
    enterprise_value = _required_value(
        dcf_data,
        "기업가치",
        "민감도 DCF",
    )
    equity_value = _required_value(
        equity_data,
        "지분가치",
        "민감도 지분가치",
    )
    per_share_value = _required_value(
        equity_data,
        "주당 내재가치",
        "민감도 지분가치",
    )
    if per_share_value <= 0:
        raise ValueError("주당 내재가치는 양수여야 합니다.")

    shares_million = equity_value / per_share_value
    bridge_adjustment = equity_value - enterprise_value
    validated_wacc_offsets = [float(value) for value in wacc_offsets]
    validated_growth_offsets = [float(value) for value in growth_offsets]
    wacc_grid = [base_wacc + value for value in validated_wacc_offsets]
    growth_grid = [base_growth + value for value in validated_growth_offsets]

    values = []
    for growth_rate in growth_grid:
        row_values = []
        for wacc_rate in wacc_grid:
            if wacc_rate <= growth_rate:
                raise ValueError("민감도 분석에서는 WACC가 영구성장률보다 커야 합니다.")
            discount_factors = [
                1 / (1 + wacc_rate) ** period
                for period in range(1, len(fcff_forecast) + 1)
            ]
            explicit_pv = sum(
                fcff * factor
                for fcff, factor in zip(
                    fcff_forecast,
                    discount_factors,
                    strict=True,
                )
            )
            terminal_value = (
                fcff_forecast[-1]
                * (1 + growth_rate)
                / (wacc_rate - growth_rate)
            )
            revalued_enterprise = (
                explicit_pv + terminal_value * discount_factors[-1]
            )
            revalued_equity = revalued_enterprise + bridge_adjustment
            row_values.append(revalued_equity / shares_million)
        values.append(row_values)

    return {
        "WACC": wacc_grid,
        "영구성장률": growth_grid,
        "WACC offsets": validated_wacc_offsets,
        "성장률 offsets": validated_growth_offsets,
        "주당 내재가치": values,
        "기준 WACC index": validated_wacc_offsets.index(0.0),
        "기준 성장률 index": validated_growth_offsets.index(0.0),
        "기업가치-지분가치 조정": bridge_adjustment,
        "유통주식수(백만주)": shares_million,
    }


def build_challenge_conclusion(
    comparison: Mapping[str, object],
) -> str:
    if not isinstance(comparison, Mapping):
        raise TypeError("Challenge 비교 결과는 매핑이어야 합니다.")

    management = _require_mapping(
        comparison.get(MANAGEMENT_ASSERTION_CASE),
        f"Challenge 비교['{MANAGEMENT_ASSERTION_CASE}']",
    )
    reviewer = _require_mapping(
        comparison.get(AUDITOR_PROFESSIONAL_JUDGMENT_CASE),
        f"Challenge 비교['{AUDITOR_PROFESSIONAL_JUDGMENT_CASE}']",
    )
    adjustments = _require_mapping(
        reviewer.get("조정 가정"),
        f"{AUDITOR_PROFESSIONAL_JUDGMENT_CASE}['조정 가정']",
    )
    management_value = _required_value(
        management,
        "주당 내재가치",
        MANAGEMENT_ASSERTION_CASE,
    )
    reviewer_value = _required_value(
        reviewer,
        "주당 내재가치",
        AUDITOR_PROFESSIONAL_JUDGMENT_CASE,
    )
    gap = reviewer_value / management_value - 1

    return (
        f"{AUDITOR_PROFESSIONAL_JUDGMENT_CASE}에 따른 주당 내재가치는 "
        f"{reviewer_value:,.0f}원으로, {MANAGEMENT_ASSERTION_CASE} "
        f"{management_value:,.0f}원 대비 {gap:+.1%}입니다. "
        "주요 가정 조정은 "
        f"매출성장률 {float(adjustments['revenue_growth_adjustment']):+.1%}p, "
        f"EBIT Margin {float(adjustments['ebit_margin_adjustment']):+.1%}p, "
        f"WACC {float(adjustments['wacc_adjustment']):+.1%}p, "
        f"영구성장률 {float(adjustments['terminal_growth_adjustment']):+.1%}p입니다. "
        "본 결과는 감사의견이 아닌 가정 검토 시뮬레이션입니다."
    )


def build_auditor_range_conclusion(
    comparison: Mapping[str, object],
) -> str:
    """Summarise the auditor-developed range without implying an audit opinion."""

    if not isinstance(comparison, Mapping):
        raise TypeError("감사인 범위 비교 결과는 매핑이어야 합니다.")
    management = _require_mapping(
        comparison.get(MANAGEMENT_ASSERTION_CASE),
        f"범위 비교['{MANAGEMENT_ASSERTION_CASE}']",
    )
    lower = _require_mapping(
        comparison.get(AUDITOR_RANGE_LOWER_CASE),
        f"범위 비교['{AUDITOR_RANGE_LOWER_CASE}']",
    )
    upper = _require_mapping(
        comparison.get(AUDITOR_RANGE_UPPER_CASE),
        f"범위 비교['{AUDITOR_RANGE_UPPER_CASE}']",
    )
    management_value = _required_value(
        management, "주당 내재가치", MANAGEMENT_ASSERTION_CASE
    )
    lower_value = _required_value(
        lower, "주당 내재가치", AUDITOR_RANGE_LOWER_CASE
    )
    upper_value = _required_value(
        upper, "주당 내재가치", AUDITOR_RANGE_UPPER_CASE
    )
    midpoint = float(comparison.get("감사인 범위 중앙값", 0.0))
    position = (
        "감사인 범위 안에 포함됩니다"
        if bool(comparison.get("경영진 주장 포함 여부"))
        else "감사인 범위 밖에 있습니다"
    )
    return (
        f"감사인의 전문가적 판단에 따른 주당 내재가치 범위는 "
        f"{lower_value:,.0f}원~{upper_value:,.0f}원이며 중앙값은 "
        f"{midpoint:,.0f}원입니다. 경영진 주장 {management_value:,.0f}원은 "
        f"{position}. 본 범위는 충분하고 적합한 감사증거의 확보 여부를 "
        "전제로 한 가정 검토 시뮬레이션이며 감사의견이 아닙니다."
    )
