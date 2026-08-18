from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from fcff_model import calculate_fcff


excel_path = Path("data/raw/orion_dcf.xlsx")
output_path = Path("data/processed/fcff_forecast.csv")

workbook = load_workbook(
    excel_path,
    data_only=True,
    read_only=True,
)


years = [2026, 2027, 2028, 2029, 2030]

# 각 추정명세서의 연도별 열
schedule_columns = ["F", "G", "H", "I", "J"]

# DCF 시트의 연도별 열
dcf_columns = ["C", "D", "E", "F", "G"]


reconciliation_results = []


for year, schedule_col, dcf_col in zip(
    years,
    schedule_columns,
    dcf_columns,
):
    ebit = workbook["영업실적추정"][f"{schedule_col}17"].value
    tax_rate = workbook["DCF"][f"{dcf_col}9"].value
    depreciation = workbook["Capex_D&A"][f"{schedule_col}8"].value
    capex = workbook["Capex_D&A"][f"{schedule_col}15"].value
    change_in_nwc = workbook["NWC"][f"{schedule_col}21"].value

    excel_fcff = workbook["DCF"][f"{dcf_col}15"].value

    python_result = calculate_fcff(
        ebit=ebit,
        tax_rate=tax_rate,
        depreciation=depreciation,
        capex=capex,
        change_in_nwc=change_in_nwc,
    )

    python_fcff = python_result["FCFF"]
    difference = python_fcff - excel_fcff

    reconciliation_results.append(
        {
            "연도": year,
            "EBIT": ebit,
            "법인세율": tax_rate,
            "NOPAT": python_result["NOPAT"],
            "감가상각비": depreciation,
            "Capex": capex,
            "NWC 증감": change_in_nwc,
            "Python FCFF": python_fcff,
            "Excel FCFF": excel_fcff,
            "대사 차이": difference,
        }
    )


result_df = pd.DataFrame(reconciliation_results)

pd.set_option("display.float_format", lambda x: f"{x:,.4f}")

print("\n[2026~2030년 FCFF 대사]")
print(result_df.to_string(index=False))


tolerance = 0.000001

for _, row in result_df.iterrows():
    assert abs(row["대사 차이"]) < tolerance, (
        f"{int(row['연도'])}년 FCFF 대사 실패: "
        f"{row['대사 차이']:,.10f}"
    )


output_path.parent.mkdir(parents=True, exist_ok=True)
result_df.to_csv(
    output_path,
    index=False,
    encoding="utf-8-sig",
)

print("\n전체 검증 결과: PASS")
print(f"대사 결과 저장 위치: {output_path}")