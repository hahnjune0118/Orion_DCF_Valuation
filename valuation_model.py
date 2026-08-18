def calculate_wacc(
    risk_free_rate,
    equity_risk_premium,
    beta,
    country_risk_premium,
    pre_tax_cost_of_debt,
    tax_rate,
    equity_weight,
    debt_weight,
):
    weight_sum = equity_weight + debt_weight

    if abs(weight_sum - 1) > 0.000001:
        raise ValueError(
            "자기자본 비중과 타인자본 비중의 합계가 "
            "100%가 아닙니다."
        )

    cost_of_equity = (
        risk_free_rate
        + beta * equity_risk_premium
        + country_risk_premium
    )

    after_tax_cost_of_debt = (
        pre_tax_cost_of_debt
        * (1 - tax_rate)
    )

    wacc = (
        cost_of_equity * equity_weight
        + after_tax_cost_of_debt * debt_weight
    )

    return {
        "자기자본비용": cost_of_equity,
        "세후 타인자본비용": after_tax_cost_of_debt,
        "WACC": wacc,
        "자본구조 비중 합계": weight_sum,
    }


def calculate_dcf(
    fcff_forecast,
    wacc,
    terminal_growth_rate,
):
    if not fcff_forecast:
        raise ValueError("FCFF 전망값이 없습니다.")

    if wacc <= terminal_growth_rate:
        raise ValueError(
            "WACC는 영구성장률보다 커야 합니다."
        )

    discount_factors = []
    present_values = []

    for period, fcff in enumerate(
        fcff_forecast,
        start=1,
    ):
        discount_factor = 1 / (1 + wacc) ** period
        present_value = fcff * discount_factor

        discount_factors.append(discount_factor)
        present_values.append(present_value)

    terminal_fcff = fcff_forecast[-1]

    terminal_value = (
        terminal_fcff
        * (1 + terminal_growth_rate)
        / (wacc - terminal_growth_rate)
    )

    terminal_period = len(fcff_forecast)

    present_value_of_terminal_value = (
        terminal_value
        / (1 + wacc) ** terminal_period
    )

    present_value_of_forecast_fcff = sum(
        present_values
    )

    enterprise_value = (
        present_value_of_forecast_fcff
        + present_value_of_terminal_value
    )

    terminal_value_share = (
        present_value_of_terminal_value
        / enterprise_value
    )

    return {
        "할인계수": discount_factors,
        "FCFF 현재가치": present_values,
        "추정기간 FCFF 현재가치": (
            present_value_of_forecast_fcff
        ),
        "계속기업가치": terminal_value,
        "계속기업가치 현재가치": (
            present_value_of_terminal_value
        ),
        "기업가치": enterprise_value,
        "계속기업가치 비중": terminal_value_share,
    }