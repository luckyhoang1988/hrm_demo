# Quy trình làm việc — HRM App

## Trước khi thêm tính năng mới
- Đọc CLAUDE.md để nắm rõ models, views, URLs hiện tại
- Kiểm tra xem có code/function nào dùng lại được không — không tạo mới nếu đã có
- Nếu tính năng liên quan đến model → cần tạo migration

## Khi thay đổi models.py
1. Sửa `<app>/models.py`
2. Chạy `python -X utf8 manage.py makemigrations <app>`
3. Chạy `python -X utf8 manage.py migrate`
4. Kiểm tra `python -X utf8 manage.py check` không có lỗi

## Khi thêm quyền mới (permission)
- Thêm vào cả `UserProfile` VÀ `StaffGroup` trong `employees/models.py`
- Cập nhật hàm `get_user_features()` trong `employees/helpers.py`
- Tạo migration

## Khi thêm trạng thái nhân viên mới
- Thêm vào `STATUS_CHOICES` trong models.py
- Cập nhật `LEAVE_STATUSES` hoặc `DATE_STATUSES` nếu cần
- Cập nhật `STATUS_COLORS` trong view `dashboard` và `export_status_excel`
- Thêm CSS pill màu tương ứng trong employee_list.html

## Sau khi hoàn thành tính năng
- Cập nhật section "Phiên bản hiện tại" trong CLAUDE.md
- Nếu thêm model/field mới → cập nhật phần Models trong CLAUDE.md
- Xóa thông tin lỗi thời trong CLAUDE.md nếu có

## Quy tắc code
- Mọi view phải có `@login_required`
- Luôn kiểm tra `request.user.is_superuser` trước khi check quyền
- Luôn dùng `select_related('department')` khi query Employee trong vòng lặp
- Ngày hiển thị trong template: `|date:"d/m/Y"`
- `employee_code` luôn lưu UPPERCASE
