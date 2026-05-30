---
name: check-celery
description: Kiểm tra và debug Celery tasks trong HRM project (check_offer_expiry, check_certificate_expiry, sync_training_plan_status)
---

Kiểm tra trạng thái Celery và debug tasks. Báo cáo bằng tiếng Việt.

## Celery tasks trong HRM

| Task | Lịch chạy | File |
|------|----------|------|
| `check_offer_expiry` | Hàng ngày 8:30 | `talent/tasks.py` |
| `check_certificate_expiry` | Hàng ngày 8:35 | `talent/tasks.py` |
| `sync_training_plan_status` | Thứ Hai 9:00 | `talent/tasks.py` |

## Chạy Celery trên local (2 terminal riêng biệt)

**Terminal 1 — Worker:**
```bash
celery -A myproject worker --pool=solo -l info
```

**Terminal 2 — Beat (scheduler):**
```bash
celery -A myproject beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Chạy task thủ công để test

```bash
python -X utf8 manage.py shell -c "
from talent.tasks import check_offer_expiry, check_certificate_expiry, sync_training_plan_status

# Chạy ngay lập tức (không qua Celery queue)
print('=== check_offer_expiry ===')
result = check_offer_expiry()
print('Kết quả:', result)

print('=== check_certificate_expiry ===')
result = check_certificate_expiry()
print('Kết quả:', result)

print('=== sync_training_plan_status ===')
result = sync_training_plan_status()
print('Kết quả:', result)
"
```

## Kiểm tra lịch task trong DB

```bash
python -X utf8 manage.py shell -c "
from django_celery_beat.models import PeriodicTask
tasks = PeriodicTask.objects.all()
for t in tasks:
    print(f'{t.name}: {t.crontab or t.interval} | enabled={t.enabled} | last_run={t.last_run_at}')
"
```

## Kiểm tra kết quả task đã chạy

```bash
python -X utf8 manage.py shell -c "
from django_celery_results.models import TaskResult
# Xem 10 task gần nhất
results = TaskResult.objects.order_by('-date_done')[:10]
for r in results:
    print(f'{r.task_name} | {r.status} | {r.date_done} | {r.result[:100] if r.result else \"-\"}')
"
```

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Fix |
|-----|------------|-----|
| `Connection refused` | Redis chưa chạy | Khởi động Redis hoặc `docker compose up redis` |
| Task không chạy theo lịch | Beat chưa chạy | Mở terminal 2 chạy celery beat |
| `ProgrammingError` trong task | DB migration chưa apply | `python manage.py migrate` |
| Task chạy xong không có kết quả | `CELERY_RESULT_BACKEND` chưa cấu hình | Kiểm tra settings.py |

## Trong Docker

```bash
# Xem log celery worker
docker compose logs -f celery

# Xem log celery beat
docker compose logs -f celery-beat

# Restart celery
docker compose restart celery celery-beat
```
