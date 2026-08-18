"""Validate the auditable source registry for the Orion DCF model."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


REQUIRED_COLUMNS = [
    "source_id",
    "항목명",
    "값/범위",
    "단위",
    "기간",
    "연결/별도",
    "자료유형",
    "문서명",
    "공시일",
    "평가기준일",
    "URL 또는 파일경로",
    "페이지/주석/셀",
    "추출방식",
    "최종확인일",
    "신뢰도",
    "비고",
]

REQUIRED_VALUE_COLUMNS = [
    column for column in REQUIRED_COLUMNS if column != "비고"
]

ALLOWED_SCOPE = {"연결", "별도", "연결/별도", "해당 없음"}
ALLOWED_SOURCE_TYPES = {"공시값", "시장자료", "계산값", "분석가 가정"}
ALLOWED_CONFIDENCE = {"높음", "중간", "낮음"}
UNKNOWN_MARKERS = {"", "미정", "불명", "불명확", "확인 필요", "unknown", "n/a"}
SOURCE_ID_PATTERN = re.compile(r"^(FIL|MKT|ASM|CALC|CODE)-\d{3}$")


def _is_unknown(value: str) -> bool:
    return value.strip().lower() in UNKNOWN_MARKERS


def validate_registry(path: str | Path) -> dict:
    """Return a machine-readable validation report for ``path``."""
    registry_path = Path(path)
    errors: list[str] = []
    warnings: list[str] = []

    with registry_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing_columns = [
            column for column in REQUIRED_COLUMNS if column not in fieldnames
        ]
        if missing_columns:
            errors.append(
                "필수열 누락: " + ", ".join(missing_columns)
            )
        rows = list(reader)

    source_ids = [row.get("source_id", "").strip() for row in rows]
    duplicate_ids = sorted(
        source_id
        for source_id, count in Counter(source_ids).items()
        if source_id and count > 1
    )
    if duplicate_ids:
        errors.append("source_id 중복: " + ", ".join(duplicate_ids))

    missing_required_cells: list[str] = []
    invalid_ids: list[str] = []
    missing_units: list[str] = []
    ambiguous_periods: list[str] = []
    ambiguous_scopes: list[str] = []
    invalid_types: list[str] = []
    invalid_confidence: list[str] = []

    for line_number, row in enumerate(rows, start=2):
        source_id = row.get("source_id", "").strip() or f"행 {line_number}"
        for column in REQUIRED_VALUE_COLUMNS:
            if _is_unknown(row.get(column, "")):
                missing_required_cells.append(f"{source_id}:{column}")

        if source_id != f"행 {line_number}" and not SOURCE_ID_PATTERN.fullmatch(source_id):
            invalid_ids.append(source_id)
        if _is_unknown(row.get("단위", "")):
            missing_units.append(source_id)
        if _is_unknown(row.get("기간", "")):
            ambiguous_periods.append(source_id)
        if row.get("연결/별도", "").strip() not in ALLOWED_SCOPE:
            ambiguous_scopes.append(source_id)
        if row.get("자료유형", "").strip() not in ALLOWED_SOURCE_TYPES:
            invalid_types.append(source_id)
        if row.get("신뢰도", "").strip() not in ALLOWED_CONFIDENCE:
            invalid_confidence.append(source_id)

    if missing_required_cells:
        errors.append(
            "필수값 누락: " + ", ".join(missing_required_cells)
        )
    if invalid_ids:
        errors.append("source_id 형식 오류: " + ", ".join(invalid_ids))
    if missing_units:
        errors.append("단위 미기재: " + ", ".join(missing_units))
    if ambiguous_periods:
        warnings.append("기간 불명확: " + ", ".join(ambiguous_periods))
    if ambiguous_scopes:
        warnings.append("연결범위 불명확: " + ", ".join(ambiguous_scopes))
    if invalid_types:
        errors.append("자료유형 오류: " + ", ".join(invalid_types))
    if invalid_confidence:
        errors.append("신뢰도 오류: " + ", ".join(invalid_confidence))

    low_confidence = [
        row["source_id"]
        for row in rows
        if row.get("신뢰도", "").strip() == "낮음"
    ]
    low_without_gap = [
        row["source_id"]
        for row in rows
        if row.get("신뢰도", "").strip() == "낮음"
        and "DG-" not in row.get("비고", "")
    ]
    if low_without_gap:
        errors.append(
            "낮은 신뢰도이나 DATA_GAPS 연결 없음: "
            + ", ".join(low_without_gap)
        )

    return {
        "registry": str(registry_path),
        "row_count": len(rows),
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "duplicate_source_id": len(duplicate_ids),
            "missing_required_cells": len(missing_required_cells),
            "missing_unit": len(missing_units),
            "ambiguous_period": len(ambiguous_periods),
            "ambiguous_scope": len(ambiguous_scopes),
            "low_confidence": len(low_confidence),
            "low_confidence_without_gap": len(low_without_gap),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "registry",
        nargs="?",
        default="data/metadata/source_registry.csv",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = validate_registry(args.registry)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if report["valid"] else "FAIL"
        print(f"source registry validation: {status}")
        print(f"rows: {report['row_count']}")
        for key, value in report["counts"].items():
            print(f"{key}: {value}")
        for message in report["errors"]:
            print(f"ERROR: {message}")
        for message in report["warnings"]:
            print(f"WARNING: {message}")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
