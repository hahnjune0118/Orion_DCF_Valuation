from copy import deepcopy
from pathlib import Path

import pytest

from dashboard_components import calculate_fdd_overlay, prepare_fdd_review_data
from orion_dcf import run_orion_dcf


ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = ROOT / "data" / "raw" / "orion_dcf.xlsx"
DASHBOARD_PATH = ROOT / "orion_dashboard.py"
DASHBOARD_SOURCE = DASHBOARD_PATH.read_text(encoding="utf-8")
FDD_PAGE_SOURCE = DASHBOARD_SOURCE.split("# FDD-01", 1)[1]


@pytest.fixture(scope="module")
def model():
    return run_orion_dcf(EXCEL_PATH)


@pytest.fixture(scope="module")
def review_data(model):
    return prepare_fdd_review_data(model)


def test_page_5_is_added_after_current_page_1_to_4_order():
    labels = (
        '"1. 가치평가 개요"',
        '"2. 계산구조"',
        '"3. 시나리오 및 주요 가정 검토"',
        '"4. 시장가치 검증"',
        '"5. FDD 및 거래가격 검토"',
    )
    positions = [DASHBOARD_SOURCE.index(label) for label in labels]
    assert positions == sorted(positions)
    assert '"5. FDD 및 거래가격 검토": mo.lazy(' in DASHBOARD_SOURCE
    assert "show_loading_indicator=True" in DASHBOARD_SOURCE


def test_page_5_uses_single_integrated_workbench_instead_of_inner_tabs():
    assert "fdd_inner_tabs = mo.ui.tabs" not in FDD_PAGE_SOURCE
    assert "fdd_workbench_view = mo.vstack" in FDD_PAGE_SOURCE
    for label in (
        "Quality of Earnings (QoE)",
        "Net Working Capital (NWC)",
        "Purchase Price Adjustment (PPA)",
        "Cash-like / Debt-like 및 Net Debt 검토",
        "비영업자산 및 Equity Value 조정",
        "FDD 조정 지분가치 Bridge",
    ):
        assert label in FDD_PAGE_SOURCE


def test_page_5_exposes_2023a_to_2025a_reference_selection():
    for period in ("2023A", "2024A", "2025A"):
        assert period in FDD_PAGE_SOURCE
    assert "fdd_qoe_period_selector" in FDD_PAGE_SOURCE
    assert "fdd-selected-col" in FDD_PAGE_SOURCE


def test_page_5_uses_single_model_and_performs_no_workbook_reload():
    assert "prepare_fdd_review_data(model)" in FDD_PAGE_SOURCE
    assert 'model_mapping.get("FDD")' in (
        ROOT / "dashboard_components.py"
    ).read_text(encoding="utf-8")
    assert "load_workbook" not in FDD_PAGE_SOURCE
    assert "openpyxl" not in FDD_PAGE_SOURCE
    assert "excel_path" not in FDD_PAGE_SOURCE
    assert "run_orion_dcf" not in FDD_PAGE_SOURCE


def test_base_page_5_values_are_the_same_model_values(model, review_data):
    base = review_data["base"]
    assert base["enterprise_value"] == pytest.approx(model["DCF"]["기업가치"])
    assert base["equity_value"] == pytest.approx(model["지분가치"]["지분가치"])
    assert base["value_per_share"] == pytest.approx(
        model["지분가치"]["주당 내재가치"]
    )


def test_default_overlay_reproduces_base_and_does_not_mutate_model(model):
    original = deepcopy(model)
    review = prepare_fdd_review_data(model)
    review_original = deepcopy(review)

    overlay = calculate_fdd_overlay(
        review,
        ligachem_recognition_rate=100,
        short_term_financial_instrument_recognition_rate=100,
        nwc_price_adjustment_recognition_rate=0,
    )

    assert overlay["equity_value"] == pytest.approx(
        model["지분가치"]["지분가치"], abs=1e-6
    )
    assert overlay["value_per_share"] == pytest.approx(
        model["지분가치"]["주당 내재가치"], abs=1e-6
    )
    assert overlay["difference_vs_base"] == pytest.approx(0.0, abs=1e-6)
    assert model == original
    assert review == review_original


def test_80_percent_ligachem_reduces_equity_by_20_percent_of_gross(review_data):
    overlay = calculate_fdd_overlay(
        review_data,
        ligachem_recognition_rate=80,
        short_term_financial_instrument_recognition_rate=100,
        nwc_price_adjustment_recognition_rate=0,
    )
    gross_ligachem = review_data["non_operating_asset_input_amounts"][
        "리가켐바이오 시장가치"
    ]
    assert overlay["difference_vs_base"] == pytest.approx(
        -0.20 * gross_ligachem,
        abs=1e-6,
    )


def test_zero_percent_nwc_recognition_produces_zero_applied_ppa(review_data):
    overlay = calculate_fdd_overlay(
        review_data,
        ligachem_recognition_rate=100,
        short_term_financial_instrument_recognition_rate=100,
        nwc_price_adjustment_recognition_rate=0,
    )
    assert overlay["applied_nwc_adjustment"] == pytest.approx(0.0)


def test_page_5_has_exactly_three_temporary_overlay_sliders():
    controls = FDD_PAGE_SOURCE.split("# FDD-02", 1)[1].split("# FDD-03", 1)[0]
    assert controls.count("mo.ui.slider(") == 3
    assert controls.count("include_input=True") == 3
    assert 'label="리가켐바이오 인정률 (%)"' in controls
    assert 'label="단기금융상품 Cash-like 인정률 (%)"' in controls
    assert 'label="NWC 가격조정 적용률 (%)"' in controls
    assert controls.count("step=5") == 3
    assert controls.count("value=100") == 2
    assert controls.count("value=0") == 1


def test_page_5_uses_dense_workbench_visual_contract():
    for style in (
        "fdd-process-grid",
        "fdd-stage",
        "fdd-pane",
        "fdd-pane-head",
        "fdd-pane-title",
        "fdd-workspace",
    ):
        assert style in FDD_PAGE_SOURCE
    assert "go.Waterfall" not in FDD_PAGE_SOURCE
    assert "Quality of Earnings (QoE)" in FDD_PAGE_SOURCE
    assert "Net Working Capital (NWC)" in FDD_PAGE_SOURCE
    assert "Purchase Price Adjustment (PPA)" in FDD_PAGE_SOURCE
