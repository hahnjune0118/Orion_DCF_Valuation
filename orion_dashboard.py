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
        build_fcff_waterfall_figure,
        build_fcff_waterfall_insight,
        build_formula_explorer_insight,
        build_valuation_formula_catalog,
        calculate_fcff_waterfall_kpis,
        prepare_fcff_waterfall_data,
        prepare_formula_explorer_data,
        reconcile_formula_result,
        select_forecast_row,
    )
    from orion_dcf import run_orion_dcf

    return (
        Path,
        build_fcff_waterfall_figure,
        build_fcff_waterfall_insight,
        build_formula_explorer_insight,
        build_valuation_formula_catalog,
        calculate_fcff_waterfall_kpis,
        escape,
        go,
        mo,
        pd,
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
    current_price = 104_330

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
                padding: 28px 32px 26px 32px;
                margin-bottom: 4px;
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
                max-width: 1080px;
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
                padding: 17px 18px 15px 18px;
                min-height: 114px;
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
                font-size: 11px;
                line-height: 1.45;
                margin-bottom: 14px;
            }}

            .fcff-mini-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 8px;
                margin: 14px 0;
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
                margin: 8px 0 14px 0;
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
                padding: 18px;
                min-height: 420px;
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
                line-height: 1.6;
                margin-bottom: 14px;
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
                gap: 8px;
                margin: 12px 0;
            }}

            .formula-kpi {{
                background: {COLORS["background"]};
                border-radius: 8px;
                padding: 10px 11px;
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

            @media (max-width: 900px) {{
                .formula-kpi-grid {{
                    grid-template-columns: repeat(2, minmax(0, 1fr));
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
def _(mo, upside, value_per_share):
    dashboard_header = mo.md(
        f"""
        <div class="pitch-header">
            <div class="pitch-eyebrow">
                ORION · DCF VALUATION · EXECUTIVE VIEW
            </div>

            <div class="pitch-title">
                기준 시나리오상 주당 내재가치는
                {value_per_share:,.0f}원으로,
                기준주가 대비 {upside:.1%}의 상승여력을 시사
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
    current_price,
    enterprise_value,
    equity_value,
    kpi_card,
    mo,
    upside,
    value_per_share,
    wacc,
):
    kpi_strip = mo.hstack(
        [
            kpi_card(
                "주당 내재가치",
                f"{value_per_share:,.0f}원",
                "기준 시나리오",
                COLORS["blue"],
            ),
            kpi_card(
                "상승여력",
                f"{upside:.1%}",
                f"기준주가 {current_price:,.0f}원 대비",
                COLORS["gold"],
            ),
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
def _(dashboard_css, dashboard_header, kpi_strip, mo):
    executive_top = mo.vstack(
        [
            dashboard_css,
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
def _(excel_path, run_orion_dcf, wacc):
    base_terminal_growth = 0.02

    wacc_grid = sorted(
        {
            0.085,
            0.090,
            round(wacc, 6),
            0.100,
            0.105,
        }
    )

    growth_grid = [
        0.010,
        0.015,
        0.020,
        0.025,
        0.030,
    ]

    sensitivity_values = []

    for growth_rate in growth_grid:
        sensitivity_row = []

        for wacc_rate in wacc_grid:
            sensitivity_model = run_orion_dcf(
                excel_path,
                wacc_adjustment=wacc_rate - wacc,
                terminal_growth_adjustment=(
                    growth_rate - base_terminal_growth
                ),
            )

            sensitivity_row.append(
                sensitivity_model["지분가치"]["주당 내재가치"]
                / 1_000
            )

        sensitivity_values.append(sensitivity_row)

    sensitivity_text = []

    for row_index, growth_rate in enumerate(growth_grid):
        text_row = []

        for column_index, wacc_rate in enumerate(wacc_grid):
            value = sensitivity_values[row_index][column_index]

            if (
                abs(wacc_rate - wacc) < 0.00001
                and abs(growth_rate - base_terminal_growth) < 0.00001
            ):
                text_row.append(f"● {value:,.0f}")
            else:
                text_row.append(f"{value:,.0f}")

        sensitivity_text.append(text_row)
    return growth_grid, sensitivity_text, sensitivity_values, wacc_grid


@app.cell
def _(
    COLORS,
    apply_chart_style,
    go,
    growth_grid,
    sensitivity_text,
    sensitivity_values,
    wacc_grid,
):
    sensitivity_fig = go.Figure(
        data=go.Heatmap(
            z=sensitivity_values,
            x=[f"{rate:.2%}" for rate in wacc_grid],
            y=[f"{rate:.1%}" for rate in growth_grid],
            text=sensitivity_text,
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
            "<b>WACC 및 영구성장률 민감도</b>"
            "<br><sup>주당 내재가치, 천원 · ● 기준 시나리오</sup>"
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
        height=390,
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
        height=390,
    )
    return (scenario_fig,)


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
        height=390,
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
        height=390,
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
                "padding": "18px",
                "min-height": "390px",
                "box-shadow": "0 2px 8px rgba(16, 42, 67, 0.05)",
            }
        )
    )
    fcff_waterfall_view = mo.ui.plotly(fcff_waterfall_fig)
    fcff_waterfall_row = mo.hstack(
        [fcff_waterfall_summary, fcff_waterfall_view],
        widths=[0.25, 0.75],
        gap=1,
        align="stretch",
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
    )

    bridge_fig = apply_chart_style(
        bridge_fig,
        height=390,
    )
    return (bridge_fig,)


@app.cell
def _(
    bridge_fig,
    fcff_fig,
    fcff_waterfall_row,
    mo,
    scenario_fig,
    sensitivity_fig,
):
    sensitivity_view = mo.ui.plotly(sensitivity_fig)
    scenario_view = mo.ui.plotly(scenario_fig)
    fcff_view = mo.ui.plotly(fcff_fig)
    bridge_view = mo.ui.plotly(bridge_fig)

    visual_section_header = mo.md(
        """
        <div class="section-title">
            가치평가 결과 및 핵심 변동요인
        </div>
        <div class="section-subtitle">
            할인율·영구성장률 민감도, 사업 시나리오,
            현금창출력 및 지분가치 연결
        </div>
        """
    )

    visual_grid = mo.vstack(
        [
            mo.hstack(
                [sensitivity_view, scenario_view],
                widths=[1.15, 0.85],
                gap=1,
            ),
            mo.hstack(
                [fcff_view, bridge_view],
                widths=[1, 1],
                gap=1,
            ),
            fcff_waterfall_row,
        ],
        gap=1,
    )
    return visual_grid, visual_section_header


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
        return '<div class="formula-kpi-grid">' + "".join(_cards) + "</div>"

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
                "padding": "18px",
                "min-height": "420px",
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
            "padding": "14px 16px",
            "margin": "10px 0 12px 0",
        }
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
                    <span class="formula-badge {_badge_class}">{_status}</span>
                    <div class="formula-insight">{escape(formula_insight)}</div>
                    """
                ),
                _formula_detail,
            ],
            gap=0.5,
        ).style(
            {
                "background": COLORS["surface"],
                "border": f"1px solid {COLORS['line']}",
                "border-radius": "10px",
                "padding": "18px",
                "min-height": "420px",
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
        <div class="section-title">가치평가 산식 및 계산 계보</div>
        <div class="section-subtitle">
            공시자료에서 주당 내재가치까지의 계산 논리와 모델 대사
        </div>
        """
    )
    _formula_body = mo.hstack(
        [formula_explorer_left, formula_explorer_right],
        widths=[0.38, 0.62],
        gap=1,
        align="stretch",
    )
    formula_explorer_section = mo.vstack(
        [_formula_header, formula_lineage, _formula_body],
        gap=0.7,
    )
    return (formula_explorer_section,)


@app.cell
def _(
    executive_top,
    formula_explorer_section,
    mo,
    visual_grid,
    visual_section_header,
):
    valuation_overview_page = mo.vstack(
        [
            executive_top,
            visual_section_header,
            visual_grid,
            formula_explorer_section,
        ],
        gap=1.1,
    )

    valuation_overview_page
    return


if __name__ == "__main__":
    app.run()
