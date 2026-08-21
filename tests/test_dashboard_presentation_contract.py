from pathlib import Path


DASHBOARD_SOURCE = (
    Path(__file__).resolve().parents[1] / "orion_dashboard.py"
).read_text(encoding="utf-8")


def test_company_identity_and_market_are_presented_in_executive_view():
    assert "주식회사 오리온" in DASHBOARD_SOURCE
    assert "271560" in DASHBOARD_SOURCE
    assert 'class="market-label">코스피</span>' in DASHBOARD_SOURCE


def test_adjustment_sliders_accept_direct_numeric_input():
    assert DASHBOARD_SOURCE.count("include_input=True") == 8
    assert "매출성장률 조정 (%p)" in DASHBOARD_SOURCE
    assert "EBIT Margin 조정 (%p)" in DASHBOARD_SOURCE
    assert "WACC 조정 (%p)" in DASHBOARD_SOURCE
    assert "영구성장률 조정 (%p)" in DASHBOARD_SOURCE


def test_professional_audit_terms_and_standard_reference_are_visible():
    assert "경영진 주장 vs 감사인의 전문가적 판단" in DASHBOARD_SOURCE
    assert "감사기준서 540" in DASHBOARD_SOURCE
    assert "문단 28" in DASHBOARD_SOURCE
    assert "A118" in DASHBOARD_SOURCE
    assert "A121" in DASHBOARD_SOURCE
    assert "A124" in DASHBOARD_SOURCE
    assert "A139" in DASHBOARD_SOURCE
    assert "감사기준서 450 · A6" in DASHBOARD_SOURCE
    assert "왜곡표시 금액" in DASHBOARD_SOURCE
    assert "감사인 범위추정치 민감도" in DASHBOARD_SOURCE
    assert "한국공인회계사회 원문" in DASHBOARD_SOURCE
    assert "Management Case 민감도" not in DASHBOARD_SOURCE
    assert "감사인 독립검토 Case 민감도" not in DASHBOARD_SOURCE


def test_shared_styles_and_two_column_calculation_layout_are_preserved():
    assert "[dashboard_css, dashboard_chapters]" not in DASHBOARD_SOURCE
    assert DASHBOARD_SOURCE.count("dashboard_css,") >= 4
    assert "[formula_explorer_section, fcff_waterfall_row]" in DASHBOARD_SOURCE
    assert "[formula_explorer_left, formula_explorer_right]" in DASHBOARD_SOURCE
    assert "[fcff_waterfall_summary, fcff_waterfall_view]" in DASHBOARD_SOURCE
    assert 'wrap=False' in DASHBOARD_SOURCE


def test_executive_headline_uses_current_market_price_without_duplicate_kpis():
    assert "Valuation 시나리오상 주당 내재가치는" in DASHBOARD_SOURCE
    assert "주식 시장가치" in DASHBOARD_SOURCE
    assert "(오리온 271560; 2026.08.21 기준)" in DASHBOARD_SOURCE
    assert 'class="pitch-inline-meta"' in DASHBOARD_SOURCE
    assert 'class="market-value-group"' in DASHBOARD_SOURCE
    assert ".market-value-group {{" in DASHBOARD_SOURCE
    assert DASHBOARD_SOURCE.count('class="dynamic-value-chip"') == 3
    assert "current_price = 125_000" in DASHBOARD_SOURCE
    assert 'kpi_card(\n                "주당 내재가치"' not in DASHBOARD_SOURCE
    assert 'kpi_card(\n                "상승여력"' not in DASHBOARD_SOURCE


def test_calculation_page_uses_structure_language_and_escaped_css():
    assert "가치평가 산식 및 계산 구조" in DASHBOARD_SOURCE
    assert "도달하는 계산 구조를 검증합니다" in DASHBOARD_SOURCE
    assert "계산 계보" not in DASHBOARD_SOURCE
    assert ".market-label {{" in DASHBOARD_SOURCE
    assert "range=[0, _bridge_peak * 1.18]" in DASHBOARD_SOURCE


def test_sensitivity_page_is_compact_and_omits_redundant_scenario_chart():
    assert "scenario_view =" not in DASHBOARD_SOURCE
    assert "[sensitivity_view, auditor_range_sensitivity_view]" not in DASHBOARD_SOURCE
    assert "widths=[0.25, 0.40, 0.35]" in DASHBOARD_SOURCE
    assert "감사기준서 540 · 문단 28" in DASHBOARD_SOURCE
    assert "감사기준서 540 · A121" in DASHBOARD_SOURCE
    assert "font-size: 13px" in DASHBOARD_SOURCE


def test_calculation_rows_use_balanced_compact_widths():
    assert DASHBOARD_SOURCE.count("widths=[0.22, 0.78]") == 2
    assert DASHBOARD_SOURCE.count('align="stretch"') >= 2
    assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in DASHBOARD_SOURCE
    assert "grid-template-columns: repeat(6, minmax(0, 1fr))" in DASHBOARD_SOURCE
    assert 'class="formula-kpi-grid formula-input-grid"' in DASHBOARD_SOURCE
    assert "_formula_footer = mo.hstack(" in DASHBOARD_SOURCE
