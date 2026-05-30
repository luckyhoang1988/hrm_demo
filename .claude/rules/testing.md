# Quy tắc Viết Tests — HRM App

## Project chưa có tests — Ưu tiên viết theo thứ tự

1. **employees** — core của toàn app, quyền phụ thuộc vào đây
2. **payroll** — logic tính lương phức tạp, dễ sai
3. **attendance** — tính ngày nghỉ có nhiều edge case
4. **talent** — workflow phức tạp (stage → certificate)
5. **api** — test tất cả endpoints
6. **contracts, system_settings** — logic đơn giản hơn

## Nguyên tắc

### Viết test thực sự hữu ích
- Test **business logic**, không test Django framework
- Một test = một hành vi cụ thể (không nhồi nhiều assertions vào một test)
- Test tên phải đọc được như văn xuôi: `test_employee_code_auto_uppercase`

### Tốc độ
- Dùng `TestCase` (transaction rollback) — nhanh hơn `TransactionTestCase`
- Dùng `setUpTestData()` cho data không thay đổi, `setUp()` cho data cần reset
- Tránh tạo quá nhiều object trong setUp

### Test View
```python
# Luôn test các trường hợp auth:
# 1. Chưa đăng nhập → redirect login
# 2. Đăng nhập nhưng không quyền → 403 hoặc redirect
# 3. Đúng quyền → 200/redirect thành công
```

## Lệnh chạy (dùng python -X utf8 trên Windows)

```bash
# Chạy tất cả
python -X utf8 manage.py test --verbosity=2

# Chạy một app
python -X utf8 manage.py test employees --verbosity=2

# Chạy nhanh (parallel)
python -X utf8 manage.py test --parallel

# Dừng khi có test fail đầu tiên
python -X utf8 manage.py test --failfast
```

## Coverage — biết đang test bao nhiêu %

```bash
pip install coverage
coverage run manage.py test
coverage report -m          # xem % theo từng file
coverage html               # tạo HTML report vào htmlcov/
```

## Không test những thứ này

- `Employee.objects.create(...)` — Django ORM đã test rồi
- Template rendering thuần túy — không có logic
- Admin interface — Django đã test
- Third-party packages (DRF, Celery, django_celery_beat)
