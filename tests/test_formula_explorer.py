from copy import deepcopy
import json
from pathlib import Path

import pytest

from dashboard_components import (
    FORMULA_RECONCILIATION_TOLERANCE,
    SUPPORTED_FORMULA_STAGES,
    build_formula_explorer_insight,
    build_valuation_formula_catalog,
    prepare_formula_explorer_data,
    reconcile_formula_result,
)
from orion_dcf import run_orion_dcf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"
SNAPSHOT_PATH = (
    PROJECT_ROOT / "artifacts" / "baseline" / "model_snapshot.json"
)


@pytest.fixture(scope="module")
def model():
    return run_orion_dcf(EXCEL_PATH)


@pytest.fixture(scope="module")
def baseline():
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def test_formula_catalog_has_all_supported_stages_and_is_defensive():
    first = build_valuation_formula_catalog()
    second = build_valuation_formula_catalog()

    assert tuple(first) == SUPPORTED_FORMULA_STAGES
    assert all("기호 수식" in first[stage] for stage in first)
    first["FCFF"]["경제적 의미"] = "changed"
    assert second["FCFF"]["경제적 의미"] != "changed"


@pytest.mark.parametrize("stage", ["매출액", "EBIT", "FCFF"])
@pytest.mark.parametrize("year", range(2026, 2031))
def test_forecast_formula_stages_reconcile(model, stage, year):
    result = prepare_formula_explorer_data(model, stage, year)

    assert result["단계"] == stage
    assert result["연도"] == year
    assert result["대사상태"] == "PASS"
    assert abs(result["차이"]) <= FORMULA_RECONCILIATION_TOLERANCE
    assert result["원본 단위"] == "백만원"
    assert result["표시 단위"] == "십억원"


@pytest.mark.parametrize("year", range(2026, 2031))
def test_operating_tax_and_fcff_contract(model, year):
    row = next(item for item in model["전망"] if item["연도"] == year)
    result = prepare_formula_explorer_data(model, "FCFF", year)
    raw = result["원본 입력값"]

    assert raw["영업관련 법인세"] == pytest.approx(
        row["EBIT"] - row["NOPAT"], abs=1e-6
    )
    assert result["재계산값"] == pytest.approx(
        row["NOPAT"] + row["D&A"] - row["Capex"] - row["NWC 증감"],
        abs=1e-6,
    )
    expected_direction = (
        "현금유출" if row["NWC 증감"] > 0 else "현금유입"
    )
    assert expected_direction in build_formula_explorer_insight(result)


def test_wacc_recalculates_from_actual_model_inputs(model):
    result = prepare_formula_explorer_data(model, "WACC")
    inputs = result["원본 입력값"]
    details = result["계산 세부"]

    expected_ke = (
        inputs["무위험수익률"]
        + inputs["베타"] * inputs["주식시장위험프리미엄"]
        + inputs["국가위험프리미엄"]
    )
    expected_after_tax_kd = inputs["세전 타인자본비용"] * (
        1 - inputs["법인세율"]
    )
    expected_wacc = (
        expected_ke * inputs["자기자본 비중"]
        + expected_after_tax_kd * inputs["타인자본 비중"]
        + inputs["WACC 조정"]
    )

    assert details["자기자본비용"] == pytest.approx(expected_ke)
    assert details["세후 타인자본비용"] == pytest.approx(expected_after_tax_kd)
    assert details["자본구조 비중 합계"] == pytest.approx(1.0)
    assert result["재계산값"] == pytest.approx(expected_wacc)
    assert result["대사상태"] == "PASS"


def test_dcf_discount_factors_and_all_value_layers_reconcile(model):
    result = prepare_formula_explorer_data(model, "DCF")
    details = result["계산 세부"]
    wacc = model["WACC"]["WACC"]
    growth = model["DCF"]["영구성장률"]
    fcff = [row["FCFF"] for row in model["전망"]]

    expected_factors = [1 / (1 + wacc) ** period for period in range(1, 6)]
    expected_pv = [
        value * factor
        for value, factor in zip(fcff, expected_factors, strict=True)
    ]
    expected_terminal = fcff[-1] * (1 + growth) / (wacc - growth)
    expected_terminal_pv = expected_terminal * expected_factors[-1]
    expected_enterprise_value = sum(expected_pv) + expected_terminal_pv

    assert wacc > growth
    assert details["할인계수"] == pytest.approx(expected_factors)
    assert details["할인계수"] == pytest.approx(model["DCF"]["할인계수"])
    assert details["FCFF 현재가치"] == pytest.approx(expected_pv)
    assert details["FCFF 현재가치"] == pytest.approx(
        model["DCF"]["FCFF 현재가치"]
    )
    assert details["추정기간 FCFF 현재가치"] == pytest.approx(sum(expected_pv))
    assert details["추정기간 FCFF 현재가치"] == pytest.approx(
        model["DCF"]["추정기간 FCFF 현재가치"]
    )
    assert details["계속기업가치"] == pytest.approx(expected_terminal)
    assert details["계속기업가치"] == pytest.approx(
        model["DCF"]["계속기업가치"]
    )
    assert details["계속기업가치 현재가치"] == pytest.approx(
        expected_terminal_pv
    )
    assert details["계속기업가치 현재가치"] == pytest.approx(
        model["DCF"]["계속기업가치 현재가치"]
    )
    assert result["재계산값"] == pytest.approx(expected_enterprise_value)
    assert result["모델값"] == pytest.approx(model["DCF"]["기업가치"])
    assert result["대사상태"] == "PASS"


def test_equity_value_reconciles_and_sign_convention_is_explicit(model):
    result = prepare_formula_explorer_data(model, "지분가치")
    inputs = result["원본 입력값"]

    assert result["재계산값"] == pytest.approx(
        inputs["기업가치"] + inputs["순비영업 조정액"]
    )
    assert result["모델값"] == pytest.approx(model["지분가치"]["지분가치"])
    assert "비영업자산은 가산" in result["부호규칙"]
    assert "리스부채" in result["부호규칙"]
    assert "비지배지분" in result["부호규칙"]
    assert result["대사상태"] == "PASS"


def test_per_share_value_and_upside_reconcile(model):
    result = prepare_formula_explorer_data(model, "주당 내재가치")
    inputs = result["원본 입력값"]
    details = result["계산 세부"]
    expected_per_share = (
        inputs["지분가치"] / inputs["유통주식수(백만주)"]
    )
    expected_upside = expected_per_share / inputs["기준주가"] - 1

    assert result["재계산값"] == pytest.approx(expected_per_share)
    assert result["모델값"] == pytest.approx(
        model["지분가치"]["주당 내재가치"]
    )
    assert details["재계산 내재 상승여력"] == pytest.approx(expected_upside)
    assert details["모델 내재 상승여력"] == pytest.approx(
        model["지분가치"]["내재 상승여력"]
    )
    assert details["내재 상승여력 차이"] == pytest.approx(0.0)
    assert result["대사상태"] == "PASS"


def test_display_unit_conversion_uses_source_precision(model):
    result = prepare_formula_explorer_data(model, "FCFF", 2026)

    assert result["표시 입력값"]["NOPAT"] == pytest.approx(
        result["원본 입력값"]["NOPAT"] / 1_000
    )
    assert result["재계산값"] == pytest.approx(286462.6575452737)
    assert result["표시 단위"] == "십억원"


@pytest.mark.parametrize("stage", ["매출액", "EBIT", "FCFF"])
def test_forecast_stage_requires_supported_year(model, stage):
    with pytest.raises(ValueError, match="분석 연도"):
        prepare_formula_explorer_data(model, stage)
    with pytest.raises(ValueError, match="지원하지 않는 전망 연도"):
        prepare_formula_explorer_data(model, stage, 2031)


def test_unsupported_stage_is_rejected(model):
    with pytest.raises(ValueError, match="지원하지 않는 가치평가 단계"):
        prepare_formula_explorer_data(model, "배당할인모형")


def test_missing_required_input_is_rejected(model):
    broken = deepcopy(model)
    del broken["전망"][0]["D&A"]

    with pytest.raises(KeyError, match="필수 입력 누락"):
        prepare_formula_explorer_data(broken, "FCFF", 2026)


def test_reconciliation_detects_failure_without_mutating_input():
    source = {
        "재계산값": 101.0,
        "모델값": 100.0,
        "허용오차": 0.01,
    }
    original = deepcopy(source)
    result = reconcile_formula_result(source)

    assert result["대사상태"] == "FAIL"
    assert result["차이"] == pytest.approx(1.0)
    assert source == original


@pytest.mark.parametrize(
    ("stage", "year"),
    [
        ("매출액", 2026),
        ("EBIT", 2027),
        ("FCFF", 2028),
        ("WACC", None),
        ("DCF", None),
        ("지분가치", None),
        ("주당 내재가치", None),
    ],
)
def test_formula_preparation_does_not_mutate_model(model, stage, year):
    original = deepcopy(model)

    prepare_formula_explorer_data(model, stage, year)

    assert model == original


def test_baseline_json_file_and_core_outputs_are_unchanged(model, baseline):
    baseline_bytes_before = SNAPSHOT_PATH.read_bytes()

    prepare_formula_explorer_data(model, "FCFF", 2026)
    prepare_formula_explorer_data(model, "DCF")
    prepare_formula_explorer_data(model, "주당 내재가치")

    assert SNAPSHOT_PATH.read_bytes() == baseline_bytes_before
    expected = baseline["model_outputs"]

    assert model["전망"] == expected["전망"]
    assert model["WACC"]["WACC"] == expected["WACC"]["WACC"]
    assert model["DCF"]["기업가치"] == expected["DCF"]["기업가치"]
    assert model["지분가치"]["지분가치"] == expected["지분가치"]["지분가치"]
    assert model["지분가치"]["주당 내재가치"] == expected["지분가치"][
        "주당 내재가치"
    ]
