import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go

    from pathlib import Path
    from orion_dcf import run_orion_dcf
    from valuation_model import calculate_dcf

    return Path, calculate_dcf, go, mo, pd, px, run_orion_dcf


@app.cell
def _(Path, pd, run_orion_dcf):
    project_root = Path.cwd()

    excel_path = (
        project_root
        / "data"
        / "raw"
        / "orion_dcf.xlsx"
    )

    model = run_orion_dcf(excel_path)

    forecast_df = pd.DataFrame(model["전망"])
    return excel_path, forecast_df, model


@app.cell
def _(mo):
    mo.md("""
    # 오리온 DCF Valuation Lab

    **평가기준일:** 2025년 12월 31일
    **평가방법:** FCFF 기준 DCF
    **통화단위:** 백만원, 주당가치 원

    본 분석은 오리온의 K-IFRS 연결재무제표와 분석 가정을
    기반으로 기업가치 및 주당 내재가치를 산출합니다.
    """)
    return


@app.cell
def _(mo, model):
    wacc = model["WACC"]["WACC"]
    enterprise_value = model["DCF"]["기업가치"]
    equity_value = model["지분가치"]["지분가치"]
    value_per_share = model["지분가치"]["주당 내재가치"]
    current_price = 104_330

    mo.md(
        f"""
        ## 기준 시나리오

        | WACC | 기업가치 | 지분가치 | 주당 내재가치 |
        |---:|---:|---:|---:|
        | {wacc:.2%} | {enterprise_value:,.0f}백만원 | {equity_value:,.0f}백만원 | **{value_per_share:,.0f}원** |

        기준주가: **{current_price:,.0f}원**  
        내재 상승여력: **{value_per_share / current_price - 1:.1%}**
        """
    )
    return current_price, enterprise_value, equity_value, value_per_share, wacc


@app.cell
def _(forecast_df):
    display_columns = [
        "연도",
        "한국 매출액",
        "중국 매출액",
        "기타 국가 매출액",
        "매출액",
        "EBIT",
        "영업이익률",
        "D&A",
        "Capex",
        "NWC 증감",
        "FCFF",
    ]

    forecast_display = forecast_df[display_columns].copy()

    forecast_display["영업이익률"] = (
        forecast_display["영업이익률"]
        .map(lambda value: f"{value:.1%}")
    )

    amount_columns = [
        column
        for column in display_columns
        if column not in ["연도", "영업이익률"]
    ]

    for column in amount_columns:
        forecast_display[column] = (
            forecast_display[column]
            .map(lambda value: f"{value:,.0f}")
        )

    forecast_display
    return


@app.cell
def _(forecast_df, px):
    profit_chart = px.line(
        forecast_df,
        x="연도",
        y=["EBIT", "FCFF"],
        markers=True,
        title="EBIT 및 FCFF 전망",
        labels={
            "value": "금액(백만원)",
            "variable": "구분",
        },
    )

    profit_chart.update_layout(
        template="plotly_white",
        hovermode="x unified",
        legend_title_text="",
        yaxis_tickformat=",.0f",
    )

    profit_chart
    return


@app.cell
def _(enterprise_value, mo, value_per_share):
    model_status = (
        round(value_per_share) == 244_708
        and round(enterprise_value) == 6_774_772
    )

    model_status_output = mo.md(
        """
        ## ✅ 기준모형 대사 완료

        Python 계산엔진의 기업가치와 주당 내재가치가
        Excel 기준모형과 일치합니다.
        """
        if model_status
        else
        """
        ## ❌ 기준모형 대사 실패

        입력자료, 계산식 또는 반올림 기준을 확인해야 합니다.
        """
    )

    model_status_output
    return


@app.cell
def _(mo, wacc):
    wacc_control = mo.ui.slider(
        start=7.0,
        stop=13.0,
        step=0.01,
        value=wacc * 100,
        label="WACC (%)",
        show_value=True,
    )

    terminal_growth_control = mo.ui.slider(
        start=0.0,
        stop=4.0,
        step=0.1,
        value=2.0,
        label="영구성장률 (%)",
        show_value=True,
    )

    mo.hstack(
        [
            wacc_control,
            terminal_growth_control,
        ]
    )
    return terminal_growth_control, wacc_control


@app.cell
def _(
    calculate_dcf,
    current_price,
    forecast_df,
    model,
    terminal_growth_control,
    value_per_share,
    wacc_control,
):
    scenario_wacc = wacc_control.value / 100

    scenario_terminal_growth = (
        terminal_growth_control.value / 100
    )

    scenario_dcf = calculate_dcf(
        fcff_forecast=forecast_df["FCFF"].tolist(),
        wacc=scenario_wacc,
        terminal_growth_rate=scenario_terminal_growth,
    )

    net_non_operating_adjustment = model[
        "지분가치"
    ]["순비영업 조정액"]

    shares_outstanding = model[
        "지분가치"
    ]["유통주식수(백만주)"]

    scenario_enterprise_value = scenario_dcf["기업가치"]

    scenario_equity_value = (
        scenario_enterprise_value
        + net_non_operating_adjustment
    )

    scenario_value_per_share = (
        scenario_equity_value
        / shares_outstanding
    )

    scenario_upside = (
        scenario_value_per_share
        / current_price
        - 1
    )

    change_from_base = (
        scenario_value_per_share
        / value_per_share
        - 1
    )
    return (
        change_from_base,
        net_non_operating_adjustment,
        scenario_dcf,
        scenario_enterprise_value,
        scenario_equity_value,
        scenario_terminal_growth,
        scenario_upside,
        scenario_value_per_share,
        scenario_wacc,
        shares_outstanding,
    )


@app.cell
def _(
    change_from_base,
    enterprise_value,
    equity_value,
    mo,
    scenario_enterprise_value,
    scenario_equity_value,
    scenario_terminal_growth,
    scenario_upside,
    scenario_value_per_share,
    scenario_wacc,
    value_per_share,
    wacc,
):
    mo.md(f"""
    ## 선택 시나리오 가치평가

    | 항목 | 기준 시나리오 | 선택 시나리오 | 변동 |
    |---|---:|---:|---:|
    | WACC | {wacc:.2%} | {scenario_wacc:.2%} | {(scenario_wacc - wacc) * 10_000:+,.1f}bp |
    | 영구성장률 | 2.00% | {scenario_terminal_growth:.2%} | {(scenario_terminal_growth - 0.02) * 10_000:+,.1f}bp |
    | 기업가치 | {enterprise_value:,.0f} | {scenario_enterprise_value:,.0f} | {scenario_enterprise_value / enterprise_value - 1:+.1%} |
    | 지분가치 | {equity_value:,.0f} | {scenario_equity_value:,.0f} | {scenario_equity_value / equity_value - 1:+.1%} |
    | 주당 내재가치 | {value_per_share:,.0f}원 | **{scenario_value_per_share:,.0f}원** | **{change_from_base:+.1%}** |

    기준주가 대비 선택 시나리오 상승여력: **{scenario_upside:+.1%}**
    """)
    return


@app.cell
def _(mo, scenario_dcf):
    scenario_terminal_share = scenario_dcf[
        "계속기업가치 비중"
    ]

    mo.md(
        f"""
        ### 계속기업가치 의존도

        선택 시나리오에서 계속기업가치가 기업가치에서 차지하는 비중은
        **{scenario_terminal_share:.1%}**입니다.

        {
            "⚠️ 기업가치의 75% 이상이 계속기업가치에서 발생합니다. "
            "WACC와 영구성장률 가정에 대한 추가 검토가 필요합니다."
            if scenario_terminal_share >= 0.75
            else
            "✅ 계속기업가치 비중이 75% 미만입니다."
        }
        """
    )
    return


@app.cell
def _(calculate_dcf, pd):
    def build_sensitivity_table(
        fcff_forecast,
        wacc_values,
        terminal_growth_values,
        net_adjustment,
        shares,
    ):
        table_values = []

        for sensitivity_wacc in wacc_values:
            row_values = []

            for sensitivity_growth in terminal_growth_values:
                sensitivity_dcf = calculate_dcf(
                    fcff_forecast=fcff_forecast,
                    wacc=sensitivity_wacc,
                    terminal_growth_rate=sensitivity_growth,
                )

                sensitivity_equity_value = (
                    sensitivity_dcf["기업가치"]
                    + net_adjustment
                )

                sensitivity_value_per_share = (
                    sensitivity_equity_value
                    / shares
                )

                row_values.append(
                    sensitivity_value_per_share
                )

            table_values.append(row_values)

        row_labels = [
            f"{value:.1%}"
            for value in wacc_values
        ]

        column_labels = [
            f"{value:.1%}"
            for value in terminal_growth_values
        ]

        table = pd.DataFrame(
            table_values,
            index=row_labels,
            columns=column_labels,
        )

        table.index.name = "WACC"
        table.columns.name = "영구성장률"

        return table

    return (build_sensitivity_table,)


@app.cell
def _(
    build_sensitivity_table,
    forecast_df,
    net_non_operating_adjustment,
    shares_outstanding,
):
    sensitivity_wacc_values = [
        0.085,
        0.090,
        0.095,
        0.100,
        0.105,
    ]

    sensitivity_growth_values = [
        0.010,
        0.015,
        0.020,
        0.025,
        0.030,
    ]

    sensitivity_df = build_sensitivity_table(
        fcff_forecast=forecast_df["FCFF"].tolist(),
        wacc_values=sensitivity_wacc_values,
        terminal_growth_values=sensitivity_growth_values,
        net_adjustment=net_non_operating_adjustment,
        shares=shares_outstanding,
    )

    sensitivity_rounded = (
        sensitivity_df
        .round(0)
        .astype(int)
    )

    sensitivity_rounded
    return sensitivity_df, sensitivity_rounded


@app.cell
def _(px, sensitivity_rounded):
    sensitivity_chart = px.imshow(
        sensitivity_rounded,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdYlGn",
        labels={
            "x": "영구성장률",
            "y": "WACC",
            "color": "주당가치(원)",
        },
        title="WACC × 영구성장률 주당가치 민감도",
    )

    sensitivity_chart.update_layout(
        template="plotly_white",
        height=520,
        xaxis_side="top",
    )

    sensitivity_chart.update_coloraxes(
        colorbar_tickformat=",.0f",
    )

    sensitivity_chart
    return


@app.cell
def _(mo, sensitivity_df):
    growth_direction_check = all(
        sensitivity_df.loc[row].is_monotonic_increasing
        for row in sensitivity_df.index
    )

    wacc_direction_check = all(
        sensitivity_df[column].is_monotonic_decreasing
        for column in sensitivity_df.columns
    )

    sensitivity_status_output = mo.md(
        """
        ## ✅ 민감도 방향성 검증 완료

        - 영구성장률이 상승하면 주당가치가 상승합니다.
        - WACC가 상승하면 주당가치가 하락합니다.
        """
        if (
            growth_direction_check
            and wacc_direction_check
        )
        else
        """
        ## ❌ 민감도 방향성 검증 실패

        DCF 계산식, 행·열 방향 또는 입력값을 확인해야 합니다.
        """
    )

    sensitivity_status_output
    return growth_direction_check, wacc_direction_check


@app.cell
def _(mo):
    business_scenario_selector = mo.ui.dropdown(
        options=["비관", "기준", "낙관"],
        value="기준",
        label="사업 시나리오",
    )

    business_scenario_selector
    return (business_scenario_selector,)


@app.cell
def _(business_scenario_selector, excel_path, pd, run_orion_dcf):
    business_scenario_parameters = {
        "비관": {
            "revenue_growth_adjustment": -0.01,
            "ebit_margin_adjustment": -0.01,
            "wacc_adjustment": 0.005,
            "terminal_growth_adjustment": -0.005,
        },
        "기준": {
            "revenue_growth_adjustment": 0.0,
            "ebit_margin_adjustment": 0.0,
            "wacc_adjustment": 0.0,
            "terminal_growth_adjustment": 0.0,
        },
        "낙관": {
            "revenue_growth_adjustment": 0.01,
            "ebit_margin_adjustment": 0.01,
            "wacc_adjustment": -0.005,
            "terminal_growth_adjustment": 0.005,
        },
    }

    business_scenario_models = {
        scenario_name: run_orion_dcf(
            excel_path,
            **scenario_parameters,
        )
        for scenario_name, scenario_parameters
        in business_scenario_parameters.items()
    }

    selected_business_model = business_scenario_models[
        business_scenario_selector.value
    ]

    selected_business_df = pd.DataFrame(
        selected_business_model["전망"]
    )
    return (
        business_scenario_models,
        business_scenario_parameters,
        selected_business_df,
        selected_business_model,
    )


@app.cell
def _(business_scenario_models, pd):
    business_scenario_summary = pd.DataFrame(
        [
            {
                "시나리오": scenario_name,
                "2026년 매출액": scenario_model[
                    "전망"
                ][0]["매출액"],
                "2030년 매출액": scenario_model[
                    "전망"
                ][-1]["매출액"],
                "2030년 영업이익률": scenario_model[
                    "전망"
                ][-1]["영업이익률"],
                "2030년 FCFF": scenario_model[
                    "전망"
                ][-1]["FCFF"],
                "WACC": scenario_model[
                    "WACC"
                ]["WACC"],
                "기업가치": scenario_model[
                    "DCF"
                ]["기업가치"],
                "주당 내재가치": scenario_model[
                    "지분가치"
                ]["주당 내재가치"],
            }
            for scenario_name, scenario_model
            in business_scenario_models.items()
        ]
    )

    business_scenario_summary_display = (
        business_scenario_summary.copy()
    )

    for amount_column in [
        "2026년 매출액",
        "2030년 매출액",
        "2030년 FCFF",
        "기업가치",
        "주당 내재가치",
    ]:
        business_scenario_summary_display[amount_column] = (
            business_scenario_summary_display[
                amount_column
            ].map(lambda value: f"{value:,.0f}")
        )

    for rate_column in [
        "2030년 영업이익률",
        "WACC",
    ]:
        business_scenario_summary_display[rate_column] = (
            business_scenario_summary_display[
                rate_column
            ].map(lambda value: f"{value:.1%}")
        )

    business_scenario_summary_display
    return


@app.cell
def _(
    business_scenario_parameters,
    business_scenario_selector,
    current_price,
    mo,
    selected_business_model,
):
    selected_scenario_name = (
        business_scenario_selector.value
    )

    selected_scenario_parameters = (
        business_scenario_parameters[
            selected_scenario_name
        ]
    )

    selected_scenario_value_per_share = (
        selected_business_model[
            "지분가치"
        ]["주당 내재가치"]
    )

    selected_scenario_enterprise_value = (
        selected_business_model[
            "DCF"
        ]["기업가치"]
    )

    selected_scenario_upside = (
        selected_scenario_value_per_share
        / current_price
        - 1
    )

    mo.md(
        f"""
        ## {selected_scenario_name} 시나리오

        | 주요 가정 | 기준 대비 조정 |
        |---|---:|
        | 매출성장률 | {selected_scenario_parameters["revenue_growth_adjustment"]:+.1%}p |
        | EBIT 이익률 | {selected_scenario_parameters["ebit_margin_adjustment"]:+.1%}p |
        | WACC | {selected_scenario_parameters["wacc_adjustment"]:+.1%}p |
        | 영구성장률 | {selected_scenario_parameters["terminal_growth_adjustment"]:+.1%}p |

        **기업가치:** {selected_scenario_enterprise_value:,.0f}백만원  
        **주당 내재가치:** {selected_scenario_value_per_share:,.0f}원  
        **기준주가 대비 상승여력:** {selected_scenario_upside:+.1%}
        """
    )
    return selected_scenario_name, selected_scenario_parameters


@app.cell
def _(business_scenario_models, pd, px):
    business_scenario_fcff_df = pd.concat(
        [
            pd.DataFrame(
                {
                    "연도": [
                        result["연도"]
                        for result in scenario_model["전망"]
                    ],
                    "FCFF": [
                        result["FCFF"]
                        for result in scenario_model["전망"]
                    ],
                    "시나리오": scenario_name,
                }
            )
            for scenario_name, scenario_model
            in business_scenario_models.items()
        ],
        ignore_index=True,
    )

    business_scenario_fcff_chart = px.line(
        business_scenario_fcff_df,
        x="연도",
        y="FCFF",
        color="시나리오",
        markers=True,
        category_orders={
            "시나리오": ["비관", "기준", "낙관"],
        },
        color_discrete_map={
            "비관": "#D62728",
            "기준": "#1F77B4",
            "낙관": "#2CA02C",
        },
        title="시나리오별 FCFF 전망",
    )

    business_scenario_fcff_chart.update_layout(
        template="plotly_white",
        hovermode="x unified",
        legend_title_text="",
        yaxis_tickformat=",.0f",
    )

    business_scenario_fcff_chart
    return


@app.cell
def _(mo):
    fcff_year_selector = mo.ui.dropdown(
        options=[2026, 2027, 2028, 2029, 2030],
        value=2026,
        label="FCFF 분석연도",
    )

    fcff_year_selector
    return (fcff_year_selector,)


@app.cell
def _(fcff_year_selector, selected_business_df):
    selected_fcff_year = int(
        fcff_year_selector.value
    )

    fcff_bridge_row = (
        selected_business_df.loc[
            selected_business_df["연도"]
            == selected_fcff_year
        ]
        .iloc[0]
    )

    bridge_ebit = fcff_bridge_row["EBIT"]

    bridge_cash_tax = (
        fcff_bridge_row["NOPAT"]
        - fcff_bridge_row["EBIT"]
    )

    bridge_nopat = fcff_bridge_row["NOPAT"]
    bridge_depreciation = fcff_bridge_row["D&A"]
    bridge_capex_effect = -fcff_bridge_row["Capex"]
    bridge_nwc_effect = -fcff_bridge_row["NWC 증감"]
    bridge_fcff = fcff_bridge_row["FCFF"]

    reconstructed_fcff = (
        bridge_ebit
        + bridge_cash_tax
        + bridge_depreciation
        + bridge_capex_effect
        + bridge_nwc_effect
    )

    fcff_bridge_difference = (
        reconstructed_fcff - bridge_fcff
    )

    fcff_conversion_ratio = (
        bridge_fcff / bridge_ebit
    )
    return (
        bridge_capex_effect,
        bridge_cash_tax,
        bridge_depreciation,
        bridge_ebit,
        bridge_fcff,
        bridge_nopat,
        bridge_nwc_effect,
        fcff_bridge_difference,
        fcff_conversion_ratio,
        selected_fcff_year,
    )


@app.cell
def _(
    bridge_capex_effect,
    bridge_cash_tax,
    bridge_depreciation,
    bridge_ebit,
    bridge_fcff,
    bridge_nopat,
    bridge_nwc_effect,
    go,
    selected_fcff_year,
    selected_scenario_name,
):
    fcff_waterfall_chart = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=[
                "absolute",
                "relative",
                "total",
                "relative",
                "relative",
                "relative",
                "total",
            ],
            x=[
                "EBIT",
                "현금법인세",
                "NOPAT",
                "D&A",
                "Capex",
                "NWC 증감",
                "FCFF",
            ],
            y=[
                bridge_ebit,
                bridge_cash_tax,
                0,
                bridge_depreciation,
                bridge_capex_effect,
                bridge_nwc_effect,
                0,
            ],
            text=[
                f"{bridge_ebit:,.0f}",
                f"{bridge_cash_tax:,.0f}",
                f"{bridge_nopat:,.0f}",
                f"{bridge_depreciation:,.0f}",
                f"{bridge_capex_effect:,.0f}",
                f"{bridge_nwc_effect:,.0f}",
                f"{bridge_fcff:,.0f}",
            ],
            textposition="outside",
            connector={
                "line": {
                    "color": "#8A8A8A",
                    "width": 1,
                }
            },
            increasing={
                "marker": {
                    "color": "#2CA02C",
                }
            },
            decreasing={
                "marker": {
                    "color": "#D62728",
                }
            },
            totals={
                "marker": {
                    "color": "#1F4E78",
                }
            },
        )
    )

    fcff_waterfall_chart.update_layout(
        title=(
            f"{selected_scenario_name} 시나리오 "
            f"{selected_fcff_year}년 EBIT → FCFF"
        ),
        template="plotly_white",
        showlegend=False,
        height=560,
        yaxis_title="금액(백만원)",
        yaxis_tickformat=",.0f",
    )

    fcff_waterfall_chart
    return


@app.cell
def _(
    bridge_capex_effect,
    bridge_cash_tax,
    bridge_depreciation,
    bridge_ebit,
    bridge_fcff,
    bridge_nopat,
    bridge_nwc_effect,
    fcff_bridge_difference,
    fcff_conversion_ratio,
    mo,
):
    bridge_status = (
        abs(fcff_bridge_difference) < 0.000001
    )

    mo.md(
        f"""
        ## FCFF 연결표 검증

        | 항목 | 금액 |
        |---|---:|
        | EBIT | {bridge_ebit:,.0f}백만원 |
        | 현금법인세 | {bridge_cash_tax:,.0f}백만원 |
        | NOPAT | {bridge_nopat:,.0f}백만원 |
        | D&A 가산 | {bridge_depreciation:,.0f}백만원 |
        | Capex 차감 | {bridge_capex_effect:,.0f}백만원 |
        | NWC 증감 효과 | {bridge_nwc_effect:,.0f}백만원 |
        | **FCFF** | **{bridge_fcff:,.0f}백만원** |

        **EBIT 대비 FCFF 현금전환율:** {fcff_conversion_ratio:.1%}  
        **Footing 차이:** {fcff_bridge_difference:,.10f}백만원  
        **검증 결과:** {"✅ PASS" if bridge_status else "❌ FAIL"}
        """
    )
    return


@app.cell
def _(selected_business_model):
    selected_equity_bridge = selected_business_model[
        "지분가치"
    ]

    bridge_enterprise_value = selected_business_model[
        "DCF"
    ]["기업가치"]

    bridge_excess_cash = selected_equity_bridge[
        "초과현금"
    ]

    bridge_financial_assets = (
        selected_equity_bridge["단기금융상품"]
        + selected_equity_bridge[
            "유동 당기손익-공정가치측정 금융자산"
        ]
    )

    bridge_investments = (
        selected_equity_bridge["리가켐바이오 시장가치"]
        + selected_equity_bridge[
            "기타 관계기업 및 공동기업투자"
        ]
        + selected_equity_bridge[
            "비유동 기타포괄손익-공정가치측정 금융자산"
        ]
    )

    bridge_investment_property = (
        selected_equity_bridge["투자부동산 공정가치"]
    )

    bridge_financial_debt_effect = (
        -selected_equity_bridge["금융기관차입금"]
    )

    bridge_lease_effect = (
        -selected_equity_bridge["리스부채"]
    )

    bridge_nci_effect = (
        -selected_equity_bridge["비지배지분"]
    )

    bridge_equity_value = selected_equity_bridge[
        "지분가치"
    ]

    reconstructed_equity_value = (
        bridge_enterprise_value
        + bridge_excess_cash
        + bridge_financial_assets
        + bridge_investments
        + bridge_investment_property
        + bridge_financial_debt_effect
        + bridge_lease_effect
        + bridge_nci_effect
    )

    equity_bridge_difference = (
        reconstructed_equity_value
        - bridge_equity_value
    )
    return (
        bridge_enterprise_value,
        bridge_equity_value,
        bridge_excess_cash,
        bridge_financial_assets,
        bridge_financial_debt_effect,
        bridge_investment_property,
        bridge_investments,
        bridge_lease_effect,
        bridge_nci_effect,
        equity_bridge_difference,
        selected_equity_bridge,
    )


@app.cell
def _(
    bridge_enterprise_value,
    bridge_equity_value,
    bridge_excess_cash,
    bridge_financial_assets,
    bridge_financial_debt_effect,
    bridge_investment_property,
    bridge_investments,
    bridge_lease_effect,
    bridge_nci_effect,
    go,
    selected_scenario_name,
):
    equity_waterfall_chart = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=[
                "absolute",
                "relative",
                "relative",
                "relative",
                "relative",
                "relative",
                "relative",
                "relative",
                "total",
            ],
            x=[
                "기업가치",
                "초과현금",
                "금융자산",
                "투자자산",
                "투자부동산",
                "금융기관차입금",
                "리스부채",
                "비지배지분",
                "지분가치",
            ],
            y=[
                bridge_enterprise_value,
                bridge_excess_cash,
                bridge_financial_assets,
                bridge_investments,
                bridge_investment_property,
                bridge_financial_debt_effect,
                bridge_lease_effect,
                bridge_nci_effect,
                0,
            ],
            text=[
                f"{bridge_enterprise_value:,.0f}",
                f"{bridge_excess_cash:+,.0f}",
                f"{bridge_financial_assets:+,.0f}",
                f"{bridge_investments:+,.0f}",
                f"{bridge_investment_property:+,.0f}",
                f"{bridge_financial_debt_effect:+,.0f}",
                f"{bridge_lease_effect:+,.0f}",
                f"{bridge_nci_effect:+,.0f}",
                f"{bridge_equity_value:,.0f}",
            ],
            textposition="outside",
            connector={
                "line": {
                    "color": "#8A8A8A",
                    "width": 1,
                }
            },
            increasing={
                "marker": {
                    "color": "#2CA02C",
                }
            },
            decreasing={
                "marker": {
                    "color": "#D62728",
                }
            },
            totals={
                "marker": {
                    "color": "#1F4E78",
                }
            },
        )
    )

    equity_waterfall_chart.update_layout(
        title=(
            f"{selected_scenario_name} 시나리오 "
            "기업가치 → 지분가치"
        ),
        template="plotly_white",
        showlegend=False,
        height=600,
        yaxis_title="금액(백만원)",
        yaxis_tickformat=",.0f",
    )

    equity_waterfall_chart
    return


@app.cell
def _(
    bridge_enterprise_value,
    bridge_equity_value,
    bridge_excess_cash,
    bridge_financial_assets,
    bridge_financial_debt_effect,
    bridge_investment_property,
    bridge_investments,
    bridge_lease_effect,
    bridge_nci_effect,
    equity_bridge_difference,
    mo,
    selected_equity_bridge,
):
    equity_bridge_status = (
        abs(equity_bridge_difference) < 0.000001
    )

    selected_bridge_value_per_share = (
        bridge_equity_value
        / selected_equity_bridge[
            "유통주식수(백만주)"
        ]
    )

    mo.md(
        f"""
        ## 기업가치–지분가치 연결표 검증

        | 항목 | 금액 |
        |---|---:|
        | DCF 기업가치 | {bridge_enterprise_value:,.0f}백만원 |
        | 초과현금 | +{bridge_excess_cash:,.0f}백만원 |
        | 금융자산 | +{bridge_financial_assets:,.0f}백만원 |
        | 투자자산 | +{bridge_investments:,.0f}백만원 |
        | 투자부동산 | +{bridge_investment_property:,.0f}백만원 |
        | 금융기관차입금 | {bridge_financial_debt_effect:+,.0f}백만원 |
        | 리스부채 | {bridge_lease_effect:+,.0f}백만원 |
        | 비지배지분 | {bridge_nci_effect:+,.0f}백만원 |
        | **지분가치** | **{bridge_equity_value:,.0f}백만원** |
        | **주당 내재가치** | **{selected_bridge_value_per_share:,.0f}원** |

        **Footing 차이:** {equity_bridge_difference:,.10f}백만원  
        **검증 결과:** {"✅ PASS" if equity_bridge_status else "❌ FAIL"}
        """
    )
    return


@app.cell
def _(pd):
    def build_region_analysis(forecast_data):
        region_mapping = {
            "한국 매출액": "한국",
            "중국 매출액": "중국",
            "기타 국가 매출액": "기타 국가",
        }

        long_data = (
            forecast_data[
                [
                    "연도",
                    *region_mapping.keys(),
                ]
            ]
            .melt(
                id_vars=["연도"],
                value_vars=list(region_mapping.keys()),
                var_name="지역",
                value_name="매출액",
            )
        )

        long_data["지역"] = long_data[
            "지역"
        ].map(region_mapping)

        summary_rows = []

        for source_column, region_name in region_mapping.items():
            first_revenue = forecast_data[
                source_column
            ].iloc[0]

            final_revenue = forecast_data[
                source_column
            ].iloc[-1]

            forecast_cagr = (
                final_revenue / first_revenue
            ) ** (1 / 4) - 1

            final_revenue_mix = (
                final_revenue
                / forecast_data["매출액"].iloc[-1]
            )

            summary_rows.append(
                {
                    "지역": region_name,
                    "2026년 매출액": first_revenue,
                    "2030년 매출액": final_revenue,
                    "2026~2030 CAGR": forecast_cagr,
                    "2030년 매출비중": final_revenue_mix,
                }
            )

        summary_data = pd.DataFrame(summary_rows)

        return long_data, summary_data

    return (build_region_analysis,)


@app.cell
def _(build_region_analysis, selected_business_df):
    region_revenue_long_df, region_summary_df = (
        build_region_analysis(
            selected_business_df
        )
    )

    region_summary_display = region_summary_df.copy()

    for region_amount_column in [
        "2026년 매출액",
        "2030년 매출액",
    ]:
        region_summary_display[region_amount_column] = (
            region_summary_display[
                region_amount_column
            ].map(lambda value: f"{value:,.0f}")
        )

    for region_rate_column in [
        "2026~2030 CAGR",
        "2030년 매출비중",
    ]:
        region_summary_display[region_rate_column] = (
            region_summary_display[
                region_rate_column
            ].map(lambda value: f"{value:.1%}")
        )

    region_summary_display
    return region_revenue_long_df, region_summary_df


@app.cell
def _(px, region_revenue_long_df, selected_scenario_name):
    region_revenue_chart = px.area(
        region_revenue_long_df,
        x="연도",
        y="매출액",
        color="지역",
        category_orders={
            "지역": ["한국", "중국", "기타 국가"],
        },
        color_discrete_map={
            "한국": "#1F77B4",
            "중국": "#D62728",
            "기타 국가": "#2CA02C",
        },
        title=(
            f"{selected_scenario_name} 시나리오 "
            "지역별 매출액 전망"
        ),
    )

    region_revenue_chart.update_layout(
        template="plotly_white",
        hovermode="x unified",
        legend_title_text="",
        height=520,
        yaxis_title="매출액(백만원)",
        yaxis_tickformat=",.0f",
    )

    region_revenue_chart
    return


@app.cell
def _(mo, region_revenue_long_df, region_summary_df, selected_business_df):
    region_revenue_recalculated = (
        region_revenue_long_df
        .groupby("연도")["매출액"]
        .sum()
        .reset_index(name="지역합계")
    )

    region_revenue_footing = (
        selected_business_df[
            ["연도", "매출액"]
        ]
        .merge(
            region_revenue_recalculated,
            on="연도",
            how="left",
        )
    )

    region_revenue_footing["차이"] = (
        region_revenue_footing["지역합계"]
        - region_revenue_footing["매출액"]
    )

    maximum_region_difference = (
        region_revenue_footing["차이"]
        .abs()
        .max()
    )

    region_mix_sum = (
        region_summary_df[
            "2030년 매출비중"
        ].sum()
    )

    region_footing_status = (
        maximum_region_difference < 0.000001
        and abs(region_mix_sum - 1) < 0.000001
    )

    mo.md(
        f"""
        ## 지역별 매출액 검증

        **지역별 매출액 합계와 연결 매출액의 최대 차이:**  
        {maximum_region_difference:,.10f}백만원

        **2030년 지역별 매출비중 합계:**  
        {region_mix_sum:.2%}

        **검증 결과:** {"✅ PASS" if region_footing_status else "❌ FAIL"}
        """
    )
    return maximum_region_difference, region_mix_sum


@app.cell
def _(pd):
    def build_validation_table(
        base_enterprise_value,
        base_value_per_share,
        base_wacc,
        fcff_difference,
        equity_difference,
        region_difference,
        region_mix,
        capital_weight_sum,
        selected_wacc_spread,
        sensitivity_direction_status,
        business_scenario_order_status,
    ):
        validation_rows = []

        def add_numeric_check(
            check_name,
            actual,
            expected,
            tolerance,
            note,
        ):
            difference = actual - expected

            validation_rows.append(
                {
                    "검증항목": check_name,
                    "실제값": f"{actual:,.10f}",
                    "기대값": f"{expected:,.10f}",
                    "차이": f"{difference:,.10f}",
                    "허용오차": f"{tolerance:,.10f}",
                    "상태": (
                        "PASS"
                        if abs(difference) <= tolerance
                        else "FAIL"
                    ),
                    "설명": note,
                }
            )

        add_numeric_check(
            check_name="기준 기업가치 Golden Master",
            actual=base_enterprise_value,
            expected=6_774_771.675811715,
            tolerance=0.001,
            note="Python 기업가치와 Excel 기준모형 대사",
        )

        add_numeric_check(
            check_name="기준 주당가치 Golden Master",
            actual=base_value_per_share,
            expected=244_708.45588436097,
            tolerance=0.001,
            note="Python 주당가치와 Excel 기준모형 대사",
        )

        add_numeric_check(
            check_name="기준 WACC",
            actual=base_wacc,
            expected=0.09477625,
            tolerance=0.000000000001,
            note="자기자본비용 및 세후 타인자본비용 가중",
        )

        add_numeric_check(
            check_name="EBIT–FCFF 연결표",
            actual=fcff_difference,
            expected=0.0,
            tolerance=0.000001,
            note="선택 연도 FCFF 구성요소 합계 검증",
        )

        add_numeric_check(
            check_name="기업가치–지분가치 연결표",
            actual=equity_difference,
            expected=0.0,
            tolerance=0.000001,
            note="비영업자산 및 차감항목 합계 검증",
        )

        add_numeric_check(
            check_name="지역별 매출액 합계",
            actual=region_difference,
            expected=0.0,
            tolerance=0.000001,
            note="지역별 매출액 합계와 연결 매출액 대사",
        )

        add_numeric_check(
            check_name="지역별 매출비중 합계",
            actual=region_mix,
            expected=1.0,
            tolerance=0.000001,
            note="2030년 지역별 매출비중 합계",
        )

        add_numeric_check(
            check_name="자본구조 비중 합계",
            actual=capital_weight_sum,
            expected=1.0,
            tolerance=0.000001,
            note="자기자본 비중과 타인자본 비중 합계",
        )

        validation_rows.append(
            {
                "검증항목": "WACC와 영구성장률 관계",
                "실제값": f"{selected_wacc_spread:.4%}",
                "기대값": "0보다 큼",
                "차이": "-",
                "허용오차": "-",
                "상태": (
                    "PASS"
                    if selected_wacc_spread > 0
                    else "FAIL"
                ),
                "설명": "Gordon Growth Model의 수학적 성립 조건",
            }
        )

        validation_rows.append(
            {
                "검증항목": "민감도 방향성",
                "실제값": str(sensitivity_direction_status),
                "기대값": "True",
                "차이": "-",
                "허용오차": "-",
                "상태": (
                    "PASS"
                    if sensitivity_direction_status
                    else "FAIL"
                ),
                "설명": "WACC 상승 시 가치 하락, 성장률 상승 시 가치 상승",
            }
        )

        validation_rows.append(
            {
                "검증항목": "사업 시나리오 순서",
                "실제값": str(business_scenario_order_status),
                "기대값": "True",
                "차이": "-",
                "허용오차": "-",
                "상태": (
                    "PASS"
                    if business_scenario_order_status
                    else "FAIL"
                ),
                "설명": "낙관 가치 > 기준 가치 > 비관 가치",
            }
        )

        return pd.DataFrame(validation_rows)

    return (build_validation_table,)


@app.cell
def _(
    build_validation_table,
    business_scenario_models,
    enterprise_value,
    equity_bridge_difference,
    fcff_bridge_difference,
    growth_direction_check,
    maximum_region_difference,
    model,
    region_mix_sum,
    selected_business_model,
    selected_scenario_parameters,
    value_per_share,
    wacc,
    wacc_direction_check,
):
    scenario_values_for_check = {
        scenario_name: scenario_model[
            "지분가치"
        ]["주당 내재가치"]
        for scenario_name, scenario_model
        in business_scenario_models.items()
    }

    business_scenario_order_check = (
        scenario_values_for_check["낙관"]
        > scenario_values_for_check["기준"]
        > scenario_values_for_check["비관"]
    )

    selected_terminal_growth_for_check = (
        0.02
        + selected_scenario_parameters[
            "terminal_growth_adjustment"
        ]
    )

    selected_wacc_for_check = selected_business_model[
        "WACC"
    ]["WACC"]

    selected_wacc_spread = (
        selected_wacc_for_check
        - selected_terminal_growth_for_check
    )

    sensitivity_direction_check = (
        growth_direction_check
        and wacc_direction_check
    )

    capital_weight_sum_for_check = model[
        "WACC"
    ]["자본구조 비중 합계"]

    validation_df = build_validation_table(
        base_enterprise_value=enterprise_value,
        base_value_per_share=value_per_share,
        base_wacc=wacc,
        fcff_difference=fcff_bridge_difference,
        equity_difference=equity_bridge_difference,
        region_difference=maximum_region_difference,
        region_mix=region_mix_sum,
        capital_weight_sum=capital_weight_sum_for_check,
        selected_wacc_spread=selected_wacc_spread,
        sensitivity_direction_status=(
            sensitivity_direction_check
        ),
        business_scenario_order_status=(
            business_scenario_order_check
        ),
    )

    validation_df
    return scenario_values_for_check, validation_df


@app.cell
def _(mo, selected_business_model, selected_scenario_name, validation_df):
    failed_validation_count = (
        validation_df["상태"] == "FAIL"
    ).sum()

    passed_validation_count = (
        validation_df["상태"] == "PASS"
    ).sum()

    overall_model_status = (
        failed_validation_count == 0
    )

    selected_terminal_value_share = (
        selected_business_model[
            "DCF"
        ]["계속기업가치 비중"]
    )

    terminal_value_risk_message = (
        "⚠️ 계속기업가치 비중이 75% 이상입니다. "
        "WACC와 영구성장률 가정에 대한 추가 검토가 필요합니다."
        if selected_terminal_value_share >= 0.75
        else
        "✅ 계속기업가치 비중이 75% 미만입니다."
    )

    mo.md(
        f"""
        # 모형검증 결과

        ## {"✅ 전체 PASS" if overall_model_status else "❌ 검증 실패"}

        - 통과: **{passed_validation_count}개**
        - 실패: **{failed_validation_count}개**
        - 선택 시나리오: **{selected_scenario_name}**
        - 계속기업가치 비중: **{selected_terminal_value_share:.1%}**

        {terminal_value_risk_message}
        """
    )
    return


@app.cell
def _(pd):
    source_register_df = pd.DataFrame(
        [
            {
                "출처 ID": "S1",
                "항목": "연결포괄손익계산서",
                "기간·기준일": "2023~2025 회계연도",
                "출처": "[오리온]사업보고서(2026.03.18)",
                "공시 위치": "42~43쪽",
                "모형 사용처": "매출액·매출원가·EBIT",
                "근거 유형": "공시 직접관측",
                "URL": "https://dart.fss.or.kr/",
            },
            {
                "출처 ID": "S2",
                "항목": "D&A·Capex·현금흐름",
                "기간·기준일": "2023~2025 회계연도",
                "출처": "[오리온]사업보고서(2026.03.18)",
                "공시 위치": "16쪽, 44~46쪽",
                "모형 사용처": "D&A·Capex·영업현금흐름 검토",
                "근거 유형": "공시 직접관측",
                "URL": "https://dart.fss.or.kr/",
            },
            {
                "출처 ID": "S3",
                "항목": "연결재무상태표",
                "기간·기준일": "2023~2025년 말",
                "출처": "[오리온]사업보고서(2026.03.18)",
                "공시 위치": "41~42쪽",
                "모형 사용처": "NWC·비영업자산·차감항목",
                "근거 유형": "공시 직접관측",
                "URL": "https://dart.fss.or.kr/",
            },
            {
                "출처 ID": "S4",
                "항목": "투자부동산 공정가치",
                "기간·기준일": "2025년 12월 31일",
                "출처": "[오리온]사업보고서(2026.03.18)",
                "공시 위치": "78쪽",
                "모형 사용처": "비영업자산",
                "근거 유형": "공시 직접관측",
                "URL": "https://dart.fss.or.kr/",
            },
            {
                "출처 ID": "S5",
                "항목": "관계기업·공동기업투자",
                "기간·기준일": "2025년 12월 31일",
                "출처": "[오리온]사업보고서(2026.03.18)",
                "공시 위치": "83~85쪽",
                "모형 사용처": "리가켐바이오 및 기타 투자자산",
                "근거 유형": "공시 직접관측·시장가치",
                "URL": "https://dart.fss.or.kr/",
            },
            {
                "출처 ID": "S6",
                "항목": "발행주식수·자기주식수",
                "기간·기준일": "2025년 12월 31일",
                "출처": "[오리온]사업보고서(2026.03.18)",
                "공시 위치": "7~8쪽",
                "모형 사용처": "유통주식수·주당가치",
                "근거 유형": "공시 직접관측",
                "URL": "https://dart.fss.or.kr/",
            },
            {
                "출처 ID": "S7",
                "항목": "2025년 12월 평균주가",
                "기간·기준일": "2025년 12월",
                "출처": "[오리온]사업보고서(2026.03.18)",
                "공시 위치": "273쪽",
                "모형 사용처": "내재 상승여력 참고",
                "근거 유형": "시장 참고자료",
                "URL": "https://dart.fss.or.kr/",
            },
            {
                "출처 ID": "S8",
                "항목": "지역별 매출액",
                "기간·기준일": "2024~2025 회계연도",
                "출처": "[오리온]사업보고서(2026.03.18)",
                "공시 위치": "68쪽",
                "모형 사용처": "한국·중국·기타 국가 매출액 추정",
                "근거 유형": "공시 직접관측",
                "URL": "https://dart.fss.or.kr/",
            },
            {
                "출처 ID": "S9",
                "항목": "진천공장 투자계획",
                "기간·기준일": "2025년 6월~2027년 12월",
                "출처": "[오리온]사업보고서(2026.03.18)",
                "공시 위치": "7쪽",
                "모형 사용처": "성장 Capex 가정",
                "근거 유형": "공시기반 추정",
                "URL": "https://dart.fss.or.kr/",
            },
            {
                "출처 ID": "S10",
                "항목": "2025년 감사보고서",
                "기간·기준일": "2025 회계연도",
                "출처": "오리온 IR",
                "공시 위치": "재무정보",
                "모형 사용처": "사업보고서 교차검증",
                "근거 유형": "회사 공시자료",
                "URL": (
                    "https://www.orionworld.com/"
                    "en/invest/finance/79"
                ),
            },
            {
                "출처 ID": "S11",
                "항목": "2025년 4분기 실적자료",
                "기간·기준일": "2025 회계연도",
                "출처": "오리온 IR",
                "공시 위치": "재무정보",
                "모형 사용처": "경영진 설명·실적 교차검증",
                "근거 유형": "보조자료",
                "URL": (
                    "https://www.orionworld.com/"
                    "en/invest/finance/78"
                ),
            },
            {
                "출처 ID": "S12",
                "항목": "한국 금리자료",
                "기간·기준일": "2025년",
                "출처": "한국은행 경제통계시스템",
                "공시 위치": "시장금리",
                "모형 사용처": "무위험수익률 참고",
                "근거 유형": "시장자료",
                "URL": "https://ecos.bok.or.kr/",
            },
        ]
    )

    source_register_df
    return (source_register_df,)


@app.cell
def _(pd):
    assumption_register_df = pd.DataFrame(
        [
            {
                "가정 항목": "지역별 매출성장률",
                "Excel 위치": "가정!F7:J9",
                "근거": "2025년 지역별 성장률 및 사업확장 전망",
                "분류": "분석가 가정",
                "주요 위험": "국가별 수요·환율·경쟁환경",
            },
            {
                "가정 항목": "매출원가율",
                "Excel 위치": "가정!F13:J13",
                "근거": "과거 원가율 및 점진적 정상화",
                "분류": "공시기반 분석가 가정",
                "주요 위험": "원재료가격·환율·제품구성",
            },
            {
                "가정 항목": "판매비율·일반관리비율",
                "Excel 위치": "가정!F14:J15",
                "근거": "과거 비용률 및 영업효율화",
                "분류": "공시기반 분석가 가정",
                "주요 위험": "광고선전비·인건비·해외법인 비용",
            },
            {
                "가정 항목": "정상화 현금법인세율",
                "Excel 위치": "가정!F16:J16",
                "근거": "EBIT 기준 25.5%",
                "분류": "분석가 가정",
                "주요 위험": "국가별 세율·일시적 세무조정",
            },
            {
                "가정 항목": "D&A 비율",
                "Excel 위치": "가정!F17:J17",
                "근거": "과거 D&A와 매출액의 관계",
                "분류": "공시기반 분석가 가정",
                "주요 위험": "신규 설비의 내용연수·가동시점",
            },
            {
                "가정 항목": "유지보수·성장 Capex",
                "Excel 위치": "가정!F18:J19",
                "근거": "과거 Capex 및 진천공장 투자계획",
                "분류": "공시기반 추정",
                "주요 위험": "총투자액의 연도별 집행시점",
            },
            {
                "가정 항목": "DSO·재고일수·DPO",
                "Excel 위치": "가정!F22:J24",
                "근거": "과거 운전자본 회전일수",
                "분류": "공시기반 분석가 가정",
                "주요 위험": "재고정책·거래조건·공급망 변화",
            },
            {
                "가정 항목": "WACC",
                "Excel 위치": "가정!C30:C36",
                "근거": "무위험수익률·ERP·베타·국가위험",
                "분류": "시장자료 및 예시 가정",
                "주요 위험": "비교기업 베타·목표 자본구조",
            },
            {
                "가정 항목": "영구성장률",
                "Excel 위치": "가정!C37",
                "근거": "장기 명목성장률 2.0%",
                "분류": "분석가 가정",
                "주요 위험": "장기 인플레이션·성숙기 성장률",
            },
            {
                "가정 항목": "종료시점 EV/EBITDA",
                "Excel 위치": "가정!C38",
                "근거": "8.0배 교차검증",
                "분류": "분석가 가정",
                "주요 위험": "비교기업·시장국면에 따른 배수 변화",
            },
            {
                "가정 항목": "필요 영업현금",
                "Excel 위치": "가정!C39",
                "근거": "매출액의 2.0%",
                "분류": "분석가 가정",
                "주요 위험": "실제 최소 현금수요와의 차이",
            },
        ]
    )

    assumption_register_df
    return (assumption_register_df,)


@app.cell
def _(assumption_register_df, mo, source_register_df):
    required_source_columns = [
        "출처 ID",
        "항목",
        "기간·기준일",
        "출처",
        "모형 사용처",
        "근거 유형",
    ]

    source_missing_count = (
        source_register_df[
            required_source_columns
        ]
        .isna()
        .sum()
        .sum()
    )

    duplicate_source_id_count = (
        source_register_df[
            "출처 ID"
        ]
        .duplicated()
        .sum()
    )

    assumption_missing_count = (
        assumption_register_df
        .isna()
        .sum()
        .sum()
    )

    source_audit_status = (
        source_missing_count == 0
        and duplicate_source_id_count == 0
        and assumption_missing_count == 0
    )

    mo.md(
        f"""
        # 출처 및 가정대장 검증

        - 등록 출처: **{len(source_register_df)}개**
        - 등록 주요 가정: **{len(assumption_register_df)}개**
        - 출처 필수항목 누락: **{source_missing_count}개**
        - 출처 ID 중복: **{duplicate_source_id_count}개**
        - 가정대장 누락: **{assumption_missing_count}개**

        **검증 결과:** {"✅ PASS" if source_audit_status else "❌ FAIL"}
        """
    )
    return


@app.cell
def _(mo):
    mo.md("""
    # 주요 한계 및 유의사항

    1. **사후적 교육용 평가**
       2025 회계연도 사업보고서는 2025년 12월 31일 이후에
       공시됐습니다. 따라서 본 모형은 평가기준일 당시 이용 가능한
       정보만으로 수행한 동시점 평가가 아니라 사후적 교육용 분석입니다.

    2. **WACC의 단순화**
       베타 0.9와 목표 자본구조는 예시 가정입니다. 정식 평가에서는
       비교기업 선정, 무차입 베타 산출 및 재레버링 과정이 필요합니다.

    3. **성장 Capex의 집행시점**
       진천공장 총투자액의 정확한 연도별 집행계획이 공시되지 않아
       2026년과 2027년에 추정 배분했습니다.

    4. **리가켐바이오 가치**
       공시된 시장가치를 사용했으며 세금누출, 유동성 할인,
       대량매각 할인 및 거래비용은 반영하지 않았습니다.

    5. **기타 비영업자산**
       기타 관계기업·공동기업투자는 장부금액, 투자부동산은 공시된
       공정가치를 사용했습니다. 별도의 자산가치평가는 수행하지 않았습니다.

    6. **주가 비교기준**
       104,330원은 2025년 12월 평균주가이며 평가기준일 종가가 아닙니다.

    7. **시나리오의 단순화**
       매출성장률 조정을 모든 지역과 전망연도에 동일하게 적용했습니다.
       실제 분석에서는 국가별 성장률·환율·가격·판매량을 분리해야 합니다.

    8. **가치평가는 가격예측이 아님**
       DCF 결과는 선택한 가정 아래의 내재가치 추정치이며,
       미래 시장가격을 보장하지 않습니다.
    """)
    return


@app.cell
def _(forecast_df, model, scenario_values_for_check):
    portfolio_revenue_cagr = (
        forecast_df["매출액"].iloc[-1]
        / forecast_df["매출액"].iloc[0]
    ) ** (1 / 4) - 1

    portfolio_terminal_share = model[
        "DCF"
    ]["계속기업가치 비중"]

    portfolio_2030_margin = forecast_df[
        "영업이익률"
    ].iloc[-1]

    portfolio_scenario_low = (
        scenario_values_for_check["비관"]
    )

    portfolio_scenario_high = (
        scenario_values_for_check["낙관"]
    )
    return (
        portfolio_2030_margin,
        portfolio_revenue_cagr,
        portfolio_scenario_high,
        portfolio_scenario_low,
        portfolio_terminal_share,
    )


@app.cell
def _(
    current_price,
    enterprise_value,
    equity_value,
    mo,
    portfolio_2030_margin,
    portfolio_revenue_cagr,
    portfolio_scenario_high,
    portfolio_scenario_low,
    portfolio_terminal_share,
    value_per_share,
    wacc,
):
    mo.md(f"""
    # 오리온 DCF Valuation Lab

    ## Executive Summary

    | 핵심 지표 | 기준 시나리오 |
    |---|---:|
    | 2026~2030년 매출액 CAGR | {portfolio_revenue_cagr:.1%} |
    | 2030년 EBIT 이익률 | {portfolio_2030_margin:.1%} |
    | WACC | {wacc:.2%} |
    | 영구성장률 | 2.0% |
    | 기업가치 | {enterprise_value:,.0f}백만원 |
    | 지분가치 | {equity_value:,.0f}백만원 |
    | **주당 내재가치** | **{value_per_share:,.0f}원** |
    | 기준주가 | {current_price:,.0f}원 |
    | 내재 상승여력 | {value_per_share / current_price - 1:+.1%} |
    | 시나리오 가치범위 | {portfolio_scenario_low:,.0f}~{portfolio_scenario_high:,.0f}원 |

    ### 핵심 가치동인

    - 기타 국가 매출액의 높은 성장과 지역별 매출구성 변화
    - 2028년 이후 성장 Capex 종료에 따른 FCFF 증가
    - 리가켐바이오 지분 및 단기금융상품 등 순비영업자산
    - WACC와 영구성장률에 대한 높은 계속기업가치 민감도

    ### 주요 판단위험

    - 기업가치의 {portfolio_terminal_share:.1%}가 계속기업가치에서 발생
    - WACC는 정식 비교기업 베타 분석이 아닌 예시 가정
    - 진천공장 투자액의 연도별 집행시점은 분석가 추정
    - 주당가치의 상당 부분이 비영업 투자자산 가치에 의존
    """)
    return


if __name__ == "__main__":
    app.run()
