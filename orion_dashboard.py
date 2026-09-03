import marimo

__generated_with = "0.23.16"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go

    from html import escape
    from pathlib import Path
    from dashboard_components import (
        build_auditor_range_conclusion,
        build_fcff_waterfall_figure,
        build_fcff_waterfall_insight,
        build_formula_explorer_insight,
        build_valuation_formula_catalog,
        calculate_fcff_waterfall_kpis,
        prepare_auditor_range_comparison,
        prepare_challenge_sensitivity_data,
        prepare_fcff_waterfall_data,
        prepare_formula_explorer_data,
        reconcile_formula_result,
        select_forecast_row,
    )
    from orion_dcf import run_orion_dcf
    from market_calibration import (
        calculate_historical_multiple_ranges,
        calculate_trading_comps_ranges,
        load_market_calibration_data,
        prepare_beta_calibration,
        prepare_football_field_ranges,
        solve_reverse_dcf_growth,
    )

    return (
        Path,
        build_auditor_range_conclusion,
        build_fcff_waterfall_figure,
        build_fcff_waterfall_insight,
        build_formula_explorer_insight,
        build_valuation_formula_catalog,
        calculate_fcff_waterfall_kpis,
        calculate_historical_multiple_ranges,
        calculate_trading_comps_ranges,
        escape,
        go,
        mo,
        pd,
        load_market_calibration_data,
        prepare_beta_calibration,
        prepare_football_field_ranges,
        prepare_auditor_range_comparison,
        prepare_challenge_sensitivity_data,
        prepare_fcff_waterfall_data,
        prepare_formula_explorer_data,
        reconcile_formula_result,
        run_orion_dcf,
        select_forecast_row,
        solve_reverse_dcf_growth,
    )


@app.cell
def _(Path, load_market_calibration_data, pd, run_orion_dcf):
    project_root = Path.cwd()

    excel_path = (
        project_root
        / "data"
        / "raw"
        / "orion_dcf.xlsx"
    )

    # 클라우드 실행 시 GitHub에서 Excel 원본을 내려받습니다.
    if not excel_path.exists():
        from tempfile import gettempdir
        from urllib.request import urlretrieve

        cloud_excel_path = Path(gettempdir()) / "orion_dcf.xlsx"

        urlretrieve(
            "https://raw.githubusercontent.com/"
            "hahnjune0118/Orion_DCF_Valuation/"
            "main/data/raw/orion_dcf.xlsx",
            cloud_excel_path,
        )

        excel_path = cloud_excel_path

    model = run_orion_dcf(excel_path)
    forecast_df = pd.DataFrame(model["전망"])
    market_calibration_path = (
        project_root / "data" / "metadata" / "market_calibration.csv"
    )
    if not market_calibration_path.exists():
        from tempfile import gettempdir
        from urllib.request import urlretrieve

        cloud_market_path = Path(gettempdir()) / "market_calibration.csv"
        urlretrieve(
            "https://raw.githubusercontent.com/"
            "hahnjune0118/Orion_DCF_Valuation/"
            "main/data/metadata/market_calibration.csv",
            cloud_market_path,
        )
        market_calibration_path = cloud_market_path
    market_peers = load_market_calibration_data(market_calibration_path)
    return excel_path, forecast_df, market_peers, model


@app.cell
def _(model):
    current_price = 125_000

    value_per_share = float(
        model["지분가치"]["주당 내재가치"]
    )

    enterprise_value = float(
        model["DCF"]["기업가치"]
    )

    equity_value = float(
        model["지분가치"]["지분가치"]
    )

    wacc = float(
        model["WACC"]["WACC"]
    )

    upside = value_per_share / current_price - 1
    return (
        current_price,
        enterprise_value,
        equity_value,
        upside,
        value_per_share,
        wacc,
    )


@app.cell
def _(mo):
    COLORS = {
        "navy": "#102A43",
        "blue": "#1F5A94",
        "teal": "#247B7B",
        "gold": "#C18A2D",
        "orange": "#D97732",
        "ink": "#243B53",
        "muted": "#64748B",
        "line": "#D9E2EC",
        "surface": "#FFFFFF",
        "background": "#F4F7FA",
        "open_blue": "#EAF2F8",
        "open_gold": "#FBF4E6",
        "waterfall_total": "#3478B8",
        "waterfall_increase": "#2A9D8F",
        "waterfall_decrease": "#E07A5F",
    }

    dashboard_css = mo.md(
        f"""
        <style>
            body {{
                background: {COLORS["background"]};
            }}

            .pitch-header {{
                background: {COLORS["navy"]};
                color: white;
                border-radius: 12px;
                padding: 18px 24px 17px 24px;
                margin-bottom: 4px;
            }}

            .company-identity {{
                display: flex;
                align-items: center;
                gap: 9px;
                flex-wrap: wrap;
                margin-bottom: 9px;
            }}

            .company-name {{
                color: #FFFFFF;
                font-size: 15px;
                font-weight: 780;
                letter-spacing: -0.01em;
            }}

            .ticker-code {{
                display: inline-flex;
                align-items: center;
                min-height: 21px;
                padding: 2px 8px;
                border: 1px solid #4C7292;
                border-radius: 999px;
                background: #1D3D5C;
                color: #E7F0F8;
                font-size: 11px;
                font-weight: 760;
                letter-spacing: 0.04em;
            }}

            .market-label {{
                display: inline-flex;
                align-items: center;
                min-height: 21px;
                padding: 2px 8px;
                border: 1px solid #4C7292;
                border-radius: 999px;
                background: #EAF2F8;
                color: #1F5A94;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 0.03em;
            }}

            .pitch-eyebrow {{
                color: #A9C7E8;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 0.11em;
                text-transform: uppercase;
                margin-bottom: 10px;
            }}

            .pitch-title {{
                color: white;
                font-size: 27px;
                font-weight: 750;
                line-height: 1.28;
                margin: 0;
                max-width: 1500px;
            }}

            .dynamic-value-chip {{
                display: inline-flex;
                align-items: center;
                min-height: 34px;
                margin: 2px 3px;
                padding: 2px 10px;
                border: 1px solid #8FB4D2;
                border-radius: 7px;
                background: #F7FBFF;
                color: {COLORS["navy"]};
                box-shadow:
                    inset 0 0 0 1px rgba(31, 90, 148, 0.08),
                    0 2px 6px rgba(0, 0, 0, 0.16);
                font-variant-numeric: tabular-nums;
                font-weight: 820;
                line-height: 1;
                vertical-align: baseline;
                white-space: nowrap;
            }}

            .dynamic-value-chip::before {{
                content: "";
                width: 6px;
                height: 6px;
                margin-right: 7px;
                border-radius: 50%;
                background: {COLORS["teal"]};
                box-shadow: 0 0 0 3px rgba(36, 123, 123, 0.13);
            }}

            .pitch-inline-meta {{
                display: inline-block;
                color: #BFD3E5;
                font-size: 12px;
                font-weight: 650;
                line-height: 1.35;
                vertical-align: middle;
                white-space: nowrap;
            }}

            .market-value-group {{
                display: inline-flex;
                align-items: baseline;
                gap: 3px;
                white-space: nowrap;
            }}

            .pitch-subtitle {{
                color: #D9E6F2;
                font-size: 14px;
                line-height: 1.6;
                margin-top: 12px;
                max-width: 1080px;
            }}

            .pitch-meta {{
                display: inline-block;
                background: #1D3D5C;
                color: #D9E6F2;
                border: 1px solid #315B7D;
                border-radius: 999px;
                padding: 5px 11px;
                margin-top: 16px;
                font-size: 11px;
            }}

            .kpi-card {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["line"]};
                border-radius: 10px;
                padding: 12px 15px;
                min-height: 88px;
                box-shadow: 0 2px 8px rgba(16, 42, 67, 0.06);
            }}

            .kpi-label {{
                color: {COLORS["muted"]};
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.04em;
                margin-bottom: 8px;
            }}

            .kpi-value {{
                color: {COLORS["navy"]};
                font-size: 25px;
                font-weight: 780;
                line-height: 1.15;
            }}

            .kpi-caption {{
                color: {COLORS["muted"]};
                font-size: 11px;
                margin-top: 9px;
                line-height: 1.35;
            }}

            .section-title {{
                color: {COLORS["navy"]};
                font-size: 17px;
                font-weight: 750;
                margin: 6px 0 2px 0;
            }}

            .section-subtitle {{
                color: {COLORS["muted"]};
                font-size: 12px;
                margin-bottom: 8px;
            }}

            .fcff-panel-title {{
                color: {COLORS["navy"]};
                font-size: 15px;
                font-weight: 750;
                margin-bottom: 4px;
            }}

            .fcff-panel-caption {{
                color: {COLORS["muted"]};
                font-size: 12px;
                line-height: 1.45;
                margin-bottom: 14px;
            }}

            .fcff-mini-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 8px;
                margin: 9px 0;
            }}

            .fcff-mini-kpi {{
                background: {COLORS["background"]};
                border-radius: 8px;
                padding: 10px;
            }}

            .fcff-mini-label {{
                color: {COLORS["muted"]};
                font-size: 10px;
                font-weight: 700;
            }}

            .fcff-mini-value {{
                color: {COLORS["navy"]};
                font-size: 17px;
                font-weight: 780;
                margin-top: 3px;
            }}

            .fcff-insight {{
                border-left: 3px solid {COLORS["gold"]};
                background: {COLORS["open_gold"]};
                color: {COLORS["ink"]};
                border-radius: 0 8px 8px 0;
                padding: 11px 12px;
                font-size: 11px;
                line-height: 1.55;
                margin-top: 10px;
            }}

            .formula-lineage {{
                display: flex;
                align-items: center;
                gap: 7px;
                flex-wrap: wrap;
                margin: 6px 0 8px 0;
            }}

            .formula-node {{
                border-radius: 999px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 700;
                white-space: nowrap;
            }}

            .formula-node-current {{
                background: {COLORS["blue"]};
                color: #FFFFFF;
                box-shadow: 0 2px 6px rgba(31, 90, 148, 0.18);
            }}

            .formula-node-complete {{
                background: #DDF3F0;
                color: #176B63;
                border: 1px solid #ABDCD5;
            }}

            .formula-node-future {{
                background: #EEF2F6;
                color: {COLORS["muted"]};
                border: 1px solid {COLORS["line"]};
            }}

            .formula-node-aux {{
                background: {COLORS["open_gold"]};
                color: #8A5A10;
                border: 1px dashed #D7A344;
            }}

            .formula-arrow {{
                color: #9AAABD;
                font-size: 13px;
                font-weight: 700;
            }}

            .formula-panel {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["line"]};
                border-radius: 10px;
                padding: 12px;
                min-height: 0;
                box-shadow: 0 2px 8px rgba(16, 42, 67, 0.05);
            }}

            .formula-label {{
                color: {COLORS["muted"]};
                font-size: 10px;
                font-weight: 750;
                letter-spacing: 0.05em;
                margin-bottom: 5px;
                text-transform: uppercase;
            }}

            .formula-copy {{
                color: {COLORS["ink"]};
                font-size: 12px;
                line-height: 1.45;
                margin-bottom: 8px;
            }}

            .formula-equation {{
                background: #F7FAFC;
                border: 1px solid {COLORS["line"]};
                border-radius: 9px;
                padding: 14px 16px;
                margin: 10px 0 12px 0;
            }}

            .formula-substitution {{
                color: {COLORS["navy"]};
                font-size: 17px;
                font-weight: 760;
                line-height: 1.5;
                margin-top: 4px;
            }}

            .formula-kpi-grid {{
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 6px;
                margin: 8px 0;
            }}

            .formula-input-grid {{
                grid-template-columns: repeat(6, minmax(0, 1fr));
            }}

            .formula-status-inline {{
                display: flex;
                align-items: center;
                gap: 8px;
                min-width: 0;
            }}

            .formula-insight-compact {{
                flex: 1;
                min-width: 0;
                border-left: 3px solid {COLORS["gold"]};
                background: {COLORS["open_gold"]};
                color: {COLORS["ink"]};
                border-radius: 0 7px 7px 0;
                padding: 7px 9px;
                font-size: 11px;
                line-height: 1.35;
            }}

            .katex-display {{
                margin: 0.25em 0 !important;
            }}

            .formula-kpi {{
                background: {COLORS["background"]};
                border-radius: 8px;
                padding: 8px 9px;
                border-top: 3px solid {COLORS["blue"]};
            }}

            .formula-kpi-label {{
                color: {COLORS["muted"]};
                font-size: 9px;
                font-weight: 700;
            }}

            .formula-kpi-value {{
                color: {COLORS["navy"]};
                font-size: 14px;
                font-weight: 780;
                margin-top: 4px;
                word-break: break-word;
            }}

            .formula-badge {{
                display: inline-block;
                border-radius: 999px;
                padding: 5px 10px;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.04em;
            }}

            .formula-badge-pass {{
                background: #DDF3F0;
                color: #176B63;
                border: 1px solid #ABDCD5;
            }}

            .formula-badge-fail {{
                background: #FBE9E4;
                color: #B75036;
                border: 1px solid #F0B7A8;
            }}

            .formula-insight {{
                border-left: 3px solid {COLORS["gold"]};
                background: {COLORS["open_gold"]};
                color: {COLORS["ink"]};
                border-radius: 0 8px 8px 0;
                padding: 11px 12px;
                font-size: 11px;
                line-height: 1.55;
                margin-top: 12px;
            }}

            .formula-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 11px;
                margin-top: 10px;
            }}

            .formula-table th {{
                text-align: right;
                color: {COLORS["muted"]};
                font-weight: 700;
                border-bottom: 1px solid {COLORS["line"]};
                padding: 6px 7px;
            }}

            .formula-table th:first-child,
            .formula-table td:first-child {{
                text-align: left;
            }}

            .formula-table td {{
                text-align: right;
                color: {COLORS["ink"]};
                border-bottom: 1px solid #E9EEF3;
                padding: 6px 7px;
            }}

            .chapter-intro {{
                background: {COLORS["surface"]};
                border-left: 4px solid {COLORS["blue"]};
                border-radius: 0 10px 10px 0;
                padding: 9px 14px;
                margin-bottom: 4px;
            }}

            .chapter-kicker {{
                color: {COLORS["blue"]};
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.10em;
                text-transform: uppercase;
                margin-bottom: 4px;
            }}

            .chapter-title {{
                color: {COLORS["navy"]};
                font-size: 20px;
                font-weight: 780;
                line-height: 1.3;
            }}

            .chapter-copy {{
                color: {COLORS["muted"]};
                font-size: 12px;
                line-height: 1.55;
                margin-top: 5px;
            }}

            .challenge-panel {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["line"]};
                border-radius: 10px;
                padding: 12px;
                box-shadow: 0 2px 8px rgba(16, 42, 67, 0.05);
            }}

            .challenge-panel-head {{
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 5px;
            }}

            .challenge-panel-caption {{
                color: {COLORS["muted"]};
                font-size: 13px;
                line-height: 1.45;
                margin-top: 3px;
            }}

            .challenge-case-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 10px;
                margin: 12px 0;
            }}

            .challenge-case {{
                background: {COLORS["background"]};
                border-radius: 9px;
                padding: 13px;
                border-top: 3px solid {COLORS["blue"]};
            }}

            .challenge-case-review {{
                border-top-color: {COLORS["gold"]};
            }}

            .challenge-case-name {{
                color: {COLORS["muted"]};
                font-size: 13px;
                font-weight: 750;
                margin-bottom: 4px;
            }}

            .challenge-case-value {{
                color: {COLORS["navy"]};
                font-size: 22px;
                font-weight: 800;
            }}

            .challenge-case-meta {{
                color: {COLORS["muted"]};
                font-size: 13px;
                line-height: 1.5;
                margin-top: 5px;
            }}

            .challenge-status {{
                display: inline-block;
                border-radius: 999px;
                background: {COLORS["open_gold"]};
                color: #8A5A10;
                border: 1px solid #E4C27B;
                padding: 5px 10px;
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 0.04em;
            }}

            .challenge-conclusion {{
                border-left: 3px solid {COLORS["gold"]};
                background: {COLORS["open_gold"]};
                color: {COLORS["ink"]};
                border-radius: 0 8px 8px 0;
                padding: 12px 13px;
                font-size: 13px;
                line-height: 1.6;
                margin-top: 12px;
            }}

            .audit-standard {{
                background: {COLORS["open_blue"]};
                border: 1px solid #C9DCEB;
                border-radius: 8px;
                padding: 8px 10px;
                margin-top: 7px;
            }}

            .audit-standard-ref {{
                color: {COLORS["blue"]};
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 0.04em;
                margin-bottom: 4px;
            }}

            .audit-standard-quote {{
                color: {COLORS["ink"]};
                font-size: 13px;
                line-height: 1.55;
                margin: 0;
            }}

            .audit-standard-source {{
                color: {COLORS["blue"]};
                font-size: 13px;
                font-weight: 700;
                text-decoration: none;
                white-space: nowrap;
            }}

            .audit-standard-source:hover {{
                text-decoration: underline;
            }}

            .model-governance {{
                margin-top: 10px;
                padding: 9px 10px;
                border: 1px solid {COLORS["line"]};
                border-radius: 8px;
                background: {COLORS["soft"]};
            }}

            .model-governance summary {{
                cursor: pointer;
                color: {COLORS["navy"]};
                font-size: 12px;
                font-weight: 800;
            }}

            .model-governance[open] summary {{
                margin-bottom: 8px;
            }}

            .challenge-table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 13px;
                margin-top: 12px;
            }}

            .range-control-label {{
                color: {COLORS["navy"]};
                font-size: 13px;
                font-weight: 800;
                margin: 5px 0 2px;
            }}

            .audit-standard-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 8px;
                margin-top: 10px;
            }}

            .audit-standard-grid .audit-standard {{
                margin-top: 0;
            }}

            .standard-inline {{
                border-left: 3px solid {COLORS["blue"]};
                background: {COLORS["open_blue"]};
                color: {COLORS["ink"]};
                border-radius: 0 7px 7px 0;
                padding: 7px 10px;
                font-size: 12px;
                line-height: 1.45;
            }}

            .standard-inline strong {{
                color: {COLORS["blue"]};
            }}

            .misstatement-card {{
                display: grid;
                grid-template-columns: 1fr auto;
                align-items: center;
                gap: 12px;
                margin-top: 8px;
                padding: 9px 11px;
                border: 1px solid #E4C27B;
                border-radius: 8px;
                background: {COLORS["open_gold"]};
            }}

            .misstatement-label {{
                color: #8A5A10;
                font-size: 12px;
                font-weight: 800;
            }}

            .misstatement-value {{
                color: {COLORS["navy"]};
                font-size: 20px;
                font-weight: 820;
                font-variant-numeric: tabular-nums;
                white-space: nowrap;
            }}

            .challenge-table th,
            .challenge-table td {{
                padding: 7px 8px;
                border-bottom: 1px solid #E9EEF3;
                text-align: right;
            }}

            .challenge-table th {{
                color: {COLORS["muted"]};
                font-weight: 750;
            }}

            .challenge-table th:first-child,
            .challenge-table td:first-child {{
                text-align: left;
            }}

            .market-grid {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 12px;
                margin: 12px 0;
            }}

            .market-card {{
                background: {COLORS["surface"]};
                border: 1px solid #CBD5E1;
                border-top: 3px solid {COLORS["blue"]};
                border-radius: 10px;
                padding: 15px 16px;
                min-height: 116px;
                box-shadow: 0 2px 8px rgba(16, 42, 67, 0.05);
            }}

            .market-card-label {{
                color: #475569;
                font-size: 14px;
                font-weight: 780;
                line-height: 1.4;
            }}

            .market-card-value {{
                color: {COLORS["navy"]};
                font-size: 27px;
                font-weight: 810;
                margin-top: 7px;
                font-variant-numeric: tabular-nums;
            }}

            .market-card-note {{
                color: #475569;
                font-size: 14px;
                line-height: 1.55;
                margin-top: 7px;
            }}

            .market-section {{
                margin-top: 18px;
                min-width: 0;
            }}

            .market-section-title {{
                color: {COLORS["navy"]};
                font-size: 22px;
                font-weight: 800;
                line-height: 1.35;
                margin-bottom: 4px;
            }}

            .market-section-copy {{
                color: #475569;
                font-size: 15px;
                line-height: 1.6;
                margin-bottom: 10px;
                max-width: 1180px;
            }}

            .market-chart-card {{
                min-width: 0;
                overflow-x: auto;
                background: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 8px 10px 2px;
            }}

            .chart-insight {{
                margin: 8px 0 16px;
                padding: 11px 13px;
                border-left: 3px solid {COLORS["teal"]};
                border-radius: 0 8px 8px 0;
                background: #EDF7F6;
                color: #243B53;
                font-size: 15px;
                line-height: 1.6;
            }}

            .reverse-concept {{
                background: #F7FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 16px;
            }}

            .reverse-flow {{
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 10px;
                margin-top: 13px;
            }}

            .reverse-step {{
                min-width: 0;
                background: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-top: 3px solid {COLORS["teal"]};
                border-radius: 9px;
                padding: 12px;
            }}

            .reverse-step-number {{
                color: {COLORS["teal"]};
                font-size: 13px;
                font-weight: 800;
            }}

            .reverse-step-title {{
                color: {COLORS["navy"]};
                font-size: 15px;
                font-weight: 800;
                line-height: 1.4;
                margin-top: 3px;
            }}

            .reverse-step-copy {{
                color: #475569;
                font-size: 14px;
                line-height: 1.5;
                margin-top: 4px;
            }}

            .reverse-recon-grid {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 9px;
                margin-top: 12px;
            }}

            .reverse-recon-item {{
                min-width: 0;
                background: #F7FAFC;
                border: 1px solid #D9E2EC;
                border-radius: 8px;
                padding: 10px 11px;
            }}

            .reverse-recon-label {{
                color: #475569;
                font-size: 13px;
                font-weight: 700;
                line-height: 1.4;
            }}

            .reverse-recon-value {{
                color: {COLORS["navy"]};
                font-size: 18px;
                font-weight: 820;
                line-height: 1.25;
                margin-top: 3px;
                overflow-wrap: anywhere;
            }}

            .reconciled-badge {{
                display: inline-flex;
                align-items: center;
                border-radius: 999px;
                padding: 5px 10px;
                background: #DDF3F0;
                border: 1px solid #ABDCD5;
                color: #176B63;
                font-size: 13px;
                font-weight: 820;
                letter-spacing: 0.03em;
            }}

            .interpretation-panel {{
                background: #F7FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 15px 17px;
                color: #243B53;
                font-size: 15px;
                line-height: 1.65;
            }}

            .interpretation-panel ul {{
                margin: 8px 0 0 20px;
                padding: 0;
            }}

            .interpretation-panel li {{
                margin: 5px 0;
            }}

            .market-table-wrap {{
                overflow-x: auto;
                border: 1px solid {COLORS["line"]};
                border-radius: 9px;
                background: {COLORS["surface"]};
            }}

            .market-table {{
                width: 100%;
                min-width: 900px;
                border-collapse: collapse;
                font-size: 14px;
            }}

            .market-table th,
            .market-table td {{
                padding: 7px 8px;
                border-bottom: 1px solid #E9EEF3;
                text-align: right;
                white-space: nowrap;
            }}

            .market-table th {{
                color: #334E68;
                font-weight: 800;
                background: #F8FAFC;
            }}

            .market-table th:first-child,
            .market-table td:first-child {{
                text-align: left;
            }}

            .market-warning {{
                border-left: 3px solid {COLORS["orange"]};
                background: #FFF4ED;
                color: {COLORS["ink"]};
                border-radius: 0 7px 7px 0;
                padding: 8px 10px;
                font-size: 14px;
                line-height: 1.6;
            }}

            @media (max-width: 900px) {{
                .formula-kpi-grid,
                .formula-input-grid,
                .market-grid {{
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }}

                .reverse-flow,
                .reverse-recon-grid {{
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }}

                .pitch-header {{
                    padding: 22px 20px;
                }}

                .pitch-title {{
                    font-size: 22px;
                }}

                .market-section-title {{
                    font-size: 20px;
                }}
            }}

            @media (max-width: 640px) {{
                .formula-kpi-grid,
                .challenge-case-grid,
                .market-grid,
                .reverse-flow,
                .reverse-recon-grid {{
                    grid-template-columns: 1fr;
                }}

                .chapter-title {{
                    font-size: 18px;
                }}

                .challenge-panel-head {{
                    display: block;
                }}

                .challenge-status {{
                    margin-top: 8px;
                }}

                .market-card-value {{
                    font-size: 25px;
                }}

                .market-chart-card {{
                    padding: 4px;
                }}
            }}
        </style>
        """
    )
    return COLORS, dashboard_css


@app.cell
def _(mo):
    def kpi_card(label, value, caption, accent):
        return mo.md(
            f"""
            <div class="kpi-card" style="border-top: 4px solid {accent};">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-caption">{caption}</div>
            </div>
            """
        )

    return (kpi_card,)


@app.cell
def _(current_price, mo, upside, value_per_share):
    dashboard_header = mo.md(
        f"""
        <div class="pitch-header">
            <div class="company-identity">
                <span class="company-name">주식회사 오리온</span>
                <span class="ticker-code">271560</span>
                <span class="market-label">코스피</span>
            </div>
            <div class="pitch-eyebrow">
                DCF VALUATION · EXECUTIVE VIEW
            </div>

            <div class="pitch-title">
                Valuation 시나리오상 Implied Share Price는
                <span class="dynamic-value-chip" title="모델 계산값">{value_per_share:,.0f}</span>원으로
                Current Share Price
                <span class="market-value-group"><span class="dynamic-value-chip" title="시장 기준값">{current_price:,.0f}</span>원<span class="pitch-inline-meta">(오리온 271560; 2026.08.21 기준)</span></span>
                대비 <span class="dynamic-value-chip" title="모델 계산값">{upside:.1%}</span>의
                상승여력을 시사합니다.
            </div>

            <div class="pitch-subtitle">
                지역별 매출액 전망과 영업수익성, 투자소요 및
                운전자본 변동을 FCFF로 전환하여 산정했습니다.
                가치 변동의 핵심 변수는 WACC와 Terminal Growth Rate입니다.
            </div>

            <div class="pitch-meta">
                평가기준일 2025.12.31 · FCFF 기준 DCF · 단위: 백만원, 원
            </div>
        </div>
        """
    )
    return (dashboard_header,)


@app.cell
def _(
    COLORS,
    enterprise_value,
    equity_value,
    kpi_card,
    mo,
    wacc,
):
    kpi_strip = mo.hstack(
        [
            kpi_card(
                "Enterprise Value (EV)",
                f"{enterprise_value / 1_000_000:.2f}조원",
                "FCFF 현재가치 + 계속가치",
                COLORS["teal"],
            ),
            kpi_card(
                "Equity Value",
                f"{equity_value / 1_000_000:.2f}조원",
                "Enterprise Value (EV)에서 Net Debt 등 조정",
                COLORS["blue"],
            ),
            kpi_card(
                "WACC",
                f"{wacc:.2%}",
                "기준 할인율",
                COLORS["orange"],
            ),
        ],
        widths="equal",
        gap=1,
    )
    return (kpi_strip,)


@app.cell
def _(dashboard_header, kpi_strip, mo):
    executive_top = mo.vstack(
        [
            dashboard_header,
            kpi_strip,
        ],
        gap=1.1,
    )
    return (executive_top,)


@app.cell
def _():
    def apply_chart_style(fig, height=360):
        fig.update_layout(
            height=height,
            margin=dict(l=45, r=35, t=75, b=45),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            font=dict(
                family="Arial, Pretendard, sans-serif",
                color="#243B53",
                size=12,
            ),
            title=dict(
                font=dict(size=16, color="#102A43"),
                x=0.02,
                xanchor="left",
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            hoverlabel=dict(
                bgcolor="#FFFFFF",
                bordercolor="#D9E2EC",
                font_color="#243B53",
            ),
        )

        fig.update_xaxes(
            showgrid=False,
            linecolor="#D9E2EC",
            tickfont=dict(color="#64748B"),
        )
        fig.update_yaxes(
            gridcolor="#E9EEF3",
            zeroline=False,
            linecolor="#D9E2EC",
            tickfont=dict(color="#64748B"),
        )
        return fig

    return (apply_chart_style,)


@app.cell
def _(model, prepare_challenge_sensitivity_data):
    management_sensitivity = prepare_challenge_sensitivity_data(model)
    return (management_sensitivity,)


@app.cell
def _(
    COLORS,
    apply_chart_style,
    go,
    management_sensitivity,
):
    _management_values = [
        [value / 1_000 for value in row]
        for row in management_sensitivity["주당 내재가치"]
    ]
    _management_text = []
    for _row_index, _row in enumerate(_management_values):
        _text_row = []
        for _column_index, _value in enumerate(_row):
            if (
                _row_index == management_sensitivity["기준 성장률 index"]
                and _column_index
                == management_sensitivity["기준 WACC index"]
            ):
                _text_row.append(f"● {_value:,.0f}")
            else:
                _text_row.append(f"{_value:,.0f}")
        _management_text.append(_text_row)

    sensitivity_fig = go.Figure(
        data=go.Heatmap(
            z=_management_values,
            x=[
                f"{rate:.2%}"
                for rate in management_sensitivity["WACC"]
            ],
            y=[
                f"{rate:.2%}"
                for rate in management_sensitivity["영구성장률"]
            ],
            text=_management_text,
            texttemplate="%{text}",
            textfont=dict(size=12),
            colorscale=[
                [0.00, "#EAF2F8"],
                [0.45, "#9DBDD8"],
                [1.00, COLORS["blue"]],
            ],
            colorbar=dict(
                title="천원",
                thickness=12,
            ),
            xgap=2,
            ygap=2,
            hovertemplate=(
                "WACC %{x}<br>"
                "Terminal Growth Rate %{y}<br>"
                "Implied Share Price %{z:,.0f}천원"
                "<extra></extra>"
            ),
        )
    )

    sensitivity_fig.update_layout(
        title=(
            "<b>Base Case Sensitivity</b>"
            "<br><sup>WACC × Terminal Growth Rate · Implied Share Price, 천원 · ● 기준</sup>"
        )
    )

    sensitivity_fig.update_xaxes(
        title="WACC",
        side="top",
    )

    sensitivity_fig.update_yaxes(
        title="Terminal Growth Rate",
    )

    sensitivity_fig = apply_chart_style(
        sensitivity_fig,
        height=255,
    )
    return (sensitivity_fig,)


@app.cell
def _(current_price, excel_path, pd, run_orion_dcf):
    scenario_inputs = {
        "보수": {
            "revenue_growth_adjustment": -0.015,
            "ebit_margin_adjustment": -0.010,
            "wacc_adjustment": 0.010,
            "terminal_growth_adjustment": -0.005,
        },
        "기준": {
            "revenue_growth_adjustment": 0.000,
            "ebit_margin_adjustment": 0.000,
            "wacc_adjustment": 0.000,
            "terminal_growth_adjustment": 0.000,
        },
        "낙관": {
            "revenue_growth_adjustment": 0.015,
            "ebit_margin_adjustment": 0.010,
            "wacc_adjustment": -0.0075,
            "terminal_growth_adjustment": 0.005,
        },
    }

    scenario_records = []

    for scenario_name, assumptions in scenario_inputs.items():
        scenario_model = run_orion_dcf(
            excel_path,
            **assumptions,
        )

        scenario_records.append(
            {
                "시나리오": scenario_name,
                "주당 내재가치": (
                    scenario_model["지분가치"]["주당 내재가치"]
                    / 1_000
                ),
                "상승여력": (
                    scenario_model["지분가치"]["주당 내재가치"]
                    / current_price
                    - 1
                ),
            }
        )

    scenario_df = pd.DataFrame(scenario_records)
    return (scenario_df,)


@app.cell
def _(COLORS, apply_chart_style, current_price, go, scenario_df):
    scenario_colors = [
        "#AAB7C4",
        COLORS["blue"],
        COLORS["gold"],
    ]

    scenario_fig = go.Figure(
        go.Bar(
            x=scenario_df["시나리오"],
            y=scenario_df["주당 내재가치"],
            marker_color=scenario_colors,
            text=[
                f"{value:,.0f}천원"
                for value in scenario_df["주당 내재가치"]
            ],
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "%{x}<br>"
                "Implied Share Price %{y:,.0f}천원"
                "<extra></extra>"
            ),
        )
    )

    scenario_fig.add_hline(
        y=current_price / 1_000,
        line_dash="dot",
        line_color=COLORS["ink"],
        line_width=1.5,
        annotation_text=f"기준주가 {current_price / 1_000:,.0f}천원",
        annotation_position="bottom right",
    )

    scenario_fig.update_layout(
        title=(
            "<b>시나리오별 Implied Share Price</b>"
            "<br><sup>사업가정과 할인율을 동시 조정</sup>"
        ),
        showlegend=False,
    )

    scenario_fig.update_yaxes(
        title="천원",
        range=[
            0,
            scenario_df["주당 내재가치"].max() * 1.22,
        ],
    )

    scenario_fig = apply_chart_style(
        scenario_fig,
        height=350,
    )
    return (scenario_fig,)


@app.cell
def _(mo):
    auditor_lower_revenue_growth = mo.ui.slider(
        start=-3.0,
        stop=0.0,
        step=0.25,
        value=-1.5,
        label="범위 하단 (%p)",
        show_value=False,
        include_input=True,
        debounce=True,
        full_width=True,
    )
    auditor_upper_revenue_growth = mo.ui.slider(
        start=-3.0,
        stop=0.0,
        step=0.25,
        value=-0.5,
        label="범위 상단 (%p)",
        show_value=False,
        include_input=True,
        debounce=True,
        full_width=True,
    )
    auditor_lower_ebit_margin = mo.ui.slider(
        start=-3.0,
        stop=1.0,
        step=0.25,
        value=-1.0,
        label="범위 하단 (%p)",
        show_value=False,
        include_input=True,
        debounce=True,
        full_width=True,
    )
    auditor_upper_ebit_margin = mo.ui.slider(
        start=-3.0,
        stop=1.0,
        step=0.25,
        value=-0.25,
        label="범위 상단 (%p)",
        show_value=False,
        include_input=True,
        debounce=True,
        full_width=True,
    )
    auditor_lower_wacc = mo.ui.slider(
        start=0.0,
        stop=2.0,
        step=0.10,
        value=1.0,
        label="범위 하단 가치용 (%p)",
        show_value=False,
        include_input=True,
        debounce=True,
        full_width=True,
    )
    auditor_upper_wacc = mo.ui.slider(
        start=0.0,
        stop=2.0,
        step=0.10,
        value=0.5,
        label="범위 상단 가치용 (%p)",
        show_value=False,
        include_input=True,
        debounce=True,
        full_width=True,
    )
    auditor_lower_terminal_growth = mo.ui.slider(
        start=-1.5,
        stop=0.0,
        step=0.25,
        value=-0.5,
        label="범위 하단 (%p)",
        show_value=False,
        include_input=True,
        debounce=True,
        full_width=True,
    )
    auditor_upper_terminal_growth = mo.ui.slider(
        start=-1.5,
        stop=0.0,
        step=0.25,
        value=-0.25,
        label="범위 상단 (%p)",
        show_value=False,
        include_input=True,
        debounce=True,
        full_width=True,
    )
    return (
        auditor_lower_ebit_margin,
        auditor_lower_revenue_growth,
        auditor_lower_terminal_growth,
        auditor_lower_wacc,
        auditor_upper_ebit_margin,
        auditor_upper_revenue_growth,
        auditor_upper_terminal_growth,
        auditor_upper_wacc,
    )


@app.cell
def _(
    auditor_lower_ebit_margin,
    auditor_lower_revenue_growth,
    auditor_lower_terminal_growth,
    auditor_lower_wacc,
    auditor_upper_ebit_margin,
    auditor_upper_revenue_growth,
    auditor_upper_terminal_growth,
    auditor_upper_wacc,
    build_auditor_range_conclusion,
    current_price,
    excel_path,
    model,
    prepare_auditor_range_comparison,
    prepare_challenge_sensitivity_data,
    run_orion_dcf,
):
    auditor_lower_adjustments = {
        "revenue_growth_adjustment": auditor_lower_revenue_growth.value / 100,
        "ebit_margin_adjustment": auditor_lower_ebit_margin.value / 100,
        "wacc_adjustment": auditor_lower_wacc.value / 100,
        "terminal_growth_adjustment": auditor_lower_terminal_growth.value / 100,
    }
    auditor_upper_adjustments = {
        "revenue_growth_adjustment": auditor_upper_revenue_growth.value / 100,
        "ebit_margin_adjustment": auditor_upper_ebit_margin.value / 100,
        "wacc_adjustment": auditor_upper_wacc.value / 100,
        "terminal_growth_adjustment": auditor_upper_terminal_growth.value / 100,
    }
    auditor_lower_model = run_orion_dcf(
        excel_path,
        **auditor_lower_adjustments,
    )
    auditor_upper_model = run_orion_dcf(
        excel_path,
        **auditor_upper_adjustments,
    )
    auditor_range_comparison = prepare_auditor_range_comparison(
        model,
        auditor_lower_model,
        auditor_upper_model,
        auditor_lower_adjustments,
        auditor_upper_adjustments,
        current_price,
    )
    auditor_range_conclusion = build_auditor_range_conclusion(
        auditor_range_comparison
    )
    auditor_lower_sensitivity = prepare_challenge_sensitivity_data(
        auditor_lower_model
    )
    auditor_upper_sensitivity = prepare_challenge_sensitivity_data(
        auditor_upper_model
    )
    return (
        auditor_lower_adjustments,
        auditor_lower_model,
        auditor_lower_sensitivity,
        auditor_range_comparison,
        auditor_range_conclusion,
        auditor_upper_adjustments,
        auditor_upper_model,
        auditor_upper_sensitivity,
    )


@app.cell
def _(
    COLORS,
    apply_chart_style,
    auditor_lower_sensitivity,
    auditor_upper_sensitivity,
    go,
):
    _lower_values = [
        [value / 1_000 for value in row]
        for row in auditor_lower_sensitivity["주당 내재가치"]
    ]
    _upper_values = [
        [value / 1_000 for value in row]
        for row in auditor_upper_sensitivity["주당 내재가치"]
    ]
    _midpoint_values = [
        [
            (lower_value + upper_value) / 2
            for lower_value, upper_value in zip(
                lower_row, upper_row, strict=True
            )
        ]
        for lower_row, upper_row in zip(
            _lower_values, _upper_values, strict=True
        )
    ]
    _range_text = []
    for _row_index, (_lower_row, _upper_row) in enumerate(
        zip(_lower_values, _upper_values, strict=True)
    ):
        _text_row = []
        for _column_index, (_lower_value, _upper_value) in enumerate(
            zip(_lower_row, _upper_row, strict=True)
        ):
            _range_label = f"{_lower_value:,.0f}–{_upper_value:,.0f}"
            if (
                _row_index
                == auditor_lower_sensitivity["기준 성장률 index"]
                and _column_index
                == auditor_lower_sensitivity["기준 WACC index"]
            ):
                _text_row.append(f"● {_range_label}")
            else:
                _text_row.append(_range_label)
        _range_text.append(_text_row)

    auditor_range_sensitivity_fig = go.Figure(
        data=go.Heatmap(
            z=_midpoint_values,
            x=[
                f"{offset:+.2%}p"
                for offset in auditor_lower_sensitivity["WACC offsets"]
            ],
            y=[
                f"{offset:+.2%}p"
                for offset in auditor_lower_sensitivity["성장률 offsets"]
            ],
            text=_range_text,
            texttemplate="%{text}",
            textfont=dict(size=12),
            colorscale=[
                [0.00, "#FBF4E6"],
                [0.45, "#E4C27B"],
                [1.00, COLORS["gold"]],
            ],
            colorbar=dict(title="Median, 천원", thickness=12),
            xgap=2,
            ygap=2,
            hovertemplate=(
                "WACC 변동 %{x}<br>"
                "Terminal Growth Rate 변동 %{y}<br>"
                "Valuation Range Median %{z:,.0f}천원"
                "<extra></extra>"
            ),
        )
    )
    auditor_range_sensitivity_fig.update_layout(
        title=(
            "<b>Independent Valuation Range Sensitivity</b>"
            "<br><sup>셀: 하단–상단, 천원 · 색상: Median · ● 기준</sup>"
        )
    )
    auditor_range_sensitivity_fig.update_xaxes(
        title="WACC 변동", side="top"
    )
    auditor_range_sensitivity_fig.update_yaxes(title="Terminal Growth Rate 변동")
    auditor_range_sensitivity_fig = apply_chart_style(
        auditor_range_sensitivity_fig,
        height=255,
    )
    return (auditor_range_sensitivity_fig,)


@app.cell
def _(
    COLORS,
    auditor_lower_ebit_margin,
    auditor_lower_revenue_growth,
    auditor_lower_terminal_growth,
    auditor_lower_wacc,
    auditor_range_comparison,
    auditor_range_conclusion,
    auditor_upper_ebit_margin,
    auditor_upper_revenue_growth,
    auditor_upper_terminal_growth,
    auditor_upper_wacc,
    escape,
    mo,
):
    _management = auditor_range_comparison["경영진 주장"]
    _lower = auditor_range_comparison["감사인 범위 하단"]
    _upper = auditor_range_comparison["감사인 범위 상단"]
    _midpoint = auditor_range_comparison["감사인 범위 중앙값"]
    _misstatement = auditor_range_comparison["왜곡표시 금액"]
    _misstatement_direction = auditor_range_comparison["왜곡표시 방향"]
    _nearest_range_value = auditor_range_comparison["가장 가까운 범위 금액"]
    _status_label = {
        "OUTSIDE_RANGE": "Base Case 범위 밖",
        "WITHIN_RANGE": "Base Case 범위 내",
    }.get(
        auditor_range_comparison["검토상태"],
        auditor_range_comparison["검토상태"],
    )
    _range_position = (
        "내"
        if _lower["주당 내재가치"]
        <= _management["주당 내재가치"]
        <= _upper["주당 내재가치"]
        else "밖"
    )
    _ib_range_conclusion = (
        f"Independent Valuation Range는 "
        f"{_lower['주당 내재가치']:,.0f}원–{_upper['주당 내재가치']:,.0f}원이며 "
        f"중앙값은 {_midpoint:,.0f}원입니다. "
        f"Base Case {_management['주당 내재가치']:,.0f}원은 범위 {_range_position}에 있습니다. "
        "핵심 가정 변화가 가치평가 결과에 미치는 영향을 독립적으로 검토한 범위입니다."
    )

    challenge_controls = mo.vstack(
        [
            mo.md(
                """
                <div class="fcff-panel-title">Downside Assumption Range</div>
                <div class="fcff-panel-caption">
                    Revenue CAGR, EBIT Margin, WACC, Terminal Growth Rate의
                    downside 범위를 설정합니다. Slider 옆 입력란에 %p 값을 직접 입력할 수 있습니다.
                </div>
                """
            ),
            mo.vstack(
                [
                    mo.md('<div class="range-control-label">Revenue CAGR 조정 (%p)</div>'),
                    mo.hstack(
                        [auditor_lower_revenue_growth, auditor_upper_revenue_growth],
                        widths=[1, 1], gap=0.8, wrap=False,
                    ),
                    mo.md('<div class="range-control-label">EBIT Margin 조정 (%p)</div>'),
                    mo.hstack(
                        [auditor_lower_ebit_margin, auditor_upper_ebit_margin],
                        widths=[1, 1], gap=0.8, wrap=False,
                    ),
                    mo.md('<div class="range-control-label">WACC 조정 (%p)</div>'),
                    mo.hstack(
                        [auditor_lower_wacc, auditor_upper_wacc],
                        widths=[1, 1], gap=0.8, wrap=False,
                    ),
                    mo.md('<div class="range-control-label">Terminal Growth Rate 조정 (%p)</div>'),
                    mo.hstack(
                        [auditor_lower_terminal_growth, auditor_upper_terminal_growth],
                        widths=[1, 1], gap=0.8, wrap=False,
                    ),
                ],
                gap=0.45,
            ),

        ],
        gap=0.7,
    ).style(
        {
            "background": COLORS["surface"],
            "border": f"1px solid {COLORS['line']}",
            "border-radius": "10px",
            "padding": "12px",
            "box-shadow": "0 2px 8px rgba(16, 42, 67, 0.05)",
        }
    )

    _comparison_rows = [
        (
            "Revenue CAGR",
            f"{_management['매출 CAGR']:.2%}",
            f"{_lower['매출 CAGR']:.2%}",
            f"{_upper['매출 CAGR']:.2%}",
        ),
        (
            "평균 EBIT Margin",
            f"{_management['평균 EBIT Margin']:.2%}",
            f"{_lower['평균 EBIT Margin']:.2%}",
            f"{_upper['평균 EBIT Margin']:.2%}",
        ),
        (
            "WACC",
            f"{_management['WACC']:.2%}",
            f"{_lower['WACC']:.2%}",
            f"{_upper['WACC']:.2%}",
        ),
        (
            "Terminal Growth Rate",
            f"{_management['영구성장률']:.2%}",
            f"{_lower['영구성장률']:.2%}",
            f"{_upper['영구성장률']:.2%}",
        ),
        (
            "Implied Share Price",
            f"{_management['주당 내재가치']:,.0f}원",
            f"{_lower['주당 내재가치']:,.0f}원",
            f"{_upper['주당 내재가치']:,.0f}원",
        ),
        (
            "상승여력",
            f"{_management['상승여력']:.1%}",
            f"{_lower['상승여력']:.1%}",
            f"{_upper['상승여력']:.1%}",
        ),
    ]
    _table_body = "".join(
        "<tr>"
        f"<td>{escape(label)}</td>"
        f"<td>{escape(management_value)}</td>"
        f"<td>{escape(lower_value)}</td>"
        f"<td>{escape(upper_value)}</td>"
        "</tr>"
        for label, management_value, lower_value, upper_value in _comparison_rows
    )
    challenge_summary = mo.md(
        f"""
        <div class="challenge-panel">
            <div class="challenge-panel-head">
                <div>
                    <div class="fcff-panel-title">
                        Base Case vs Independent Valuation Range
                    </div>
                    <div class="challenge-panel-caption">
                        Base Case의 방법·가정·데이터를 독립적 downside scenario와 비교
                    </div>
                </div>
                <span class="challenge-status">{escape(_status_label)}</span>
            </div>
            <div class="challenge-case-grid">
                <div class="challenge-case">
                    <div class="challenge-case-name">BASE CASE · MANAGEMENT CASE</div>
                    <div class="challenge-case-value">{_management['주당 내재가치']:,.0f}원</div>
                    <div class="challenge-case-meta">
                        WACC {_management['WACC']:.2%} · g {_management['영구성장률']:.2%}<br>
                        상승여력 {_management['상승여력']:.1%}
                    </div>
                </div>
                <div class="challenge-case challenge-case-review">
                    <div class="challenge-case-name">INDEPENDENT VALUATION RANGE · DOWNSIDE CASE</div>
                    <div class="challenge-case-value">
                        {_lower['주당 내재가치']:,.0f}–{_upper['주당 내재가치']:,.0f}원
                    </div>
                    <div class="challenge-case-meta">
                        Median {_midpoint:,.0f}원 · Valuation Range 폭 {auditor_range_comparison['범위폭']:,.0f}원<br>
                        상승여력 {_lower['상승여력']:.1%}–{_upper['상승여력']:.1%}
                    </div>
                </div>
            </div>
            <table class="challenge-table">
                <thead>
                    <tr><th>Key Assumption</th><th>Base Case</th><th>Range Low</th><th>Range High</th></tr>
                </thead>
                <tbody>{_table_body}</tbody>
            </table>
            <div class="challenge-conclusion">{escape(_ib_range_conclusion)}</div>
            <details class="model-governance">
                <summary>Model Governance 상세</summary>
                <div class="standard-inline">
                    <strong>감사기준서 540 · A121</strong> — 대체 가정·데이터 또는
                    독립적인 방법·가정·데이터를 적용해 점추정치나 범위를 도출할 수 있습니다.
                </div>
                <div class="audit-standard">
                    <div class="audit-standard-ref">감사기준서 540 · 문단 29(a) 및 A124</div>
                    <p class="audit-standard-quote">
                        범위에는 충분하고 적합한 증거로 뒷받침되는 금액만 포함하며,
                        양 극단과 그 사이 금액의 합리성을 함께 검토합니다.
                    </p>
                </div>
                <div class="misstatement-card">
                    <div>
                        <div class="misstatement-label">
                            범위 이탈 판단적 왜곡표시 · {_misstatement_direction}
                        </div>
                        <div class="challenge-case-meta">
                            Base Case와 가장 가까운 범위 금액
                            {_nearest_range_value:,.0f}원의 차이
                        </div>
                    </div>
                    <div class="misstatement-value">{_misstatement:,.0f}원/주</div>
                </div>
                <div class="standard-inline" style="margin-top: 7px;">
                    <strong>감사기준서 540 · A139 / 감사기준서 450 · A6</strong> —
                    Base Case가 증거로 뒷받침되는 범위를 벗어나는 경우,
                    가장 가까운 범위 지점과의 차이를 별도로 추적합니다.
                </div>
                <a
                    class="audit-standard-source"
                    href="https://kicpa.or.kr/board/read.brd?boardId=acc0102&amp;bltnNo=11786004332051&amp;cmd=READ"
                    target="_blank"
                    rel="noopener noreferrer"
                >한국공인회계사회 원문 · 첨부 기준서 pp. 480, 517–519 ↗</a>
            </details>
        </div>
        """
    )
    return challenge_controls, challenge_summary


@app.cell
def _(forecast_df):
    forecast_display = forecast_df.copy()

    forecast_display["연도"] = (
        forecast_display["연도"]
        .astype(int)
        .astype(str)
    )

    forecast_display["FCFF(십억원)"] = (
        forecast_display["FCFF"] / 1_000
    )

    forecast_display["영업이익률(%)"] = (
        forecast_display["영업이익률"] * 100
    )
    return (forecast_display,)


@app.cell
def _(mo):
    fcff_year_selector = mo.ui.dropdown(
        options={f"{year}E": year for year in range(2026, 2031)},
        value="2026E",
        label="분석 연도",
        allow_select_none=False,
        full_width=True,
    )
    return (fcff_year_selector,)


@app.cell
def _(COLORS, apply_chart_style, forecast_display, go):
    fcff_fig = go.Figure()

    fcff_fig.add_trace(
        go.Bar(
            x=forecast_display["연도"],
            y=forecast_display["FCFF(십억원)"],
            name="FCFF",
            marker_color=COLORS["blue"],
            text=[
                f"{value:,.0f}"
                for value in forecast_display["FCFF(십억원)"]
            ],
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "%{x}E<br>"
                "FCFF %{y:,.0f}십억원"
                "<extra></extra>"
            ),
        )
    )

    fcff_fig.add_trace(
        go.Scatter(
            x=forecast_display["연도"],
            y=forecast_display["영업이익률(%)"],
            name="영업이익률",
            mode="lines+markers+text",
            line=dict(
                color=COLORS["gold"],
                width=3,
            ),
            marker=dict(
                size=8,
                color="#FFFFFF",
                line=dict(
                    color=COLORS["gold"],
                    width=2,
                ),
            ),
            text=[
                f"{value:.1f}%"
                for value in forecast_display["영업이익률(%)"]
            ],
            textposition="top center",
            yaxis="y2",
            hovertemplate=(
                "%{x}E<br>"
                "영업이익률 %{y:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    fcff_fig.update_layout(
        title=(
            "<b>FCFF 및 영업수익성 전망</b>"
            "<br><sup>명시적 예측기간 2026E–2030E</sup>"
        ),
        yaxis=dict(
            title="FCFF, 십억원",
            rangemode="tozero",
            gridcolor="#E9EEF3",
        ),
        yaxis2=dict(
            title="영업이익률",
            overlaying="y",
            side="right",
            ticksuffix="%",
            showgrid=False,
            range=[
                max(
                    0,
                    forecast_display["영업이익률(%)"].min() - 3,
                ),
                forecast_display["영업이익률(%)"].max() + 3,
            ],
        ),
    )

    fcff_fig = apply_chart_style(
        fcff_fig,
        height=300,
    )
    return (fcff_fig,)


@app.cell
def _(
    apply_chart_style,
    build_fcff_waterfall_figure,
    build_fcff_waterfall_insight,
    calculate_fcff_waterfall_kpis,
    fcff_year_selector,
    forecast_df,
    prepare_fcff_waterfall_data,
    select_forecast_row,
):
    _selected_fcff_row = select_forecast_row(
        forecast_df,
        fcff_year_selector.value,
    )
    _fcff_waterfall_data = prepare_fcff_waterfall_data(
        _selected_fcff_row
    )
    fcff_waterfall_kpis = calculate_fcff_waterfall_kpis(
        _fcff_waterfall_data
    )
    fcff_waterfall_insight = build_fcff_waterfall_insight(
        _fcff_waterfall_data,
        fcff_waterfall_kpis,
    )
    fcff_waterfall_fig = build_fcff_waterfall_figure(
        _fcff_waterfall_data
    )
    fcff_waterfall_fig = apply_chart_style(
        fcff_waterfall_fig,
        height=285,
    )
    return (
        fcff_waterfall_fig,
        fcff_waterfall_insight,
        fcff_waterfall_kpis,
    )


@app.cell
def _(
    COLORS,
    fcff_waterfall_fig,
    fcff_waterfall_insight,
    fcff_waterfall_kpis,
    fcff_year_selector,
    mo,
):
    _fcff_kpis = fcff_waterfall_kpis
    fcff_waterfall_summary = (
        mo.vstack(
            [
                mo.md(
                    """
                    <div class="fcff-panel-title">현금흐름 전환 분석</div>
                    <div class="fcff-panel-caption">
                        연도를 선택해 EBIT에서 FCFF까지의 전환 구조를 검토합니다.
                    </div>
                    """
                ),
                fcff_year_selector,
                mo.md(
                    f"""
                    <div class="fcff-mini-grid">
                        <div class="fcff-mini-kpi">
                            <div class="fcff-mini-label">EBIT</div>
                            <div class="fcff-mini-value">{_fcff_kpis["EBIT"]:,.1f}</div>
                        </div>
                        <div class="fcff-mini-kpi">
                            <div class="fcff-mini-label">NOPAT</div>
                            <div class="fcff-mini-value">{_fcff_kpis["NOPAT"]:,.1f}</div>
                        </div>
                        <div class="fcff-mini-kpi">
                            <div class="fcff-mini-label">FCFF</div>
                            <div class="fcff-mini-value">{_fcff_kpis["FCFF"]:,.1f}</div>
                        </div>
                        <div class="fcff-mini-kpi">
                            <div class="fcff-mini-label">현금전환율</div>
                            <div class="fcff-mini-value">{_fcff_kpis["현금전환율"]:.1%}</div>
                        </div>
                    </div>
                    <div class="fcff-panel-caption">금액 단위: 십억원</div>
                    <div class="fcff-insight">{fcff_waterfall_insight}</div>
                    """
                ),
            ],
            gap=0.5,
        )
        .style(
            {
                "background": COLORS["surface"],
                "border": f"1px solid {COLORS['line']}",
                "border-radius": "10px",
                "padding": "12px",
                "box-shadow": "0 2px 8px rgba(16, 42, 67, 0.05)",
            }
        )
    )
    fcff_waterfall_view = mo.ui.plotly(fcff_waterfall_fig)
    _fcff_header = mo.md(
        """
        <div class="section-title">EBIT에서 FCFF로의 전환</div>
        <div class="section-subtitle">
            영업관련 법인세·D&amp;A·Capex·NWC 증감의 현금흐름 효과
        </div>
        """
    )
    fcff_waterfall_row = mo.vstack(
        [
            _fcff_header,
            mo.hstack(
                [fcff_waterfall_summary, fcff_waterfall_view],
                widths=[0.22, 0.78],
                gap=1,
                align="stretch",
                wrap=False,
            ),
        ],
        gap=0.45,
    )
    return (fcff_waterfall_row,)


@app.cell
def _(enterprise_value, equity_value, model):
    equity_bridge = model["지분가치"]

    other_non_operating_assets = (
        equity_bridge["비영업자산 합계"]
        - equity_bridge["초과현금"]
        - equity_bridge["리가켐바이오 시장가치"]
    )

    bridge_labels = [
        "기업가치",
        "초과현금",
        "리가켐바이오",
        "기타 비영업자산",
        "리스부채",
        "비지배지분",
        "지분가치",
    ]

    bridge_values = [
        enterprise_value / 1_000_000,
        equity_bridge["초과현금"] / 1_000_000,
        equity_bridge["리가켐바이오 시장가치"] / 1_000_000,
        other_non_operating_assets / 1_000_000,
        -equity_bridge["리스부채"] / 1_000_000,
        -equity_bridge["비지배지분"] / 1_000_000,
        0,
    ]

    bridge_text = [
        f"{enterprise_value / 1_000_000:.2f}",
        f"+{equity_bridge['초과현금'] / 1_000_000:.2f}",
        f"+{equity_bridge['리가켐바이오 시장가치'] / 1_000_000:.2f}",
        f"+{other_non_operating_assets / 1_000_000:.2f}",
        f"-{equity_bridge['리스부채'] / 1_000_000:.2f}",
        f"-{equity_bridge['비지배지분'] / 1_000_000:.2f}",
        f"{equity_value / 1_000_000:.2f}",
    ]
    return bridge_labels, bridge_text, bridge_values


@app.cell
def _(
    COLORS,
    apply_chart_style,
    bridge_labels,
    bridge_text,
    bridge_values,
    go,
):
    _bridge_peak = (
        bridge_values[0]
        + sum(max(value, 0) for value in bridge_values[1:-1])
    )
    bridge_fig = go.Figure(
        go.Waterfall(
            x=bridge_labels,
            y=bridge_values,
            measure=[
                "absolute",
                "relative",
                "relative",
                "relative",
                "relative",
                "relative",
                "total",
            ],
            text=bridge_text,
            textposition="outside",
            connector=dict(
                line=dict(
                    color=COLORS["line"],
                    width=1,
                )
            ),
            increasing=dict(
                marker=dict(color=COLORS["waterfall_increase"])
            ),
            decreasing=dict(
                marker=dict(color=COLORS["waterfall_decrease"])
            ),
            totals=dict(
                marker=dict(color=COLORS["waterfall_total"])
            ),
            hovertemplate=(
                "%{x}<br>"
                "%{text}조원"
                "<extra></extra>"
            ),
        )
    )

    bridge_fig.update_layout(
        title=(
            "<b>Enterprise Value (EV)에서 Equity Value로의 연결</b>"
            "<br><sup>비영업자산 및 Net Debt 등 조정 · 조원</sup>"
        ),
        showlegend=False,
    )

    bridge_fig.update_yaxes(
        title="조원",
        range=[0, _bridge_peak * 1.18],
    )

    bridge_fig = apply_chart_style(
        bridge_fig,
        height=300,
    )
    return (bridge_fig,)


@app.cell
def _(
    auditor_range_sensitivity_fig,
    bridge_fig,
    challenge_controls,
    challenge_summary,
    fcff_fig,
    mo,
    sensitivity_fig,
):
    sensitivity_view = mo.ui.plotly(sensitivity_fig)
    auditor_range_sensitivity_view = mo.ui.plotly(
        auditor_range_sensitivity_fig
    )
    fcff_view = mo.ui.plotly(fcff_fig)
    bridge_view = mo.ui.plotly(bridge_fig)

    overview_visuals = mo.vstack(
        [
            mo.md(
                """
                <div class="section-title">영업전망과 Equity Bridge</div>
                <div class="section-subtitle">
                    FCFF 창출력과 기업가치에서 지분가치로의 연결
                </div>
                """
            ),
            mo.hstack(
                [fcff_view, bridge_view],
                widths=[1, 1],
                gap=1,
            ),
        ],
        gap=0.7,
    )

    sensitivity_chapter_body = mo.vstack(
        [
            mo.md(
                """
                <div class="section-title">Scenario &amp; Assumption Review</div>
                <div class="section-subtitle">
                    Base Case를 독립적 downside 가정과 비교하고 가치 차이로 연결
                </div>
                """
            ),
            mo.hstack(
                [
                    challenge_controls,
                    challenge_summary,
                    mo.vstack(
                        [
                            mo.md(
                                """
                                <div class="section-title">WACC × Terminal Growth Rate</div>
                                <div class="section-subtitle">
                                    Base Case와 Independent Valuation Range 비교
                                </div>
                                """
                            ),
                            sensitivity_view,
                            auditor_range_sensitivity_view,
                        ],
                        gap=0.45,
                    ),
                ],
                widths=[0.25, 0.40, 0.35],
                gap=1,
                align="start",
                wrap=False,
            ),
        ],
        gap=0.55,
    )
    return overview_visuals, sensitivity_chapter_body


@app.cell
def _(build_valuation_formula_catalog, mo):
    _formula_stages = list(build_valuation_formula_catalog())
    formula_stage_selector = mo.ui.dropdown(
        options={
            (
                "Enterprise Value (EV)"
                if stage == "DCF"
                else "Equity Value"
                if stage == "지분가치"
                else "Implied Share Price"
                if stage == "주당 내재가치"
                else stage
            ): stage
            for stage in _formula_stages
        },
        value="FCFF",
        label="가치평가 단계",
        allow_select_none=False,
        full_width=True,
    )
    formula_year_selector = mo.ui.dropdown(
        options={f"{year}E": year for year in range(2026, 2031)},
        value="2026E",
        label="분석 연도",
        allow_select_none=False,
        full_width=True,
    )
    return formula_stage_selector, formula_year_selector


@app.cell
def _(
    build_formula_explorer_insight,
    formula_stage_selector,
    formula_year_selector,
    model,
    prepare_formula_explorer_data,
    reconcile_formula_result,
):
    _formula_stage = formula_stage_selector.value
    formula_year_is_applicable = _formula_stage in {
        "매출액",
        "EBIT",
        "FCFF",
    }
    _formula_year = (
        formula_year_selector.value
        if formula_year_is_applicable
        else None
    )
    _prepared_formula_result = prepare_formula_explorer_data(
        model,
        _formula_stage,
        _formula_year,
    )
    formula_result = reconcile_formula_result(
        _prepared_formula_result
    )
    formula_insight = build_formula_explorer_insight(
        formula_result
    )
    return formula_insight, formula_result, formula_year_is_applicable


@app.cell
def _(escape):
    def format_formula_metric(value, stage, metric_name=""):
        numeric_value = float(value)
        if stage == "WACC" or "비중" in metric_name or "상승여력" in metric_name:
            return f"{numeric_value:.2%}"
        if stage in {"DCF", "지분가치"}:
            return f"{numeric_value / 1_000_000:,.3f}조원"
        if stage == "주당 내재가치":
            return f"{numeric_value:,.0f}원"
        return f"{numeric_value / 1_000:,.1f}십억원"

    def formula_input_cards(formula_result):
        _stage = str(formula_result["단계"])
        _inputs = dict(formula_result["표시 입력값"])
        _details = dict(formula_result.get("계산 세부", {}))
        _cards = []

        if _stage == "WACC":
            _ordered_items = [
                ("Risk-free Rate", _inputs["무위험수익률"], "rate"),
                (
                    "Equity Risk Premium (ERP)",
                    _inputs["주식시장위험프리미엄"],
                    "rate",
                ),
                ("베타", _inputs["베타"], "multiple"),
                ("Country Risk Premium (CRP)", _inputs["국가위험프리미엄"], "rate"),
                ("자기자본비용", _details["자기자본비용"], "rate"),
                (
                    "세전 타인자본비용",
                    _inputs["세전 타인자본비용"],
                    "rate",
                ),
                (
                    "세후 타인자본비용",
                    _details["세후 타인자본비용"],
                    "rate",
                ),
                ("자기자본 비중", _inputs["자기자본 비중"], "rate"),
                ("타인자본 비중", _inputs["타인자본 비중"], "rate"),
            ]
        elif _stage == "DCF":
            _ordered_items = [
                ("WACC", _inputs["WACC"], "rate"),
                ("Terminal Growth Rate", _inputs["영구성장률"], "rate"),
                (
                    "추정기간 FCFF 현재가치",
                    _details["추정기간 FCFF 현재가치"] / 1_000_000,
                    "trillion",
                ),
                (
                    "계속기업가치",
                    _details["계속기업가치"] / 1_000_000,
                    "trillion",
                ),
                (
                    "계속기업가치 현재가치",
                    _details["계속기업가치 현재가치"] / 1_000_000,
                    "trillion",
                ),
                (
                    "계속기업가치 비중",
                    _details["계속기업가치 비중"],
                    "rate",
                ),
            ]
        elif _stage == "지분가치":
            _ordered_items = [
                ("Enterprise Value (EV)", _inputs["기업가치"], "trillion"),
                (
                    "비영업자산 합계",
                    _details["비영업자산 합계"] / 1_000_000,
                    "trillion",
                ),
                (
                    "금융기관차입금 (차감)",
                    _details["금융기관차입금"] / 1_000_000,
                    "trillion",
                ),
                (
                    "리스부채 (차감)",
                    _details["리스부채"] / 1_000_000,
                    "trillion",
                ),
                (
                    "비지배지분 (차감)",
                    _details["비지배지분"] / 1_000_000,
                    "trillion",
                ),
                (
                    "순비영업 조정액",
                    _inputs["순비영업 조정액"],
                    "trillion",
                ),
            ]
        elif _stage == "주당 내재가치":
            _ordered_items = [
                ("Equity Value", _inputs["지분가치"], "trillion"),
                (
                    "유통주식수",
                    _inputs["유통주식수(백만주)"],
                    "shares",
                ),
                ("기준주가", _inputs["기준주가"], "won"),
                (
                    "내재 상승여력",
                    _details["모델 내재 상승여력"],
                    "rate",
                ),
            ]
        else:
            _ordered_items = [
                (
                    key,
                    value,
                    "rate" if "이익률" in key else "billion",
                )
                for key, value in _inputs.items()
                if not isinstance(value, list)
            ]

        for _label, _value, _kind in _ordered_items:
            if _kind == "rate":
                _formatted = f"{float(_value):.2%}"
            elif _kind == "multiple":
                _formatted = f"{float(_value):.2f}x"
            elif _kind == "trillion":
                _formatted = f"{float(_value):,.3f}조원"
            elif _kind == "shares":
                _formatted = f"{float(_value):,.3f}백만주"
            elif _kind == "won":
                _formatted = f"{float(_value):,.0f}원"
            else:
                _formatted = f"{float(_value):,.1f}십억원"
            _cards.append(
                '<div class="formula-kpi">'
                f'<div class="formula-kpi-label">{escape(str(_label))}</div>'
                f'<div class="formula-kpi-value">{escape(_formatted)}</div>'
                "</div>"
            )
        return (
            '<div class="formula-kpi-grid formula-input-grid">'
            + "".join(_cards)
            + "</div>"
        )

    def formula_raw_input_table(formula_result):
        _raw_inputs = dict(formula_result["원본 입력값"])
        _rows = []
        for _label, _value in _raw_inputs.items():
            if isinstance(_value, list):
                _shown = ", ".join(f"{float(item):,.6f}" for item in _value)
            else:
                _shown = f"{float(_value):,.6f}"
            _rows.append(
                "<tr>"
                f"<td>{escape(str(_label))}</td>"
                f"<td>{escape(_shown)}</td>"
                "</tr>"
            )
        return (
            '<table class="formula-table">'
            "<thead><tr><th>입력 항목</th><th>원본값</th></tr></thead>"
            f"<tbody>{''.join(_rows)}</tbody></table>"
        )

    return format_formula_metric, formula_input_cards, formula_raw_input_table


@app.cell
def _(formula_result, mo):
    _lineage_nodes = [
        ("지역별 매출액", "매출액", False),
        ("EBIT", "EBIT", False),
        ("NOPAT", "FCFF", False),
        ("FCFF", "FCFF", False),
        ("WACC · 할인율 입력", "WACC", True),
        ("Enterprise Value (EV)", "DCF", False),
        ("Equity Value", "지분가치", False),
        ("Implied Share Price", "주당 내재가치", False),
    ]
    _stage_order = {
        "매출액": 0,
        "EBIT": 1,
        "FCFF": 3,
        "WACC": 4,
        "DCF": 5,
        "지분가치": 6,
        "주당 내재가치": 7,
    }
    _current_index = _stage_order[str(formula_result["단계"])]
    _lineage_parts = []
    for _index, (_label, _node_stage, _is_auxiliary) in enumerate(_lineage_nodes):
        if _index == _current_index:
            _node_class = "formula-node-current"
        elif _is_auxiliary:
            _node_class = "formula-node-aux"
        elif _index < _current_index:
            _node_class = "formula-node-complete"
        else:
            _node_class = "formula-node-future"
        _lineage_parts.append(
            f'<span class="formula-node {_node_class}">{_label}</span>'
        )
        if _index < len(_lineage_nodes) - 1:
            _lineage_parts.append('<span class="formula-arrow">→</span>')

    formula_lineage = mo.md(
        '<div class="formula-lineage">'
        + "".join(_lineage_parts)
        + "</div>"
    )
    return (formula_lineage,)


@app.cell
def _(
    formula_result,
    formula_stage_selector,
    formula_year_is_applicable,
    formula_year_selector,
    mo,
):
    _year_control = (
        formula_year_selector
        if formula_year_is_applicable
        else mo.md(
            """
            <div class="formula-copy" style="margin-top: 8px;">
                해당 단계는 특정 전망연도가 아닌 평가기준일 전체 모델 기준입니다.
            </div>
            """
        )
    )
    _source_detail = mo.accordion(
        {
            "데이터 출처 및 모델 경로": mo.md(
                f"`{formula_result['데이터 출처 또는 모델 경로']}`"
            )
        },
        lazy=True,
    )
    formula_explorer_left = (
        mo.vstack(
            [
                mo.md(
                    """
                    <div class="fcff-panel-title">분석 기준</div>
                    <div class="fcff-panel-caption">
                        가치평가 단계와 전망연도를 선택합니다.
                    </div>
                    """
                ),
                formula_stage_selector,
                _year_control,
                mo.md(
                    f"""
                    <div style="margin-top: 14px;">
                        <div class="formula-label">경제적 의미</div>
                        <div class="formula-copy">{formula_result["경제적 의미"]}</div>
                        <div class="formula-label">부호 규칙</div>
                        <div class="formula-copy">{formula_result["부호규칙"]}</div>
                        <div class="formula-label">단위 통제</div>
                        <div class="formula-copy">
                            원본 {formula_result["원본 단위"]} · 표시 {formula_result["표시 단위"]}
                        </div>
                    </div>
                    """
                ),
                _source_detail,
            ],
            gap=0.5,
        ).style(
            {
                "background": "#FFFFFF",
                "border": "1px solid #D9E2EC",
                "border-radius": "10px",
                "padding": "12px",
                "box-shadow": "0 2px 8px rgba(16, 42, 67, 0.05)",
            }
        )
    )
    return (formula_explorer_left,)


@app.cell
def _(
    COLORS,
    escape,
    format_formula_metric,
    formula_input_cards,
    formula_insight,
    formula_raw_input_table,
    formula_result,
    mo,
    model,
):
    _stage = str(formula_result["단계"])
    _status = str(formula_result["대사상태"])
    _badge_class = (
        "formula-badge-pass"
        if _status == "PASS"
        else "formula-badge-fail"
    )
    _model_value = format_formula_metric(
        formula_result["모델값"],
        _stage,
    )
    _recalculated_value = format_formula_metric(
        formula_result["재계산값"],
        _stage,
    )
    _difference_value = format_formula_metric(
        formula_result["차이"],
        _stage,
    )
    _tolerance_value = format_formula_metric(
        formula_result["허용오차"],
        _stage,
    )
    _input_cards_html = formula_input_cards(formula_result)

    _dcf_table_html = ""
    if _stage == "DCF":
        _details = dict(formula_result["계산 세부"])
        _dcf_rows = []
        for _row, _factor, _pv in zip(
            model["전망"],
            _details["할인계수"],
            _details["FCFF 현재가치"],
            strict=True,
        ):
            _dcf_rows.append(
                "<tr>"
                f"<td>{int(_row['연도'])}E</td>"
                f"<td>{_row['FCFF'] / 1_000:,.1f}</td>"
                f"<td>{_factor:.4f}</td>"
                f"<td>{_pv / 1_000:,.1f}</td>"
                "</tr>"
            )
        _dcf_table_html = (
            '<table class="formula-table">'
            "<thead><tr><th>연도</th><th>FCFF, 십억원</th>"
            "<th>할인계수</th><th>현재가치, 십억원</th></tr></thead>"
            f"<tbody>{''.join(_dcf_rows)}</tbody></table>"
        )

    _formula_detail = mo.accordion(
        {
            "원본 입력값 및 정밀도 확인": mo.md(
                formula_raw_input_table(formula_result)
            )
        },
        lazy=True,
    )
    _equation_block = mo.vstack(
        [
            mo.md('<div class="formula-label">모형 수식</div>'),
            mo.md(f'$$ {formula_result["기호 수식"]} $$'),
            mo.md(
                f"""
                <div class="formula-label">실제 수치 대입</div>
                <div class="formula-substitution">
                    {escape(str(formula_result["표시 수식"]))}
                </div>
                """
            ),
        ],
        gap=0.25,
    ).style(
        {
            "background": "#F7FAFC",
            "border": f"1px solid {COLORS['line']}",
            "border-radius": "9px",
            "padding": "6px 10px",
            "margin": "5px 0 6px 0",
        }
    )
    _formula_footer = mo.hstack(
        [
            mo.md(
                f"""
                <div class="formula-status-inline">
                    <span class="formula-badge {_badge_class}">{_status}</span>
                    <div class="formula-insight-compact">{escape(formula_insight)}</div>
                </div>
                """
            ),
            _formula_detail,
        ],
        widths=[0.76, 0.24],
        gap=0.6,
        align="center",
        wrap=False,
    )
    formula_explorer_right = (
        mo.vstack(
            [
                mo.md(
                    f"""
                    <div class="fcff-panel-title">{escape(_stage)} 계산 및 대사</div>
                    """
                ),
                _equation_block,
                mo.md(
                    f"""
                    {_input_cards_html}
                    {_dcf_table_html}
                    <div class="formula-kpi-grid">
                        <div class="formula-kpi" style="border-top-color: {COLORS['blue']};">
                            <div class="formula-kpi-label">모델값</div>
                            <div class="formula-kpi-value">{_model_value}</div>
                        </div>
                        <div class="formula-kpi" style="border-top-color: {COLORS['teal']};">
                            <div class="formula-kpi-label">재계산값</div>
                            <div class="formula-kpi-value">{_recalculated_value}</div>
                        </div>
                        <div class="formula-kpi" style="border-top-color: {COLORS['gold']};">
                            <div class="formula-kpi-label">차이</div>
                            <div class="formula-kpi-value">{_difference_value}</div>
                        </div>
                        <div class="formula-kpi" style="border-top-color: {COLORS['muted']};">
                            <div class="formula-kpi-label">허용오차</div>
                            <div class="formula-kpi-value">{_tolerance_value}</div>
                        </div>
                    </div>
                    """
                ),
                _formula_footer,
            ],
            gap=0.3,
        ).style(
            {
                "background": COLORS["surface"],
                "border": f"1px solid {COLORS['line']}",
                "border-radius": "10px",
                "padding": "12px",
                "box-shadow": "0 2px 8px rgba(16, 42, 67, 0.05)",
            }
        )
    )
    return (formula_explorer_right,)


@app.cell
def _(
    formula_explorer_left,
    formula_explorer_right,
    formula_lineage,
    mo,
):
    _formula_header = mo.md(
        """
        <div class="section-title">가치평가 산식 및 계산 구조</div>
        <div class="section-subtitle">
            공시자료에서 Implied Share Price까지의 계산 논리와 모델 대사
        </div>
        """
    )
    _formula_body = mo.hstack(
        [formula_explorer_left, formula_explorer_right],
        widths=[0.22, 0.78],
        gap=1,
        align="stretch",
        wrap=False,
    )
    formula_explorer_section = mo.vstack(
        [_formula_header, formula_lineage, _formula_body],
        gap=0.45,
    )
    return (formula_explorer_section,)


@app.cell
def _(
    calculate_historical_multiple_ranges,
    calculate_trading_comps_ranges,
    current_price,
    management_sensitivity,
    market_peers,
    model,
    prepare_beta_calibration,
    prepare_football_field_ranges,
):
    _wacc_components = model["WACC"]["구성요소"]
    _target_de = (
        float(_wacc_components["타인자본 비중"])
        / float(_wacc_components["자기자본 비중"])
    )
    beta_calibration = prepare_beta_calibration(
        market_peers,
        _target_de,
        float(_wacc_components["법인세율"]),
    )
    trading_ranges = calculate_trading_comps_ranges(model, market_peers)
    historical_ranges = calculate_historical_multiple_ranges(model)
    _dcf_values = [
        value
        for row in management_sensitivity["주당 내재가치"]
        for value in row
    ]
    football_ranges = prepare_football_field_ranges(
        _dcf_values,
        trading_ranges,
        historical_ranges,
        current_price,
    )
    return beta_calibration, football_ranges, historical_ranges, trading_ranges


@app.cell
def _(mo):
    reverse_margin = mo.ui.slider(
        start=12.0,
        stop=22.0,
        step=0.1,
        value=16.2,
        label="2030 정상 영업이익률 (%)",
        include_input=True,
        full_width=True,
    )
    reverse_asset_realization = mo.ui.slider(
        start=0,
        stop=100,
        step=5,
        value=0,
        label="비영업자산 가치인식률 (%)",
        include_input=True,
        full_width=True,
    )
    return reverse_asset_realization, reverse_margin


@app.cell
def _(
    current_price,
    model,
    reverse_asset_realization,
    reverse_margin,
    solve_reverse_dcf_growth,
):
    _selected_margin = float(reverse_margin.value) / 100
    _selected_realization = float(reverse_asset_realization.value) / 100
    reverse_result = solve_reverse_dcf_growth(
        model,
        current_price,
        _selected_margin,
        _selected_realization,
    )
    reverse_tradeoff = []
    for _margin_percent in range(120, 221, 5):
        _margin = _margin_percent / 1_000
        try:
            _point = solve_reverse_dcf_growth(
                model,
                current_price,
                _margin,
                _selected_realization,
            )
        except ValueError:
            continue
        reverse_tradeoff.append(
            {
                "margin": _margin,
                "growth": _point["revenue_cagr"],
            }
        )
    return reverse_result, reverse_tradeoff


@app.cell
def _(
    COLORS,
    apply_chart_style,
    current_price,
    football_ranges,
    go,
    market_peers,
    model,
    reverse_result,
    reverse_tradeoff,
):
    _multiple_specs = [
        ("EV/EBITDA", "ev_ebitda"),
        ("EV/EBIT", "ev_ebit"),
        ("P/E", "pe"),
    ]
    _forecast_2026 = model["전망"][0]
    _equity_context = model["지분가치"]
    _market_equity_value = (
        current_price * float(_equity_context["유통주식수(백만주)"])
    )
    _equity_bridge = float(_equity_context["지분가치"]) - float(
        model["DCF"]["기업가치"]
    )
    _market_enterprise_value = _market_equity_value - _equity_bridge
    _orion_peer = {
        "company": "오리온(평가대상)",
        "ticker": "271560",
        "region": "한국",
        "fiscal_period": "FY2026E",
        "reference_date": "현재 주가 125,000원 기준",
        "comparison_note": "평가대상 · 현재 주가 기준",
        "ev_ebitda": _market_enterprise_value
        / (float(_forecast_2026["EBIT"]) + float(_forecast_2026["D&A"])),
        "ev_ebit": _market_enterprise_value / float(_forecast_2026["EBIT"]),
        "pe": _market_equity_value / float(_forecast_2026["NOPAT"]),
    }
    _domestic_peers = [peer for peer in market_peers if peer["region"] == "한국"]
    _overseas_peers = [peer for peer in market_peers if peer["region"] != "한국"]
    _chart_peers = [*_domestic_peers, _orion_peer, *_overseas_peers]
    _peer_names = [str(peer["company"]) for peer in _chart_peers]
    _multiple_colors = [COLORS["blue"], COLORS["teal"], COLORS["gold"]]
    peer_multiples_fig = go.Figure()
    for (_multiple, _field), _color in zip(
        _multiple_specs,
        _multiple_colors,
        strict=True,
    ):
        peer_multiples_fig.add_trace(
            go.Bar(
                x=_peer_names,
                y=[float(peer[_field]) for peer in _chart_peers],
                name=_multiple,
                marker=dict(
                    color=_color,
                    line=dict(
                        color=[
                            COLORS["orange"]
                            if peer is _orion_peer
                            else _color
                            for peer in _chart_peers
                        ],
                        width=[
                            3 if peer is _orion_peer else 0
                            for peer in _chart_peers
                        ],
                    ),
                    pattern=dict(
                        shape=[
                            "/" if peer is _orion_peer else ""
                            for peer in _chart_peers
                        ]
                    ),
                ),
                text=[f"{float(peer[_field]):.1f}x" for peer in _chart_peers],
                textposition="outside",
                textfont=dict(size=13, color=COLORS["ink"]),
                cliponaxis=False,
                customdata=[
                    [
                        peer["ticker"],
                        peer["region"],
                        peer["fiscal_period"],
                        peer["reference_date"],
                        peer.get("comparison_note", "비교기업 · 저장 시점 자료"),
                    ]
                    for peer in _chart_peers
                ],
                hovertemplate=(
                    "<b>%{x}</b> · %{customdata[0]}<br>"
                    "국가 %{customdata[1]} · 기준연도 %{customdata[2]}<br>"
                    + _multiple + " %{y:.1f}x<br>"
                    "%{customdata[4]}<br>"
                    "자료 기준일 %{customdata[3]}<extra></extra>"
                ),
            )
        )
    _domestic_count = len(_domestic_peers) + 1
    if 0 < _domestic_count < len(_chart_peers):
        peer_multiples_fig.add_vline(
            x=_domestic_count - 0.5,
            line_color="#94A3B8",
            line_dash="dot",
            line_width=1,
        )
    peer_multiples_fig.update_layout(
        title=(
            "<b>Trading Comps 배수 비교</b>"
            "<br><sup>국내외 식품기업 FY2026E 시장배수</sup>"
        ),
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(t=110, b=90, l=70, r=30),
    )
    peer_multiples_fig.update_xaxes(title="비교기업", tickfont=dict(size=13))
    peer_multiples_fig.update_yaxes(title="시장배수 (x)", tickfont=dict(size=13))
    peer_multiples_fig = apply_chart_style(peer_multiples_fig, height=460)
    peer_multiples_fig.update_layout(
        title_font=dict(size=20),
        legend_font=dict(size=13),
    )
    peer_multiples_fig.update_xaxes(
        tickfont=dict(size=13),
        title_font=dict(size=14),
    )
    peer_multiples_fig.update_yaxes(
        tickfont=dict(size=13),
        title_font=dict(size=14),
    )

    _football_colors = {
        "DCF": COLORS["blue"],
        "Trading Comps": COLORS["teal"],
        "Historical": COLORS["gold"],
        "Market": COLORS["orange"],
    }
    _method_labels = {
        "DCF Sensitivity": "DCF 민감도",
        "Trading EV/EBITDA": "Trading Comps EV/EBITDA",
        "Trading EV/EBIT": "Trading Comps EV/EBIT",
        "Trading P/E": "Trading Comps P/E",
        "Historical Multiple": "과거 시장배수",
        "Current Price": "현재 주가",
    }
    football_field_fig = go.Figure()
    for _row in reversed(football_ranges):
        _method = _method_labels.get(str(_row["method"]), str(_row["method"]))
        _low = float(_row["low"]) / 1_000
        _mid = float(_row["mid"]) / 1_000
        _high = float(_row["high"]) / 1_000
        _color = _football_colors[str(_row["group"])]
        if _high > _low:
            football_field_fig.add_trace(
                go.Scatter(
                    x=[_low, _high],
                    y=[_method, _method],
                    mode="lines",
                    line=dict(color=_color, width=12),
                    hovertemplate=(
                        f"{_method}<br>"
                        f"하단 {_low:,.0f}천원 · 상단 {_high:,.0f}천원"
                        "<extra></extra>"
                    ),
                    showlegend=False,
                )
            )
        football_field_fig.add_trace(
            go.Scatter(
                x=[_low, _mid, _high] if _high > _low else [_mid],
                y=[_method, _method, _method] if _high > _low else [_method],
                mode="markers+text",
                marker=dict(
                    color=[_color, "#FFFFFF", _color] if _high > _low else [_color],
                    line=dict(color=_color, width=3),
                    size=[7, 12, 7] if _high > _low else [12],
                    symbol=["circle", "diamond", "circle"] if _high > _low else ["diamond"],
                ),
                text=(
                    [f"{_low:,.0f}", f"{_mid:,.0f}", f"{_high:,.0f}"]
                    if _high > _low
                    else [f"{_mid:,.0f}천원"]
                ),
                textposition=(
                    ["bottom left", "top center", "bottom right"]
                    if _high > _low
                    else ["middle right"]
                ),
                textfont=dict(size=12, color=COLORS["ink"]),
                hovertemplate=(
                    f"{_method}<br>"
                    "내재 주당가치 %{x:,.0f}천원/주<extra></extra>"
                ),
                showlegend=False,
            )
        )
    football_field_fig.add_vline(
        x=current_price / 1_000,
        line_dash="dot",
        line_color=COLORS["orange"],
        line_width=4,
        annotation_text=f"현재 주가 {current_price / 1_000:,.0f}천원",
        annotation_position="top right",
    )
    football_field_fig.update_layout(
        title=(
            "<b>Football Field 가치평가 범위</b>"
            "<br><sup>DCF·Trading Comps·과거 시장배수 비교 · ◇ 중앙값</sup>"
        )
    )
    football_field_fig.update_xaxes(title="내재 주당가치 (천원/주)")
    football_field_fig = apply_chart_style(football_field_fig, height=450)
    football_field_fig.update_layout(title_font=dict(size=20))
    football_field_fig.update_xaxes(
        tickfont=dict(size=13),
        title_font=dict(size=14),
    )
    football_field_fig.update_yaxes(tickfont=dict(size=13))

    reverse_tradeoff_fig = go.Figure()
    reverse_tradeoff_fig.add_trace(
        go.Scatter(
            x=[point["margin"] * 100 for point in reverse_tradeoff],
            y=[point["growth"] * 100 for point in reverse_tradeoff],
            mode="lines+markers",
            line=dict(color=COLORS["teal"], width=3),
            marker=dict(size=5),
            hovertemplate=(
                "2030 정상 영업이익률 %{x:.1f}%<br>"
                "현재 주가 내재 5년 매출 CAGR %{y:.1f}%<br>"
                f"비영업자산 가치인식률 {reverse_result['non_operating_asset_realization']:.0%}"
                "<extra></extra>"
            ),
            showlegend=False,
        )
    )
    reverse_tradeoff_fig.add_trace(
        go.Scatter(
            x=[reverse_result["terminal_ebit_margin"] * 100],
            y=[reverse_result["revenue_cagr"] * 100],
            mode="markers",
            marker=dict(
                color=COLORS["orange"],
                size=16,
                line=dict(color="#FFFFFF", width=2),
            ),
            hovertemplate="선택 가정<extra></extra>",
            showlegend=False,
        )
    )
    reverse_tradeoff_fig.add_hline(
        y=0,
        line_dash="dot",
        line_color="#9AAABD",
    )
    reverse_tradeoff_fig.update_layout(
        title=(
            "<b>Reverse DCF 내재 가정</b>"
            "<br><sup>현재 주가와 일치하는 정상 영업이익률–매출 CAGR 조합</sup>"
        )
    )
    reverse_tradeoff_fig.update_xaxes(title="2030 정상 영업이익률 (%)")
    reverse_tradeoff_fig.update_yaxes(title="현재 주가 내재 5년 매출 CAGR (%)")
    reverse_tradeoff_fig = apply_chart_style(
        reverse_tradeoff_fig,
        height=410,
    )
    reverse_tradeoff_fig = reverse_tradeoff_fig.update_layout(
        title_font=dict(size=20)
    )
    reverse_tradeoff_fig = reverse_tradeoff_fig.update_xaxes(
        tickfont=dict(size=13),
        title_font=dict(size=14),
    )
    reverse_tradeoff_fig = reverse_tradeoff_fig.update_yaxes(
        tickfont=dict(size=13),
        title_font=dict(size=14),
    )
    return (
        football_field_fig,
        peer_multiples_fig,
        reverse_tradeoff_fig,
    )


@app.cell
def _(
    beta_calibration,
    current_price,
    football_field_fig,
    mo,
    model,
    peer_multiples_fig,
    reverse_asset_realization,
    reverse_margin,
    reverse_result,
    reverse_tradeoff_fig,
):
    _wacc = model["WACC"]["구성요소"]
    _calibration_cards = mo.md(
        f"""
        <div class="market-grid">
            <div class="market-card">
                <div class="market-card-label">비교기업 기준 Relevered Beta</div>
                <div class="market-card-value">{beta_calibration['relevered_beta']:.2f}</div>
                <div class="market-card-note">
                    Unlevered Beta 중앙값 {beta_calibration['median_unlevered_beta']:.2f} → 오리온 목표 D/E 적용
                </div>
            </div>
            <div class="market-card">
                <div class="market-card-label">무위험수익률</div>
                <div class="market-card-value">{float(_wacc['무위험수익률']):.1%}</div>
                <div class="market-card-note">
                    국고채 10년물 · 한국은행 ECOS · 2025-12-31 기준
                </div>
            </div>
            <div class="market-card">
                <div class="market-card-label">검증 대상 WACC</div>
                <div class="market-card-value">{float(model['WACC']['WACC']):.2%}</div>
                <div class="market-card-note">
                    ERP {float(_wacc['주식시장위험프리미엄']):.1%} + 국가위험프리미엄 {float(_wacc['국가위험프리미엄']):.1%} 반영
                </div>
            </div>
        </div>
        """
    )
    _reverse_summary = mo.md(
        f"""
        <div class="challenge-panel">
            <div class="challenge-panel-head">
                <div>
                    <div class="fcff-panel-title">Reverse DCF 결과 요약</div>
                    <div class="challenge-panel-caption">
                        선택한 정상 영업이익률에 대응하는 매출 CAGR을 계산합니다.
                    </div>
                </div>
                <span class="reconciled-badge">{reverse_result['reconciliation_status']}</span>
            </div>
            <div class="challenge-conclusion">
                현재 주가 {current_price:,.0f}원은 비영업자산 가치인식률
                {reverse_result['non_operating_asset_realization']:.0%}를 전제로 할 때,
                향후 5년 매출 CAGR <strong>{reverse_result['revenue_cagr']:.1%}</strong>와
                <strong>{reverse_result['terminal_ebit_margin']:.1%}</strong>의 정상 영업이익률을
                전제합니다.<br><br>
                이는 유일한 해답이 아니라 현재 주가를 설명하는 등가 조합입니다. 따라서
                성장률이 낮아질수록 더 높은 수익성이 요구되고, 수익성이 낮아질수록 더 높은
                성장이 요구됩니다.
            </div>
        </div>
        """
    )
    _reverse_controls = mo.vstack(
        [
            mo.md(
                """
                <div class="fcff-panel-title">Reverse DCF 입력 가정</div>
                <div class="fcff-panel-caption">
                    정상 영업이익률과 비영업자산 가치인식률을 조정합니다.
                </div>
                """
            ),
            reverse_margin,
            reverse_asset_realization,
        ],
        gap=0.5,
    )
    _reverse_concept = mo.md(
        """
        <div class="reverse-concept">
            <div class="market-section-title">Reverse DCF 입력 가정 및 결과</div>
            <div class="market-section-copy">
                Reverse DCF는 목표주가를 산출하는 분석이 아니라, 현재 주가와 일치하도록
                미래 영업가정을 역으로 계산하는 분석입니다. 하나의 주가만으로 성장률과
                수익성을 동시에 확정할 수 없으므로, 선택한 정상 영업이익률을 고정한 뒤
                이에 대응하는 매출 CAGR을 계산합니다.
            </div>
        </div>
        """
    )
    market_calibration_body = mo.vstack(
        [
            mo.md(
                """
                <div class="market-section">
                    <div class="market-section-title">시장가치 교차검증 핵심 가정</div>
                    <div class="market-section-copy">
                        비교기업 Beta와 시장 입력자료를 이용해 DCF의 WACC 가정을 간결하게 검증합니다.
                    </div>
                </div>
                """
            ),
            _calibration_cards,
            mo.md(
                """
                <div class="market-section">
                    <div class="market-section-title">Trading Comps</div>
                    <div class="market-section-copy">
                        국내외 식품기업의 FY2026E EV/EBITDA, EV/EBIT, P/E를 같은 축에서 비교합니다.
                    </div>
                </div>
                """
            ),
            mo.ui.plotly(peer_multiples_fig),
            mo.md(
                """
                <div class="market-section">
                    <div class="market-section-title">Football Field 가치평가 범위</div>
                    <div class="market-section-copy">
                        DCF, Trading Comps, 과거 시장배수의 가치평가 범위를 현재 주가와 비교합니다.
                    </div>
                </div>
                """
            ),
            mo.ui.plotly(football_field_fig),
            _reverse_concept,
            mo.hstack(
                [_reverse_controls, _reverse_summary],
                widths=[0.28, 0.72],
                gap=1,
                align="stretch",
                wrap=True,
            ),
            mo.ui.plotly(reverse_tradeoff_fig),
            mo.md(
                """
                <div class="market-section">
                    <div class="market-section-title">출처 및 산정 기준</div>
                    <div class="market-warning">
                        Trading Comps는 MarketScreener FY2026E 저장 시점 자료, 무위험수익률은
                        한국은행 ECOS, ERP·국가위험프리미엄은 Damodaran 자료를 사용했습니다.
                        P/E는 2026E NOPAT을 정규화 이익 대용치로 사용했으며 보고서 발행 전 동일
                        공급자·관측주기로 재대사해야 합니다.
                    </div>
                </div>
                """
            ),
        ],
        gap=0.75,
    )
    return (market_calibration_body,)


@app.cell
def _(
    dashboard_css,
    executive_top,
    fcff_waterfall_row,
    formula_explorer_section,
    market_calibration_body,
    mo,
    overview_visuals,
    sensitivity_chapter_body,
):
    overview_page = mo.vstack(
        [
            dashboard_css,
            executive_top,
            overview_visuals,
        ],
        gap=1.1,
    )

    calculation_structure_page = mo.vstack(
        [
            dashboard_css,
            mo.md(
                """
                <div class="chapter-intro">
                    <div class="chapter-kicker">MODEL LOGIC</div>
                    <div class="chapter-title">계산구조</div>
                    <div class="chapter-copy">
                        매출액에서 EBIT·NOPAT·FCFF를 거쳐 기업가치와
                        Implied Share Price에 도달하는 계산 구조를 검증합니다.
                    </div>
                </div>
                """
            ),
            mo.vstack(
                [formula_explorer_section, fcff_waterfall_row],
                gap=0.45,
            ),
        ],
        gap=1.1,
    )

    sensitivity_analysis_page = mo.vstack(
        [
            dashboard_css,
            mo.md(
                """
                <div class="chapter-intro">
                    <div class="chapter-kicker">SCENARIO ANALYSIS</div>
                    <div class="chapter-title">Scenario &amp; Assumption Review</div>
                    <div class="chapter-copy">
                        Base Case와 Independent Valuation Range를 비교해 Key Assumption Risk를
                        식별합니다. WACC·Terminal Growth Rate·Revenue CAGR·EBIT Margin 변화가
                        Implied Share Price와 valuation range에 미치는 영향을 분석합니다.
                    </div>
                </div>
                """
            ),
            sensitivity_chapter_body,
        ],
        gap=1.1,
    )

    market_calibration_page = mo.vstack(
        [
            dashboard_css,
            mo.md(
                """
                <div class="chapter-intro">
                    <div class="chapter-kicker">시장가치 검증</div>
                    <div class="chapter-title">시장가치 교차검증</div>
                    <div class="chapter-copy">
                        DCF·Trading Comps·과거 시장배수의 가치평가 범위를 비교하고,
                        Reverse DCF를 통해 현재 주가에 내재된 성장률과 정상 영업이익률을 확인합니다.
                    </div>
                </div>
                """
            ),
            market_calibration_body,
        ],
        gap=1.1,
    )

    dashboard_chapters = mo.ui.tabs(
        {
            "1. 가치평가 개요": mo.lazy(
                overview_page,
                show_loading_indicator=True,
            ),
            "2. 계산구조": mo.lazy(
                calculation_structure_page,
                show_loading_indicator=True,
            ),
            "3. Scenario & Assumption Review": mo.lazy(
                sensitivity_analysis_page,
                show_loading_indicator=True,
            ),
            "4. 시장가치 검증": mo.lazy(
                market_calibration_page,
                show_loading_indicator=True,
            ),
        }
    )

    dashboard_chapters
    return


if __name__ == "__main__":
    app.run()
