from copy import deepcopy
import json
from pathlib import Path

import pytest

from dashboard_components import (
    FORMULA_RECONCILIATION_TOLERANCE,
    build_formula_explorer_insight,
    prepare_formula_explorer_data,
    reconcile_formula_result,
)
from orion_dcf import run_orion_dcf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"
SNAPSHOT_PATH = PROJECT_ROOT / "artifacts" / "baseline" / "model_snapshot.json"
FORECAST_STAGES = ("매출액", "EBIT", "FCFF")
VALUATION_DATE_STAGES = ("WACC", "DCF", "지분가치", "주당 내재가치")


@pytest.fixture(scope="module")
def model():
    return run_orion_dcf(EXCEL_PATH)


@pytest.mark.parametrize("stage", FORECAST_STAGES + VALUATION_DATE_STAGES)
def test_selected_stage_matches_formula_result(model, stage):
    year = 2026 if stage in FORECAST_STAGES else None
    result = prepare_formula_explorer_data(model, stage, year)

    assert result["단계"] == stage
    assert result["대사상태"] == "PASS"


@pytest.mark.parametrize("year", range(2026, 2031))
@pytest.mark.parametrize("stage", FORECAST_STAGES)
def test_forecast_stage_reacts_to_selected_year(model, stage, year):
    result = prepare_formula_explorer_data(model, stage, year)

    assert result["연도"] == year
    assert str(year) in build_formula_explorer_insight(result)
    assert result["표시 수식"]


@pytest.mark.parametrize("stage", VALUATION_DATE_STAGES)
def test_valuation_date_stage_is_independent_of_year(model, stage):
    base = prepare_formula_explorer_data(model, stage)

    # The dashboard intentionally does not pass the selector value for these
    # stages.  Repeated preparation therefore remains a valuation-date result.
    repeated = prepare_formula_explorer_data(model, stage)

    assert base == repeated
    assert base["연도"] is None


@pytest.mark.parametrize(
    ("stage", "year", "source_unit", "display_unit"),
    [
        ("매출액", 2026, "백만원", "십억원"),
        ("EBIT", 2026, "백만원", "십억원"),
        ("FCFF", 2026, "백만원", "십억원"),
        ("WACC", None, "비율", "%"),
        ("DCF", None, "백만원", "조원"),
        ("지분가치", None, "백만원", "조원"),
        ("주당 내재가치", None, "원/주", "원/주"),
    ],
)
def test_formula_has_numeric_substitution_and_explicit_units(
    model, stage, year, source_unit, display_unit
):
    result = prepare_formula_explorer_data(model, stage, year)

    assert "=" in result["표시 수식"]
    assert any(character.isdigit() for character in result["표시 수식"])
    assert result["원본 단위"] == source_unit
    assert result["표시 단위"] == display_unit


def test_reconciliation_payload_supports_pass_and_fail_badges(model):
    passed = prepare_formula_explorer_data(model, "FCFF", 2026)
    failed = reconcile_formula_result(
        {
            **passed,
            "재계산값": passed["모델값"]
            + FORMULA_RECONCILIATION_TOLERANCE * 10,
        }
    )

    assert passed["대사상태"] == "PASS"
    assert failed["대사상태"] == "FAIL"
    assert abs(failed["차이"]) > failed["허용오차"]


@pytest.mark.parametrize(
    ("year", "direction"),
    [(2026, "현금유출"), (2028, "현금유입"), (2030, "현금유입")],
)
def test_fcff_nwc_sign_rule_is_visible(model, year, direction):
    result = prepare_formula_explorer_data(model, "FCFF", year)

    assert "Capex는 차감" in result["부호규칙"]
    assert direction in build_formula_explorer_insight(result)


def test_wacc_component_payload_is_complete(model):
    result = prepare_formula_explorer_data(model, "WACC")
    inputs = result["원본 입력값"]
    details = result["계산 세부"]

    required_inputs = {
        "무위험수익률",
        "주식시장위험프리미엄",
        "베타",
        "국가위험프리미엄",
        "세전 타인자본비용",
        "법인세율",
        "자기자본 비중",
        "타인자본 비중",
    }
    assert required_inputs <= inputs.keys()
    assert {"자기자본비용", "세후 타인자본비용"} <= details.keys()
    assert result["모델값"] == pytest.approx(model["WACC"]["WACC"])


def test_dcf_detail_payload_is_complete(model):
    result = prepare_formula_explorer_data(model, "DCF")
    details = result["계산 세부"]

    assert len(result["원본 입력값"]["FCFF 전망"]) == 5
    assert len(details["할인계수"]) == 5
    assert len(details["FCFF 현재가치"]) == 5
    assert details["추정기간 FCFF 현재가치"] == pytest.approx(
        model["DCF"]["추정기간 FCFF 현재가치"]
    )
    assert details["계속기업가치"] == pytest.approx(model["DCF"]["계속기업가치"])
    assert details["계속기업가치 현재가치"] == pytest.approx(
        model["DCF"]["계속기업가치 현재가치"]
    )
    assert details["계속기업가치 비중"] == pytest.approx(
        model["DCF"]["계속기업가치 비중"]
    )


def test_equity_bridge_sign_rules_and_details_are_explicit(model):
    result = prepare_formula_explorer_data(model, "지분가치")
    details = result["계산 세부"]

    assert "비영업자산은 가산" in result["부호규칙"]
    assert "금융부채" in result["부호규칙"]
    assert "리스부채" in result["부호규칙"]
    assert "비지배지분" in result["부호규칙"]
    assert details["금융기관차입금"] == pytest.approx(
        model["지분가치"]["금융기관차입금"]
    )


def test_per_share_payload_includes_price_and_upside(model):
    result = prepare_formula_explorer_data(model, "주당 내재가치")
    inputs = result["원본 입력값"]
    details = result["계산 세부"]

    assert inputs["유통주식수(백만주)"] == pytest.approx(
        model["지분가치"]["유통주식수(백만주)"]
    )
    assert inputs["기준주가"] == pytest.approx(model["지분가치"]["기준주가"])
    assert details["모델 내재 상승여력"] == pytest.approx(
        model["지분가치"]["내재 상승여력"]
    )


def test_formula_explorer_does_not_mutate_model_or_forecast(model):
    original_model = deepcopy(model)
    original_forecast = deepcopy(model["전망"])

    for stage in FORECAST_STAGES:
        for year in range(2026, 2031):
            prepare_formula_explorer_data(model, stage, year)
    for stage in VALUATION_DATE_STAGES:
        prepare_formula_explorer_data(model, stage)

    assert model == original_model
    assert model["전망"] == original_forecast


def test_existing_baseline_values_remain_unchanged(model):
    baseline_before = SNAPSHOT_PATH.read_bytes()
    baseline = json.loads(baseline_before.decode("utf-8"))["model_outputs"]

    for stage in ("FCFF", "WACC", "DCF", "지분가치", "주당 내재가치"):
        year = 2026 if stage == "FCFF" else None
        prepare_formula_explorer_data(model, stage, year)

    assert SNAPSHOT_PATH.read_bytes() == baseline_before
    assert model["전망"] == baseline["전망"]
    assert model["WACC"]["WACC"] == baseline["WACC"]["WACC"]
    assert model["DCF"]["기업가치"] == baseline["DCF"]["기업가치"]
    assert model["지분가치"]["지분가치"] == baseline["지분가치"]["지분가치"]
    assert model["지분가치"]["주당 내재가치"] == baseline["지분가치"][
        "주당 내재가치"
    ]
