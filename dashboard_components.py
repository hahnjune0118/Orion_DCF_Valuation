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
