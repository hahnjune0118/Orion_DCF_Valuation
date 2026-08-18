import marimo

__generated_with = "0.23.16"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go

    from pathlib import Path
    from orion_dcf import run_orion_dcf

    return Path, go, mo, pd, run_orion_dcf


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
                marker=dict(color=COLORS["blue"])
            ),
            decreasing=dict(
                marker=dict(color=COLORS["orange"])
            ),
            totals=dict(
                marker=dict(color=COLORS["navy"])
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
def _(bridge_fig, fcff_fig, mo, scenario_fig, sensitivity_fig):
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
        ],
        gap=1,
    )
    return visual_grid, visual_section_header


@app.cell
def _(executive_top, mo, visual_grid, visual_section_header):
    valuation_overview_page = mo.vstack(
        [
            executive_top,
            visual_section_header,
            visual_grid,
        ],
        gap=1.1,
    )

    valuation_overview_page
    return


if __name__ == "__main__":
    app.run()
