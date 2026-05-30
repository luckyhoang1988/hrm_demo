---
name: debug-payroll
description: Debug và kiểm tra tính toán lương, thuế TNCN, BHXH trong payroll module
---

Debug payroll calculations. Báo cáo bằng tiếng Việt với giải thích chi tiết từng bước tính.

## Cấu trúc tính lương (thứ tự quan trọng)

```
1. PayrollConfig.get()          # Lấy config chung (lương cơ sở, BHXH%)
2. SalaryConfig (nếu có)        # Ưu tiên hơn Contract nếu is_active=True
3. OTRecord                     # Tăng ca trong tháng
4. Payslip.calculate()          # Tính tổng, gọi TRƯỚC save()
5. payslip.save()               # Lưu vào DB
6. payslip.generate_lines()     # Tạo PayslipLine, gọi SAU save()
```

## Bước 1 — Kiểm tra PayrollConfig

```bash
python -X utf8 manage.py shell -c "
from payroll.models import PayrollConfig
config = PayrollConfig.get()
print('Lương cơ sở:', config.base_salary)
print('BHXH NV:', config.employee_social_insurance_rate, '%')
print('BHXH CTY:', config.employer_social_insurance_rate, '%')
print('BHYT NV:', config.employee_health_insurance_rate, '%')
print('BHTN:', config.unemployment_insurance_rate, '%')
"
```

## Bước 2 — Kiểm tra SalaryConfig của nhân viên

```bash
python -X utf8 manage.py shell -c "
from payroll.models import SalaryConfig
from employees.models import Employee
emp = Employee.objects.get(employee_code='NV-001')  # đổi mã NV
config = SalaryConfig.objects.filter(employee=emp, is_active=True).first()
if config:
    print('Basic salary:', config.basic_salary)
    print('Allowances:', config.allowances)
else:
    print('Không có SalaryConfig — dùng lương từ Contract')
"
```

## Bước 3 — Kiểm tra Payslip cụ thể

```bash
python -X utf8 manage.py shell -c "
from payroll.models import Payslip
ps = Payslip.objects.get(employee__employee_code='NV-001', month=5, year=2026)
print('Gross salary:', ps.gross_salary)
print('Social insurance (NV):', ps.employee_social_insurance)
print('Health insurance (NV):', ps.employee_health_insurance)
print('PIT (thuế TNCN):', ps.pit_amount)
print('Net salary:', ps.net_salary)
print()
# Xem chi tiết dòng lương
for line in ps.lines.all():
    print(f'  {line.name}: {line.amount}')
"
```

## Bước 4 — Tính lại Payslip thủ công

```bash
python -X utf8 manage.py shell -c "
from payroll.models import Payslip
ps = Payslip.objects.get(pk=<payslip_id>)
ps.calculate()   # Tính lại (CHƯA lưu)
print('Net salary mới:', ps.net_salary)
ps.save()        # Lưu
ps.generate_lines()  # Tạo lại dòng chi tiết
print('Đã tính lại xong')
"
```

## Bước 5 — Kiểm tra PITBracket (bậc thuế TNCN)

```bash
python -X utf8 manage.py shell -c "
from payroll.models import PITBracket
brackets = PITBracket.objects.filter(year=2026).order_by('income_from')
for b in brackets:
    print(f'Từ {b.income_from:,} đến {b.income_to or \"∞\":,}: {b.rate}%')
if not brackets.exists():
    print('Không có PITBracket — đang dùng bảng thuế hardcoded trong code')
"
```

## Các lỗi thường gặp

| Lỗi | Nguyên nhân | Fix |
|-----|------------|-----|
| `net_salary` âm | Trừ thuế sai | Kiểm tra taxable income |
| `pit_amount = 0` | Chưa có PITBracket | Tạo PITBracket hoặc check logic fallback |
| `generate_lines()` không tạo lines | Chưa `save()` trước | Đảm bảo thứ tự: calculate → save → generate_lines |
| Lương OT sai | `multiplier` sai | Kiểm tra OTRecord.save() logic |

## Báo cáo

Sau mỗi debug: giải thích **con số cụ thể** và **công thức tính**. Ví dụ:
```
Thuế TNCN = (Thu nhập chịu thuế - Giảm trừ cá nhân - Giảm trừ người phụ thuộc) × Thuế suất
= (20,000,000 - 11,000,000 - 0) × 10%
= 9,000,000 × 10% = 900,000 VND
```
