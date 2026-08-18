def calculate_equity_bridge(
    enterprise_value,
    cash_and_cash_equivalents,
    revenue,
    required_operating_cash_ratio,
    short_term_financial_instruments,
    current_fvtpl_financial_assets,
    ligachem_market_value,
    other_associates_and_jvs,
    non_current_fvoci_financial_assets,
    investment_property_fair_value,
    financial_debt,
    lease_liabilities,
    non_controlling_interests,
    shares_outstanding_millions,
    current_share_price=None,
):
    if shares_outstanding_millions <= 0:
        raise ValueError(
            "유통주식수는 0보다 커야 합니다."
        )

    required_operating_cash = (
        revenue * required_operating_cash_ratio
    )

    excess_cash = (
        cash_and_cash_equivalents
        - required_operating_cash
    )

    non_operating_assets = (
        excess_cash
        + short_term_financial_instruments
        + current_fvtpl_financial_assets
        + ligachem_market_value
        + other_associates_and_jvs
        + non_current_fvoci_financial_assets
        + investment_property_fair_value
    )

    debt_like_items = (
        financial_debt
        + lease_liabilities
        + non_controlling_interests
    )

    net_non_operating_adjustment = (
        non_operating_assets
        - debt_like_items
    )

    equity_value = (
        enterprise_value
        + net_non_operating_adjustment
    )

    implied_value_per_share = (
        equity_value
        / shares_outstanding_millions
    )

    implied_upside = None

    if current_share_price is not None:
        implied_upside = (
            implied_value_per_share
            / current_share_price
            - 1
        )

    return {
        "현금및현금성자산": cash_and_cash_equivalents,
        "필요 영업현금": required_operating_cash,
        "초과현금": excess_cash,
        "단기금융상품": short_term_financial_instruments,
        "유동 당기손익-공정가치측정 금융자산": (
            current_fvtpl_financial_assets
        ),
        "리가켐바이오 시장가치": ligachem_market_value,
        "기타 관계기업 및 공동기업투자": (
            other_associates_and_jvs
        ),
        "비유동 기타포괄손익-공정가치측정 금융자산": (
            non_current_fvoci_financial_assets
        ),
        "투자부동산 공정가치": (
            investment_property_fair_value
        ),
        "비영업자산 합계": non_operating_assets,
        "금융기관차입금": financial_debt,
        "리스부채": lease_liabilities,
        "비지배지분": non_controlling_interests,
        "차감항목 합계": debt_like_items,
        "순비영업 조정액": net_non_operating_adjustment,
        "지분가치": equity_value,
        "유통주식수(백만주)": shares_outstanding_millions,
        "주당 내재가치": implied_value_per_share,
        "내재 상승여력": implied_upside,
    }