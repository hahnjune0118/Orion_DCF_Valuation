# 프로젝트 상태

## 현재 체크포인트

| 항목 | 상태 |
|---|---|
| 현재 Phase | Phase 1 — 모델 감사 및 통제 기반 |
| 완료 작업 | 1.1 재현 가능한 기준선과 모델 거버넌스 구축 |
| 작업 브랜치 | `valuation-v2` |
| 기준선 원천 커밋 | `0f54ca2000c25a75649288887b806028ad5a5433` |
| 기준선 ID | `orion-dcf-2025-12-31-v1` |
| 가치평가기준일 | 2025-12-31 |
| 정보기준일 | 2026-03-18 |
| 다음 작업 | **1.2 출처대장, 데이터 사전 및 계보 구축** |

## 작업 1.1 완료내용

- 깨끗한 `main` 커밋에서 `valuation-v2` 브랜치 생성
- 저장소, Python/Marimo, 의존성, 모델 모듈, Excel 및 테스트 구조 조사
- 기준 시나리오를 `artifacts/baseline/model_snapshot.json`으로 동결
- Excel 및 주요 모델 파일의 SHA-256·크기·수정시각 기록
- 프로젝트 헌장, 의사결정, 이슈, 자료공백 및 모델목록 문서 생성
- 입력 Excel 지문, 2026~2030 전체 전망 및 핵심 가치평가 결과를 검증하는 회귀 테스트 추가

## 검증 결과

| 검증 | 결과 | 비고 |
|---|---|---|
| 변경 전 `python -m pytest -q` | PASS — 18개 | 1.51초 |
| 변경 후 `python -m pytest -q` | PASS — 21개 | 1.57초 |
| `python -m marimo check orion_dashboard.py` | PASS | 컨테이너의 읽기전용 `/root/.config` 탐색 경고만 발생 |
| Excel 수식 캐시 검사 | PASS | 수식 677개, 캐시 오류 0개 |
| 입력 Excel SHA-256 | PASS | `1e57dc7508b04b5e1c6ee546e8435634589427cc2828f0d9542806b394acde8d` |

## 다음 작업 1.2의 입력

- `docs/blueprint/PROJECT_CHARTER.md`
- `docs/model_governance/MODEL_INVENTORY.md`
- `artifacts/baseline/model_snapshot.json`
- `artifacts/baseline/environment.txt`
- `docs/checkpoints/ISSUES.md`
- `docs/checkpoints/DATA_GAPS.md`

다음 작업에서는 현행 Excel과 Python의 모든 중요 입력을 `공시값/외부 시장자료/계산값/분석가 가정`으로 구분하고 source ID를 부여한다. 이번 기준선 수치는 그 과정에서 임의로 변경하지 않는다.
