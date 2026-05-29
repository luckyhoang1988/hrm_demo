# Hướng dẫn triển khai HRM App lên VPS (Ubuntu 22.04)

## Yêu cầu VPS

- Ubuntu 22.04 LTS
- RAM: tối thiểu 2GB (khuyến nghị 4GB)
- Disk: tối thiểu 20GB
- Port 80 mở trong firewall

---

## Bước 1 — Cài Docker trên VPS

Kết nối SSH vào VPS rồi chạy:

```bash
# Cập nhật hệ thống
sudo apt update && sudo apt upgrade -y

# Cài Docker (tự động cài kèm Docker Compose)
curl -fsSL https://get.docker.com | sh

# Thêm user hiện tại vào group docker (tránh phải dùng sudo mỗi lần)
sudo usermod -aG docker $USER

# Đăng xuất rồi đăng nhập lại để áp dụng group
exit
```

Kiểm tra Docker đã cài thành công:

```bash
docker --version
docker compose version
```

---

## Bước 2 — Clone repository

```bash
# Clone code về VPS
git clone https://github.com/<your-username>/<your-repo>.git hrm
cd hrm
```

> Nếu repo private, cần dùng Personal Access Token của GitHub:
> `git clone https://<token>@github.com/<username>/<repo>.git hrm`

---

## Bước 3 — Tạo file `.env`

```bash
cp .env.example .env
nano .env
```

Điền các thông tin sau vào `.env`:

```
# Tạo SECRET_KEY mới bằng lệnh này (chạy trên máy bất kỳ có Python):
# python3 -c "import secrets; print(secrets.token_urlsafe(50))"
SECRET_KEY=<key-mới-tạo-ở-trên>

DEBUG=False

# Thay <IP-VPS> bằng IP thật của VPS
ALLOWED_HOSTS=<IP-VPS>,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://<IP-VPS>

# Đặt mật khẩu mạnh cho PostgreSQL
DATABASE_URL=postgresql://postgres:<mat-khau-db>@db:5432/hrm_db
DB_PASSWORD=<mat-khau-db>

# Celery dùng Redis (giữ nguyên)
CELERY_BROKER_URL=redis://redis:6379/0

DJANGO_LOG_LEVEL=WARNING
```

> **Lưu ý bảo mật:** File `.env` chứa thông tin nhạy cảm, KHÔNG bao giờ commit lên Git.

---

## Bước 4 — Build và khởi động containers

```bash
# Build image và chạy tất cả services ở background
docker compose up --build -d

# Theo dõi log của web service cho đến khi healthy
docker compose logs -f web
```

Chờ đến khi thấy dòng:
```
web  | [INFO] Booting worker with pid: ...
```

Kiểm tra tất cả containers đang chạy:

```bash
docker compose ps
```

Kết quả mong đợi — tất cả STATUS là `running` hoặc `healthy`:
```
NAME              STATUS
hrm-db-1          running (healthy)
hrm-redis-1       running (healthy)
hrm-web-1         running (healthy)
hrm-celery-1      running
hrm-celery-beat-1 running
hrm-nginx-1       running
```

---

## Bước 5 — Tạo tài khoản admin

```bash
docker compose exec web python manage.py createsuperuser
```

Nhập username, email, password khi được hỏi.

---

## Bước 6 — Kiểm tra hoạt động

```bash
# Kiểm tra API health
curl http://<IP-VPS>/api/health/
# Kết quả mong đợi: {"status": "ok"}
```

Mở trình duyệt: `http://<IP-VPS>/`

---

## Cập nhật code sau này

Khi có code mới trên GitHub:

```bash
cd hrm

# Pull code mới
git pull

# Rebuild và restart (downtime ~10-30 giây)
docker compose up --build -d

# Theo dõi quá trình restart
docker compose logs -f web
```

---

## Các lệnh quản lý thường dùng

```bash
# Xem log tất cả services
docker compose logs -f

# Xem log một service cụ thể
docker compose logs -f web
docker compose logs -f celery

# Restart một service
docker compose restart web
docker compose restart nginx

# Dừng tất cả
docker compose down

# Dừng và xóa volumes (CẨN THẬN: mất data database!)
docker compose down -v

# Chạy Django management command
docker compose exec web python manage.py <lệnh>

# Backup database
docker compose exec db pg_dump -U postgres hrm_db > backup_$(date +%Y%m%d).sql

# Restore database
docker compose exec -T db psql -U postgres hrm_db < backup_YYYYMMDD.sql
```

---

## Xử lý sự cố

### Container web không healthy

```bash
docker compose logs web
# Kiểm tra lỗi migration hoặc settings
```

### Lỗi 502 Bad Gateway từ Nginx

```bash
docker compose ps          # Kiểm tra web có running không
docker compose logs nginx  # Xem log nginx
```

### Lỗi permission media/static

```bash
docker compose exec web chown -R www-data:www-data /app/media /app/staticfiles
```
