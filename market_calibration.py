"""Market calibration, relative valuation, and reverse-DCF utilities.

All monetary model inputs are KRW millions.  The functions in this module are
deliberately independent of marimo so they can be tested and reused in other
valuation deliverables.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import csv
from math import isfinite
from pathlib import Path
from statistics import median


SUPPORTED_MULTIPLES = ("EV/EBITDA", "EV/EBIT", "P/E")


def _number(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label}은(는) 숫자여야 합니다.")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{label}은(는) 숫자여야 합니다.") from exc
    if not isfinite(result):
        raise ValueError(f"{label}은(는) 유한한 숫자여야 합니다.")
    return result


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label}은(는) 매핑이어야 합니다.")
    return value


def _percentile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ValueError("백분위수를 계산할 값이 없습니다.")
    if not 0 <= probability <= 1:
        raise ValueError("백분위수 확률은 0과 1 사이여야 합니다.")
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    weight = position - lower_index
    return (
        ordered[lower_index] * (1 - weight)
        + ordered[upper_index] * weight
    )


def load_market_calibration_data(
    csv_path: str | Path,
) -> list[dict[str, object]]:
    """Load the controlled peer snapshot without mutating source records."""

    numeric_fields = {
        "ev_ebitda",
        "ev_ebit",
        "pe",
        "levered_beta",
        "debt_to_equity",
    }
    rows: list[dict[str, object]] = []
    with Path(csv_path).open(encoding="utf-8-sig", newline="") as handle:
        for raw_row in csv.DictReader(handle):
            row: dict[str, object] = dict(raw_row)
            for field in numeric_fields:
                row[field] = _number(row[field], field)
            rows.append(row)
    if not 5 <= len(rows) <= 8:
        raise ValueError("Trading Comps는 5~8개여야 합니다.")
    if len({str(row["ticker"]) for row in rows}) != len(rows):
        raise ValueError("Trading Comps ticker는 중복될 수 없습니다.")
    return rows


def calculate_unlevered_beta(
    levered_beta: object,
    debt_to_equity: object,
    tax_rate: object,
) -> float:
    """Hamada-unlever a peer beta using gross D/E."""

    beta = _number(levered_beta, "Levered Beta")
    de_ratio = _number(debt_to_equity, "D/E")
    tax = _number(tax_rate, "법인세율")
    if beta <= 0 or de_ratio < 0 or not 0 <= tax < 1:
        raise ValueError("Beta>0, D/E>=0, 0<=세율<1 조건을 충족해야 합니다.")
    return beta / (1 + (1 - tax) * de_ratio)


def calculate_relevered_beta(
    unlevered_beta: object,
    target_debt_to_equity: object,
    tax_rate: object,
) -> float:
    """Hamada-relever an asset beta to Orion's target capital structure."""

    beta = _number(unlevered_beta, "Unlevered Beta")
    de_ratio = _number(target_debt_to_equity, "목표 D/E")
    tax = _number(tax_rate, "법인세율")
    if beta <= 0 or de_ratio < 0 or not 0 <= tax < 1:
        raise ValueError("Beta>0, D/E>=0, 0<=세율<1 조건을 충족해야 합니다.")
    return beta * (1 + (1 - tax) * de_ratio)


def prepare_beta_calibration(
    peers: Sequence[Mapping[str, object]],
    target_debt_to_equity: object,
    tax_rate: object,
) -> dict[str, object]:
    """Unlever each peer, take the median, and relever to Orion."""

    if not 5 <= len(peers) <= 8:
        raise ValueError("Beta Relevering 대상 Trading Comps는 5~8개여야 합니다.")
    peer_results = []
    for peer in peers:
        unlevered = calculate_unlevered_beta(
            peer["levered_beta"], peer["debt_to_equity"], tax_rate
        )
        peer_results.append(
            {
                **dict(peer),
                "unlevered_beta": unlevered,
            }
        )
    median_unlevered = median(
        float(peer["unlevered_beta"]) for peer in peer_results
    )
    relevered = calculate_relevered_beta(
        median_unlevered, target_debt_to_equity, tax_rate
    )
    return {
        "peers": peer_results,
        "median_unlevered_beta": median_unlevered,
        "target_debt_to_equity": float(target_debt_to_equity),
        "relevered_beta": relevered,
    }


def _valuation_context(model: Mapping[str, object]) -> dict[str, float]:
    forecast = model.get("전망")
    if not isinstance(forecast, Sequence) or not forecast:
        raise TypeError("모델 전망은 비어 있지 않은 행 시퀀스여야 합니다.")
    first = _mapping(forecast[0], "첫 전망 행")
    equity = _mapping(model.get("지분가치"), "모델 지분가치")
    dcf = _mapping(model.get("DCF"), "모델 DCF")
    ebit = _number(first["EBIT"], "2026E EBIT")
    ebitda = ebit + _number(first["D&A"], "2026E D&A")
    normalized_income = _number(first["NOPAT"], "2026E NOPAT")
    enterprise_value = _number(dcf["기업가치"], "기업가치")
    equity_value = _number(equity["지분가치"], "지분가치")
    shares = _number(equity["유통주식수(백만주)"], "유통주식수")
    if min(ebit, ebitda, normalized_income, shares) <= 0:
        raise ValueError("상대가치 계산의 이익·주식수 입력은 양수여야 합니다.")
    return {
        "ebit": ebit,
        "ebitda": ebitda,
        "normalized_income": normalized_income,
        "bridge": equity_value - enterprise_value,
        "shares": shares,
    }


def _value_per_share_from_multiple(
    multiple_name: str,
    multiple: float,
    context: Mapping[str, float],
) -> float:
    if multiple_name == "EV/EBITDA":
        equity_value = multiple * context["ebitda"] + context["bridge"]
    elif multiple_name == "EV/EBIT":
        equity_value = multiple * context["ebit"] + context["bridge"]
    elif multiple_name == "P/E":
        equity_value = multiple * context["normalized_income"]
    else:
        raise ValueError(f"지원하지 않는 배수입니다: {multiple_name}")
    return equity_value / context["shares"]


def calculate_trading_comps_ranges(
    model: Mapping[str, object],
    peers: Sequence[Mapping[str, object]],
    lower_percentile: float = 0.25,
    upper_percentile: float = 0.75,
) -> dict[str, dict[str, object]]:
    """Apply peer interquartile multiples to Orion's 2026E metrics."""

    context = _valuation_context(model)
    result: dict[str, dict[str, object]] = {}
    field_by_multiple = {
        "EV/EBITDA": "ev_ebitda",
        "EV/EBIT": "ev_ebit",
        "P/E": "pe",
    }
    for multiple_name, field in field_by_multiple.items():
        multiples = [_number(peer[field], field) for peer in peers]
        low_multiple = _percentile(multiples, lower_percentile)
        median_multiple = _percentile(multiples, 0.50)
        high_multiple = _percentile(multiples, upper_percentile)
        result[multiple_name] = {
            "low_multiple": low_multiple,
            "median_multiple": median_multiple,
            "high_multiple": high_multiple,
            "low": _value_per_share_from_multiple(
                multiple_name, low_multiple, context
            ),
            "mid": _value_per_share_from_multiple(
                multiple_name, median_multiple, context
            ),
            "high": _value_per_share_from_multiple(
                multiple_name, high_multiple, context
            ),
            "basis": "2026E",
        }
    return result


def calculate_historical_multiple_ranges(
    model: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    """Apply Orion's observed FY2021–FY2025 min/max multiples to 2026E."""

    context = _valuation_context(model)
    history = {
        "EV/EBITDA": [7.08, 6.62, 5.42, 4.30, 4.72],
        "EV/EBIT": [10.16, 9.23, 7.49, 6.12, 5.66],
        "P/E": [15.90, 12.90, 12.20, 7.72, 10.90],
    }
    result: dict[str, dict[str, object]] = {}
    for multiple_name, multiples in history.items():
        low_multiple = min(multiples)
        high_multiple = max(multiples)
        median_multiple = median(multiples)
        result[multiple_name] = {
            "low_multiple": low_multiple,
            "median_multiple": median_multiple,
            "high_multiple": high_multiple,
            "low": _value_per_share_from_multiple(
                multiple_name, low_multiple, context
            ),
            "mid": _value_per_share_from_multiple(
                multiple_name, median_multiple, context
            ),
            "high": _value_per_share_from_multiple(
                multiple_name, high_multiple, context
            ),
            "basis": "FY2021–FY2025 observed range",
        }
    return result


def prepare_football_field_ranges(
    dcf_values: Sequence[object],
    trading_ranges: Mapping[str, Mapping[str, object]],
    historical_ranges: Mapping[str, Mapping[str, object]],
    current_price: object,
) -> list[dict[str, object]]:
    """Create chart-ready value ranges with a consistent KRW/share basis."""

    values = [_number(value, "DCF 민감도 값") for value in dcf_values]
    rows: list[dict[str, object]] = [
        {
            "method": "DCF Sensitivity",
            "low": _percentile(values, 0.10),
            "mid": _percentile(values, 0.50),
            "high": _percentile(values, 0.90),
            "group": "DCF",
        }
    ]
    for multiple_name in SUPPORTED_MULTIPLES:
        row = trading_ranges[multiple_name]
        rows.append(
            {
                "method": f"Trading {multiple_name}",
                "low": float(row["low"]),
                "mid": float(row["mid"]),
                "high": float(row["high"]),
                "group": "Trading Comps",
            }
        )
    combined_historical = [historical_ranges[name] for name in SUPPORTED_MULTIPLES]
    rows.append(
        {
            "method": "Historical Multiple",
            "low": min(float(row["low"]) for row in combined_historical),
            "mid": median(float(row["mid"]) for row in combined_historical),
            "high": max(float(row["high"]) for row in combined_historical),
            "group": "Historical",
        }
    )
    rows.append(
        {
            "method": "Current Price",
            "low": _number(current_price, "Current Share Price"),
            "mid": _number(current_price, "Current Share Price"),
            "high": _number(current_price, "Current Share Price"),
            "group": "Market",
        }
    )
    return rows


def reverse_dcf_value_per_share(
    model: Mapping[str, object],
    revenue_cagr: object,
    terminal_ebit_margin: object,
    non_operating_asset_realization: object = 1.0,
) -> float:
    """Rebuild FCFF from a CAGR/margin pair and return KRW per share.

    Revenue grows at a constant CAGR. EBIT margin converges linearly from the
    base 2026E margin to the selected 2030 normal margin. Reinvestment ratios
    and NWC intensity remain anchored to the base forecast by year.
    """

    cagr = _number(revenue_cagr, "매출 CAGR")
    normal_margin = _number(terminal_ebit_margin, "Normalized EBIT Margin")
    realization = _number(
        non_operating_asset_realization, "비영업자산 가치인식률"
    )
    if cagr <= -1 or not 0 < normal_margin < 1 or not 0 <= realization <= 1:
        raise ValueError(
            "Revenue CAGR>-100%, 0<Normalized EBIT Margin<100%, "
            "0<=비영업자산 가치인식률<=100% 조건이 필요합니다."
        )
    forecast = model.get("전망")
    if not isinstance(forecast, Sequence) or len(forecast) != 5:
        raise ValueError("Reverse DCF는 5개년 전망을 요구합니다.")
    base_year = _mapping(model.get("기준연도"), "기준연도")
    wacc_data = _mapping(model.get("WACC"), "WACC")
    dcf_data = _mapping(model.get("DCF"), "DCF")
    equity_data = _mapping(model.get("지분가치"), "지분가치")
    base_revenue = _number(base_year["매출액"], "2025A 매출액")
    first_row = _mapping(forecast[0], "2026E 전망")
    starting_margin = _number(first_row["영업이익률"], "2026E 영업이익률")
    tax = _number(
        _mapping(wacc_data.get("구성요소"), "WACC 구성요소")["법인세율"],
        "법인세율",
    )
    wacc = _number(wacc_data["WACC"], "WACC")
    perpetual_growth = _number(dcf_data["영구성장률"], "영구성장률")
    bridge = (
        _number(equity_data["지분가치"], "지분가치")
        - _number(dcf_data["기업가치"], "기업가치")
    )
    shares = _number(equity_data["유통주식수(백만주)"], "유통주식수")

    previous_nwc = (
        _number(first_row["NWC"], "2026E NWC")
        - _number(first_row["NWC 증감"], "2026E NWC 증감")
    )
    fcff_values = []
    for index, source_row_object in enumerate(forecast, start=1):
        source_row = _mapping(source_row_object, "전망 행")
        source_revenue = _number(source_row["매출액"], "전망 매출액")
        revenue = base_revenue * (1 + cagr) ** index
        interpolation = (index - 1) / (len(forecast) - 1)
        margin = (
            starting_margin
            + (normal_margin - starting_margin) * interpolation
        )
        ebit = revenue * margin
        depreciation = revenue * (
            _number(source_row["D&A"], "D&A") / source_revenue
        )
        capex = revenue * (
            _number(source_row["Capex"], "Capex") / source_revenue
        )
        current_nwc = revenue * (
            _number(source_row["NWC"], "NWC") / source_revenue
        )
        change_in_nwc = current_nwc - previous_nwc
        fcff = ebit * (1 - tax) + depreciation - capex - change_in_nwc
        fcff_values.append(fcff)
        previous_nwc = current_nwc

    discount_factors = [
        1 / (1 + wacc) ** period
        for period in range(1, len(fcff_values) + 1)
    ]
    explicit_value = sum(
        fcff * factor
        for fcff, factor in zip(fcff_values, discount_factors, strict=True)
    )
    terminal_value = (
        fcff_values[-1]
        * (1 + perpetual_growth)
        / (wacc - perpetual_growth)
    )
    enterprise_value = explicit_value + terminal_value * discount_factors[-1]
    return (enterprise_value + bridge * realization) / shares


def solve_reverse_dcf_growth(
    model: Mapping[str, object],
    current_price: object,
    terminal_ebit_margin: object,
    non_operating_asset_realization: object = 1.0,
    lower_bound: float = -0.60,
    upper_bound: float = 0.40,
    tolerance: float = 0.50,
    max_iterations: int = 100,
) -> dict[str, float]:
    """Solve the five-year revenue CAGR implied by price at a fixed margin."""

    target = _number(current_price, "Current Share Price")
    margin = _number(terminal_ebit_margin, "Normalized EBIT Margin")
    realization = _number(
        non_operating_asset_realization, "비영업자산 가치인식률"
    )
    low_value = reverse_dcf_value_per_share(
        model, lower_bound, margin, realization
    )
    high_value = reverse_dcf_value_per_share(
        model, upper_bound, margin, realization
    )
    if not low_value <= target <= high_value:
        raise ValueError(
            "Current Share Price가 Reverse DCF 탐색구간의 Valuation Range 밖에 있습니다."
        )
    low = lower_bound
    high = upper_bound
    midpoint = (low + high) / 2
    implied_value = reverse_dcf_value_per_share(
        model, midpoint, margin, realization
    )
    for _ in range(max_iterations):
        midpoint = (low + high) / 2
        implied_value = reverse_dcf_value_per_share(
            model, midpoint, margin, realization
        )
        if abs(implied_value - target) <= tolerance:
            break
        if implied_value < target:
            low = midpoint
        else:
            high = midpoint
    forecast = model.get("전망")
    if not isinstance(forecast, Sequence) or len(forecast) != 5:
        raise ValueError("Reverse DCF는 5개년 전망을 요구합니다.")
    base_year = _mapping(model.get("기준연도"), "기준연도")
    terminal_year = _mapping(forecast[-1], "최종 전망 행")
    dcf_data = _mapping(model.get("DCF"), "모델 DCF")
    wacc_data = _mapping(model.get("WACC"), "모델 WACC")
    baseline_revenue_cagr = (
        _number(terminal_year["매출액"], "2030E 매출액")
        / _number(base_year["매출액"], "2025A 매출액")
    ) ** (1 / len(forecast)) - 1

    return {
        "revenue_cagr": midpoint,
        "terminal_ebit_margin": margin,
        "non_operating_asset_realization": realization,
        "implied_value_per_share": implied_value,
        "target_price": target,
        "difference": implied_value - target,
        "wacc": _number(wacc_data["WACC"], "WACC"),
        "perpetual_growth": _number(dcf_data["영구성장률"], "영구성장률"),
        "baseline_revenue_cagr": baseline_revenue_cagr,
        "baseline_terminal_ebit_margin": _number(
            terminal_year["영업이익률"], "2030E 영업이익률"
        ),
        "tolerance": float(tolerance),
        "reconciliation_status": (
            "RECONCILED"
            if abs(implied_value - target) <= tolerance
            else "REVIEW"
        ),
    }
