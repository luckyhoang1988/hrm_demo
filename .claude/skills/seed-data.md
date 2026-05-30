---
name: seed-data
description: Tạo dữ liệu mẫu (seed data) cho development và testing của HRM project
---

Tạo dữ liệu mẫu để test tính năng. Báo cáo bằng tiếng Việt.

## Các management commands có sẵn

```bash
# Seed nhân viên (employees)
python -X utf8 manage.py seed_employees

# Seed hợp đồng (contracts)
python -X utf8 manage.py seed_contracts

# Seed talent (tuyển dụng + đào tạo)
python -X utf8 manage.py seed_talent

# Seed toàn bộ pipeline talent
python -X utf8 manage.py seed_full_pipeline

# Seed cấu hình payroll
python -X utf8 manage.py seed_payroll_config
```

## Bước thực hiện

1. Kiểm tra DB đã có dữ liệu chưa (tránh seed trùng)
2. Hỏi user muốn seed module nào
3. Chạy command tương ứng
4. Xác nhận bằng cách kiểm tra số lượng record

```bash
# Kiểm tra số lượng sau khi seed
python -X utf8 manage.py shell -c "
from employees.models import Employee
from departments.models import Department
print(f'Departments: {Department.objects.count()}')
print(f'Employees: {Employee.objects.count()}')
"
```

## Seed thủ công (nếu command chưa có)

Nếu cần tạo dữ liệu cho module chưa có seed command (attendance, payroll):

```bash
python -X utf8 manage.py shell
```

Rồi tạo object trong Django shell. Hướng dẫn user từng bước.

## Lưu ý

- Seed data chỉ dùng cho **development/testing**, không bao giờ chạy trên production
- Nếu đã có data → hỏi user có muốn xóa và seed lại không trước khi làm
- Sau khi seed → nhắc user restart server nếu cần
