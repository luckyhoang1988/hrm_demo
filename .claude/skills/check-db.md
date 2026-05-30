---
name: check-db
description: Kiểm tra trạng thái database, migrations, và health của HRM project
---

Kiểm tra toàn diện trạng thái project. Báo cáo bằng tiếng Việt. Dùng ✅ / ⚠️ / ❌.

## Bước 1 — Kiểm tra cấu hình

```bash
python -X utf8 manage.py check
```

✅ "System check identified no issues" — không có lỗi
❌ Nếu có lỗi → giải thích và hướng dẫn sửa

## Bước 2 — Kiểm tra migrations

```bash
python -X utf8 manage.py showmigrations
```

Kiểm tra:
- `[x]` = đã apply ✅
- `[ ]` = chưa apply ⚠️ → nhắc chạy `python -X utf8 manage.py migrate`

## Bước 3 — Kiểm tra kết nối DB

```bash
python -X utf8 manage.py shell -c "
from django.db import connection
try:
    connection.ensure_connection()
    print('DB connection: OK')
    cursor = connection.cursor()
    cursor.execute('SELECT COUNT(*) FROM employees_employee')
    count = cursor.fetchone()[0]
    print(f'Employees: {count} records')
except Exception as e:
    print(f'DB Error: {e}')
"
```

## Bước 4 — Kiểm tra data nhanh

```bash
python -X utf8 manage.py shell -c "
from departments.models import Department
from employees.models import Employee
from system_settings.models import AppStatus
from payroll.models import PayrollConfig

print(f'Departments: {Department.objects.count()}')
print(f'Employees: {Employee.objects.count()}')
print(f'Active employees: {Employee.objects.filter(status=\"dang_lam\").count()}')

app_status = AppStatus.get()
print(f'Contracts app: {\"ON\" if app_status.app_contracts_active else \"OFF\"}')
print(f'Attendance app: {\"ON\" if app_status.app_attendance_active else \"OFF\"}')
print(f'Payroll app: {\"ON\" if app_status.app_payroll_active else \"OFF\"}')
print(f'Talent app: {\"ON\" if app_status.app_talent_active else \"OFF\"}')
"
```

## Bước 5 — Báo cáo tổng hợp

```
🏥 Health Check — HRM Project
==============================
⚙️  System check: ✅ No issues
🗄️  Database: ✅ Connected
📋  Migrations: ✅ All applied / ⚠️ X chưa apply

📊 Data:
   - Phòng ban: X
   - Nhân viên: Y (Z đang làm)

🔌 App toggles:
   - Contracts: ON/OFF
   - Attendance: ON/OFF
   - Payroll: ON/OFF
   - Talent: ON/OFF
```

Nếu phát hiện vấn đề → hướng dẫn cách fix cụ thể.
