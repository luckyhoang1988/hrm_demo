# CLAUDE.md — myproject / HRM App

## Tổng quan dự án

Django 6.0.5, Python 3.14. Database: **PostgreSQL** (local, port 5432).

```bash
python manage.py runserver  # http://127.0.0.1:8000/
```

**9 app chính:**
| App | Chức năng | Namespace URL |
|---|---|---|
| `core` | BaseModel abstract, Notification, CurrentUserMiddleware | — |
| `departments` | Department, EmployeeGroup | — |
| `employees` | Nhân viên, dashboard, import/export | — |
| `contracts` | Hợp đồng lao động | `contracts` |
| `system_settings` | Tài khoản, phân quyền, toggle app | `system_settings` |
| `talent` | Tuyển dụng & Đào tạo (11 models) | `talent` |
| `attendance` | Chấm công & Nghỉ phép (8 models) | `attendance` |
| `payroll` | Bảng lương, thuế TNCN, BHXH (7 models) | `payroll` |
| `api` | REST API (DRF) — 7 ViewSets | — |

---

## Cấu trúc thư mục

```
myproject/
├── myproject/          # settings.py, urls.py, celery.py
├── core/               # models.py (BaseModel, Notification), middleware.py, tasks.py
├── departments/        # models.py (Department, EmployeeGroup), serializers.py
├── employees/          # models.py, views.py, helpers.py, forms.py, signals.py, serializers.py
├── contracts/          # models.py, views.py, forms.py, urls.py
├── system_settings/    # models.py (AppStatus), views.py, urls.py
├── talent/             # models.py (11 models), views.py, forms.py, urls.py, tasks.py
│   └── management/commands/seed_talent.py
├── attendance/         # models.py (8 models), views.py, forms.py, serializers.py
├── payroll/            # models.py (7 models), views.py, urls.py, serializers.py
│   └── management/commands/seed_payroll_config.py
└── api/                # views.py (7 ViewSets), urls.py, permissions.py
```

---

## Models

### departments/models.py

**Department** — `name` (unique). Bảng: `departments_department`.
**EmployeeGroup** — Nhóm phân quyền. ManyToMany với Department.
Import: `from departments.models import Department, EmployeeGroup`

### employees/models.py

**Employee** — Model nhân viên chính.

| Trường | Mô tả |
|---|---|
| `user` | OneToOne → User (nullable) — liên kết đăng nhập |
| `employee_code` | unique, auto-uppercase, auto-gen `NV-YY####` nếu trống |
| `status` | 8 loại trạng thái (xem bên dưới) |
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

**UserGroupPermission** — Quyền UserProfile trên EmployeeGroup: `can_add`, `can_edit`, `can_delete`
**StaffGroup** — Nhóm user, bộ quyền như UserProfile. `members` ManyToMany với User.
**StaffGroupDeptPerm** — Quyền StaffGroup trên EmployeeGroup: `can_add`, `can_edit`, `can_delete`
**ActivityLog** — Log hành động: user, action, target_type, target_name, detail, ip, created_at
**StatusLog** — Lịch sử thay đổi trạng thái Employee.

### system_settings/models.py

**AppStatus** — Singleton (pk=1), dùng `AppStatus.get()`. Toggle: `app_contracts_active`, `app_attendance_active`, `app_payroll_active`, `app_talent_active`

### talent/models.py (11 models)

**Tuyển dụng:**
- `JobPosition` — `priority` (low/normal/high/urgent), `status` (draft/open/interviewing/filled/cancelled)
- `Applicant` — 6 stage (new/screening/interview/offer/hired/rejected), `hired_at` tự set khi stage→hired, `converted_employee` FK→Employee
- `Interview` — `meeting_url`, `score_technical/communication/culture_fit` (1-5), `recommendation`, property `average_score`
- `JobOffer` — OneToOne với Applicant, `status` (draft/sent/accepted/rejected/expired)
- `ApplicantStageHistory` — Audit trail stage: `from_stage`, `to_stage`, `changed_by`, `changed_at`

**Đào tạo:**
- `TrainingCourse` — `passing_score` (default 60), `learning_objectives`, `prerequisites`, `is_mandatory`
- `TrainingSession` — `online_meeting_url`, `recording_url`, `materials_file`
- `TrainingEnrollment` — Auto-set `result='pass'/'fail'` khi nhập score ≥/< passing_score trong `save()`. Tự tạo Certificate khi result='pass'
- `TrainingCertificate` — `certificate_number` (CERT-YYYYMMDD-NNNN, đếm theo ngày), `expiry_date`, `is_active`
- `TrainingNeedAssessment` — Đề xuất nhu cầu đào tạo. `status` (pending/approved/rejected/enrolled)
- `EmployeeTrainingPlan` — Kế hoạch đào tạo theo năm. `unique_together = (employee, course, year)`. `status` (not_started/in_progress/completed/overdue)

**Celery tasks** (`talent/tasks.py`): `notify_stage_change`, `check_offer_expiry` (8:30), `check_certificate_expiry` (8:35), `sync_training_plan_status` (thứ Hai 9:00)

### attendance/models.py (8 models)

**Chấm công:** `WorkShift`, `PublicHoliday`, `AttendanceRecord` (6 status, tự tính actual_hours/ot_hours trong `save()`)
**Nghỉ phép:** `LeaveType`, `LeavePolicy` (12 ngày + 1/5 năm thâm niên), `LeaveBalance` (property `remaining_days`), `LeaveRequest` (tự tính total_days bỏ weekend+lễ), `LeaveApproval`

### payroll/models.py (7 models)

**PayrollConfig** — Singleton (pk=1), `PayrollConfig.get()`. Fallback khi không có InsuranceConfig.
**InsuranceConfig** — BHXH/BHYT/BHTN theo năm. `salary_cap`, `personal_deduction`, `dependent_deduction`.
**PITBracket** — Bậc thuế TNCN. `unique_together = (year, order)`.
**SalaryConfig** — Lương riêng từng NV. Ưu tiên hơn Contract khi `is_active=True`. `allowances` JSONField.
**OTRecord** — Tăng ca cần duyệt. `pending → approved/rejected`. Auto-fill `multiplier` trong `save()`.
**Payslip** — `unique_together = (employee, month, year)`. Method `calculate()` gọi trước `save()`, `generate_lines()` gọi SAU `save()`.
**PayslipLine** — Chi tiết phiếu lương. `category`: `earning`/`deduction`/`tax`.

Hàm `_calculate_pit(taxable_income, year)` — ưu tiên PITBracket DB, fallback hardcoded.

---

## Hệ thống phân quyền

**Logic OR**: quyền cuối = UserProfile OR tất cả StaffGroup của user.

**`employees/helpers.py`** — dùng chung toàn bộ app:
```python
get_allowed_departments(user)  # → QuerySet Department user được xem
get_user_perms(user)           # → {'can_add', 'editable_depts', 'deletable_depts'}
get_user_features(user)        # → {'app_employees', 'can_export', ...}
_get_client_ip(request)        # → IP string
log_activity(user, action, target_type, target_name, detail, ip)
```
Import: `from employees.helpers import get_user_features, log_activity, _get_client_ip`

- Superuser bypass tất cả — luôn check `request.user.is_superuser` trước.
- `editable_depts = None` → sửa tất cả. `editable_depts` là **set of department names**.

**`api/permissions.py`**: `HasEmployeesAppPermission`, `HasAttendanceAppPermission`, `HasPayrollAppPermission`

---

## URLs — Web

### Global: `/` home | `/login/` | `/logout/`

### /employees/
CRUD: `employee_list`, `employee_create`, `employee_detail`, `employee_update`, `employee_delete`
Actions: `employee_terminate`, `employee_reactivate`, `employee_change_status`
Export/Import: `export_csv`, `export_excel`, `import_excel`, `download_import_template`
Khác: `check_employee_code` (AJAX), `dashboard`, `export_status_excel`, `change_password`

### /settings/ (namespace `system_settings`)
Departments: `department_manage`, `department_update`, `department_delete`
Groups: `group_list`, `group_create`, `group_update`, `group_delete`
Users: `user_list`, `user_create`, `user_delete`, `admin_reset_password`, `user_link_employee` (AJAX)
Staff: `staff_group_create`, `staff_group_update`, `staff_group_delete`
Khác: `permission_manage`, `activity_log`, `toggle_app`

### /contracts/ (namespace `contracts`)
CRUD: `contract_list`, `contract_create`, `contract_detail`, `contract_update`, `contract_delete`
Actions: `contract_renew`, `contract_terminate`, `contract_print`
Dashboard: `contract_dashboard`, `contract_dashboard_export_excel`, `contract_export_excel`

### /talent/ (namespace `talent`)

| URL pattern | View name |
|---|---|
| `/talent/` | `talent_home` |
| `/talent/jobs/` + CRUD | `job_list/create/detail/update/delete` |
| `/talent/applicants/` + CRUD | `applicant_list/create/detail/update/delete` |
| `/talent/applicants/<pk>/change-stage/` | `applicant_change_stage` |
| `/talent/applicants/<pk>/convert/` | `applicant_convert` |
| `/talent/applicants/kanban/` | `applicant_kanban` |
| `/talent/applicants/generate-code/` | `generate_employee_code` (AJAX) |
| `/talent/interviews/<pk>/delete/` | `interview_delete` |
| `/talent/offers/create/` + edit | `offer_create`, `offer_update` |
| `/talent/recruitment-dashboard/` | `recruitment_dashboard` |
| `/talent/courses/` + CRUD | `course_list/create/detail/update/delete` |
| `/talent/sessions/` + CRUD | `session_list/create/detail/update/delete` |
| `/talent/sessions/<pk>/bulk-score/` | `bulk_score_update` |
| `/talent/enrollments/create/` + update/delete | `enrollment_create/update/delete` |
| `/talent/certificates/` + detail/print | `certificate_list/detail/print` |
| `/talent/training-dashboard/` | `training_dashboard` |
| `/talent/needs/` | `need_list` |
| `/talent/needs/create/` | `need_create` |
| `/talent/needs/<pk>/review/` | `need_review` |
| `/talent/plans/` | `plan_list` |
| `/talent/plans/create/` | `plan_create` |
| `/talent/plans/<pk>/delete/` | `plan_delete` |

### /attendance/ (namespace `attendance`)
Records: `attendance_list/create/update/delete`, `attendance_import`, `attendance_dashboard`
Shifts: `shift_list/create/update/delete`
Holidays: `holiday_manage`
Leave types: `leave_type_list/create/update/delete`, `leave_policy_update`
Balance: `leave_balance_list/create/init`
Requests: `leave_request_list/create/detail/cancel`, `leave_approve`, `leave_reject`

### /payroll/ (namespace `payroll`)
Payslips: `payslip_list`, `payslip_bulk_create`, `payslip_detail/update/delete/print`
Config: `payroll_config`, `insurance_config_list/create/delete`, `salary_config_list/create/update/delete`
OT: `ot_list/create`, `ot_approve/reject/delete`

---

## URLs — REST API (`/api/`)

Auth: `POST /api/token/` | Health: `GET /api/health/`
Swagger: `/api/docs/` | Schema: `/api/schema/`

| Endpoint | Methods | Custom actions |
|---|---|---|
| `/api/employees/` | CRUD | — |
| `/api/departments/` | CRUD | — |
| `/api/attendance/records/` | CRUD | — |
| `/api/attendance/leave-requests/` | CRUD | `approve`, `reject` |
| `/api/attendance/leave-types/` | GET only | — |
| `/api/payroll/payslips/` | CRUD | `recalculate` (draft only), `confirm` |
| `/api/payroll/ot-records/` | CRUD | `approve`, `reject` |

**Query params:** `?search=` | `?ordering=` | `?status=` | `?employee=` | `?month=&year=` | `?department=`

---

## Quy ước code

### Web Views
- Mọi view: `@login_required`. Luôn check `request.user.is_superuser` trước khi check quyền.
- `employee_code` lưu UPPERCASE (`EmployeeForm.clean_employee_code`).
- `department` là FK — filter `department__in=` hoặc `department__name=`. Không dùng chuỗi thô.
- `select_related('department')` khi loop qua Employee (tránh N+1).
- Ngày trong template: `|date:"d/m/Y"`. Khi `.values('department__name')`: `{{ d.department__name }}`.
- `auto_terminate_employees()` gọi ở đầu `employee_list`.
- Sort/pagination: `base_filter_qs = request.GET.copy()` bỏ sort/order/page → `.urlencode()`.
- `log_activity()` sau mỗi thao tác quan trọng. `paginator.count` thay vì `.count()` thủ công.
- Status filter mặc định `'active'` → ẩn `nghi_viec` (không phải chỉ `dang_lam`).

### REST API
- Permission class trong `api/permissions.py` — tái dùng `get_user_features` + `get_user_perms`.
- Trường tính toán tự động là `read_only` trong serializer.
- Custom actions dùng `@action(detail=True, methods=['post'])`.
- `perform_create()` trong ViewSet để inject logic trước khi save.

### Khi thêm tính năng mới
- **Quyền mới**: cập nhật `UserProfile`, `StaffGroup`, `get_user_features()`, tạo migration.
- **Trạng thái mới**: cập nhật `STATUS_CHOICES`, `DASH_STATUS_COLORS`, `EXCEL_STATUS_COLORS`.
- **Sau mỗi tính năng**: cập nhật CLAUDE.md.
- Windows: `python -X utf8` khi chạy lệnh có tiếng Việt (tránh UnicodeEncodeError).

---

## Dependencies & Settings

```
django>=6.0  openpyxl  Pillow  psycopg2-binary  dj-database-url  python-decouple
celery[redis]  django-celery-beat  django-celery-results
djangorestframework  drf-spectacular  gunicorn  redis  sqlalchemy
```

```python
SESSION_COOKIE_AGE = 900        # auto-logout 15 phút
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
REST_FRAMEWORK = {'PAGE_SIZE': 50, ...}
```

`.env` local: `DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/hrm_db`
`.env` Docker: `DATABASE_URL=postgresql://postgres:PASSWORD@db:5432/hrm_db`

**Celery local:**
```bash
celery -A myproject worker --pool=solo -l info          # Terminal 1
celery -A myproject beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler  # Terminal 2
```

---

## Docker

5 services: `nginx` (port 80), `web` (Django+Gunicorn), `db` (postgres:16), `redis` (7-alpine), `celery`

```bash
docker-compose up --build   # Lần đầu
docker-compose up -d        # Chạy nền
docker-compose down         # Dừng
docker-compose logs -f web  # Logs
docker-compose exec web python manage.py createsuperuser
```

Local ↔ Docker: đổi `DATABASE_URL` (localhost ↔ db), `CELERY_BROKER_URL` (filesystem ↔ redis), `DEBUG`.

---

## Lịch sử phiên bản

| Version | Tính năng chính |
|---|---|
| v1–v23 | Employees CRUD, Dashboard, Contracts, system_settings, AppStatus, auto-logout |
| v24–v29 | App Talent: 8 models, Kanban, PDF cert, seed data, hired→nhân viên |
| v30–v31 | App Departments tách riêng, User↔Employee link (AJAX) |
| v32–v35 | core app, App Payroll (7 models, thuế TNCN, BHXH), Celery tasks, Notifications |
| v36 | Analytics: Chart.js 4.4.0 cho Employees/Attendance/Talent |
| v37–v40 | App API (DRF): 7 ViewSets, Token auth, Swagger, approve/reject/recalculate |
| v41 | Docker: 5 services (nginx/web/db/redis/celery), Gunicorn, Redis broker |
| v42 | Tối ưu Talent: 9 DB indexes, fix cert_number/avg_time_to_hire/N+1, thêm 10 fields mới, 3 models (ApplicantStageHistory/TrainingNeedAssessment/EmployeeTrainingPlan), 4 Celery tasks, views/forms/templates cho needs+plans |
| v43 | Approval workflow Talent: TrainingNeedAssessment (permission check + notification), EmployeeTrainingPlan (nhân viên đề xuất → trưởng phòng duyệt), JobPosition (trưởng phòng đề xuất → HR/Admin duyệt). Helper `_can_review_talent`, 5 views mới (plan_request_create, plan_approve, plan_reject, job_approve, job_reject), tabs phân vai trong job_list/need_list/plan_list |
| v44 | Tối ưu code Talent: fix N+1 (job_detail, sync_training_plan_status), transaction.atomic() trong applicant_convert, capacity check enrollment_add, helper `_process_approval()` + `_paginate()`, cache get_user_perms(), ApplicantConvertForm, notification khi cert hết hạn, constants thay magic strings, fix UI (màu button, CSS class, colspan) |
| v45 | UX form toàn project: thêm field `priority` còn thiếu trong `job_form.html`, thêm JS scroll-to-error vào 23 form templates (employees/contracts/attendance/talent/payroll), thêm inline field errors còn thiếu cho shift_form/leave_type_form/leave_balance_form/leave_policy_form |
