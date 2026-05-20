# CLAUDE.md — myproject / HRM App

## Tổng quan dự án

Django 6.0.5, Python 3.14. Database: **PostgreSQL** (local, port 5432).

```bash
python manage.py runserver  # http://127.0.0.1:8000/
```

**9 app chính:**
| App | Chức năng | Namespace URL |
|---|---|---|
| `core` | Nền tảng: BaseModel abstract, Notification, CurrentUserMiddleware | — |
| `departments` | Phòng ban & Nhóm bộ phận (Department, EmployeeGroup) | — |
| `employees` | Quản lý nhân viên, dashboard, import/export | — |
| `contracts` | Hợp đồng lao động | `contracts` |
| `system_settings` | Tài khoản, phân quyền, phòng ban, toggle app | `system_settings` |
| `talent` | Tuyển dụng & Đào tạo | `talent` |
| `attendance` | Chấm công & Nghỉ phép | `attendance` |
| `payroll` | Bảng lương, tính thuế TNCN, BHXH | `payroll` |
| `api` | REST API (DRF) — Employees, Attendance, Payroll | — |

---

## Cấu trúc thư mục

```
myproject/
├── myproject/          # settings.py, urls.py, celery.py
├── core/               # models.py (BaseModel, Notification), middleware.py, tasks.py, context_processors.py
├── departments/        # models.py (Department, EmployeeGroup), serializers.py, migrations/
├── employees/          # models.py, views.py, helpers.py, forms.py, signals.py, serializers.py
├── contracts/          # models.py, views.py, forms.py, urls.py
├── system_settings/    # models.py (AppStatus), views.py, urls.py
├── talent/             # models.py (8 models), views.py (37+ views), urls.py
│   └── management/commands/seed_talent.py
├── attendance/         # models.py (8 models), views.py (28 views), forms.py, serializers.py
├── payroll/            # models.py (7 models), views.py, urls.py, serializers.py
│   └── management/commands/seed_payroll_config.py
└── api/                # views.py (7 ViewSets), urls.py, permissions.py
```

---

## Models

### departments/models.py

**Department** — Phòng ban. `name` (unique). Bảng: `departments_department`.

**EmployeeGroup** — Nhóm bộ phận để phân quyền. ManyToMany với Department. Bảng: `departments_employeegroup`.

Import: `from departments.models import Department, EmployeeGroup`

### employees/models.py

**Employee** — Model nhân viên chính.

| Trường | Mô tả |
|---|---|
| `user` | FK → User (OneToOne nullable) — liên kết tài khoản đăng nhập |
| `employee_code` | Mã NV (unique, auto-uppercase, auto-gen NV-YY#### nếu trống) |
| `status` | 8 loại trạng thái |
| `department` | FK → Department (PROTECT) |
| `termination_date/reason` | Khi `status = nghi_viec` |
| `scheduled_termination_date` | Lên lịch tự chuyển `nghi_viec` |
| `status_start_date/end_date` | Dùng cho LEAVE_STATUSES + DATE_STATUSES |
| `status_note` | Chỉ dùng cho LEAVE_STATUSES |

**8 trạng thái:** `dang_lam`, `thu_viec`, `thuc_tap_sinh`, `nghi_phep`, `nghi_sinh`, `nghi_khong_luong`, `nghi_om`, `nghi_viec`

**LEAVE_STATUSES** (có start/end + note): `nghi_phep`, `nghi_sinh`, `nghi_khong_luong`, `nghi_om`

**DATE_STATUSES** (có start/end, không note, bắt buộc): `thu_viec`, `thuc_tap_sinh`

**Properties:** `is_active`, `days_until_status_end`, `status_expiring_soon`, `days_until_termination`

**UserProfile** (1-1 với User) — Quyền cá nhân: `app_employees`, `app_contracts`, `app_attendance`, `app_payroll`, `app_talent`, `can_export`, `can_import`, `can_view_dashboard`

**UserGroupPermission** — Quyền UserProfile trên từng EmployeeGroup: `can_add`, `can_edit`, `can_delete`

**StaffGroup** — Nhóm user, cùng bộ quyền như UserProfile. `members` ManyToMany với User.

**StaffGroupDeptPerm** — Quyền StaffGroup trên từng EmployeeGroup: `can_add`, `can_edit`, `can_delete`

**ActivityLog** — Log hành động: user, action, target_type, target_name, detail, ip, created_at

**StatusLog** — Lịch sử thay đổi trạng thái Employee.

### system_settings/models.py

**AppStatus** — Singleton (pk=1), dùng `AppStatus.get()`. Toggle kích hoạt app:
- `app_contracts_active`, `app_attendance_active`, `app_payroll_active`, `app_talent_active`

### talent/models.py (8 models)

Tuyển dụng: `JobPosition`, `Applicant` (6 stage: new/screening/interview/offer/hired/rejected), `Interview`, `JobOffer`

Đào tạo: `TrainingCourse`, `TrainingSession`, `TrainingEnrollment`, `TrainingCertificate` (tự tạo khi result='pass')

`Applicant.converted_employee` → FK nullable → Employee

### attendance/models.py (8 models)

Chấm công: `WorkShift`, `PublicHoliday`, `AttendanceRecord` (6 status, tự tính actual_hours/ot_hours trong save())

Nghỉ phép: `LeaveType`, `LeavePolicy` (12 ngày + 1/5 năm thâm niên), `LeaveBalance` (allocated/used/pending/carried, property `remaining_days`), `LeaveRequest` (tự tính total_days bỏ qua weekend+lễ), `LeaveApproval`

### payroll/models.py (7 models)

**PayrollConfig** — Singleton (pk=1), dùng `PayrollConfig.get()`. Fallback khi không có InsuranceConfig theo năm.

**InsuranceConfig** — Cấu hình BHXH/BHYT/BHTN theo năm (unique: year). Gồm tỷ lệ NV + chủ, `salary_cap`, `personal_deduction`, `dependent_deduction`.

**PITBracket** — Bậc thuế TNCN theo năm. `unique_together = (year, order)`.

**SalaryConfig** — Cấu hình lương riêng từng NV. Ưu tiên hơn Contract khi `is_active=True`. Có `basic_salary`, `allowances` JSONField, `dependents`, `effective_from/to`. Property `gross_salary`.

**OTRecord** — Bản ghi tăng ca cần duyệt. Status: `pending` → `approved`/`rejected`. Auto-fill `multiplier` từ `ot_type` trong `save()`. OT approved mới được tính vào lương.

**Payslip** — Phiếu lương tháng. `unique_together = (employee, month, year)`.

| Field | Mô tả |
|---|---|
| `employee`, `contract` | FK → Employee / Contract |
| `month`, `year` | Kỳ lương |
| `basic_salary`, `allowances_detail` | Snapshot (từ SalaryConfig ưu tiên, fallback Contract) |
| `ot_hours`, `ot_pay` | Từ OTRecord approved (fallback AttendanceRecord) |
| `gross_salary` | basic + allowances + OT + other_additions |
| `bhxh/bhyt/bhtn_amount`, `total_insurance` | Tính theo InsuranceConfig (có salary_cap), fallback PayrollConfig |
| `dependents`, `taxable_income`, `pit_amount` | Thuế TNCN theo PITBracket DB (fallback hardcoded) |
| `net_salary` | gross - insurance - PIT - other_deductions |
| `status` | `draft` / `confirmed` |

**Method `payslip.calculate(config=None, insurance_config=None)`** — tính lại toàn bộ, gọi trước `save()`.

**Method `payslip.generate_lines()`** — tạo PayslipLine chi tiết, gọi SAU `save()`.

**Hàm `_calculate_pit(taxable_income, year=None)`** — ưu tiên PITBracket DB; fallback hardcoded.

**PayslipLine** — Dòng chi tiết phiếu lương. FK → Payslip. `category`: `earning`/`deduction`/`tax`.

---

## Hệ thống phân quyền

**Logic OR**: quyền cuối = quyền cá nhân (UserProfile) OR quyền từ tất cả StaffGroup.

**`employees/helpers.py`** — 5 hàm dùng chung trong tất cả app:
```python
get_allowed_departments(user)  # → QuerySet Department user được xem
get_user_perms(user)           # → {'can_add', 'editable_depts', 'deletable_depts'}
get_user_features(user)        # → {'app_employees', 'can_export', ...}
_get_client_ip(request)        # → IP string
log_activity(user, action, target_type, target_name, detail, ip)
```

Import trong app khác: `from employees.helpers import get_user_features, log_activity, _get_client_ip`

- Superuser bypass tất cả quyền — luôn check `request.user.is_superuser` trước.
- `editable_depts = None` → được sửa tất cả. `editable_depts` là **set of department names**.

**`api/permissions.py`** — 3 DRF permission class (tái dùng helpers):
- `HasEmployeesAppPermission` — check `app_employees` + object-level (editable/deletable_depts)
- `HasAttendanceAppPermission` — check `app_attendance`
- `HasPayrollAppPermission` — check `app_payroll`

---

## URLs — Web (Template Views)

### Global (myproject/urls.py)
`/` → home | `/login/` | `/logout/`

### /employees/ — employees/urls.py

| URL | Tên |
|---|---|
| `/employees/` | `employee_list` |
| `/employees/create/` | `employee_create` |
| `/employees/<pk>/` | `employee_detail` |
| `/employees/edit/<pk>/` | `employee_update` |
| `/employees/delete/<pk>/` | `employee_delete` |
| `/employees/terminate/<pk>/` | `employee_terminate` |
| `/employees/reactivate/<pk>/` | `employee_reactivate` |
| `/employees/change-status/<pk>/` | `employee_change_status` |
| `/employees/export/csv/` | `export_csv` |
| `/employees/export/excel/` | `export_excel` |
| `/employees/import/` | `import_excel` |
| `/employees/import/template/` | `download_import_template` |
| `/employees/check-code/` | `check_employee_code` (AJAX) |
| `/employees/dashboard/` | `dashboard` |
| `/employees/dashboard/export-status/` | `export_status_excel` |
| `/employees/change-password/` | `change_password` |

### /settings/ — system_settings/urls.py (namespace `system_settings`)

| URL | Tên |
|---|---|
| `/settings/` | `settings_home` |
| `/settings/departments/` | `department_manage` |
| `/settings/departments/edit/<pk>/` | `department_update` |
| `/settings/departments/delete/<pk>/` | `department_delete` |
| `/settings/employee-groups/` | `group_list` |
| `/settings/employee-groups/create/` | `group_create` |
| `/settings/employee-groups/edit/<pk>/` | `group_update` |
| `/settings/employee-groups/delete/<pk>/` | `group_delete` |
| `/settings/users/` | `user_list` |
| `/settings/users/create/` | `user_create` |
| `/settings/users/delete/<pk>/` | `user_delete` |
| `/settings/users/<pk>/reset-password/` | `admin_reset_password` |
| `/settings/users/<pk>/link-employee/` | `user_link_employee` (AJAX POST) |
| `/settings/staff-groups/create/` | `staff_group_create` |
| `/settings/staff-groups/<pk>/edit/` | `staff_group_update` |
| `/settings/staff-groups/<pk>/delete/` | `staff_group_delete` |
| `/settings/permissions/` | `permission_manage` |
| `/settings/activity-log/` | `activity_log` |
| `/settings/toggle-app/<app_name>/` | `toggle_app` |

### /contracts/ — contracts/urls.py (namespace `contracts`)

| URL | Tên |
|---|---|
| `/contracts/` | `contract_list` |
| `/contracts/create/` | `contract_create` |
| `/contracts/<pk>/` | `contract_detail` |
| `/contracts/<pk>/edit/` | `contract_update` |
| `/contracts/<pk>/delete/` | `contract_delete` |
| `/contracts/<pk>/renew/` | `contract_renew` |
| `/contracts/<pk>/terminate/` | `contract_terminate` |
| `/contracts/<pk>/print/` | `contract_print` |
| `/contracts/dashboard/` | `contract_dashboard` |
| `/contracts/dashboard/export/excel/` | `contract_dashboard_export_excel` |
| `/contracts/export/excel/` | `contract_export_excel` |

### /talent/ — talent/urls.py (namespace `talent`)

| URL | Tên |
|---|---|
| `/talent/` | `talent_home` |
| `/talent/jobs/` | `job_list` |
| `/talent/jobs/create/` | `job_create` |
| `/talent/jobs/<pk>/` | `job_detail` |
| `/talent/jobs/<pk>/edit/` | `job_update` |
| `/talent/jobs/<pk>/delete/` | `job_delete` |
| `/talent/applicants/` | `applicant_list` |
| `/talent/applicants/create/` | `applicant_create` |
| `/talent/applicants/generate-code/` | `generate_employee_code` (AJAX) |
| `/talent/applicants/<pk>/` | `applicant_detail` |
| `/talent/applicants/<pk>/edit/` | `applicant_update` |
| `/talent/applicants/<pk>/delete/` | `applicant_delete` |
| `/talent/applicants/<pk>/change-stage/` | `applicant_change_stage` |
| `/talent/applicants/<pk>/convert/` | `applicant_convert` |
| `/talent/applicants/kanban/` | `applicant_kanban` |
| `/talent/interviews/create/` | `interview_create` |
| `/talent/interviews/<pk>/delete/` | `interview_delete` |
| `/talent/offers/create/` | `offer_create` |
| `/talent/offers/<pk>/edit/` | `offer_update` |
| `/talent/recruitment-dashboard/` | `recruitment_dashboard` |
| `/talent/courses/` | `course_list` |
| `/talent/courses/create/` | `course_create` |
| `/talent/courses/<pk>/` | `course_detail` |
| `/talent/courses/<pk>/edit/` | `course_update` |
| `/talent/courses/<pk>/delete/` | `course_delete` |
| `/talent/sessions/` | `session_list` |
| `/talent/sessions/create/` | `session_create` |
| `/talent/sessions/<pk>/` | `session_detail` |
| `/talent/sessions/<pk>/edit/` | `session_update` |
| `/talent/sessions/<pk>/delete/` | `session_delete` |
| `/talent/sessions/<pk>/bulk-score/` | `bulk_score_update` |
| `/talent/enrollments/create/` | `enrollment_create` |
| `/talent/certificates/` | `certificate_list` |
| `/talent/certificates/<pk>/` | `certificate_detail` |
| `/talent/certificates/<pk>/print/` | `certificate_print` |
| `/talent/training-dashboard/` | `training_dashboard` |

### /attendance/ — attendance/urls.py (namespace `attendance`)

| URL | Tên |
|---|---|
| `/attendance/` | `attendance_home` |
| `/attendance/records/` | `attendance_list` |
| `/attendance/records/create/` | `attendance_create` |
| `/attendance/records/<pk>/edit/` | `attendance_update` |
| `/attendance/records/<pk>/delete/` | `attendance_delete` |
| `/attendance/records/import/` | `attendance_import` |
| `/attendance/dashboard/` | `attendance_dashboard` |
| `/attendance/shifts/` | `shift_list` |
| `/attendance/shifts/create/` | `shift_create` |
| `/attendance/shifts/<pk>/edit/` | `shift_update` |
| `/attendance/shifts/<pk>/delete/` | `shift_delete` |
| `/attendance/holidays/` | `holiday_manage` |
| `/attendance/leave-types/` | `leave_type_list` |
| `/attendance/leave-types/create/` | `leave_type_create` |
| `/attendance/leave-types/<pk>/edit/` | `leave_type_update` |
| `/attendance/leave-types/<pk>/delete/` | `leave_type_delete` |
| `/attendance/policy/` | `leave_policy_update` |
| `/attendance/balance/` | `leave_balance_list` |
| `/attendance/balance/create/` | `leave_balance_create` |
| `/attendance/balance/init/` | `leave_balance_init` |
| `/attendance/leaves/` | `leave_request_list` |
| `/attendance/leaves/create/` | `leave_request_create` |
| `/attendance/leaves/<pk>/` | `leave_request_detail` |
| `/attendance/leaves/<pk>/cancel/` | `leave_request_cancel` |
| `/attendance/leaves/<pk>/approve/` | `leave_approve` |
| `/attendance/leaves/<pk>/reject/` | `leave_reject` |

### /payroll/ — payroll/urls.py (namespace `payroll`)

| URL | Tên |
|---|---|
| `/payroll/` | `payslip_list` |
| `/payroll/bulk-create/` | `payslip_bulk_create` |
| `/payroll/<pk>/` | `payslip_detail` |
| `/payroll/<pk>/edit/` | `payslip_update` |
| `/payroll/<pk>/delete/` | `payslip_delete` |
| `/payroll/<pk>/print/` | `payslip_print` |
| `/payroll/config/` | `payroll_config` |
| `/payroll/insurance/` | `insurance_config_list` |
| `/payroll/insurance/create/` | `insurance_config_create` |
| `/payroll/insurance/<pk>/delete/` | `insurance_config_delete` |
| `/payroll/salary-config/` | `salary_config_list` |
| `/payroll/salary-config/create/` | `salary_config_create` |
| `/payroll/salary-config/<pk>/edit/` | `salary_config_update` |
| `/payroll/salary-config/<pk>/delete/` | `salary_config_delete` |
| `/payroll/ot/` | `ot_list` |
| `/payroll/ot/create/` | `ot_create` |
| `/payroll/ot/<pk>/approve/` | `ot_approve` |
| `/payroll/ot/<pk>/reject/` | `ot_reject` |
| `/payroll/ot/<pk>/delete/` | `ot_delete` |

---

## URLs — REST API (`/api/`)

**Authentication:** `Authorization: Token <token>` hoặc Session.
Lấy token: `POST /api/token/` với body `{"username": "...", "password": "..."}`.
Swagger UI: `/api/docs/` | OpenAPI schema: `/api/schema/`

**Serializers:**
- `departments/serializers.py` — `DepartmentSerializer`
- `employees/serializers.py` — `EmployeeSerializer`
- `attendance/serializers.py` — `LeaveTypeSerializer`, `AttendanceRecordSerializer`, `LeaveRequestSerializer`
- `payroll/serializers.py` — `PayslipSerializer`, `PayslipLineSerializer`, `OTRecordSerializer`

| URL | Method | Chức năng |
|---|---|---|
| `/api/token/` | POST | Lấy auth token |
| `/api/health/` | GET | Health check (không cần login) |
| `/api/employees/` | GET, POST | Danh sách + tạo nhân viên |
| `/api/employees/{id}/` | GET, PUT, PATCH, DELETE | Chi tiết nhân viên |
| `/api/departments/` | GET, POST | Danh sách + tạo phòng ban |
| `/api/departments/{id}/` | GET, PUT, PATCH, DELETE | Chi tiết phòng ban |
| `/api/attendance/records/` | GET, POST | Bản ghi chấm công |
| `/api/attendance/records/{id}/` | GET, PUT, PATCH, DELETE | Chi tiết chấm công |
| `/api/attendance/leave-requests/` | GET, POST | Đơn xin nghỉ |
| `/api/attendance/leave-requests/{id}/` | GET, PUT, PATCH, DELETE | Chi tiết đơn nghỉ |
| `/api/attendance/leave-requests/{id}/approve/` | POST | Duyệt đơn (2 cấp) |
| `/api/attendance/leave-requests/{id}/reject/` | POST | Từ chối đơn |
| `/api/attendance/leave-types/` | GET | Danh sách loại nghỉ (read-only) |
| `/api/payroll/payslips/` | GET, POST | Danh sách + tạo phiếu lương (auto calculate) |
| `/api/payroll/payslips/{id}/` | GET, PUT, PATCH, DELETE | Chi tiết phiếu lương |
| `/api/payroll/payslips/{id}/recalculate/` | POST | Tính lại phiếu lương (chỉ draft) |
| `/api/payroll/payslips/{id}/confirm/` | POST | Xác nhận phiếu lương |
| `/api/payroll/ot-records/` | GET, POST | Danh sách + tạo bản ghi OT |
| `/api/payroll/ot-records/{id}/` | GET, PUT, PATCH, DELETE | Chi tiết OT |
| `/api/payroll/ot-records/{id}/approve/` | POST | Duyệt OT |
| `/api/payroll/ot-records/{id}/reject/` | POST | Từ chối OT |

**Query params chung:** `?search=` (tìm tên/mã) | `?ordering=` (sắp xếp)

**Query params theo endpoint:**
- employees: `?status=dang_lam` | `?status=all` | `?department=3`
- attendance/records: `?employee=3` | `?date=2026-05-20` | `?month=5&year=2026` | `?status=present`
- attendance/leave-requests: `?status=pending` | `?employee=3` | `?year=2026`
- payroll/payslips: `?month=5&year=2026` | `?employee=3` | `?status=draft`
- payroll/ot-records: `?employee=3` | `?month=5&year=2026` | `?status=pending`

---

## Quy ước code

### Web Views
- Mọi view: `@login_required`. Luôn check `request.user.is_superuser` trước.
- `employee_code` lưu UPPERCASE (`EmployeeForm.clean_employee_code`).
- `department` là FK — filter bằng `department__in=` hoặc `department__name=`. Không dùng chuỗi thô.
- `select_related('department')` khi loop qua Employee (tránh N+1).
- Ngày trong template: `|date:"d/m/Y"`. Khi `.values('department__name')`: dùng `{{ d.department__name }}`.
- `auto_terminate_employees()` gọi ở đầu `employee_list` — chuyển NV đến `scheduled_termination_date`.
- Sort/pagination: dùng `base_filter_qs` — `request.GET.copy()` bỏ sort/order/page → `.urlencode()`.
- `log_activity()` sau mỗi thao tác ghi dữ liệu quan trọng.
- `paginator.count` thay vì `.count()` thủ công (tránh query thừa).
- Status filter mặc định `'active'` → ẩn `nghi_viec`, không phải chỉ `dang_lam`.

### REST API
- Permission class trong `api/permissions.py` — tái dùng `get_user_features` + `get_user_perms`.
- Các trường tính toán tự động (ot_hours, gross_salary, pit_amount...) là `read_only` trong serializer.
- Custom actions (`approve`, `reject`, `confirm`, `recalculate`) dùng `@action(detail=True, methods=['post'])`.
- `perform_create()` trong ViewSet để inject logic trước khi save (vd: `payslip.calculate()`).

### Chung
- **Thêm quyền mới**: cập nhật `UserProfile`, `StaffGroup`, `get_user_features()`, tạo migration.
- **Thêm trạng thái mới**: cập nhật `STATUS_CHOICES`, `DASH_STATUS_COLORS`, `EXCEL_STATUS_COLORS`.
- **Sau mỗi tính năng**: cập nhật CLAUDE.md.
- Windows: dùng `python -X utf8` khi chạy lệnh có output tiếng Việt (tránh UnicodeEncodeError).

---

## Dependencies

```
django>=6.0  openpyxl  Pillow  psycopg2-binary  dj-database-url  python-decouple
celery[redis]  django-celery-beat  django-celery-results  sqlalchemy
djangorestframework  drf-spectacular  gunicorn  redis
```

```python
# settings.py
DATABASES = {'default': dj_database_url.config(default=config('DATABASE_URL'), conn_max_age=600)}
SESSION_COOKIE_AGE = 900   # auto-logout 15 phút
SESSION_SAVE_EVERY_REQUEST = True
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['TokenAuthentication', 'SessionAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['IsAuthenticated'],
    'DEFAULT_PAGINATION_CLASS': 'PageNumberPagination',
    'PAGE_SIZE': 50,
}
# Celery — Redis broker (Docker), hoặc filesystem (dev local qua .env)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
STATIC_ROOT = BASE_DIR / 'staticfiles'     # collectstatic dùng cho production
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')
```

`.env` (Docker): `DATABASE_URL=postgresql://postgres:PASSWORD@db:5432/hrm_db`
`.env` (Local dev): `DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/hrm_db`

**Chạy Celery local (2 terminal riêng, thêm `-X utf8` nếu cần):**
```bash
celery -A myproject worker --pool=solo -l info          # Terminal 1 — Worker
celery -A myproject beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler  # Terminal 2 — Beat
```

---

## Docker (Phase 6)

**Cấu trúc files Docker:**
```
myproject/
├── Dockerfile               # Build image Django
├── docker-compose.yml       # 5 services: nginx, web, db, redis, celery
├── entrypoint.sh            # migrate → collectstatic → gunicorn
├── .env                     # Biến môi trường (KHÔNG commit lên git)
├── .env.example             # Template (commit lên git)
├── .dockerignore            # Files loại khỏi Docker build
└── nginx/
    └── nginx.conf           # Reverse proxy, serve static/media
```

**5 Docker services:**
| Service | Image | Vai trò |
|---|---|---|
| `nginx` | nginx:alpine | Reverse proxy, port 80 |
| `web` | build . | Django + Gunicorn, port 8000 (internal) |
| `db` | postgres:16-alpine | PostgreSQL, volume `postgres_data` |
| `redis` | redis:7-alpine | Celery broker |
| `celery` | build . | Worker + Beat (2 command khác nhau) |

**Lệnh Docker thường dùng:**
```bash
docker-compose up --build        # Build và chạy lần đầu
docker-compose up -d             # Chạy nền (detach)
docker-compose down              # Dừng và xóa containers
docker-compose logs -f web       # Xem logs service web
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell
```

**Chú ý khi chuyển đổi Local ↔ Docker:**
- Local: `DATABASE_URL` dùng `localhost`, `CELERY_BROKER_URL=filesystem://`, `DEBUG=True`
- Docker: `DATABASE_URL` dùng `db` (tên service), `CELERY_BROKER_URL=redis://redis:6379/0`, `DEBUG=False`

---

## Lịch sử phiên bản

| Version | Tính năng chính |
|---|---|
| v1–v5 | Department FK, cảnh báo trạng thái, thử việc, thực tập sinh |
| v6–v10 | Sort, bulk actions, scheduled termination, dashboard, phân trang |
| v11–v15 | Nhóm bộ phận, activity log, PostgreSQL, dashboard Tab 2, filter URL |
| v16–v20 | App Contracts: CRUD, upload, bản in, dashboard export, form tìm kiếm NV |
| v21–v23 | App system_settings, AppStatus singleton, auto-logout 15 phút |
| v24–v25 | App Talent: 7 models, 37 views, bulk ops, PDF chứng chỉ, Kanban |
| v26 | App Attendance: 8 models, 28 views, duyệt nghỉ phép 2 cấp |
| v27–v29 | seed_talent, đổi tên Kanban, bán tự động hired → nhân viên |
| v30 | Tách Department + EmployeeGroup ra app `departments` riêng |
| v31 | Liên kết User ↔ Employee: OneToOneField, AJAX link/unlink |
| v32 | Phase 1 — core app (BaseModel, Notification, Middleware), auto-gen employee_code, Contract+AttendanceRecord thêm OT fields |
| v33–v34 | Phase 2 — App Payroll đầy đủ: 7 models (InsuranceConfig, PITBracket, SalaryConfig, OTRecord, Payslip, PayslipLine), calculate()+generate_lines() |
| v35 | Phase 3 — Celery filesystem broker, 3 periodic tasks, signals, Notification UI |
| v36 | Phase 4 — Analytics: Tab "Phân tích nâng cao" cho Employees/Attendance/Talent (Chart.js 4.4.0) |
| v37 | Phase 5 — DRF Setup: djangorestframework 3.17 + drf-spectacular, Token auth, app `api/`, Swagger UI /api/docs/ |
| v38 | Employees API: DepartmentViewSet + EmployeeViewSet (CRUD), HasEmployeesAppPermission |
| v39 | Attendance API: AttendanceRecordViewSet + LeaveRequestViewSet (approve/reject 2 cấp) + LeaveTypeViewSet |
| v40 | Payroll API: PayslipViewSet (recalculate + confirm) + OTRecordViewSet (approve/reject), auto calculate() khi POST |
| v41 | Phase 6 — Docker: Dockerfile, docker-compose.yml (5 services), Nginx, Gunicorn, Redis broker, STATIC_ROOT, ALLOWED_HOSTS từ env |
