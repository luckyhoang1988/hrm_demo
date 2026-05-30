---
name: deploy
description: Hướng dẫn deploy hoặc cập nhật HRM app lên VPS đầy đủ, tránh các lỗi 400/502 đã gặp
---

## Thông tin VPS

- **IP:** `103.20.97.188` | **Domain:** `ryanapp.online` | **User:** `luckyhoang`
- **Project trên VPS:** `/home/luckyhoang/hrm/`

---

## Trường hợp 1: Cập nhật code lên VPS (thường xuyên)

### Trên máy local (Windows)
```bash
# Commit và push code mới lên GitHub
git add .
git commit -m "mô tả thay đổi"
git push
```

### Trên VPS
```bash
# 1. SSH vào VPS
ssh luckyhoang@103.20.97.188

# 2. Vào thư mục project
cd ~/hrm

# 3. Pull code mới từ Git
git pull

# 4. Build lại và khởi động (load .env mới)
docker compose up --build -d

# 5. Restart nginx để fix cache IP container (QUAN TRỌNG - không bỏ bước này)
docker compose restart nginx

# 6. Kiểm tra không có lỗi
docker compose logs --tail=20 web
docker compose ps
```

---

## Trường hợp 2: Thêm domain mới

### Bước 1 — Cấu hình DNS tại nhà cung cấp tên miền
Thêm 2 record:
| Type | Host | Value |
|------|------|-------|
| A | `@` | `103.20.97.188` |
| A | `www` | `103.20.97.188` |

Kiểm tra DNS đã trỏ chưa (chờ 5–30 phút):
```bash
nslookup ryanapp.online
# Phải ra 103.20.97.188 mới tiếp tục
```

### Bước 2 — Cập nhật nginx.conf trên máy local
Sửa file [nginx/nginx.conf](nginx/nginx.conf) dòng `server_name`:
```nginx
server_name ryanapp.online www.ryanapp.online;
```

Commit và push lên GitHub:
```bash
git add nginx/nginx.conf
git commit -m "chore: update nginx server_name for ryanapp.online"
git push
```

### Bước 3 — Cập nhật .env trên VPS
```bash
ssh luckyhoang@103.20.97.188
nano ~/hrm/.env
```

Đảm bảo 2 dòng này đúng (thêm domain vào):
```
ALLOWED_HOSTS=103.20.97.188,ryanapp.online,www.ryanapp.online,localhost
CSRF_TRUSTED_ORIGINS=http://ryanapp.online,http://www.ryanapp.online,http://103.20.97.188
```

### Bước 4 — Pull code và khởi động lại trên VPS
```bash
cd ~/hrm
git pull                        # Lấy nginx.conf mới
docker compose up --build -d    # Build lại + load .env mới (KHÔNG dùng restart)
docker compose restart nginx    # Fix cache IP container
```

### Bước 5 — Kiểm tra
```bash
docker compose ps               # Tất cả STATUS phải là running/healthy
docker compose logs --tail=20 web
```
Mở trình duyệt vào `http://ryanapp.online` — thấy trang HRM là thành công.

---

## Các lỗi thường gặp và cách fix

| Lỗi | Nguyên nhân | Fix |
|-----|------------|-----|
| `no configuration file provided` | Đang đứng sai thư mục | `cd ~/hrm` rồi chạy lại |
| **400 Bad Request** | Domain chưa có trong `ALLOWED_HOSTS` | Thêm vào `.env` → `docker compose up -d` |
| **502 Bad Gateway** | Nginx cache IP cũ của container web | `docker compose restart nginx` |
| Sửa `.env` không có tác dụng | `docker compose restart` không reload `.env` | Luôn dùng `docker compose up -d` |

---

## Lệnh quản lý thường dùng

```bash
docker compose ps                              # Xem trạng thái containers
docker compose logs -f web                     # Xem log realtime
docker compose logs --tail=50 nginx            # Xem log nginx
docker compose exec web python manage.py shell # Django shell
docker compose exec web python manage.py createsuperuser
docker compose exec db pg_dump -U postgres hrm_db > backup_$(date +%Y%m%d).sql  # Backup DB
docker compose down                            # Dừng tất cả (data còn trong volume)
```
