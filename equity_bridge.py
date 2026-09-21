"""Enterprise-value to equity-value bridge for the FDD Base Case."""

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite


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


def _components(value: Mapping[str, object] | None, label: str) -> dict[str, float]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError(f"{label}은(는) 매핑이어야 합니다.")
    return {key: _number(item, f"{label} / {key}") for key, item in value.items()}


def calculate_equity_bridge(
    enterprise_value,
    cash_like,
    debt_like,
    non_operating_assets,
    non_controlling_interests,
    applied_nwc_price_adjustment,
    shares_outstanding_millions,
    current_share_price=None,
    *,
    cash_like_components=None,
    debt_like_components=None,
    non_operating_asset_components=None,
):
    """Calculate the explicit cash-free/debt-free FDD transaction bridge."""

    enterprise_value = _number(enterprise_value, "기업가치")
    cash_like = _number(cash_like, "Cash-like")
    debt_like = _number(debt_like, "Debt-like")
    non_operating_assets = _number(non_operating_assets, "비영업자산")
    non_controlling_interests = _number(
        non_controlling_interests, "비지배지분"
    )
    applied_nwc_price_adjustment = _number(
        applied_nwc_price_adjustment, "적용 NWC 가격조정"
    )
    shares_outstanding_millions = _number(
        shares_outstanding_millions, "유통주식수"
    )
    if shares_outstanding_millions <= 0:
        raise ValueError("유통주식수는 0보다 커야 합니다.")
    if min(cash_like, debt_like, non_operating_assets, non_controlling_interests) < 0:
        raise ValueError(
            "Cash-like, Debt-like, 비영업자산 및 비지배지분은 음수일 수 없습니다."
        )

    cash_components = _components(cash_like_components, "Cash-like 구성항목")
    debt_components = _components(debt_like_components, "Debt-like 구성항목")
    non_operating_components = _components(
        non_operating_asset_components, "비영업자산 구성항목"
    )

    net_cash = cash_like - debt_like
    fdd_equity_adjustment = (
        net_cash
        + non_operating_assets
        - non_controlling_interests
        + applied_nwc_price_adjustment
    )
    equity_value = enterprise_value + fdd_equity_adjustment
    implied_value_per_share = equity_value / shares_outstanding_millions

    implied_upside = None
    if current_share_price is not None:
        current_share_price = _number(current_share_price, "기준주가")
        if current_share_price <= 0:
            raise ValueError("기준주가는 0보다 커야 합니다.")
        implied_upside = implied_value_per_share / current_share_price - 1

    required_operating_cash = -cash_components.get("필요 영업현금", 0.0)
    cash_and_equivalents = cash_components.get("현금및현금성자산", 0.0)
    excess_cash = cash_and_equivalents - required_operating_cash

    return {
        "Cash-like 자산": cash_like,
        "Debt-like 항목": debt_like,
        "순현금": net_cash,
        "순차입금 / (순현금)": -net_cash,
        "비영업자산 합계": non_operating_assets,
        "비지배지분": non_controlling_interests,
        "적용 NWC 가격조정": applied_nwc_price_adjustment,
        "FDD 지분가치 조정액": fdd_equity_adjustment,
        "순비영업 조정액": fdd_equity_adjustment,
        "지분가치": equity_value,
        "유통주식수(백만주)": shares_outstanding_millions,
        "주당 내재가치": implied_value_per_share,
        "내재 상승여력": implied_upside,
        "Cash-like 구성항목": cash_components,
        "Debt-like 구성항목": debt_components,
        "비영업자산 구성항목": non_operating_components,
        # Compatibility aliases used by existing Pages 1-4 and the legacy lab.
        "현금및현금성자산": cash_and_equivalents,
        "필요 영업현금": required_operating_cash,
        "초과현금": excess_cash,
        "단기금융상품": cash_components.get("단기금융상품", 0.0),
        "유동 당기손익-공정가치측정 금융자산": cash_components.get(
            "유동 FVTPL 금융자산", 0.0
        ),
        "리가켐바이오 시장가치": non_operating_components.get(
            "리가켐바이오 시장가치", 0.0
        ),
        "기타 관계기업 및 공동기업투자": non_operating_components.get(
            "기타 관계·공동기업", 0.0
        ),
        "비유동 기타포괄손익-공정가치측정 금융자산": (
            non_operating_components.get("비유동 OCI 금융자산", 0.0)
        ),
        "투자부동산 공정가치": non_operating_components.get(
            "투자부동산 공정가치", 0.0
        ),
        "금융기관차입금": debt_components.get("금융기관차입금", 0.0),
        "리스부채": debt_components.get("리스부채", 0.0),
        "Capex 관련 미지급금": debt_components.get(
            "Capex 관련 미지급금", 0.0
        ),
        "차감항목 합계": debt_like + non_controlling_interests,
    }
