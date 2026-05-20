---
name: check-db
description: Kiểm tra trạng thái database và migrations của project HRM
---

Thực hiện các bước sau và báo cáo bằng tiếng Việt:

1. Chạy `python manage.py showmigrations` — liệt kê migration nào đã apply ([x]) và chưa apply ([ ])
2. Chạy `python manage.py check` — kiểm tra project có lỗi cấu hình không
3. Nếu có migration chưa apply → nhắc người dùng chạy `python manage.py migrate`
4. Nếu có lỗi trong `check` → giải thích lỗi và hướng dẫn sửa

Báo cáo ngắn gọn, rõ ràng. Dùng ✅ cho trạng thái tốt, ⚠️ cho cảnh báo, ❌ cho lỗi.
