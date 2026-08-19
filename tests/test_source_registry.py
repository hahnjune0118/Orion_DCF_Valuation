import csv
import re
from pathlib import Path

from scripts.validate_source_registry import (
    REQUIRED_COLUMNS,
    validate_registry,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = PROJECT_ROOT / "data" / "metadata" / "source_registry.csv"


def _read_registry():
    with REGISTRY_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_registry(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def test_live_source_registry_is_valid():
    report = validate_registry(REGISTRY_PATH)
    assert report["valid"], report["errors"]
    assert report["counts"]["duplicate_source_id"] == 0
    assert report["counts"]["missing_unit"] == 0
    assert report["counts"]["ambiguous_period"] == 0
    assert report["counts"]["ambiguous_scope"] == 0


def test_material_valuation_inputs_are_registered():
    registered = {row["source_id"] for row in _read_registry()}
    required = {
        "FIL-001",
        "FIL-011",
        "FIL-012",
        "FIL-017",
        "FIL-020",
        "FIL-022",
        "FIL-023",
        "FIL-024",
        "FIL-028",
        "CALC-005",
        "CALC-007",
        "CALC-010",
        "CALC-012",
        "CALC-013",
        "ASM-016",
        "ASM-017",
        "ASM-018",
        "ASM-019",
        "ASM-020",
        "ASM-021",
        "ASM-022",
        "ASM-023",
        "ASM-025",
        "MKT-001",
    }
    assert required <= registered


def test_low_confidence_rows_are_linked_to_data_gaps():
    rows = _read_registry()
    unsupported = [
        row["source_id"]
        for row in rows
        if row["신뢰도"] == "낮음" and "DG-" not in row["비고"]
    ]
    assert unsupported == []


def test_referenced_data_gap_ids_exist():
    gap_text = (
        PROJECT_ROOT / "docs" / "checkpoints" / "DATA_GAPS.md"
    ).read_text(encoding="utf-8")
    defined_gap_ids = set(re.findall(r"DG-\d{3}", gap_text))
    referenced_gap_ids = {
        gap_id
        for row in _read_registry()
        for gap_id in re.findall(r"DG-\d{3}", row["비고"])
    }
    assert referenced_gap_ids <= defined_gap_ids


def test_validator_detects_duplicate_source_id(tmp_path):
    rows = _read_registry()[:2]
    rows[1]["source_id"] = rows[0]["source_id"]
    path = tmp_path / "duplicate.csv"
    _write_registry(path, rows)
    report = validate_registry(path)
    assert not report["valid"]
    assert report["counts"]["duplicate_source_id"] == 1


def test_validator_detects_missing_unit_and_ambiguous_metadata(tmp_path):
    row = _read_registry()[0]
    row["단위"] = ""
    row["기간"] = "미정"
    row["연결/별도"] = "불명확"
    path = tmp_path / "missing.csv"
    _write_registry(path, [row])
    report = validate_registry(path)
    assert not report["valid"]
    assert report["counts"]["missing_unit"] == 1
    assert report["counts"]["ambiguous_period"] == 1
    assert report["counts"]["ambiguous_scope"] == 1
