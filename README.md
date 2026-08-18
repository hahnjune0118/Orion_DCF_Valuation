## Interactive DCF Valuation Lab

[![Open in molab](https://marimo.io/molab-shield.svg)](https://molab.marimo.io/github/hahnjune0118/Orion_DCF_Valuation/blob/main/orion_valuation_lab.py)

- [분석 결과 미리보기](https://molab.marimo.io/github/hahnjune0118/Orion_DCF_Valuation/blob/main/orion_valuation_lab.py)
- [대화형 모델 실행](https://molab.marimo.io/github/hahnjune0118/Orion_DCF_Valuation/blob/main/orion_valuation_lab.py/server)


# Orion Valuation Lab

오리온의 2025년 K-IFRS 연결재무제표를 기반으로 구축한
FCFF 방식의 DCF 가치평가 프로젝트입니다.

Excel 기준모형을 Python 계산엔진으로 독립적으로 재수행하고,
Marimo를 이용해 시나리오 분석, 민감도분석, 시각화 및
자동 footing 기능을 구현했습니다.

## 기준 가치평가 결과

| 항목 | 결과 |
|---|---:|
| 평가기준일 | 2025-12-31 |
| WACC | 9.48% |
| 영구성장률 | 2.0% |
| 기업가치 | 6,774,772백만원 |
| 지분가치 | 9,673,029백만원 |
| 주당 내재가치 | 244,708원 |
| 2025년 12월 평균주가 | 104,330원 |
| 내재 상승여력 | 134.6% |

## 평가 구조

```text
지역별 매출액
→ 연결 매출액
→ EBIT
→ NOPAT
→ D&A·Capex·NWC
→ FCFF
→ 현재가치 및 계속기업가치
→ 기업가치
→ 비영업자산 및 차감항목
→ 지분가치
→ 주당 내재가치
