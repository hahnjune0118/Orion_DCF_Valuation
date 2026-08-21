from copy import deepcopy

import pytest

from dashboard_components import (
    build_auditor_range_conclusion,
    build_challenge_conclusion,
    prepare_auditor_range_comparison,
    prepare_challenge_case_comparison,
    prepare_challenge_sensitivity_data,
)


def _model(
    *,
    revenue_multiplier=1.0,
    margin=0.17,
    wacc=0.09,
    growth=0.02,
):
    revenues = [1_000.0, 1_060.0, 1_120.0, 1_180.0, 1_240.0]
    fcff = [100.0, 110.0, 120.0, 130.0, 140.0]
    forecast = [
        {
            "연도": 2026 + index,
            "매출액": revenue * revenue_multiplier,
            "영업이익률": margin,
            "FCFF": cash_flow * revenue_multiplier,
        }
        for index, (revenue, cash_flow) in enumerate(
            zip(revenues, fcff, strict=True)
        )
    ]
    factors = [1 / (1 + wacc) ** period for period in range(1, 6)]
    enterprise_value = sum(
        row["FCFF"] * factor
        for row, factor in zip(forecast, factors, strict=True)
    )
    terminal_value = forecast[-1]["FCFF"] * (1 + growth) / (wacc - growth)
    enterprise_value += terminal_value * factors[-1]
    bridge_adjustment = 50.0
    equity_value = enterprise_value + bridge_adjustment
    shares_million = 10.0
    return {
        "전망": forecast,
        "WACC": {"WACC": wacc},
        "DCF": {
            "영구성장률": growth,
            "기업가치": enterprise_value,
        },
        "지분가치": {
            "지분가치": equity_value,
            "주당 내재가치": equity_value / shares_million,
        },
    }


def _reviewer_adjustments():
    return {
        "revenue_growth_adjustment": -0.015,
        "ebit_margin_adjustment": -0.010,
        "wacc_adjustment": 0.010,
        "terminal_growth_adjustment": -0.005,
    }


def _range_adjustments():
    lower = {
        "revenue_growth_adjustment": -0.015,
        "ebit_margin_adjustment": -0.010,
        "wacc_adjustment": 0.010,
        "terminal_growth_adjustment": -0.005,
    }
    upper = {
        "revenue_growth_adjustment": -0.005,
        "ebit_margin_adjustment": -0.0025,
        "wacc_adjustment": 0.005,
        "terminal_growth_adjustment": -0.0025,
    }
    return lower, upper


def test_challenge_comparison_separates_asserted_and_reviewed_cases():
    management = _model()
    reviewer = _model(
        revenue_multiplier=0.92,
        margin=0.16,
        wacc=0.10,
        growth=0.015,
    )

    result = prepare_challenge_case_comparison(
        management,
        reviewer,
        _reviewer_adjustments(),
        current_price=100.0,
    )

    assert result["경영진 주장"]["WACC"] == pytest.approx(0.09)
    assert result["감사인의 전문가적 판단"]["WACC"] == pytest.approx(0.10)
    assert result["차이"]["평균 EBIT Margin"] == pytest.approx(-0.01)
    assert result["주당가치 차이율"] < 0
    assert result["검토상태"] == "CHALLENGED"


def test_challenge_comparison_does_not_mutate_models_or_adjustments():
    management = _model()
    reviewer = _model(revenue_multiplier=0.95, wacc=0.10, growth=0.015)
    adjustments = _reviewer_adjustments()
    original = deepcopy((management, reviewer, adjustments))

    prepare_challenge_case_comparison(
        management,
        reviewer,
        adjustments,
        current_price=100.0,
    )

    assert (management, reviewer, adjustments) == original


def test_sensitivity_center_reconciles_and_directions_are_economic():
    model = _model()
    result = prepare_challenge_sensitivity_data(model)
    values = result["주당 내재가치"]
    center_row = result["기준 성장률 index"]
    center_column = result["기준 WACC index"]

    assert values[center_row][center_column] == pytest.approx(
        model["지분가치"]["주당 내재가치"]
    )
    assert values[center_row][0] > values[center_row][-1]
    assert values[0][center_column] < values[-1][center_column]
    assert result["기업가치-지분가치 조정"] == pytest.approx(50.0)
    assert result["유통주식수(백만주)"] == pytest.approx(10.0)
    assert result["WACC offsets"][result["기준 WACC index"]] == 0.0
    assert result["성장률 offsets"][result["기준 성장률 index"]] == 0.0


def test_auditor_range_has_ordered_endpoints_midpoint_and_status():
    lower_adjustments, upper_adjustments = _range_adjustments()
    result = prepare_auditor_range_comparison(
        _model(),
        _model(revenue_multiplier=0.90, margin=0.16, wacc=0.10, growth=0.015),
        _model(revenue_multiplier=0.97, margin=0.1675, wacc=0.095, growth=0.0175),
        lower_adjustments,
        upper_adjustments,
        current_price=100.0,
    )

    lower = result["감사인 범위 하단"]["주당 내재가치"]
    upper = result["감사인 범위 상단"]["주당 내재가치"]
    assert lower < upper
    assert result["감사인 범위 중앙값"] == pytest.approx((lower + upper) / 2)
    assert result["범위폭"] == pytest.approx(upper - lower)
    assert result["경영진 주장 포함 여부"] is False
    assert result["검토상태"] == "OUTSIDE_RANGE"
    assert result["가장 가까운 범위 금액"] == pytest.approx(upper)
    assert result["왜곡표시 금액"] == pytest.approx(
        result["경영진 주장"]["주당 내재가치"] - upper
    )
    assert result["왜곡표시 방향"] == "과대"


def test_auditor_range_reports_zero_misstatement_when_assertion_is_inside():
    lower_adjustments, upper_adjustments = _range_adjustments()
    result = prepare_auditor_range_comparison(
        _model(revenue_multiplier=0.95, wacc=0.097, growth=0.016),
        _model(revenue_multiplier=0.90, margin=0.16, wacc=0.10, growth=0.015),
        _model(revenue_multiplier=0.97, margin=0.1675, wacc=0.095, growth=0.0175),
        lower_adjustments,
        upper_adjustments,
        current_price=100.0,
    )

    assert result["경영진 주장 포함 여부"] is True
    assert result["왜곡표시 금액"] == pytest.approx(0.0)
    assert result["왜곡표시 방향"] == "범위 내"


def test_auditor_range_rejects_reversed_assumption_endpoints():
    lower_adjustments, upper_adjustments = _range_adjustments()
    lower_adjustments["revenue_growth_adjustment"] = 0.0

    with pytest.raises(ValueError, match="범위 하단 가정"):
        prepare_auditor_range_comparison(
            _model(),
            _model(),
            _model(),
            lower_adjustments,
            upper_adjustments,
            current_price=100.0,
        )


def test_auditor_range_conclusion_discloses_range_and_limitation():
    lower_adjustments, upper_adjustments = _range_adjustments()
    comparison = prepare_auditor_range_comparison(
        _model(),
        _model(revenue_multiplier=0.90, margin=0.16, wacc=0.10, growth=0.015),
        _model(revenue_multiplier=0.97, margin=0.1675, wacc=0.095, growth=0.0175),
        lower_adjustments,
        upper_adjustments,
        current_price=100.0,
    )

    conclusion = build_auditor_range_conclusion(comparison)

    assert "주당 내재가치 범위" in conclusion
    assert "경영진 주장" in conclusion
    assert "감사증거" in conclusion
    assert "감사의견이 아닙니다" in conclusion


def test_challenge_conclusion_discloses_gap_assumptions_and_limitation():
    comparison = prepare_challenge_case_comparison(
        _model(),
        _model(revenue_multiplier=0.92, margin=0.16, wacc=0.10, growth=0.015),
        _reviewer_adjustments(),
        current_price=100.0,
    )

    conclusion = build_challenge_conclusion(comparison)

    assert "경영진 주장" in conclusion
    assert "감사인의 전문가적 판단" in conclusion
    assert "매출성장률 -1.5%p" in conclusion
    assert "WACC +1.0%p" in conclusion
    assert "감사의견이 아닌" in conclusion


@pytest.mark.parametrize(
    "broken_adjustments",
    [
        {},
        {
            "revenue_growth_adjustment": float("nan"),
            "ebit_margin_adjustment": 0.0,
            "wacc_adjustment": 0.0,
            "terminal_growth_adjustment": 0.0,
        },
    ],
)
def test_invalid_reviewer_adjustments_are_rejected(broken_adjustments):
    with pytest.raises((KeyError, ValueError), match="Challenge|유한"):
        prepare_challenge_case_comparison(
            _model(),
            _model(),
            broken_adjustments,
            current_price=100.0,
        )
