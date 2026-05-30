---
name: deploy
description: Hướng dẫn deploy hoặc cập nhật HRM app lên VPS đầy đủ, tránh các lỗi 400/502 đã gặp. Bao gồm cả SSL Let's Encrypt.
---

## Thông tin VPS

- **IP:** `103.20.97.188` | **Domain:** `ryanapp.online` | **User:** `luckyhoang`
- **Project trên VPS:** `/home/luckyhoang/hrm/`
- **SSL:** Let's Encrypt, cert tại `/etc/letsencrypt/live/ryanapp.online/`, hết hạn 28/08/2026 (tự gia hạn)

---

## Trường hợp 1: Cập nhật code lên VPS (thường xuyên)

### Trên máy local (Windows)
```bash
git add .
git commit -m "mô tả thay đổi"
git push
```

### Trên VPS
```bash
ssh luckyhoang@103.20.97.188
cd ~/hrm
git pull
docker compose up --build -d
docker compose restart nginx   # QUAN TRỌNG: luôn restart nginx sau khi up
docker compose logs --tail=20 web
docker compose ps
```

---

## Trường hợp 2: Deploy lần đầu trên VPS mới (đầy đủ từ A-Z)

### Bước 1 — Cài Docker
```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
exit  # đăng xuất rồi SSH lại
```

### Bước 2 — Clone code
```bash
ssh luckyhoang@103.20.97.188
git clone https://github.com/luckyhoang1988/hrm_demo.git hrm
cd hrm
```

### Bước 3 — Tạo file .env
```bash
cp .env.example .env
nano .env
```

Điền đầy đủ (dùng https:// vì đã có SSL):
```
SECRET_KEY=<tạo bằng: python3 -c "import secrets; print(secrets.token_urlsafe(50))">
DEBUG=False
ALLOWED_HOSTS=103.20.97.188,ryanapp.online,www.ryanapp.online,localhost
CSRF_TRUSTED_ORIGINS=https://ryanapp.online,https://www.ryanapp.online
DATABASE_URL=postgresql://postgres:<mat-khau-db>@db:5432/hrm_db
DB_PASSWORD=<mat-khau-db>
CELERY_BROKER_URL=redis://redis:6379/0
DJANGO_LOG_LEVEL=WARNING
```

### Bước 4 — Cấu hình DNS
Tại nhà cung cấp tên miền, thêm 2 record A:
| Type | Host | Value |
|------|------|-------|
| A | `@` | `103.20.97.188` |
| A | `www` | `103.20.97.188` |

Kiểm tra DNS trỏ chưa (chờ 5–30 phút):
```bash
nslookup ryanapp.online  # phải ra 103.20.97.188
```

### Bước 5 — Lấy SSL cert (TRƯỚC khi start Docker)
```bash
sudo apt install certbot -y
sudo certbot certonly --standalone \
  -d ryanapp.online -d www.ryanapp.online \
  --email hoangtruonghd88@gmail.com \
  --agree-tos --no-eff-email
# Cert lưu tại: /etc/letsencrypt/live/ryanapp.online/
```

### Bước 6 — Build và khởi động
```bash
cd ~/hrm
docker compose up --build -d
docker compose restart nginx
docker compose ps   # tất cả phải healthy
```

### Bước 7 — Tạo superuser
```bash
docker compose exec web python manage.py createsuperuser
```

Kiểm tra: mở `https://ryanapp.online` — thấy ổ khóa xanh là thành công.

---

## Trường hợp 3: Gia hạn SSL thủ công (nếu cần)

Certbot đã tự cài cron job gia hạn tự động. Kiểm tra:
```bash
sudo certbot renew --dry-run
# Kết quả mong đợi: "All simulated renewals succeeded"
```

Nếu gia hạn xong cần restart nginx để load cert mới:
```bash
cd ~/hrm
docker compose restart nginx
```

---

## Các lỗi thường gặp và cách fix

| Lỗi | Nguyên nhân | Fix |
|-----|------------|-----|
| `no configuration file provided` | Đứng sai thư mục | `cd ~/hrm` rồi chạy lại |
| **400 Bad Request** | Domain chưa có trong `ALLOWED_HOSTS` | Thêm vào `.env` → `docker compose up -d` |
| **502 Bad Gateway** | Nginx cache IP cũ của container web | `docker compose restart nginx` |
| Sửa `.env` không có tác dụng | `restart` không reload `.env` | Luôn dùng `docker compose up -d` |
| Nginx không start sau khi thêm SSL | Cert chưa có trên VPS | Chạy certbot lấy cert TRƯỚC khi `docker compose up` |

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
