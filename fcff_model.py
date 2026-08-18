def calculate_fcff(
    ebit,
    tax_rate,
    depreciation,
    capex,
    change_in_nwc,
):
    nopat = ebit * (1 - tax_rate)

    fcff = (
        nopat
        + depreciation
        - capex
        - change_in_nwc
    )

    return {
        "EBIT": ebit,
        "법인세율": tax_rate,
        "NOPAT": nopat,
        "감가상각비": depreciation,
        "Capex": capex,
        "NWC 증가": change_in_nwc,
        "FCFF": fcff,
    }


if __name__ == "__main__":
    orion_2026 = calculate_fcff(
        ebit=604_772,
        tax_rate=25.5 / 100,
        depreciation=176_834,
        capex=335_614,
        change_in_nwc=5_313,
    )

    for item, value in orion_2026.items():
        print(f"{item}: {value:,.2f}")