---
name: new-feature
description: Checklist và quy trình đầy đủ để thêm tính năng mới vào HRM project
---

Hướng dẫn thêm tính năng mới. Làm từng bước, hỏi user nếu không chắc. Báo cáo bằng tiếng Việt.

## Bước 1 — Thu thập yêu cầu

Hỏi user (nếu chưa rõ):
- Tính năng này làm gì? (mô tả ngắn gọn)
- Thuộc module nào? (employees / payroll / attendance / talent / contracts / system_settings)
- Ai được dùng? (superuser / user có quyền cụ thể / tất cả)
- Cần lưu dữ liệu mới không? (nếu có → cần model + migration)

## Bước 2 — Phân tích code hiện có

Dùng agent `researcher` để:
- Tìm model/view/form tương tự có thể tái sử dụng
- Xác định file nào cần sửa
- Kiểm tra có URL namespace không (`contracts:`, `attendance:`, v.v.)

Đặc biệt kiểm tra:
- `employees/helpers.py` — có function nào dùng được không?
- Các view trong app liên quan — pattern đang dùng là gì?

## Bước 3 — Lập kế hoạch

Trình bày cho user:
```
📋 Kế hoạch thực hiện [Tên tính năng]

Files cần tạo mới:
- <app>/templates/<app>/<template>.html

Files cần sửa:
- <app>/models.py (thêm field X)
- <app>/views.py (thêm view Y)
- <app>/urls.py (thêm URL Z)
- <app>/forms.py (thêm form W)

Cần migration: Có / Không
Cần quyền mới: Có / Không → cập nhật UserProfile + StaffGroup

Ước tính: [đơn giản / trung bình / phức tạp]
```

Chờ user xác nhận trước khi code.

## Bước 4 — Implement theo thứ tự

1. **Model** (nếu cần) → `python -X utf8 manage.py makemigrations` → `migrate`
2. **Form** (nếu cần)
3. **View** (logic chính)
4. **URL** (đăng ký route)
5. **Template** (giao diện)
6. **Quyền** (nếu cần) → cập nhật UserProfile + StaffGroup + get_user_features()
7. **Test thủ công** trên browser

## Bước 5 — Checklist trước khi hoàn thành

- [ ] View có `@login_required` không?
- [ ] Check `is_superuser` trước quyền không?
- [ ] Có N+1 query không? (dùng `select_related`)
- [ ] Template dùng `|date:"d/m/Y"` cho ngày không?
- [ ] `log_activity()` được gọi sau thao tác quan trọng không?
- [ ] Migration đã apply chưa? (`python manage.py check`)
- [ ] URL đúng namespace chưa?

## Bước 6 — Cập nhật CLAUDE.md

Sau khi hoàn thành, cập nhật section phù hợp trong CLAUDE.md:
- Nếu thêm model mới → thêm vào phần Models
- Nếu thêm quyền → thêm vào phần Hệ thống phân quyền
- Cập nhật bảng "Phiên bản hiện tại"

## Quy tắc quan trọng

- **Tái sử dụng** trước khi tạo mới — đọc helpers.py kỹ
- **Đặt tên** nhất quán với code hiện có (tiếng Anh cho code, tiếng Việt cho display)
- **Không thêm** tính năng ngoài yêu cầu (không over-engineer)
- **Hỏi** khi không chắc — đừng đoán
