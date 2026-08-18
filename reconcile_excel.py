from pathlib import Path

from openpyxl import load_workbook

from fcff_model import calculate_fcff


excel_path = Path("data/raw/orion_dcf.xlsx")

# data_only=True:
# Excel 수식이 아니라 수식의 최종 계산값을 읽는다.
workbook = load_workbook(
    excel_path,
    data_only=True,
    read_only=True,
)


ebit = workbook["영업실적추정"]["F17"].value
tax_rate = workbook["DCF"]["C9"].value
depreciation = workbook["Capex_D&A"]["F8"].value
capex = workbook["Capex_D&A"]["F15"].value
change_in_nwc = workbook["NWC"]["F21"].value
excel_fcff = workbook["DCF"]["C15"].value


python_result = calculate_fcff(
    ebit=ebit,
    tax_rate=tax_rate,
    depreciation=depreciation,
    capex=capex,
    change_in_nwc=change_in_nwc,
)

python_fcff = python_result["FCFF"]
difference = python_fcff - excel_fcff


print("[2026년 FCFF 대사]")
print(f"EBIT:          {ebit:,.6f}")
print(f"법인세율:      {tax_rate:.4%}")
print(f"NOPAT:         {python_result['NOPAT']:,.6f}")
print(f"감가상각비:    {depreciation:,.6f}")
print(f"Capex:         {capex:,.6f}")
print(f"NWC 증가:      {change_in_nwc:,.6f}")
print(f"Python FCFF:   {python_fcff:,.6f}")
print(f"Excel FCFF:    {excel_fcff:,.6f}")
print(f"대사 차이:     {difference:,.10f}")


tolerance = 0.000001

assert abs(difference) < tolerance, (
    f"FCFF 대사 실패: 차이 {difference:,.10f}"
)

print("검증 결과: PASS")