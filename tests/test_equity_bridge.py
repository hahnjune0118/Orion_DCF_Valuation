from copy import deepcopy
from pathlib import Path

import pytest

from dashboard_components import prepare_fdd_review_data
from orion_dcf import run_orion_dcf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"


@pytest.fixture(scope="module")
def model():
    return run_orion_dcf(EXCEL_PATH)


def test_fdd_equity_bridge_reconciles(model):
    bridge = model["FDD"]["transaction_bridge"]
    equity = model["지분가치"]
    enterprise_value = model["DCF"]["기업가치"]

    assert bridge["cash_like"] - bridge["debt_like"] == pytest.approx(
        bridge["net_cash"], abs=1e-6
    )

    expected_adjustment = (
        bridge["net_cash"]
        + bridge["non_operating_assets"]
        - bridge["non_controlling_interests"]
        + bridge["applied_nwc_price_adjustment"]
    )
    assert bridge["fdd_equity_adjustment"] == pytest.approx(
        expected_adjustment, abs=1e-6
    )
    assert equity["지분가치"] == pytest.approx(
        enterprise_value + bridge["fdd_equity_adjustment"], abs=1e-6
    )
    assert equity["주당 내재가치"] == pytest.approx(
        equity["지분가치"] / equity["유통주식수(백만주)"], abs=1e-6
    )


def test_fdd_bridge_headline_values_match_validated_base(model):
    bridge = model["FDD"]["transaction_bridge"]
    assert bridge["cash_like"] == pytest.approx(1_235_817.717, abs=0.001)
    assert bridge["debt_like"] == pytest.approx(49_203.035, abs=0.001)
    assert bridge["net_cash"] == pytest.approx(1_186_614.682, abs=0.001)
    assert bridge["non_operating_assets"] == pytest.approx(
        1_801_499.020, abs=0.001
    )
    assert bridge["fdd_equity_adjustment"] == pytest.approx(
        2_884_569.999, abs=0.001
    )


def test_share_count_must_be_positive_in_page_5_adapter(model):
    broken = deepcopy(model)
    broken["지분가치"]["유통주식수(백만주)"] = 0

    with pytest.raises(ValueError, match="유통주식수.*0보다 커야"):
        prepare_fdd_review_data(broken)
