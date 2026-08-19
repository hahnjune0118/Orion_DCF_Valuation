# 데이터 계보

## 1. 계보 요약

| 단계 | 원천·객체 | 정규화·변환 | 다음 사용처 | 통제증적 |
|---|---|---|---|---|
| 원천자료 | 2025년 사업보고서, KRX 공시뷰어 | 천원→백만원, 비용 부호 통일, 연결범위 확인 | `과거재무제표` | FIL-001–FIL-034 |
| 정규화 입력 | `data/raw/orion_dcf.xlsx`의 `과거재무제표`·`가정` | Actual과 Estimate 분리, 기간별 열 정렬 | `run_orion_dcf` | source registry의 Excel 셀 주소 |
| 전망동인 | 지역성장률, 원가·판관비율, 운전자본일수, D&A·Capex | 2026E–2030E 지역매출·EBIT·NWC·재투자 | `forecast_model.py`, `cash_flow_model.py` | ASM-001–ASM-015 |
| FCFF | EBIT, 현금법인세율, D&A, Capex, NWC 증감 | `NOPAT + D&A - Capex - ΔNWC` | `valuation_model.py` | CALC-006, CALC-007 |
| DCF | FCFF, WACC, 영구성장률, 연말 할인 | 명시적 PV + 계속가치 PV | 기업가치 | CALC-005, CALC-008–CALC-010 |
| 지분가치 | 기업가치, 초과현금, 금융자산, 관계기업, 투자부동산, 차입금성 항목, 비지배지분 | 순비영업 조정 | 지분가치·주당가치 | CALC-011–CALC-014 |
| 대시보드 | `run_orion_dcf` 반환 사전 | KPI 카드, 민감도, 시나리오, FCFF/마진, 브리지 | `orion_dashboard.py` | CODE-004–CODE-008 |

## 2. 모델 경로별 상세 매핑

| 결과 | 직접 입력 | Excel 위치 | Python 처리 | 출력 | source_id / Gap |
|---|---|---|---|---|---|
| 지역별 매출액 | 2025 지역매출, 2026–2030 성장률 | `과거재무제표!F71:F73`, `가정!F7:J9` | `forecast_segment_revenue` | 한국·중국·기타 매출 | FIL-031–FIL-033; ASM-001–ASM-003 / DG-011 |
| EBIT | 지역매출, 원가율, 판매비율, 일반관리비율 | `가정!F13:J15` | `calculate_operating_profit` | 매출액, EBIT, 영업이익률 | ASM-004–ASM-006 / DG-012 |
| NWC | 2025 기초 NWC, DSO, 재고일수, DPO, 기타자산·부채율 | `과거재무제표!F39:F41,F56:F58`, `가정!F22:J26` | `calculate_nwc`; 365일 convention | NWC·NWC 증감 | FIL-014–FIL-016,FIL-025–FIL-027,CALC-001,ASM-011–ASM-015,CODE-002 / DG-013 |
| D&A·Capex | D&A율, 유지보수율, 성장 Capex | `가정!F17:J19` | `calculate_capex_and_depreciation` | D&A, 총 Capex | FIL-034; ASM-008–ASM-010 / DG-010,DG-014 |
| NOPAT·FCFF | EBIT, 세율, D&A, Capex, NWC 증감 | `가정!F16:J16` 및 위 전망 | `calculate_fcff` | 2026–2030 FCFF | ASM-007,CALC-006,CALC-007 / DG-012 |
| WACC | Rf, ERP, β, CRP, Kd, 세율, 자본구조 | `가정!C30:C36`, `가정!F16` | `calculate_wacc` | 9.477625% | ASM-016–ASM-022,CALC-005 / DG-002–DG-006 |
| 기업가치 | FCFF, WACC, g | `가정!C37` | `calculate_dcf`; 연말 할인 | 6,774,771.675812백만원 | ASM-023,CALC-007–CALC-010,CODE-003 / DG-015 |
| 순비영업 조정 | 현금·금융상품·관계기업·투자부동산·차입금·리스·NCI·필요현금율 | `과거재무제표!F35:F37,F46,F48:F55,F59`, `가정!C39` | `calculate_equity_bridge` | 2,898,256.998649백만원 | FIL-011–FIL-013,FIL-017–FIL-024,FIL-028,ASM-025,CALC-003,CALC-004,CALC-011 / DG-007,DG-009,DG-015 |
| 주당 내재가치 | 지분가치, 유통주식수 | `과거재무제표!F65:F67` | 지분가치/백만주 | 244,708.455884원 | FIL-029,FIL-030,CALC-002,CALC-012,CALC-013 |
| 내재 상승여력 | 주당 내재가치, 12월 평균주가 | `과거재무제표!F68` 및 Python 중복값 | 내재가치/기준주가-1 | 134.552340% | MKT-001,CALC-014 / DG-008 |
| 대시보드 민감도 | WACC·g 격자 | Python 상수 | 각 조합별 `calculate_dcf` 재실행 | 히트맵 | CODE-004,CODE-005 / DG-017 |
| 시나리오 | 매출성장·마진·WACC 조정 | Python 상수 | `run_orion_dcf` 인자 조정 | 보수·기준·낙관 주당가치 | CODE-006,CODE-007 / DG-017,I-013 |

## 3. 값 분류 결과

| 분류 | 정의 | 등록 건수 | 통제 결론 |
|---|---|---:|---|
| 공시값 | 사업보고서·연결재무제표·주석에서 직접 확인 | 34 | 공시일·평가기준일·페이지·Excel 셀과 연결 |
| 시장자료 | 거래시장 가격 또는 시장 관측값 | 1 | 평균주가 원천 미확보로 DG-008에 연결 |
| 계산값 | 공시값·가정에서 산식으로 도출 | 16 | 계산식과 상위 source_id를 비고에 기록 |
| 분석가 가정 | 전망·가치평가·표시를 위한 판단 입력 | 31 | 근거 미확보분을 DG-002–DG-017에 연결 |
| **합계** |  | **82** | source_id 중복 0, 필수값 누락 0 |

> 분류 건수는 `python scripts/validate_source_registry.py --json`과 CSV 자료유형 집계로 재검증한다. 등록부의 낮은 신뢰도 항목은 30건이며 모두 DATA_GAPS ID를 보유한다.

## 4. 연결범위·기간·단위 완전성

| 검사 | 불명확 항목 수 | 기준 |
|---|---:|---|
| 연결/별도 | 0 | `연결`, `별도`, `연결/별도`, `해당 없음` 중 하나 |
| 기간 | 0 | 기준일·회계연도·전망기간·실행시점 중 하나를 명시 |
| 단위 | 0 | 금액·비율·주식수·기간·경로 등 해당 단위를 명시 |

이 수치는 메타데이터 기재 여부를 뜻한다. 기재된 가정의 외부 타당성이 검증됐음을 의미하지 않는다.

## 5. 감사 추적 절차

1. `source_registry.csv`에서 결과의 source_id를 찾는다.
2. 등록된 페이지와 Excel 셀을 공시 원문에 대조한다.
3. `DATA_DICTIONARY.md`의 부호·단위·산식을 확인한다.
4. Python 함수의 입력→출력 연결을 재실행한다.
5. `model_snapshot.json` 회귀 테스트로 기준선 변화 여부를 확인한다.
6. 낮은 신뢰도 또는 미해결 Gap은 사실로 승인하지 않고 후속 과제로 유지한다.
