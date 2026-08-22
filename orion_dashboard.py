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

    return (
        Path,
        build_auditor_range_conclusion,
        build_fcff_waterfall_figure,
        build_fcff_waterfall_insight,
        build_formula_explorer_insight,
        build_valuation_formula_catalog,
        calculate_fcff_waterfall_kpis,
        escape,
        go,
        mo,
        pd,
        prepare_auditor_range_comparison,
        prepare_challenge_sensitivity_data,
        prepare_fcff_waterfall_data,
        prepare_formula_explorer_data,
        reconcile_formula_result,
        run_orion_dcf,
        select_forecast_row,
    )


@app.cell
def _(Path, pd, run_orion_dcf):
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
    return excel_path, forecast_df, model


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

            @media (max-width: 900px) {{
                .formula-kpi-grid,
                .formula-input-grid {{
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }}

                .pitch-header {{
                    padding: 22px 20px;
                }}

                .pitch-title {{
                    font-size: 22px;
                }}
            }}

            @media (max-width: 640px) {{
                .formula-kpi-grid,
                .challenge-case-grid {{
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
                Valuation 시나리오상 주당 내재가치는
                <span class="dynamic-value-chip" title="모델 계산값">{value_per_share:,.0f}</span>원으로
                주식 시장가치
                <span class="market-value-group"><span class="dynamic-value-chip" title="시장 기준값">{current_price:,.0f}</span>원<span class="pitch-inline-meta">(오리온 271560; 2026.08.21 기준)</span></span>
                대비 <span class="dynamic-value-chip" title="모델 계산값">{upside:.1%}</span>의
                상승여력을 시사합니다.
            </div>

            <div class="pitch-subtitle">
                지역별 매출액 전망과 영업수익성, 투자소요 및
                운전자본 변동을 FCFF로 전환하여 산정했습니다.
                가치 변동의 핵심 변수는 WACC와 영구성장률입니다.
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
                "기업가치",
                f"{enterprise_value / 1_000_000:.2f}조원",
                "FCFF 현재가치 + 계속가치",
                COLORS["teal"],
            ),
            kpi_card(
                "지분가치",
                f"{equity_value / 1_000_000:.2f}조원",
                "기업가치에서 순차입금 등 조정",
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
                "영구성장률 %{y}<br>"
                "주당 내재가치 %{z:,.0f}천원"
                "<extra></extra>"
            ),
        )
    )

    sensitivity_fig.update_layout(
        title=(
            "<b>경영진 주장 민감도</b>"
            "<br><sup>WACC × 영구성장률 · 주당 내재가치, 천원 · ● 기준</sup>"
        )
    )

    sensitivity_fig.update_xaxes(
        title="WACC",
        side="top",
    )

    sensitivity_fig.update_yaxes(
        title="영구성장률",
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
                "주당 내재가치 %{y:,.0f}천원"
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
            "<b>시나리오별 주당 내재가치</b>"
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
            colorbar=dict(title="중앙값, 천원", thickness=12),
            xgap=2,
            ygap=2,
            hovertemplate=(
                "WACC 변동 %{x}<br>"
                "영구성장률 변동 %{y}<br>"
                "범위 중앙값 %{z:,.0f}천원"
                "<extra></extra>"
            ),
        )
    )
    auditor_range_sensitivity_fig.update_layout(
        title=(
            "<b>감사인 범위추정치 민감도</b>"
            "<br><sup>셀: 하단–상단, 천원 · 색상: 중앙값 · ● 기준</sup>"
        )
    )
    auditor_range_sensitivity_fig.update_xaxes(
        title="WACC 변동", side="top"
    )
    auditor_range_sensitivity_fig.update_yaxes(title="영구성장률 변동")
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
        "OUTSIDE_RANGE": "경영진 주장 범위 밖",
        "WITHIN_RANGE": "경영진 주장 범위 내",
    }.get(
        auditor_range_comparison["검토상태"],
        auditor_range_comparison["검토상태"],
    )

    challenge_controls = mo.vstack(
        [
            mo.md(
                """
                <div class="fcff-panel-title">감사인 판단 범위 조정</div>
                <div class="fcff-panel-caption">
                    네 가지 핵심 가정의 하단·상단을 설정합니다.
                    Slider 옆 입력란에 %p 값을 직접 입력할 수 있습니다.
                </div>
                """
            ),
            mo.vstack(
                [
                    mo.md('<div class="range-control-label">매출성장률 조정 (%p)</div>'),
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
                    mo.md('<div class="range-control-label">영구성장률 조정 (%p)</div>'),
                    mo.hstack(
                        [auditor_lower_terminal_growth, auditor_upper_terminal_growth],
                        widths=[1, 1], gap=0.8, wrap=False,
                    ),
                ],
                gap=0.45,
            ),
            mo.md(
                """
                <div class="standard-inline">
                    <strong>감사기준서 540 · A121</strong> — 감사인은 경영진의
                    모형에 대체 가정·데이터를 적용하거나, 감사인 자신의 방법·가정·데이터로
                    점추정치 또는 범위를 도출할 수 있습니다.
                </div>
                """
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
            "매출 CAGR",
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
            "영구성장률",
            f"{_management['영구성장률']:.2%}",
            f"{_lower['영구성장률']:.2%}",
            f"{_upper['영구성장률']:.2%}",
        ),
        (
            "주당 내재가치",
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
                        경영진 주장 vs 감사인의 전문가적 판단
                    </div>
                    <div class="challenge-panel-caption">
                        Management assertion을 방법·가정·데이터 관점에서 독립적으로 재평가
                    </div>
                </div>
                <span class="challenge-status">{escape(_status_label)}</span>
            </div>
            <div class="challenge-case-grid">
                <div class="challenge-case">
                    <div class="challenge-case-name">경영진 주장 · MANAGEMENT ASSERTION</div>
                    <div class="challenge-case-value">{_management['주당 내재가치']:,.0f}원</div>
                    <div class="challenge-case-meta">
                        WACC {_management['WACC']:.2%} · g {_management['영구성장률']:.2%}<br>
                        상승여력 {_management['상승여력']:.1%}
                    </div>
                </div>
                <div class="challenge-case challenge-case-review">
                    <div class="challenge-case-name">감사인의 전문가적 판단 · RANGE ESTIMATE</div>
                    <div class="challenge-case-value">
                        {_lower['주당 내재가치']:,.0f}–{_upper['주당 내재가치']:,.0f}원
                    </div>
                    <div class="challenge-case-meta">
                        중앙값 {_midpoint:,.0f}원 · 범위폭 {auditor_range_comparison['범위폭']:,.0f}원<br>
                        상승여력 {_lower['상승여력']:.1%}–{_upper['상승여력']:.1%}
                    </div>
                </div>
            </div>
            <table class="challenge-table">
                <thead>
                    <tr><th>검토항목</th><th>경영진 주장</th><th>범위 하단</th><th>범위 상단</th></tr>
                </thead>
                <tbody>{_table_body}</tbody>
            </table>
            <div class="challenge-conclusion">{escape(auditor_range_conclusion)}</div>
            <div class="audit-standard">
                <div class="audit-standard-ref">감사기준서 540 · 문단 29(a) 및 A124</div>
                <p class="audit-standard-quote">
                    범위에는 충분하고 적합한 감사증거로 뒷받침되는 금액만 포함되어야 하며,
                    양 극단의 합리성에 대한 증거는 그 사이 금액의 합리성도 뒷받침합니다.
                </p>
            </div>
            <div class="misstatement-card">
                <div>
                    <div class="misstatement-label">
                        범위 이탈 판단적 왜곡표시 · {_misstatement_direction}
                    </div>
                    <div class="challenge-case-meta">
                        경영진 점추정치와 가장 가까운 범위 금액
                        {_nearest_range_value:,.0f}원의 차이
                    </div>
                </div>
                <div class="misstatement-value">{_misstatement:,.0f}원/주</div>
            </div>
            <div class="standard-inline" style="margin-top: 7px;">
                <strong>감사기준서 540 · A139 / 감사기준서 450 · A6</strong> —
                경영진 점추정치를 포함하지 않는 범위가 감사증거로 뒷받침되는 경우,
                가장 가까운 범위 지점과의 차이는 판단적 왜곡표시로 집계됩니다.
            </div>
            <a
                class="audit-standard-source"
                href="https://kicpa.or.kr/board/read.brd?boardId=acc0102&amp;bltnNo=11786004332051&amp;cmd=READ"
                target="_blank"
                rel="noopener noreferrer"
            >한국공인회계사회 원문 · 첨부 기준서 pp. 480, 517–519 ↗</a>
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
            "<b>기업가치에서 지분가치로의 연결</b>"
            "<br><sup>순비영업자산 및 차감항목 조정 · 조원</sup>"
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
                <div class="section-title">핵심 가정 검토 및 판단 차이</div>
                <div class="section-subtitle">
                    경영진 주장을 감사인의 전문가적 판단으로 재평가하고 가치 차이로 연결
                </div>
                <div class="standard-inline">
                    <strong>감사기준서 540 · 문단 28</strong> — 감사인의 추가감사절차에는
                    방법, 가정 또는 사용된 데이터가 재무보고체계의 관점에서 적합한지
                    평가하는 절차가 포함되어야 합니다.
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
                                <div class="section-title">WACC × 영구성장률</div>
                                <div class="section-subtitle">
                                    경영진 점추정치와 감사인 범위추정치 비교
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
        options={stage: stage for stage in _formula_stages},
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
                ("무위험수익률", _inputs["무위험수익률"], "rate"),
                (
                    "주식시장위험프리미엄",
                    _inputs["주식시장위험프리미엄"],
                    "rate",
                ),
                ("베타", _inputs["베타"], "multiple"),
                ("국가위험프리미엄", _inputs["국가위험프리미엄"], "rate"),
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
                ("영구성장률", _inputs["영구성장률"], "rate"),
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
                ("기업가치", _inputs["기업가치"], "trillion"),
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
                ("지분가치", _inputs["지분가치"], "trillion"),
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
        ("기업가치", "DCF", False),
        ("지분가치", "지분가치", False),
        ("주당 내재가치", "주당 내재가치", False),
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
            공시자료에서 주당 내재가치까지의 계산 논리와 모델 대사
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
    dashboard_css,
    executive_top,
    fcff_waterfall_row,
    formula_explorer_section,
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
                        주당 내재가치에 도달하는 계산 구조를 검증합니다.
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
                    <div class="chapter-kicker">INDEPENDENT REVIEW</div>
                    <div class="chapter-title">민감도 분석</div>
                    <div class="chapter-copy">
                        경영진 주장과 감사인의 전문가적 판단을 분리하고,
                        방법·가정·데이터의 변화가 가치범위에 미치는 영향을 검토합니다.
                    </div>
                    <div class="standard-inline" style="margin-top: 6px;">
                        <strong>감사기준서 540 · A118</strong> — “경영진의 점추정치와
                        추정불확실성에 대한 관련 공시를 평가하기 위해 감사인의 점추정치 또는
                        범위추정치를 도출하는 것은 … 적합한 접근일 수 있다.”
                    </div>
                </div>
                """
            ),
            sensitivity_chapter_body,
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
            "3. 민감도 분석": mo.lazy(
                sensitivity_analysis_page,
                show_loading_indicator=True,
            ),
        }
    )

    dashboard_chapters
    return


if __name__ == "__main__":
    app.run()
