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
FDD_RECONCILIATION_TOLERANCE = 1e-6
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
            "기호 수식": (
                r"Equity\ Value = EV + CashLike - DebtLike + "
                r"Nonoperating\ Assets - NCI + NWC\ Adjustment"
            ),
            "부호규칙": (
                "Cash-like·비영업자산·적용 NWC 조정은 가산; "
                "Debt-like·비지배지분은 차감"
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
                "Cash-like 자산": _required_value(
                    equity, "Cash-like 자산", "model['지분가치']"
                ),
                "Debt-like 항목": _required_value(
                    equity, "Debt-like 항목", "model['지분가치']"
                ),
                "순현금": _required_value(
                    equity, "순현금", "model['지분가치']"
                ),
                "비영업자산 합계": _required_value(
                    equity, "비영업자산 합계", "model['지분가치']"
                ),
                "적용 NWC 가격조정": _required_value(
                    equity, "적용 NWC 가격조정", "model['지분가치']"
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


def _fdd_value(mapping: Mapping[str, object], key: str, path: str) -> float:
    if key not in mapping:
        raise KeyError(f"FDD 표시 필수 입력 누락: {path}['{key}']")
    return _finite_number(mapping, key)


def _fdd_optional_number(
    mapping: Mapping[str, object],
    keys: Sequence[str],
) -> float | None:
    """Return the first finite numeric value found under ``keys``.

    Presentation-only metadata may legitimately be absent from the validated
    FDD engine.  Missing optional values are therefore returned as ``None``;
    malformed values that are present still raise a clear error.
    """

    for key in keys:
        if key in mapping:
            return _finite_number(mapping, key)
    return None


def _fdd_component_map(
    mapping: Mapping[str, object],
    key: str,
    path: str,
) -> dict[str, float]:
    component_mapping = _require_mapping(mapping.get(key), f"{path}['{key}']")
    return {
        str(label): _finite_number(component_mapping, label)
        for label in component_mapping
    }


def _fdd_optional_component_map(
    mapping: Mapping[str, object],
    keys: Sequence[str],
    path: str,
) -> dict[str, float]:
    """Return the first available component mapping, otherwise ``{}``.

    This is used only for optional Page 5 presentation metadata such as raw
    pre-recognition component amounts.  Core totals remain strict.
    """

    for key in keys:
        if key not in mapping or mapping.get(key) is None:
            continue
        value = mapping.get(key)
        if not isinstance(value, Mapping):
            raise TypeError(f"{path}['{key}']은(는) 매핑이어야 합니다.")
        return {
            str(label): _finite_number(value, label)
            for label in value
        }
    return {}


def _fdd_optional_text_map(
    mapping: Mapping[str, object],
    keys: Sequence[str],
    path: str,
) -> dict[str, str]:
    for key in keys:
        if key not in mapping or mapping.get(key) is None:
            continue
        value = mapping.get(key)
        if not isinstance(value, Mapping):
            raise TypeError(f"{path}['{key}']은(는) 매핑이어야 합니다.")
        return {str(label): str(note) for label, note in value.items()}
    return {}


def _normalise_fdd_period(value: object) -> str:
    """Normalise common historical period labels to e.g. ``2025A``."""

    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        numeric = float(value)
        if isfinite(numeric) and numeric.is_integer():
            return f"{int(numeric)}A"
    text = str(value).strip()
    if text.endswith("A"):
        return text
    if text.isdigit() and len(text) == 4:
        return f"{text}A"
    return text


def _fdd_history_from_mapping(
    nwc: Mapping[str, object],
) -> list[dict[str, object]]:
    """Read NWC/revenue history without requiring a schema not in the model.

    Phase 1's validated FDD contract does not guarantee historical ratio data.
    If a supported mapping is present, preserve it; otherwise return an empty
    list rather than fabricating 2023A/2024A values in the dashboard layer.
    """

    aliases = (
        "nwc_to_revenue_by_period",
        "nwc_ratio_by_period",
        "nwc_to_revenue_history",
        "historical_nwc_ratios",
    )
    mapping: Mapping[str, object] | None = None
    for key in aliases:
        candidate = nwc.get(key)
        if candidate is None:
            continue
        if not isinstance(candidate, Mapping):
            raise TypeError(f"model['FDD']['nwc']['{key}']은(는) 매핑이어야 합니다.")
        mapping = candidate
        break

    if mapping is None:
        single_ratio = _fdd_optional_number(
            nwc,
            (
                "closing_nwc_ratio",
                "closing_nwc_to_revenue",
                "nwc_to_revenue",
                "nwc_to_revenue_2025",
            ),
        )
        if single_ratio is None:
            return []
        return [{"period": "2025A", "nwc_to_revenue": single_ratio}]

    history: list[dict[str, object]] = []
    for period in mapping:
        ratio = _finite_number(mapping, period)
        history.append(
            {
                "period": _normalise_fdd_period(period),
                "nwc_to_revenue": ratio,
            }
        )
    history.sort(key=lambda item: str(item["period"]))
    return history


def _fdd_rate_fraction(value: float) -> float:
    """Accept recognition rates stored as either 0~1 or 0~100."""

    if not isfinite(value) or value < 0:
        raise ValueError("FDD 인정률은 0 이상의 유한한 숫자여야 합니다.")
    if value <= 1.0:
        return value
    if value <= 100.0:
        return value / 100.0
    raise ValueError("FDD 인정률은 0~1 또는 0~100 범위여야 합니다.")


def _lookup_component(
    mapping: Mapping[str, object],
    aliases: Sequence[str],
) -> tuple[str | None, float | None]:
    for label in aliases:
        if label in mapping:
            return label, _finite_number(mapping, label)
    return None, None


def _lookup_recognition_rate(
    rates: Mapping[str, object],
    labels: Sequence[str],
    prefixes: Sequence[str] = (),
) -> float | None:
    candidates: list[str] = []
    for label in labels:
        candidates.append(label)
        candidates.extend(f"{prefix} / {label}" for prefix in prefixes)
    for key in candidates:
        if key in rates:
            return _fdd_rate_fraction(_finite_number(rates, key))
    return None


def _gross_component_amount(
    *,
    recognized_components: Mapping[str, object],
    raw_inputs: Mapping[str, object],
    recognition_rates: Mapping[str, object],
    aliases: Sequence[str],
    rate_prefixes: Sequence[str],
    path: str,
) -> tuple[str, float, float]:
    """Return ``(label, gross input, recognized base amount)`` for overlay.

    Raw input maps are optional in the validated Phase 1 contract.  If absent,
    gross amount is recovered from the recognized component and its base
    recognition rate.  If the rate is also absent, the recognized amount is
    used as the gross amount; this is exact for the current 100%-recognized
    Ligachem and short-term-financial-instrument Base inputs.
    """

    raw_label, raw_value = _lookup_component(raw_inputs, aliases)
    recognized_label, recognized_value = _lookup_component(
        recognized_components,
        aliases,
    )
    label = raw_label or recognized_label
    if label is None:
        raise KeyError(
            f"FDD overlay 필수 구성요소 누락: {path}에서 "
            + " / ".join(aliases)
        )

    recognized = 0.0 if recognized_value is None else recognized_value
    if raw_value is not None:
        return label, raw_value, recognized

    rate = _lookup_recognition_rate(
        recognition_rates,
        aliases,
        prefixes=rate_prefixes,
    )
    if rate is not None and rate > 0:
        return label, recognized / rate, recognized
    return label, recognized, recognized


def _assert_fdd_close(actual: float, expected: float, message: str) -> None:
    if abs(actual - expected) > FDD_RECONCILIATION_TOLERANCE:
        raise ValueError(
            f"{message}: actual={actual:,.6f}{MODEL_UNIT}, "
            f"expected={expected:,.6f}{MODEL_UNIT}"
        )


def prepare_fdd_review_data(model: Mapping[str, object]) -> dict[str, object]:
    """Transform the validated model into immutable Page 5 display data.

    The adapter performs no workbook I/O and no independent valuation.  Core
    financial totals are strict and reconciled.  Presentation-only metadata
    that Phase 1 does not guarantee (historical QoE margins, classification
    notes, NWC ratio history, gross pre-recognition inputs) is optional.
    """

    model_mapping = _require_mapping(model, "model")
    fdd = _require_mapping(model_mapping.get("FDD"), "model['FDD']")
    qoe = _require_mapping(fdd.get("qoe"), "model['FDD']['qoe']")
    nwc = _require_mapping(fdd.get("nwc"), "model['FDD']['nwc']")
    bridge = _require_mapping(
        fdd.get("transaction_bridge"),
        "model['FDD']['transaction_bridge']",
    )
    dcf = _require_mapping(model_mapping.get("DCF"), "model['DCF']")
    equity = _require_mapping(
        model_mapping.get("지분가치"),
        "model['지분가치']",
    )

    enterprise_value = _fdd_value(dcf, "기업가치", "model['DCF']")
    equity_value = _fdd_value(equity, "지분가치", "model['지분가치']")
    shares = _fdd_value(
        equity,
        "유통주식수(백만주)",
        "model['지분가치']",
    )
    if shares <= 0:
        raise ValueError("FDD 표시용 유통주식수는 0보다 커야 합니다.")
    value_per_share = _fdd_value(
        equity,
        "주당 내재가치",
        "model['지분가치']",
    )

    cash_components = _fdd_component_map(
        bridge,
        "cash_like_components",
        "model['FDD']['transaction_bridge']",
    )
    debt_components = _fdd_component_map(
        bridge,
        "debt_like_components",
        "model['FDD']['transaction_bridge']",
    )
    non_operating_components = _fdd_component_map(
        bridge,
        "non_operating_asset_components",
        "model['FDD']['transaction_bridge']",
    )
    recognition_rates = _fdd_component_map(
        bridge,
        "recognition_rates",
        "model['FDD']['transaction_bridge']",
    )

    # These richer maps were contemplated by the Page 5 UI but are not part
    # of the validated Phase 1 contract.  Read them only when supplied.
    cash_inputs = _fdd_optional_component_map(
        bridge,
        ("cash_like_input_amounts", "cash_like_amounts"),
        "model['FDD']['transaction_bridge']",
    )
    debt_inputs = _fdd_optional_component_map(
        bridge,
        ("debt_like_input_amounts", "debt_like_amounts"),
        "model['FDD']['transaction_bridge']",
    )
    non_operating_inputs = _fdd_optional_component_map(
        bridge,
        (
            "non_operating_asset_input_amounts",
            "non_operating_asset_amounts",
        ),
        "model['FDD']['transaction_bridge']",
    )
    classification_notes = _fdd_optional_text_map(
        bridge,
        ("classification_notes",),
        "model['FDD']['transaction_bridge']",
    )

    base = {
        "reported_ebitda": _fdd_value(
            qoe,
            "reported_ebitda",
            "model['FDD']['qoe']",
        ),
        "fdd_ebitda": _fdd_value(
            qoe,
            "fdd_ebitda",
            "model['FDD']['qoe']",
        ),
        "normalized_nwc_peg": _fdd_value(
            nwc,
            "normalized_peg",
            "model['FDD']['nwc']",
        ),
        "closing_nwc": _fdd_value(
            nwc,
            "closing_nwc",
            "model['FDD']['nwc']",
        ),
        "nwc_gap": _fdd_value(
            nwc,
            "nwc_gap",
            "model['FDD']['nwc']",
        ),
        "applied_nwc_adjustment": _fdd_value(
            bridge,
            "applied_nwc_price_adjustment",
            "model['FDD']['transaction_bridge']",
        ),
        "cash_like": _fdd_value(
            bridge,
            "cash_like",
            "model['FDD']['transaction_bridge']",
        ),
        "debt_like": _fdd_value(
            bridge,
            "debt_like",
            "model['FDD']['transaction_bridge']",
        ),
        "net_cash": _fdd_value(
            bridge,
            "net_cash",
            "model['FDD']['transaction_bridge']",
        ),
        "non_operating_assets": _fdd_value(
            bridge,
            "non_operating_assets",
            "model['FDD']['transaction_bridge']",
        ),
        "nci": _fdd_value(
            bridge,
            "non_controlling_interests",
            "model['FDD']['transaction_bridge']",
        ),
        "fdd_equity_adjustment": _fdd_value(
            bridge,
            "fdd_equity_adjustment",
            "model['FDD']['transaction_bridge']",
        ),
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "shares_outstanding_millions": shares,
        "value_per_share": value_per_share,
    }

    # Reconcile the strict financial contract before producing Page 5 data.
    _assert_fdd_close(
        base["cash_like"] - base["debt_like"],
        base["net_cash"],
        "Page 5 Net Cash가 model['FDD']와 대사되지 않습니다",
    )
    _assert_fdd_close(
        base["closing_nwc"] - base["normalized_nwc_peg"],
        base["nwc_gap"],
        "Page 5 NWC gap이 model['FDD']와 대사되지 않습니다",
    )
    recalculated_adjustment = (
        base["net_cash"]
        + base["non_operating_assets"]
        - base["nci"]
        + base["applied_nwc_adjustment"]
    )
    _assert_fdd_close(
        recalculated_adjustment,
        base["fdd_equity_adjustment"],
        "Page 5 FDD 지분가치 조정액이 model['FDD']와 대사되지 않습니다",
    )
    _assert_fdd_close(
        enterprise_value + base["fdd_equity_adjustment"],
        equity_value,
        "Page 5 Equity Value가 model['지분가치']와 대사되지 않습니다",
    )
    _assert_fdd_close(
        equity_value / shares,
        value_per_share,
        "Page 5 주당 FDD 가치가 model['지분가치']와 대사되지 않습니다",
    )

    adjustments_2025 = _fdd_component_map(
        qoe,
        "adjustments_2025",
        "model['FDD']['qoe']",
    )
    _assert_fdd_close(
        base["reported_ebitda"] + sum(adjustments_2025.values()),
        base["fdd_ebitda"],
        "Page 5 QoE bridge가 FDD EBITDA와 대사되지 않습니다",
    )

    adjustment_notes = _fdd_optional_text_map(
        qoe,
        ("adjustment_notes",),
        "model['FDD']['qoe']",
    )
    open_adjustments = {
        "특수관계자·보수 정상화",
        "Run-rate / Pro forma 조정",
    }
    register: list[dict[str, object]] = []
    for label, amount in adjustments_2025.items():
        if amount != 0:
            status = "Confirmed"
            default_note = "FDD EBITDA에 정량 반영"
        elif label in open_adjustments:
            status = "Open"
            default_note = "공개정보만으로 정량 확정하지 않음"
        else:
            status = "No Adjustment"
            default_note = "현재 Base Case 정량 조정 없음"
        register.append(
            {
                "항목": label,
                "조정액": amount,
                "처리": adjustment_notes.get(label, default_note),
                "상태": status,
            }
        )

    qoe_margin = _fdd_optional_number(
        qoe,
        ("fdd_ebitda_margin", "fdd_margin"),
    )
    qoe_by_period = {
        "2025A": {
            "reported_ebitda": base["reported_ebitda"],
            "qoe_adjustment": base["fdd_ebitda"] - base["reported_ebitda"],
            "fdd_ebitda": base["fdd_ebitda"],
            "fdd_margin": qoe_margin,
            "adjustments": adjustments_2025,
            "register": register,
        }
    }

    nwc_history = _fdd_history_from_mapping(nwc)
    normalized_peg_ratio = _fdd_optional_number(
        nwc,
        (
            "normalized_peg_ratio",
            "normalized_nwc_peg_ratio",
            "peg_ratio",
        ),
    )

    watchlist_labels = (
        "공급자금융약정 대상 채무",
        "분할 관련 연대채무",
        "소송 총 청구액",
        "기타 debt-like (당기법인세부채 등)",
    )
    debt_watchlist: list[dict[str, object]] = []
    for label in watchlist_labels:
        rate = _lookup_recognition_rate(
            recognition_rates,
            (label,),
            prefixes=("Debt-like",),
        )
        recognized = debt_components.get(label, 0.0)
        raw_amount = debt_inputs.get(label)
        note = classification_notes.get(
            f"Debt-like / {label}",
            classification_notes.get(label, ""),
        )
        # Do not invent a gross public-input amount when Phase 1 did not
        # return one.  Keep it nullable while still showing recognized value.
        if (
            raw_amount is None
            and label not in debt_components
            and rate is None
            and not note
        ):
            continue
        debt_watchlist.append(
            {
                "항목": label,
                "공시_입력금액": raw_amount,
                "인정률": rate,
                "FDD_반영액": recognized,
                "처리": note,
                "상태": "현재 공개정보 기준 Base Case에서 정량 반영하지 않음",
            }
        )

    # Gross inputs used only by temporary overlay.  Preserve explicit Phase 1
    # raw input maps when available; otherwise recover the two exposed slider
    # inputs from recognized components and base recognition rates.
    overlay_cash_inputs = dict(cash_inputs)
    overlay_non_operating_inputs = dict(non_operating_inputs)
    try:
        cash_label, cash_gross, _ = _gross_component_amount(
            recognized_components=cash_components,
            raw_inputs=cash_inputs,
            recognition_rates=recognition_rates,
            aliases=("단기금융상품", "단기금융예치금"),
            rate_prefixes=("Cash-like",),
            path="model['FDD']['transaction_bridge']['cash_like_components']",
        )
        overlay_cash_inputs.setdefault(cash_label, cash_gross)
    except KeyError:
        pass
    try:
        ligachem_label, ligachem_gross, _ = _gross_component_amount(
            recognized_components=non_operating_components,
            raw_inputs=non_operating_inputs,
            recognition_rates=recognition_rates,
            aliases=("리가켐바이오 시장가치", "리가켐바이오"),
            rate_prefixes=("Non-operating", "비영업자산"),
            path=(
                "model['FDD']['transaction_bridge']"
                "['non_operating_asset_components']"
            ),
        )
        overlay_non_operating_inputs.setdefault(
            ligachem_label,
            ligachem_gross,
        )
    except KeyError:
        pass

    return {
        "base": deepcopy(base),
        "qoe_by_period": deepcopy(qoe_by_period),
        "nwc_history": deepcopy(nwc_history),
        "normalized_peg_ratio": normalized_peg_ratio,
        "cash_like_components": deepcopy(cash_components),
        "debt_like_components": deepcopy(debt_components),
        "non_operating_asset_components": deepcopy(non_operating_components),
        "cash_like_input_amounts": deepcopy(overlay_cash_inputs),
        "debt_like_input_amounts": deepcopy(debt_inputs),
        "non_operating_asset_input_amounts": deepcopy(
            overlay_non_operating_inputs
        ),
        "recognition_rates": deepcopy(recognition_rates),
        "classification_notes": deepcopy(classification_notes),
        "debt_like_watchlist": deepcopy(debt_watchlist),
        "forecast_qoe_adjustments": {
            "ebit": deepcopy(
                _fdd_optional_component_map(
                    qoe,
                    ("forecast_ebit_adjustment",),
                    "model['FDD']['qoe']",
                )
            ),
            "da": deepcopy(
                _fdd_optional_component_map(
                    qoe,
                    ("forecast_da_adjustment",),
                    "model['FDD']['qoe']",
                )
            ),
            "lease_capex": deepcopy(
                _fdd_optional_component_map(
                    qoe,
                    ("lease_capex",),
                    "model['FDD']['qoe']",
                )
            ),
            "lease_capex_ratio": deepcopy(
                _fdd_optional_component_map(
                    qoe,
                    ("lease_capex_ratio",),
                    "model['FDD']['qoe']",
                )
            ),
        },
    }


def calculate_fdd_overlay(
    review_data: Mapping[str, object],
    *,
    ligachem_recognition_rate: object,
    short_term_financial_instrument_recognition_rate: object,
    nwc_price_adjustment_recognition_rate: object,
) -> dict[str, float]:
    """Calculate an isolated Page 5 scenario snapshot from copied Base values.

    The function changes only the three user-selected overlay assumptions and
    never mutates the validated Base model.
    """

    data = _require_mapping(review_data, "FDD review data")
    base = _require_mapping(data.get("base"), "FDD review data['base']")
    cash_components = _require_mapping(
        data.get("cash_like_components"),
        "FDD review data['cash_like_components']",
    )
    non_operating_components = _require_mapping(
        data.get("non_operating_asset_components"),
        "FDD review data['non_operating_asset_components']",
    )
    cash_inputs = _require_mapping(
        data.get("cash_like_input_amounts"),
        "FDD review data['cash_like_input_amounts']",
    )
    non_operating_inputs = _require_mapping(
        data.get("non_operating_asset_input_amounts"),
        "FDD review data['non_operating_asset_input_amounts']",
    )
    recognition_rates = _require_mapping(
        data.get("recognition_rates"),
        "FDD review data['recognition_rates']",
    )

    def _percent(value: object, label: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{label}은(는) 숫자여야 합니다.")
        numeric = float(value)
        if not isfinite(numeric) or not 0 <= numeric <= 100:
            raise ValueError(f"{label}은(는) 0~100 범위여야 합니다.")
        return numeric / 100.0

    ligachem_rate = _percent(ligachem_recognition_rate, "리가켐바이오 인정률")
    short_term_rate = _percent(
        short_term_financial_instrument_recognition_rate,
        "단기금융상품 Cash-like 인정률",
    )
    nwc_rate = _percent(
        nwc_price_adjustment_recognition_rate,
        "NWC 가격조정 적용률",
    )

    short_label, short_gross, short_base_recognized = _gross_component_amount(
        recognized_components=cash_components,
        raw_inputs=cash_inputs,
        recognition_rates=recognition_rates,
        aliases=("단기금융상품", "단기금융예치금"),
        rate_prefixes=("Cash-like",),
        path="FDD review data['cash_like_components']",
    )
    ligachem_label, ligachem_gross, ligachem_base_recognized = (
        _gross_component_amount(
            recognized_components=non_operating_components,
            raw_inputs=non_operating_inputs,
            recognition_rates=recognition_rates,
            aliases=("리가켐바이오 시장가치", "리가켐바이오"),
            rate_prefixes=("Non-operating", "비영업자산"),
            path="FDD review data['non_operating_asset_components']",
        )
    )

    base_cash_like = _fdd_value(base, "cash_like", "FDD review data['base']")
    base_non_operating = _fdd_value(
        base,
        "non_operating_assets",
        "FDD review data['base']",
    )
    overlay_cash_like = (
        base_cash_like
        - short_base_recognized
        + short_gross * short_term_rate
    )
    overlay_non_operating = (
        base_non_operating
        - ligachem_base_recognized
        + ligachem_gross * ligachem_rate
    )
    overlay_debt_like = _fdd_value(
        base,
        "debt_like",
        "FDD review data['base']",
    )
    overlay_net_cash = overlay_cash_like - overlay_debt_like
    overlay_applied_nwc = (
        _fdd_value(base, "nwc_gap", "FDD review data['base']")
        * nwc_rate
    )
    overlay_nci = _fdd_value(base, "nci", "FDD review data['base']")
    overlay_adjustment = (
        overlay_net_cash
        + overlay_non_operating
        - overlay_nci
        + overlay_applied_nwc
    )
    overlay_equity = (
        _fdd_value(base, "enterprise_value", "FDD review data['base']")
        + overlay_adjustment
    )
    shares = _fdd_value(
        base,
        "shares_outstanding_millions",
        "FDD review data['base']",
    )
    if shares <= 0:
        raise ValueError("FDD overlay 유통주식수는 0보다 커야 합니다.")
    base_equity = _fdd_value(
        base,
        "equity_value",
        "FDD review data['base']",
    )

    return {
        "cash_like": overlay_cash_like,
        "debt_like": overlay_debt_like,
        "net_cash": overlay_net_cash,
        "short_term_financial_instrument": short_gross * short_term_rate,
        "ligachem": ligachem_gross * ligachem_rate,
        "non_operating_assets": overlay_non_operating,
        "applied_nwc_adjustment": overlay_applied_nwc,
        "fdd_equity_adjustment": overlay_adjustment,
        "equity_value": overlay_equity,
        "value_per_share": overlay_equity / shares,
        "difference_vs_base": overlay_equity - base_equity,
    }
