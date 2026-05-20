# KẾ HOẠCH PHÁT TRIỂN HRM ENTERPRISE — myproject

## Context

Dự án HRM Django hiện có 6 app (employees, contracts, attendance, talent, departments, system_settings) đã xây dựng đúng ~80% infrastructure. Mục tiêu: phát triển thành hệ thống HRM thực tế cho SME Việt Nam, chuẩn Enterprise với vòng đời nhân viên đầy đủ, tính lương theo luật Việt Nam, workflow tự động và audit log.

**Nguyên tắc cốt lõi từ planhrm.txt:**
- Chỉ 1 nguồn dữ liệu gốc (`employees` là lõi, không lưu trùng tên/phone/email)
- Vòng đời: Ứng viên → HĐ → Đào tạo → Chấm công → Nghỉ phép → Đánh giá → Lương → Nghỉ việc
- RBAC permission, audit log, Docker, workflow tự động

---

## Phân tích Gap — Hiện tại vs. Mục tiêu

| Tính năng | Trạng thái | Ưu tiên |
|---|---|---|
| Employee Master | ✅ Có | — |
| Contracts | ✅ Có (thiếu salary components) | — |
| Attendance + Leave | ✅ Có (thiếu OT types) | — |
| Recruitment + Training | ✅ Có | — |
| **Payroll/Lương** | ❌ Thiếu | P0 - Critical |
| **Notifications/Email** | ❌ Thiếu | P1 |
| **Core app (base, utils)** | ❌ Thiếu | P1 |
| **employee_code auto NV-26XXXX** | ⚠️ Manual | P1 |
| **Performance/Appraisal** | ❌ Thiếu | P2 |
| **API REST (DRF)** | ❌ Thiếu | P2 |
| **Tests** | ❌ 0% coverage | P2 |
| **Docker/Production** | ❌ Thiếu | P3 |
| **Org Chart** | ❌ Thiếu | P3 |

---

## Kế hoạch triển khai — 6 Phase

---

### PHASE 1: Nền tảng & Chuẩn hóa (Tuần 1–3)

**Mục tiêu:** Dọn nền, chuẩn hóa cấu trúc code, thêm core app

#### Bước 1.1 — Tạo `core` app

Tạo app mới `myproject/core/` dùng làm nền cho toàn bộ hệ thống:

```python
# core/models.py

class BaseModel(models.Model):
    """Model cha cho tất cả model quan trọng"""
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    created_by = FK(User, null=True, related_name='+')
    updated_by = FK(User, null=True, related_name='+')

    class Meta:
        abstract = True

class Notification(models.Model):
    """Thông báo trong hệ thống"""
    user = FK(User)
    title = CharField(max_length=200)
    message = TextField()
    type = CharField()  # info | warning | danger | success
    link = CharField(null=True)   # URL để click vào
    is_read = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
```

File quan trọng cần tạo:
- `core/models.py` — BaseModel, Notification
- `core/utils.py` — hàm tiện ích dùng chung (đang ở employees/helpers.py → giữ nguyên, import thêm)
- `core/notifications.py` — hàm tạo + gửi notification
- `core/middleware.py` — inject request user vào thread local (dùng cho BaseModel auto-fill)

#### Bước 1.2 — Chuẩn hóa employee_code (NV-260001)

File cần sửa: `employees/models.py`, `employees/views.py`

Logic hiện tại: employee_code nhập tay (uppercase).  
Logic mới: Auto-generate theo format `NV-YY####` khi để trống.

```python
# employees/models.py — thêm method
@staticmethod
def generate_employee_code(hire_date=None):
    from datetime import date
    year = (hire_date or date.today()).strftime("%y")  # "26"
    last = Employee.objects.filter(
        employee_code__startswith=f"NV-{year}"
    ).order_by('-employee_code').first()
    seq = int(last.employee_code[-4:]) + 1 if last else 1
    return f"NV-{year}{seq:04d}"
```

#### Bước 1.3 — Chuẩn hóa Contracts: Thêm salary components

File cần sửa: `contracts/models.py`

Vấn đề: `Contract.salary` chỉ là 1 con số, không phân biệt được lương cơ bản vs phụ cấp.  
Giải pháp: Thêm `salary_components` JSONField để lưu breakdown.

```python
# contracts/models.py — thêm vào Contract model
basic_salary = DecimalField(max_digits=15, decimal_places=0, null=True)
allowances = JSONField(default=dict)
# Format: {"housing": 2000000, "transport": 500000, "meal": 500000}
# salary = basic_salary + sum(allowances.values()) — tự tính
```

Tạo migration: `python manage.py makemigrations contracts`

#### Bước 1.4 — Chuẩn hóa Attendance: OT Classification

File cần sửa: `attendance/models.py`

Vấn đề: AttendanceRecord chỉ biết số giờ OT, không biết loại OT (bình thường/đêm/cuối tuần/lễ).

```python
# attendance/models.py — thêm vào AttendanceRecord
class OTType(models.TextChoices):
    NORMAL = 'normal', 'Bình thường (1.5x)'
    NIGHT = 'night', 'Ban đêm (2.0x)'
    WEEKEND = 'weekend', 'Cuối tuần (2.0x)'
    HOLIDAY = 'holiday', 'Ngày lễ (3.0x)'

ot_type = CharField(choices=OTType.choices, null=True, blank=True)
ot_multiplier = DecimalField(max_digits=3, decimal_places=1, null=True)

# Logic: auto-fill trong save() dựa trên date + shift
def _determine_ot_type(self):
    is_holiday = PublicHoliday.objects.filter(date=self.date).exists()
    is_weekend = self.date.weekday() >= 5
    if is_holiday:
        return self.OTType.HOLIDAY, Decimal('3.0')
    elif is_weekend:
        return self.OTType.WEEKEND, Decimal('2.0')
    else:
        return self.OTType.NORMAL, Decimal('1.5')
```

---

### PHASE 2: Payroll App — Tính lương (Tuần 4–10)

**Đây là phase quan trọng nhất — hoàn thiện vòng đời nhân viên**

#### Bước 2.1 — Tạo `payroll` app với 6 models

Tạo app mới `myproject/payroll/`:

```
payroll/
├── models.py      # 6 models chính
├── views.py       # 12+ views
├── forms.py       # PayslipForm, ConfigForm
├── urls.py        # namespace 'payroll'
├── engine.py      # Tính lương engine (tách logic ra)
├── tax.py         # PIT + BHXH tính toán
└── templates/payroll/
```

**6 Models cần tạo:**

```python
# payroll/models.py

# Model 1: Cấu hình lương nhân viên (liên kết Contract)
class SalaryConfig(models.Model):
    employee = FK(Employee, on_delete=PROTECT)
    contract = FK('contracts.Contract', on_delete=PROTECT)
    effective_from = DateField()
    effective_to = DateField(null=True, blank=True)
    basic_salary = DecimalField(max_digits=15, decimal_places=0)
    allowances = JSONField(default=dict)
    # {'housing': 2000000, 'transport': 500000, 'meal': 500000}
    dependents = IntegerField(default=0)  # Số người phụ thuộc (PIT)
    is_active = BooleanField(default=True)

    @property
    def gross_salary(self):
        return self.basic_salary + sum(self.allowances.values())

# Model 2: Bảng lương tháng (Payslip)
class Payslip(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Nháp'
        SUBMITTED = 'submitted', 'Chờ duyệt'
        APPROVED = 'approved', 'Đã duyệt'
        PAID = 'paid', 'Đã thanh toán'

    employee = FK(Employee, on_delete=PROTECT)
    period_month = IntegerField()   # 1-12
    period_year = IntegerField()    # 2026
    status = CharField(choices=Status.choices, default=Status.DRAFT)

    # EARNINGS
    basic_salary = DecimalField(max_digits=15, decimal_places=0)
    allowances_total = DecimalField(max_digits=15, decimal_places=0)
    ot_pay = DecimalField(max_digits=15, decimal_places=0, default=0)
    bonus = DecimalField(max_digits=15, decimal_places=0, default=0)
    gross_salary = DecimalField(max_digits=15, decimal_places=0)

    # DEDUCTIONS
    lop_deduction = DecimalField(max_digits=15, decimal_places=0, default=0)
    bhxh_si = DecimalField(max_digits=15, decimal_places=0)  # 8%
    bhxh_hi = DecimalField(max_digits=15, decimal_places=0)  # 1.5%
    bhxh_ui = DecimalField(max_digits=15, decimal_places=0)  # 1%
    pit = DecimalField(max_digits=15, decimal_places=0)

    # NET
    net_salary = DecimalField(max_digits=15, decimal_places=0)

    # META
    paid_date = DateField(null=True)
    approved_by = FK(User, null=True, related_name='+')
    notes = TextField(blank=True)

    class Meta:
        unique_together = ['employee', 'period_month', 'period_year']

# Model 3: Chi tiết dòng payslip
class PayslipLine(models.Model):
    payslip = FK(Payslip, on_delete=CASCADE, related_name='lines')
    category = CharField()  # earning | deduction | tax
    name = CharField(max_length=200)
    amount = DecimalField(max_digits=15, decimal_places=0)
    note = CharField(blank=True)

# Model 4: OT Record (duyệt trước khi tính lương)
class OTRecord(models.Model):
    employee = FK(Employee, on_delete=CASCADE)
    date = DateField()
    hours = DecimalField(max_digits=4, decimal_places=1)
    ot_type = CharField(choices=...)  # normal | night | weekend | holiday
    multiplier = DecimalField(max_digits=3, decimal_places=1)
    approved_by = FK(User, null=True)
    status = CharField()  # pending | approved | rejected

# Model 5: Cấu hình BHXH (để thay đổi khi luật thay đổi)
class InsuranceConfig(models.Model):
    year = IntegerField(unique=True)
    si_employee_rate = DecimalField(default=Decimal('0.08'))   # 8%
    hi_employee_rate = DecimalField(default=Decimal('0.015'))  # 1.5%
    ui_employee_rate = DecimalField(default=Decimal('0.01'))   # 1%
    si_employer_rate = DecimalField(default=Decimal('0.175'))  # 17.5%
    hi_employer_rate = DecimalField(default=Decimal('0.03'))   # 3%
    ui_employer_rate = DecimalField(default=Decimal('0.01'))   # 1%
    salary_cap = DecimalField(default=Decimal('46800000'))     # 46.8M
    personal_deduction = DecimalField(default=Decimal('15500000'))  # 15.5M (2026+)
    dependent_deduction = DecimalField(default=Decimal('6200000'))  # 6.2M (2026+)

# Model 6: Bậc thuế TNCN (cập nhật theo luật)
class PITBracket(models.Model):
    year = IntegerField()
    min_income = DecimalField(max_digits=15, decimal_places=0)
    max_income = DecimalField(null=True)  # null = unlimited
    rate = DecimalField(max_digits=4, decimal_places=2)  # 0.05, 0.10...
    quick_deduction = DecimalField(default=0)  # Số trừ nhanh
```

#### Bước 2.2 — Engine tính lương (payroll/engine.py)

```python
# payroll/engine.py

def generate_payslip(employee, month, year):
    """Workflow tính lương 1 nhân viên 1 tháng"""
    config = SalaryConfig.objects.get(employee=employee, is_active=True)
    insurance = InsuranceConfig.objects.get(year=year)

    # 1. Tính gross từ SalaryConfig
    gross = config.gross_salary

    # 2. OT pay từ OTRecord đã approved
    ot_records = OTRecord.objects.filter(employee=employee, date__month=month,
                                          date__year=year, status='approved')
    hourly_rate = gross / 22 / 8
    ot_pay = sum(r.hours * hourly_rate * r.multiplier for r in ot_records)

    # 3. LOP từ nghỉ không phép (LeaveRequest.is_paid = False)
    unpaid_days = _calculate_lop(employee, month, year)
    lop = (gross / 22) * unpaid_days

    adjusted_gross = gross + ot_pay - lop

    # 4. BHXH
    base = min(adjusted_gross, insurance.salary_cap)
    bhxh = {'si': base * insurance.si_employee_rate,
             'hi': base * insurance.hi_employee_rate,
             'ui': base * insurance.ui_employee_rate}

    # 5. PIT lũy tiến
    pit = calculate_pit(adjusted_gross, sum(bhxh.values()),
                        config.dependents, year, insurance)

    # 6. Net
    net = adjusted_gross - sum(bhxh.values()) - pit

    return Payslip.objects.create(...)
```

#### Bước 2.3 — Tính PIT lũy tiến (payroll/tax.py)

```python
# payroll/tax.py

def calculate_pit(gross, total_insurance, dependents, year, insurance_config):
    """PIT Việt Nam theo lũy tiến (Resolution 110/2025)"""
    taxable = gross - total_insurance \
              - insurance_config.personal_deduction \
              - (insurance_config.dependent_deduction * dependents)

    if taxable <= 0:
        return Decimal('0')

    brackets = PITBracket.objects.filter(year=year).order_by('min_income')
    tax = Decimal('0')
    remaining = taxable

    for bracket in brackets:
        if remaining <= 0:
            break
        bracket_size = (bracket.max_income - bracket.min_income
                        if bracket.max_income else remaining)
        taxable_in_bracket = min(remaining, bracket_size)
        tax += taxable_in_bracket * bracket.rate
        remaining -= taxable_in_bracket

    return tax.quantize(Decimal('1'))
```

#### Bước 2.4 — Views & URLs (12 views cơ bản)

```
/payroll/                       payroll_home
/payroll/config/                salary_config_list
/payroll/config/create/         salary_config_create
/payroll/config/<pk>/edit/      salary_config_update
/payroll/run/                   run_payroll (chạy batch tháng)
/payroll/payslips/              payslip_list
/payroll/payslips/<pk>/         payslip_detail
/payroll/payslips/<pk>/approve/ payslip_approve
/payroll/payslips/<pk>/print/   payslip_print
/payroll/ot/                    ot_list
/payroll/ot/<pk>/approve/       ot_approve
/payroll/export/excel/          payroll_export_excel
```

#### Bước 2.5 — Seed data BHXH + PIT brackets

Tạo management command `payroll/management/commands/seed_payroll_config.py`:
- InsuranceConfig cho năm 2024, 2025, 2026
- PITBracket 7 bậc theo Resolution 110/2025 (2026+) và 2024-2025

**Bảng PIT brackets 2026 (Resolution 110/2025):**

| Bậc | Thu nhập tính thuế/tháng | Thuế suất |
|---|---|---|
| 1 | 0 – 5,000,000 | 5% |
| 2 | 5,000,001 – 10,000,000 | 10% |
| 3 | 10,000,001 – 18,000,000 | 15% |
| 4 | 18,000,001 – 32,000,000 | 20% |
| 5 | 32,000,001 – 52,000,000 | 25% |
| 6 | 52,000,001 – 80,000,000 | 30% |
| 7 | Trên 80,000,000 | 35% |

---

### PHASE 3: Notifications & Workflow (Tuần 11–13)

**Mục tiêu:** Cảnh báo tự động, giảm công việc thủ công của HR

#### Bước 3.1 — Email notifications

Thêm vào `myproject/settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
```

#### Bước 3.2 — Thêm Celery cho async tasks

```
requirements thêm: celery redis django-celery-beat
```

File cần tạo: `myproject/celery.py`, `myproject/__init__.py`

**Các scheduled tasks:**

| Task | Cron | Logic |
|---|---|---|
| `check_contract_expiry` | Mỗi sáng 7h | Contract sắp hết ≤30 ngày → tạo Notification + gửi email HR |
| `check_training_cert_expiry` | Mỗi sáng 7h | Chứng chỉ hết hạn ≤30 ngày → cảnh báo HR |
| `auto_terminate_employees` | Mỗi sáng 6h | Đã có trong views.py → chuyển thành task |
| `monthly_leave_accrual` | Ngày 1 mỗi tháng | Tính + cấp phép năm theo thâm niên |
| `run_monthly_payroll_reminder` | Ngày 25 mỗi tháng | Nhắc HR chạy payroll |

#### Bước 3.3 — Notification center trong UI

- Thêm bell icon vào navbar với badge đếm unread
- Trang `/notifications/` xem tất cả
- AJAX mark-as-read
- File cần sửa: `templates/base.html`, `core/views.py`

---

### PHASE 4: Performance & Analytics (Tuần 14–17)

**Mục tiêu:** Đánh giá nhân viên + báo cáo phân tích

#### Bước 4.1 — App `appraisal` (Đánh giá nhân viên)

Models:
```python
class AppraisalCycle(models.Model):
    """Kỳ đánh giá: Q1 2026, Mid-year 2026, Annual 2026"""
    name, period, start_date, end_date, status

class Appraisal(models.Model):
    employee, cycle, appraiser (FK Employee — người đánh giá)
    self_score, manager_score, final_score
    strengths, areas_for_improvement
    status  # draft | self_review | manager_review | completed

class AppraisalGoal(models.Model):
    appraisal, title, description, target, actual, weight (%)
    score, status
```

#### Bước 4.2 — Enhanced dashboards

Cải thiện dashboard hiện có ở từng app:
- `employees/views.py`: thêm chart turnover rate, headcount trend theo tháng
- `attendance/views.py`: thêm OT hours trend, absence rate
- `payroll/views.py`: cost per department, salary distribution
- `talent/views.py`: time-to-hire, fill rate

---

### PHASE 5: API & Tests (Tuần 18–22)

#### Bước 5.1 — Django REST Framework

```
pip install djangorestframework djangorestframework-simplejwt django-filter
```

Tạo `api/` app với:
- JWT authentication
- Serializers cho Employee, Contract, Attendance, LeaveRequest, Payslip
- ViewSets với permission theo UserProfile
- Filtering, pagination, search

Endpoints ưu tiên:
```
GET  /api/employees/          → danh sách NV (mobile app)
POST /api/attendance/checkin/ → check-in từ app/device
POST /api/leave/request/      → xin nghỉ từ self-service portal
GET  /api/payslips/mine/      → NV xem lương của mình
```

#### Bước 5.2 — Unit Tests

Tạo tests cho các logic quan trọng:
```
employees/tests.py:
  - test_employee_code_auto_generate
  - test_scheduled_termination

payroll/tests.py:
  - test_bhxh_calculation
  - test_pit_progressive_brackets
  - test_lop_calculation
  - test_payslip_generate

attendance/tests.py:
  - test_ot_type_determination
  - test_leave_balance_deduction
  - test_leave_attendance_link
```

---

### PHASE 6: Production & Docker (Tuần 23–26)

#### Bước 6.1 — Docker Compose

Tạo `docker-compose.yml`:
```yaml
services:
  web:         # Django + Gunicorn
  db:          # PostgreSQL 16
  redis:       # Cache + Celery broker
  celery:      # Celery worker
  celery-beat: # Celery Beat scheduler
  nginx:       # Reverse proxy + static files
```

Files cần tạo: `Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml`, `nginx/nginx.conf`

#### Bước 6.2 — Settings split

```
myproject/settings/
├── base.py      # Common settings
├── dev.py       # DEBUG=True, SQLite fallback
└── prod.py      # HTTPS, ALLOWED_HOSTS, email, Sentry
```

#### Bước 6.3 — CI/CD (GitHub Actions)

`.github/workflows/ci.yml`:
- Run tests trên push
- Check code style (flake8)
- Build Docker image
- Deploy to server nếu merge vào main

#### Bước 6.4 — Security & Compliance

- CSP headers (django-csp)
- Rate limiting (django-ratelimit) cho login
- HTTPS force trong production
- Database backup script (pg_dump daily)
- Sentry error tracking

---

## File cần tạo/sửa tổng hợp

### Phase 1
| File | Thao tác | Mô tả |
|---|---|---|
| `core/` | Tạo mới | App mới: BaseModel, Notification |
| `core/models.py` | Tạo mới | BaseModel, Notification |
| `core/notifications.py` | Tạo mới | Hàm create_notification() |
| `employees/models.py` | Sửa | Thêm generate_employee_code() |
| `contracts/models.py` | Sửa | Thêm basic_salary, allowances JSONField |
| `attendance/models.py` | Sửa | Thêm ot_type, ot_multiplier vào AttendanceRecord |
| `myproject/settings.py` | Sửa | Thêm 'core' vào INSTALLED_APPS |

### Phase 2
| File | Thao tác | Mô tả |
|---|---|---|
| `payroll/` | Tạo mới | App payroll hoàn chỉnh |
| `payroll/models.py` | Tạo mới | 6 models |
| `payroll/engine.py` | Tạo mới | Logic tính lương |
| `payroll/tax.py` | Tạo mới | PIT + BHXH calculation |
| `payroll/views.py` | Tạo mới | 12 views |
| `payroll/urls.py` | Tạo mới | namespace 'payroll' |
| `payroll/forms.py` | Tạo mới | SalaryConfigForm, PayslipApproveForm |
| `templates/payroll/` | Tạo mới | 8 templates |
| `payroll/management/commands/seed_payroll_config.py` | Tạo mới | Seed BHXH + PIT data |
| `myproject/urls.py` | Sửa | Include payroll.urls |
| `system_settings/models.py` | Sửa | Bật payroll app flag |

### Phase 3
| File | Thao tác | Mô tả |
|---|---|---|
| `myproject/celery.py` | Tạo mới | Celery config |
| `payroll/tasks.py` | Tạo mới | Async payroll tasks |
| `contracts/tasks.py` | Tạo mới | Contract expiry check |
| `attendance/tasks.py` | Tạo mới | Leave accrual task |
| `templates/base.html` | Sửa | Thêm notification bell |
| `.env` | Sửa | Thêm email + Redis config |

---

## Thứ tự ưu tiên triển khai

```
Phase 1 (3 tuần)  → Phase 2 (7 tuần) → Phase 3 (3 tuần)
→ Phase 4 (4 tuần) → Phase 5 (5 tuần) → Phase 6 (4 tuần)

Tổng: ~26 tuần (6 tháng) cho full enterprise HRM
MVP có thể deploy sau Phase 2: ~10 tuần
```

---

## Verification — Cách kiểm tra từng phase

**Phase 1:**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py check
# Test: Tạo NV mới, employee_code tự điền NV-26XXXX
```

**Phase 2:**
```bash
python manage.py seed_payroll_config
# Test: Tạo SalaryConfig cho 1 NV → chạy generate_payslip() trong shell
# Kiểm tra: Net = Gross - BHXH(10.5%) - PIT (theo bracket)
# Kiểm tra: Payslip xuất ra Excel đúng format
```

**Phase 3:**
```bash
celery -A myproject worker --loglevel=info
celery -A myproject beat --loglevel=info
# Test: Trigger manually task check_contract_expiry → xem email nhận được
```

**Phase 5:**
```bash
python manage.py test payroll.tests
python manage.py test attendance.tests
# Target: coverage ≥ 70% cho payroll app
```

**Phase 6:**
```bash
docker-compose up --build
# Test: http://localhost → login, tạo NV, chạy payroll
```

---

## Công thức tính lương tham chiếu (Vietnam 2026)

```
Gross = Basic + Allowances + OT pay - LOP
BHXH = min(Gross, 46,800,000) × 10.5%  (SI 8% + HI 1.5% + UI 1%)
Taxable = Gross - BHXH - 15,500,000 - (6,200,000 × dependents)
PIT = progressive brackets 5%-35%
Net = Gross - BHXH - PIT

Employer cost = Gross + min(Gross, 46,800,000) × 22%  (SI 17.5% + HI 3% + AI 0.5% + UI 1%)
```
