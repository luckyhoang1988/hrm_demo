---
name: run-tests
description: Chạy Unit Tests cho HRM project và báo cáo kết quả
---

Chạy tests cho project HRM và báo cáo kết quả bằng tiếng Việt.

## Bước 1 — Kiểm tra tests hiện có

Đọc các file tests:
- `employees/tests.py`
- `payroll/tests.py`
- `attendance/tests.py`
- `talent/tests.py`
- `contracts/tests.py`
- `api/tests.py`
- `system_settings/tests.py`

Nếu file nào còn là mặc định (chỉ có `# Create your tests here`), báo cáo là "Chưa có tests".

## Bước 2 — Chạy tests

```bash
python -X utf8 manage.py test --verbosity=2
```

Nếu muốn chạy theo từng app:
```bash
python -X utf8 manage.py test employees --verbosity=2
python -X utf8 manage.py test payroll --verbosity=2
python -X utf8 manage.py test attendance --verbosity=2
python -X utf8 manage.py test talent --verbosity=2
python -X utf8 manage.py test api --verbosity=2
```

## Bước 3 — Phân tích kết quả

Với mỗi test fail:
1. Đọc error message cẩn thận
2. Tìm file + dòng bị lỗi
3. Giải thích nguyên nhân bằng tiếng Việt
4. Đề xuất cách sửa

## Bước 4 — Báo cáo

Format báo cáo:
```
📊 Kết quả Tests
================
✅ Passed: X tests
❌ Failed: Y tests  
⚠️ Error: Z tests
⏭️ Skipped: W tests

📁 Theo app:
- employees: ✅ X passed
- payroll: ❌ Y failed → [tên test fail]
- attendance: ⚠️ Chưa có tests
...

🔍 Chi tiết lỗi:
[Mô tả từng lỗi]
```

Nếu chưa có tests → gợi ý dùng agent `test-writer` để tạo.
