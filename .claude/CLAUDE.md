# CLAUDE.md — HRM App

## Stack & Khởi động

- **Django 6.0.5 / Python 3.14 / PostgreSQL** (local port 5432)
- `python manage.py runserver` → http://127.0.0.1:8000/
- Windows + tiếng Việt: dùng `python -X utf8 manage.py ...`

## 9 App

| App | Chức năng | URL namespace |
|---|---|---|
| `core` | BaseModel, Notification, CurrentUserMiddleware | — |
| `departments` | Department, EmployeeGroup | — |
| `employees` | Nhân viên, dashboard, import/export | — |
| `contracts` | Hợp đồng lao động | `contracts` |
| `system_settings` | Tài khoản, phân quyền, toggle app | `system_settings` |
| `talent` | Tuyển dụng & Đào tạo (11 models) | `talent` |
| `attendance` | Chấm công & Nghỉ phép (8 models) | `attendance` |
| `payroll` | Bảng lương, thuế TNCN, BHXH (7 models) | `payroll` |
| `api` | REST API — 7 ViewSets (DRF) | — |

---

## Models — Hành vi quan trọng (không hiển nhiên từ code)

### employees/models.py

**Employee**
- `employee_code`: auto-uppercase, auto-gen `NV-YY####` nếu để trống
- `status` (8 loại): `dang_lam` `thu_viec` `thuc_tap_sinh` `nghi_phep` `nghi_sinh` `nghi_khong_luong` `nghi_om` `nghi_viec`
- **LEAVE_STATUSES** (`nghi_phep/sinh/khong_luong/om`): có `status_start_date`, `status_end_date`, `status_note`
- **DATE_STATUSES** (`thu_viec/thuc_tap_sinh`): có start/end, không note, bắt buộc nhập
- `scheduled_termination_date`: lên lịch tự chuyển sang `nghi_viec`
- Properties: `is_active`, `days_until_status_end`, `status_expiring_soon`, `days_until_termination`

**UserProfile** (1-1 User) — quyền cá nhân:
`app_employees` `app_contracts` `app_attendance` `app_payroll` `app_talent` `can_export` `can_import` `can_view_dashboard`

**StaffGroup** — nhóm quyền, bộ field giống UserProfile. `members` ManyToMany → User.
**UserGroupPermission / StaffGroupDeptPerm** — `can_add` `can_edit` `can_delete` trên EmployeeGroup.

### system_settings/models.py
**AppStatus** — Singleton `pk=1`, dùng `AppStatus.get()`.
Toggle: `app_contracts_active` `app_attendance_active` `app_payroll_active` `app_talent_active`

### talent/models.py

**Tuyển dụng:**
- `Applicant`: 6 stage (`new/screening/interview/offer/hired/rejected`). `hired_at` tự set khi stage→hired.
- `Interview`: `average_score` là property tính từ 3 điểm kỹ năng (1–5).
- `ApplicantStageHistory`: audit trail tự động khi đổi stage.

**Đào tạo:**
- `TrainingEnrollment.save()`: tự set `result='pass'/'fail'` và tạo `TrainingCertificate` khi pass.
- `TrainingCertificate`: số `CERT-YYYYMMDD-NNNN` đếm theo ngày.
- `EmployeeTrainingPlan`: `unique_together = (employee, course, year)`.

**Celery tasks** (`talent/tasks.py`):
`check_offer_expiry` (8:30) | `check_certificate_expiry` (8:35) | `sync_training_plan_status` (thứ Hai 9:00)

### attendance/models.py
- `AttendanceRecord.save()`: tự tính `actual_hours`, `ot_hours`.
- `LeavePolicy`: 12 ngày + 1 ngày/5 năm thâm niên.
- `LeaveRequest.save()`: tự tính `total_days` (bỏ qua weekend + ngày lễ).

### payroll/models.py
- **PayrollConfig** — Singleton `pk=1`, `PayrollConfig.get()`. Fallback khi không có InsuranceConfig.
- **SalaryConfig**: ưu tiên hơn Contract khi `is_active=True`. `allowances` là JSONField.
- **OTRecord.save()**: auto-fill `multiplier`.
- **Payslip**: `calculate()` gọi TRƯỚC `save()`, `generate_lines()` gọi SAU `save()`.
- `_calculate_pit(taxable_income, year)`: ưu tiên PITBracket DB, fallback hardcoded.

---

## Hệ thống phân quyền

**Logic OR**: quyền cuối = UserProfile **OR** bất kỳ StaffGroup nào của user.

**`employees/helpers.py`** — dùng chung toàn project:
```python
get_allowed_departments(user)  # QuerySet Department user được xem
get_user_perms(user)           # {'can_add', 'editable_depts', 'deletable_depts'}
get_user_features(user)        # {'app_employees', 'can_export', ...}
log_activity(user, action, target_type, target_name, detail, ip)
_get_client_ip(request)
```

- Superuser bypass tất cả — luôn check `is_superuser` TRƯỚC khi check quyền.
- `editable_depts = None` → được sửa tất cả phòng ban. Nếu là set → chỉ sửa phòng trong set.

**API permissions** (`api/permissions.py`): `HasEmployeesAppPermission`, `HasAttendanceAppPermission`, `HasPayrollAppPermission`

---

## Quy ước code

**Views:**
- Mọi view: `@login_required` + check `is_superuser` trước quyền.
- `select_related('department')` khi loop Employee (tránh N+1).
- `auto_terminate_employees()` gọi ở đầu `employee_list`.
- Pagination: `base_filter_qs = request.GET.copy()` bỏ sort/page → `.urlencode()`.
- `log_activity()` sau mỗi thao tác quan trọng.
- Status filter mặc định `'active'` → ẩn `nghi_viec`.
- Ngày trong template: `|date:"d/m/Y"`.

**REST API:**
- Permission class kế thừa `get_user_features` + `get_user_perms`.
- Trường tính toán tự động → `read_only=True` trong serializer.
- Custom action: `@action(detail=True, methods=['post'])`.

**Khi thêm tính năng:**
- **Quyền mới**: cập nhật `UserProfile` + `StaffGroup` + `get_user_features()` + migration.
- **Trạng thái mới**: cập nhật `STATUS_CHOICES`, `DASH_STATUS_COLORS`, `EXCEL_STATUS_COLORS`.
- **Sau mỗi tính năng**: cập nhật CLAUDE.md.

---

## URLs nhanh

**Web:** `/` | `/login/` | `/logout/` | `/employees/` | `/settings/` | `/contracts/` | `/talent/` | `/attendance/` | `/payroll/`

**API:** `POST /api/token/` | `GET /api/health/` | `/api/docs/` (Swagger)
Endpoints: `/api/employees/` `/api/departments/` `/api/attendance/records/` `/api/attendance/leave-requests/` `/api/attendance/leave-types/` `/api/payroll/payslips/` `/api/payroll/ot-records/`
Query: `?search=` `?ordering=` `?status=` `?employee=` `?month=&year=` `?department=`

---

## Settings quan trọng

```python
SESSION_COOKIE_AGE = 900        # auto-logout 15 phút
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'django-db'
REST_FRAMEWORK = {'PAGE_SIZE': 50}
```

**.env local:** `DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/hrm_db`
**.env Docker:** `DATABASE_URL=postgresql://postgres:PASSWORD@db:5432/hrm_db`

**Celery local (2 terminal):**
```bash
celery -A myproject worker --pool=solo -l info
celery -A myproject beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## Docker (xem DEPLOY.md để chi tiết)

6 services: `nginx` (port 80) · `web` · `db` · `redis` · `celery` · `celery-beat`

```bash
docker compose up --build -d    # build và chạy
docker compose logs -f web      # xem log
docker compose exec web python manage.py createsuperuser
docker compose down             # dừng (data còn trong volume)
```

---

## Phiên bản hiện tại — v45

| Nhóm | Trạng thái |
|---|---|
| Employees, Departments, Contracts | Hoàn chỉnh |
| system_settings (phân quyền, toggle app) | Hoàn chỉnh |
| Talent (tuyển dụng + đào tạo, 11 models) | Hoàn chỉnh, có approval workflow |
| Attendance (chấm công + nghỉ phép) | Hoàn chỉnh |
| Payroll (lương, thuế, BHXH) | Hoàn chỉnh |
| REST API (7 ViewSets, DRF, Swagger) | Hoàn chỉnh |
| Docker (6 services, Nginx, Gunicorn) | Hoàn chỉnh |
| Unit Tests | Chưa có |
