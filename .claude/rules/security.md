# Quy tắc Bảo mật — HRM App

## Bắt buộc trong mọi View

```python
@login_required
def my_view(request):
    # LUÔN kiểm tra superuser TRƯỚC khi check quyền khác
    if not request.user.is_superuser:
        perms = get_user_perms(request.user)
        if not perms.get('can_add'):
            return HttpResponseForbidden("Không có quyền")
```

## Không bao giờ làm

- **SQL injection**: không dùng `raw()` hoặc `extra()` với input người dùng
  ```python
  # SAI ❌
  Employee.objects.raw(f"SELECT * FROM employees WHERE name = '{name}'")
  
  # ĐÚNG ✅
  Employee.objects.filter(last_name=name)
  ```

- **XSS**: không dùng `{{ var | safe }}` với input người dùng
  ```html
  <!-- SAI ❌ -->
  {{ user_input | safe }}
  
  <!-- ĐÚNG ✅ - Django tự escape -->
  {{ user_input }}
  ```

- **CSRF**: mọi form POST phải có `{% csrf_token %}`

- **Lộ thông tin**: không log hoặc hiển thị password, SECRET_KEY, DATABASE_URL

- **File upload**: luôn validate extension, không chạy file upload trực tiếp

## Phân quyền đúng cách

```python
# Thứ tự kiểm tra:
# 1. Đăng nhập chưa? (@login_required xử lý)
# 2. Superuser? → bypass tất cả
# 3. Có quyền app không? (get_user_features)
# 4. Có quyền phòng ban không? (get_allowed_departments)
# 5. Có quyền hành động không? (get_user_perms)

from employees.helpers import get_user_features, get_user_perms, get_allowed_departments

features = get_user_features(request.user)
if not features.get('app_payroll'):
    return redirect('home')  # không có quyền xem app payroll
```

## Session & Authentication

- `SESSION_COOKIE_AGE = 900` (15 phút) — đã cấu hình, không thay đổi
- JWT token cho API — expire sau 60 phút (access), refresh token 7 ngày
- Không lưu token trong localStorage (XSS risk) — dùng httpOnly cookie nếu cần

## Môi trường

- `DEBUG=False` trên production — đã cấu hình trong Docker
- `SECRET_KEY` phải khác nhau giữa local và production
- `.env` không được commit vào git (đã có trong .gitignore)
- `ALLOWED_HOSTS` chỉ liệt kê domain thực sự dùng
