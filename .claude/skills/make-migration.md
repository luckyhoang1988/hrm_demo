---
name: make-migration
description: Tạo và apply Django migrations an toàn cho HRM project
---

Thực hiện migrations an toàn. Báo cáo bằng tiếng Việt. Giải thích từng bước để người mới học hiểu.

## Bước 1 — Kiểm tra trạng thái hiện tại

```bash
python -X utf8 manage.py showmigrations
python -X utf8 manage.py check
```

Báo cáo:
- App nào có migration chưa apply ([ ])
- Có lỗi cấu hình không

## Bước 2 — Tạo migration mới

Nếu user đã sửa models.py, hỏi app nào bị ảnh hưởng rồi chạy:

```bash
python -X utf8 manage.py makemigrations <app_name>
```

Nếu không biết app nào:
```bash
python -X utf8 manage.py makemigrations
```

Kiểm tra file migration vừa tạo: đọc nội dung và xác nhận với user.

## Bước 3 — Apply migration

```bash
python -X utf8 manage.py migrate
```

## Bước 4 — Xác nhận thành công

```bash
python -X utf8 manage.py showmigrations  # tất cả phải có [x]
python -X utf8 manage.py check           # phải "System check identified no issues"
```

## Xử lý lỗi thường gặp

**"No changes detected"**: Kiểm tra app đã trong INSTALLED_APPS chưa, file đã lưu chưa.

**"Table already exists"**: Dùng `--fake` để skip migration đó.

**"Cannot add NOT NULL column"**: Thêm `null=True, blank=True` hoặc `default=value` vào field.

**Conflict migrations**: Chạy `makemigrations --merge` để gộp.

Với mỗi lỗi: giải thích **tại sao** bị lỗi và hướng dẫn fix.
