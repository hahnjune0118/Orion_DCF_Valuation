import hashlib
import json
from pathlib import Path

import pytest

from orion_dcf import run_orion_dcf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "orion_dcf.xlsx"
SNAPSHOT_PATH = (
    PROJECT_ROOT / "artifacts" / "baseline" / "model_snapshot.json"
)


@pytest.fixture(scope="module")
def baseline():
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def current_model():
    return run_orion_dcf(EXCEL_PATH)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_close(actual, expected, tolerance, relative):
    assert actual == pytest.approx(
        expected,
        abs=tolerance,
        rel=relative,
    )


def test_baseline_input_fingerprint_is_unchanged(baseline):
    expected = baseline["input_files"]["data/raw/orion_dcf.xlsx"]
    assert _sha256(EXCEL_PATH) == expected["sha256"]
    assert EXCEL_PATH.stat().st_size == expected["size_bytes"]


def test_baseline_forecast_is_unchanged(baseline, current_model):
    expected_rows = baseline["model_outputs"]["전망"]
    actual_rows = current_model["전망"]
    tolerances = baseline["tolerances"]

    assert [row["연도"] for row in actual_rows] == [
        2026,
        2027,
        2028,
        2029,
        2030,
    ]
    assert len(actual_rows) == len(expected_rows)

    for actual, expected in zip(actual_rows, expected_rows, strict=True):
        assert actual.keys() == expected.keys()
        for key in actual:
            if key == "연도":
                assert actual[key] == expected[key]
                continue
            tolerance = (
                tolerances["rate_absolute"]
                if key == "영업이익률"
                else tolerances["amount_million_krw_absolute"]
            )
            _assert_close(
                actual[key],
                expected[key],
                tolerance,
                tolerances["relative"],
            )


def test_baseline_valuation_is_unchanged(baseline, current_model):
    expected = baseline["model_outputs"]
    tolerances = baseline["tolerances"]
    relative = tolerances["relative"]

    _assert_close(
        current_model["WACC"]["WACC"],
        expected["WACC"]["WACC"],
        tolerances["rate_absolute"],
        relative,
    )

    for key in [
        "추정기간 FCFF 현재가치",
        "계속기업가치 현재가치",
        "기업가치",
    ]:
        _assert_close(
            current_model["DCF"][key],
            expected["DCF"][key],
            tolerances["amount_million_krw_absolute"],
            relative,
        )

    _assert_close(
        current_model["DCF"]["계속기업가치 비중"],
        expected["DCF"]["계속기업가치 비중"],
        tolerances["rate_absolute"],
        relative,
    )
    _assert_close(
        current_model["지분가치"]["지분가치"],
        expected["지분가치"]["지분가치"],
        tolerances["amount_million_krw_absolute"],
        relative,
    )
    _assert_close(
        current_model["지분가치"]["주당 내재가치"],
        expected["지분가치"]["주당 내재가치"],
        tolerances["per_share_krw_absolute"],
        relative,
    )
