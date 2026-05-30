---
name: api-test
description: Kiểm tra và test REST API endpoints của HRM project
---

Test các API endpoints của HRM. Báo cáo kết quả bằng tiếng Việt.

## Bước 1 — Khởi động server

Đảm bảo Django server đang chạy:
```bash
python manage.py runserver
```

## Bước 2 — Lấy JWT Token

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"admin\", \"password\": \"admin\"}"
```

Lưu `access` token để dùng cho các request tiếp theo.

## Bước 3 — Test từng endpoint

### Health check (không cần auth)
```bash
curl http://127.0.0.1:8000/api/health/
```
Mong đợi: `{"status": "ok"}`

### Employees API
```bash
# List
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/api/employees/

# Detail
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/api/employees/1/

# Search
curl -H "Authorization: Bearer <token>" "http://127.0.0.1:8000/api/employees/?search=nguyen"

# Filter by status
curl -H "Authorization: Bearer <token>" "http://127.0.0.1:8000/api/employees/?status=dang_lam"
```

### Attendance API
```bash
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/api/attendance/records/
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/api/attendance/leave-requests/
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/api/attendance/leave-types/
```

### Payroll API
```bash
curl -H "Authorization: Bearer <token>" "http://127.0.0.1:8000/api/payroll/payslips/?month=5&year=2026"
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/api/payroll/ot-records/
```

## Bước 4 — Kiểm tra Swagger docs

Mở trình duyệt: http://127.0.0.1:8000/api/docs/

Swagger cho phép test trực tiếp với giao diện UI.

## Bước 5 — Báo cáo

Cho mỗi endpoint:
```
✅ GET /api/employees/ → 200 OK (X records)
✅ GET /api/employees/1/ → 200 OK
❌ POST /api/attendance/records/ → 400 Bad Request
   Lỗi: {"date": ["This field is required"]}
```

Giải thích lỗi và hướng dẫn fix.
