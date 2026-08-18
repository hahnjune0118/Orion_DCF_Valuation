def forecast_segment_revenue(
    base_revenue,
    growth_rates,
):
    forecast = []
    current_revenue = base_revenue

    for growth_rate in growth_rates:
        current_revenue = current_revenue * (1 + growth_rate)
        forecast.append(current_revenue)

    return forecast


def calculate_operating_profit(
    revenue,
    cost_of_sales_ratio,
    selling_expense_ratio,
    administrative_expense_ratio,
):
    cost_of_sales = -revenue * cost_of_sales_ratio
    selling_expense = -revenue * selling_expense_ratio
    administrative_expense = (
        -revenue * administrative_expense_ratio
    )

    gross_profit = revenue + cost_of_sales

    ebit = (
        gross_profit
        + selling_expense
        + administrative_expense
    )

    return {
        "매출액": revenue,
        "매출원가": cost_of_sales,
        "매출총이익": gross_profit,
        "판매비": selling_expense,
        "일반관리비": administrative_expense,
        "EBIT": ebit,
        "영업이익률": ebit / revenue,
    }