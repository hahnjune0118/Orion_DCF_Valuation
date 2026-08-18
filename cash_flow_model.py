def calculate_nwc(
    revenue,
    cost_of_sales,
    dso,
    inventory_days,
    dpo,
    other_operating_asset_ratio,
    other_operating_liability_ratio,
):
    accounts_receivable = revenue / 365 * dso

    inventory = (
        cost_of_sales / 365 * inventory_days
    )

    other_operating_assets = (
        revenue * other_operating_asset_ratio
    )

    accounts_payable = (
        cost_of_sales / 365 * dpo
    )

    other_operating_liabilities = (
        revenue * other_operating_liability_ratio
    )

    nwc = (
        accounts_receivable
        + inventory
        + other_operating_assets
        - accounts_payable
        - other_operating_liabilities
    )

    return {
        "매출채권": accounts_receivable,
        "재고자산": inventory,
        "기타 영업유동자산": other_operating_assets,
        "매입채무": accounts_payable,
        "기타 영업유동부채": other_operating_liabilities,
        "NWC": nwc,
    }


def calculate_capex_and_depreciation(
    revenue,
    depreciation_ratio,
    maintenance_capex_ratio,
    growth_capex,
):
    depreciation = revenue * depreciation_ratio
    maintenance_capex = revenue * maintenance_capex_ratio

    total_capex = (
        maintenance_capex
        + growth_capex
    )

    return {
        "D&A": depreciation,
        "유지보수 Capex": maintenance_capex,
        "성장 Capex": growth_capex,
        "총 Capex": total_capex,
    }