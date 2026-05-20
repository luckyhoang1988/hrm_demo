# Kế hoạch: App Tính lương (`payroll`)

## Context

HRM đã có 5 app: `employees`, `contracts`, `system_settings`, `talent`, `attendance`. App `payroll` là bước tiếp theo. Hạ tầng đã sẵn sàng 100%:
- `AppStatus.app_payroll_active` đã có trong `system_settings/models.py`
- `UserProfile.app_payroll` + `StaffGroup.app_payroll` đã có trong `employees/models.py`
- `get_user_features()` đã trả về `app_payroll` trong `employees/helpers.py`
- `ActivityLog` đã có target_type cho payroll
- `home.html` đã có card "Tính lương" nhưng `href="#"` (chưa kết nối)
- `settings_home.html` đã có toggle card

**Lựa chọn thiết kế (user đã xác nhận):**
- Lương cơ bản: từ `Contract.salary` (hợp đồng đang hiệu lực `status='hieu_luc'`)
- Phụ cấp: cố định + % lương + thưởng thủ công
- Ngày công: tự động từ `AttendanceRecord` + HR có thể điều chỉnh trước khi tính
- Thuế TNCN + BHXH: theo luật Việt Nam 2026 (biểu 5 bậc, giảm trừ 15.5M/6.2M, OT miễn thuế)

---

## Bước 1 — Tạo app skeleton

```
payroll/
├── __init__.py
├── apps.py
├── admin.py
├── models.py
├── forms.py
├── views.py
├── urls.py             # app_name = 'payroll'
├── calculator.py       # Logic tính toán tách riêng
├── migrations/
│   └── __init__.py
└── templates/payroll/
    └── (18 template files)
```

---

## Bước 2 — Models (`payroll/models.py`) — 7 models

### 1. SalaryConfig — Cấu hình tỷ lệ BH/thuế theo năm
```python
class SalaryConfig(Model):
    year                    # IntegerField — unique
    # Tỷ lệ NLĐ đóng
    bhxh_employee_rate      # DecimalField, default=8.00  (%)
    bhyt_employee_rate      # DecimalField, default=1.50
    bhtn_employee_rate      # DecimalField, default=1.00
    # Tỷ lệ NSDLĐ đóng
    bhxh_employer_rate      # DecimalField, default=17.50
    bhyt_employer_rate      # DecimalField, default=3.00
    bhtn_employer_rate      # DecimalField, default=1.00
    # Mức lương cap
    si_salary_cap           # DecimalField, default=46_800_000 (20×lương cơ sở)
    bhtn_salary_cap         # DecimalField, default=93_600_000 (20×lương TV vùng 1)
    # Giảm trừ gia cảnh (luật 2026)
    personal_deduction      # DecimalField, default=15_500_000
    dependent_deduction     # DecimalField, default=6_200_000
    is_active               # BooleanField
    
    class Meta:
        unique_together = [('year',)]
```

### 2. AllowanceType — Loại phụ cấp
```python
class AllowanceType(Model):
    name                # "Phụ cấp ăn ca", "Phụ cấp điện thoại"
    code                # slug ngắn
    calculation_type    # 'fixed' | 'percent_of_base'
    is_taxable          # BooleanField — tính vào thu nhập chịu thuế
    is_si_base          # BooleanField — tính vào lương đóng BH
    is_active
```

### 3. EmployeeAllowance — Phụ cấp định kỳ từng NV
```python
class EmployeeAllowance(Model):
    employee            # FK → Employee
    allowance_type      # FK → AllowanceType
    amount              # DecimalField — số tiền (nếu fixed)
    percent             # DecimalField, null — % lương (nếu percent_of_base)
    effective_from      # DateField
    effective_to        # DateField, null=True (None = còn hiệu lực)
    note
```

### 4. PayrollPeriod — Kỳ lương
```python
class PayrollPeriod(Model):
    STATUS = [
        ('draft',       'Nháp'),
        ('review',      'Đang review'),
        ('pending',     'Chờ duyệt'),
        ('approved',    'Đã duyệt'),
        ('paid',        'Đã thanh toán'),
    ]
    month               # IntegerField (1-12)
    year                # IntegerField
    status              # CharField
    note
    created_by          # FK → User (null, SET_NULL)
    created_at
    updated_at
    approved_by         # FK → User (null)
    approved_at         # DateTimeField (null)
    paid_at             # DateTimeField (null)
    # Tổng hợp toàn kỳ (cập nhật sau khi tính)
    total_gross         # DecimalField
    total_net           # DecimalField
    total_pit           # DecimalField — thuế TNCN
    total_si_employee   # DecimalField — BH NLĐ
    total_si_employer   # DecimalField — BH NSDLĐ
    total_employees     # IntegerField — số phiếu lương
    
    class Meta:
        unique_together = [('month', 'year')]
```

### 5. Payslip — Phiếu lương (snapshot)
```python
class Payslip(Model):
    STATUS = [('draft','Nháp'), ('confirmed','Xác nhận'), ('paid','Đã trả')]
    period              # FK → PayrollPeriod (on_delete=CASCADE)
    employee            # FK → Employee (on_delete=PROTECT)
    # --- Snapshot thông tin NV ---
    employee_code       # CharField (copy)
    full_name           # CharField (copy)
    department_name     # CharField (copy)
    position            # CharField (copy)
    # --- Ngày công ---
    standard_working_days   # DecimalField — ngày chuẩn tháng (trừ lễ)
    actual_working_days     # DecimalField — ngày thực tế có mặt
    ot_hours                # DecimalField — tổng giờ OT
    leave_days_paid         # DecimalField — ngày nghỉ phép có lương
    absent_days             # DecimalField — ngày vắng không phép
    # --- Thu nhập ---
    base_salary             # DecimalField — lương HĐ (snapshot)
    actual_salary           # DecimalField — lương theo ngày công
    allowances_total        # DecimalField — tổng phụ cấp chịu thuế
    allowances_nontax       # DecimalField — tổng phụ cấp KCT
    ot_pay                  # DecimalField — tiền OT (miễn thuế 2026)
    bonus                   # DecimalField, default=0 — thưởng thủ công
    gross_income            # DecimalField — tổng thu nhập
    taxable_gross           # DecimalField — phần chịu thuế (= gross - ot_pay - allowances_nontax)
    # --- Bảo hiểm ---
    si_salary               # DecimalField — lương đóng BH (snapshot, ≤ cap)
    bhxh_employee           # DecimalField
    bhyt_employee           # DecimalField
    bhtn_employee           # DecimalField
    total_si_employee       # DecimalField
    bhxh_employer           # DecimalField
    bhyt_employer           # DecimalField
    bhtn_employer           # DecimalField
    total_si_employer       # DecimalField
    # --- Thuế TNCN ---
    num_dependents          # IntegerField (snapshot)
    personal_deduction      # DecimalField (snapshot)
    dependent_deduction_total   # DecimalField
    taxable_net             # DecimalField — TNCT sau khấu trừ BH + giảm trừ
    pit_amount              # DecimalField — thuế TNCN
    # --- Kết quả ---
    other_deductions        # DecimalField, default=0 — khấu trừ khác (tạm ứng...)
    net_salary              # DecimalField — lương thực nhận
    status                  # CharField
    note
    created_at
    
    class Meta:
        unique_together = [('period', 'employee')]
```

### 6. PayslipAllowanceDetail — Chi tiết phụ cấp trong phiếu
```python
class PayslipAllowanceDetail(Model):
    payslip         # FK → Payslip (on_delete=CASCADE)
    name            # CharField (snapshot tên phụ cấp)
    amount          # DecimalField
    is_taxable      # BooleanField
```

### 7. PayrollApprovalLog — Lịch sử duyệt
```python
class PayrollApprovalLog(Model):
    ACTION = [submit, approve, reject, reopen, mark_paid]
    period      # FK → PayrollPeriod
    user        # FK → User (SET_NULL)
    action      # CharField
    comment     # TextField (null)
    acted_at    # DateTimeField (auto_now_add)
```

---

## Bước 3 — Calculator (`payroll/calculator.py`)

Logic tính toán tách hoàn toàn khỏi views để dễ test và tái sử dụng.

```python
def get_standard_working_days(year, month):
    """Đếm ngày thường trong tháng, trừ PublicHoliday."""
    # Loop từng ngày trong tháng
    # Bỏ qua Saturday (weekday=5), Sunday (weekday=6)
    # Bỏ qua ngày có trong PublicHoliday.objects.filter(date__year=year, date__month=month)

def get_employee_attendance_summary(employee, year, month):
    """Trả về dict: actual_days, ot_hours, leave_days_paid, absent_days."""
    # Query AttendanceRecord.objects.filter(employee=employee, date__year=year, date__month=month)
    # present → +1, half_day → +0.5, on_leave (is_paid=True) → +1 (paid leave)
    # absent → absent_days +1
    # Cộng dồn ot_hours

def get_base_salary(employee):
    """Lấy salary từ Contract đang hiệu lực, fallback về Employee.salary."""
    contract = Contract.objects.filter(
        employee=employee, status='hieu_luc'
    ).order_by('-start_date').first()
    return contract.salary if contract and contract.salary else employee.salary

def get_active_allowances(employee, year, month):
    """Lấy phụ cấp đang hiệu lực trong tháng."""
    # EmployeeAllowance.objects.filter(employee=employee,
    #     effective_from__lte=period_end, effective_to__isnull=True hoặc __gte=period_start)

def calculate_insurance(si_salary, config):
    """Tính BH employee + employer. Returns dict."""
    capped = min(si_salary, config.si_salary_cap)
    bhtn_capped = min(si_salary, config.bhtn_salary_cap)
    ...

def calculate_pit_2026(taxable_net):
    """Biểu thuế TNCN 5 bậc 2026."""
    if taxable_net <= 0: return 0
    brackets = [
        (10_000_000,  0.05,         0),
        (30_000_000,  0.10,   500_000),
        (60_000_000,  0.20, 2_500_000),
        (100_000_000, 0.30, 8_500_000),
        (float('inf'), 0.35, 18_500_000),
    ]
    # lũy tiến: tax = base + (taxable_net - lower_bound) × rate

def generate_payslip(employee, period, config):
    """Tính toàn bộ 1 phiếu lương. Trả về Payslip object (chưa save)."""
    # 1. Lấy ngày công từ AttendanceRecord
    # 2. Lấy base_salary từ Contract
    # 3. Tính actual_salary = base × (actual_days / standard_days)
    # 4. Tính allowances từ EmployeeAllowance
    # 5. Tính OT pay (không chịu thuế)
    # 6. Tính BH
    # 7. Tính TNCT = taxable_gross - total_si_employee - personal_deduction - dependent × num_dep
    # 8. Tính PIT
    # 9. Net = gross - total_si_employee - pit - other_deductions
    # 10. Return Payslip(...)

def bulk_calculate_payroll(period, config):
    """Tính hàng loạt cho tất cả NV active. Returns (created, updated, errors)."""
    # Employee.objects.filter(status__in=ACTIVE_STATUSES)
    # Loop → generate_payslip → Payslip.objects.update_or_create(period=period, employee=emp)
    # Cập nhật PayrollPeriod totals sau khi xong
```

**Trạng thái NV được tính lương:**
`dang_lam`, `thu_viec`, `thuc_tap_sinh`, `nghi_phep`, `nghi_sinh`, `nghi_om`, `nghi_khong_luong`
(Không tính `nghi_viec`)

---

## Bước 4 — Views (`payroll/views.py`) — 26 views

### Helper
```python
def _check_payroll(request):
    # Kiểm tra app_payroll_active + features['app_payroll']
    # Giống pattern _check_attendance() trong attendance/views.py
```

### Module Cấu hình (6 views)
| View | URL | Mô tả |
|---|---|---|
| `payroll_home` | `/payroll/` | Trang chủ — quick stats, links |
| `salary_config_manage` | `/payroll/config/` | Xem/sửa cấu hình BH+thuế theo năm |
| `allowance_type_list` | `/payroll/allowances/` | DS loại phụ cấp |
| `allowance_type_create` | `/payroll/allowances/create/` | Thêm loại phụ cấp |
| `allowance_type_update` | `/payroll/allowances/<pk>/edit/` | Sửa |
| `allowance_type_delete` | `/payroll/allowances/<pk>/delete/` | Xóa |

### Module Phụ cấp NV (4 views)
| View | URL | Mô tả |
|---|---|---|
| `employee_allowance_list` | `/payroll/employee-allowances/` | DS phụ cấp theo NV (filter phòng ban) |
| `employee_allowance_create` | `/payroll/employee-allowances/create/` | Thêm phụ cấp cho NV |
| `employee_allowance_update` | `/payroll/employee-allowances/<pk>/edit/` | Sửa |
| `employee_allowance_delete` | `/payroll/employee-allowances/<pk>/delete/` | Xóa |

### Module Kỳ lương (10 views)
| View | URL | Mô tả |
|---|---|---|
| `period_list` | `/payroll/periods/` | DS kỳ lương |
| `period_create` | `/payroll/periods/create/` | Tạo kỳ lương mới |
| `period_detail` | `/payroll/periods/<pk>/` | Chi tiết kỳ + danh sách phiếu lương |
| `period_delete` | `/payroll/periods/<pk>/delete/` | Xóa (chỉ khi draft) |
| `period_calculate` | `/payroll/periods/<pk>/calculate/` | Tính lương hàng loạt (POST) |
| `period_submit` | `/payroll/periods/<pk>/submit/` | Nộp duyệt (POST) |
| `period_approve` | `/payroll/periods/<pk>/approve/` | Duyệt (POST, superuser) |
| `period_reject` | `/payroll/periods/<pk>/reject/` | Từ chối (POST) |
| `period_mark_paid` | `/payroll/periods/<pk>/paid/` | Đánh dấu đã thanh toán (POST) |
| `period_export` | `/payroll/periods/<pk>/export/` | Xuất bảng lương Excel |

### Module Phiếu lương (4 views)
| View | URL | Mô tả |
|---|---|---|
| `payslip_list` | `/payroll/payslips/` | DS phiếu lương (NV xem của mình, HR xem tất cả) |
| `payslip_detail` | `/payroll/payslips/<pk>/` | Chi tiết phiếu lương |
| `payslip_print` | `/payroll/payslips/<pk>/print/` | In phiếu lương |
| `payslip_update` | `/payroll/payslips/<pk>/edit/` | HR điều chỉnh thủ công (bonus, other_deductions) |

### Module Dashboard (2 views)
| View | URL | Mô tả |
|---|---|---|
| `payroll_dashboard` | `/payroll/dashboard/` | Dashboard: KPI tháng, chi phí theo phòng ban, Chart.js |
| `payroll_dashboard_export` | `/payroll/dashboard/export/` | Xuất báo cáo Excel tổng hợp |

---

## Bước 5 — Forms (`payroll/forms.py`) — 8 forms

```python
SalaryConfigForm          # Cấu hình BH/thuế
AllowanceTypeForm         # Loại phụ cấp
EmployeeAllowanceForm     # Phụ cấp từng NV (với date picker)
PayrollPeriodForm         # Tạo kỳ lương (chọn tháng/năm)
PayrollCalculateForm      # Xác nhận tính lương hàng loạt (chọn config năm)
PayslipUpdateForm         # HR điều chỉnh (bonus, other_deductions, note)
PeriodApproveForm         # Duyệt (comment)
PeriodRejectForm          # Từ chối (comment bắt buộc)
```

---

## Bước 6 — Templates (18 files trong `payroll/templates/payroll/`)

| File | Dùng cho |
|---|---|
| `payroll_home.html` | Trang chủ — thống kê nhanh, card kỳ lương gần nhất, links |
| `salary_config_form.html` | Cấu hình BH/thuế — hiển thị cả công thức tính |
| `allowance_type_list.html` | DS loại phụ cấp dạng bảng |
| `allowance_type_form.html` | Form thêm/sửa loại phụ cấp |
| `allowance_type_confirm_delete.html` | Xác nhận xóa loại phụ cấp |
| `employee_allowance_list.html` | DS phụ cấp NV — group theo NV, filter phòng ban |
| `employee_allowance_form.html` | Form thêm/sửa phụ cấp NV |
| `employee_allowance_confirm_delete.html` | Xác nhận xóa |
| `period_list.html` | DS kỳ lương — badge status, tổng gross/net |
| `period_form.html` | Tạo kỳ lương mới |
| `period_detail.html` | Chi tiết kỳ + bảng phiếu lương + nút actions (tính/duyệt/xuất) |
| `period_confirm_delete.html` | Xác nhận xóa kỳ lương |
| `payslip_list.html` | DS phiếu (NV thấy của mình, HR thấy tất cả + filter) |
| `payslip_detail.html` | Chi tiết phiếu lương — bố cục như phiếu lương thật |
| `payslip_print.html` | Bản in phiếu lương A4 (không có topbar, dùng window.print()) |
| `payslip_form.html` | HR điều chỉnh bonus, khấu trừ khác |
| `payroll_dashboard.html` | Dashboard: KPI cards + Chart.js bar/pie + bảng theo phòng ban |

---

## Bước 7 — Kết nối hệ thống

### `myproject/settings.py`
```python
INSTALLED_APPS = [..., 'payroll']
```

### `myproject/urls.py`
```python
path('payroll/', include('payroll.urls')),
```

### `employees/templates/employees/home.html`
Đổi `href="#"` → `href="{% url 'payroll:payroll_home' %}"` cho card Tính lương

### Kiểm tra `system_settings`
- `settings_home.html` đã có toggle "Tính lương" — không cần thêm
- `toggle_app` view đã xử lý `app_payroll` — không cần thêm

---

## Bước 8 — Dữ liệu mặc định (migration `0001`)

```python
SalaryConfig.objects.get_or_create(
    year=2026,
    defaults={
        'bhxh_employee_rate': 8.00,
        'bhyt_employee_rate': 1.50,
        'bhtn_employee_rate': 1.00,
        'bhxh_employer_rate': 17.50,
        'bhyt_employer_rate': 3.00,
        'bhtn_employer_rate': 1.00,
        'si_salary_cap': 46_800_000,
        'bhtn_salary_cap': 93_600_000,
        'personal_deduction': 15_500_000,
        'dependent_deduction': 6_200_000,
        'is_active': True,
    }
)
```

---

## Công thức tính lương — tóm tắt

```
1. base_salary = Contract(status=hieu_luc).salary ?? Employee.salary
2. standard_days = ngày thường trong tháng - PublicHoliday
3. actual_days = Σ AttendanceRecord (present=1, half_day=0.5, on_leave_paid=1)
4. actual_salary = base_salary × (actual_days / standard_days)
5. ot_hours = Σ AttendanceRecord.ot_hours
6. ot_pay = (base_salary / standard_days / 8) × ot_hours × 1.5
7. allowances = Σ EmployeeAllowance active (fixed + % of base)
8. gross = actual_salary + allowances_taxable + allowances_nontax + ot_pay + bonus
9. taxable_gross = actual_salary + allowances_taxable + bonus  [không gồm ot_pay, allowances_nontax]
10. si_base = min(si_salary ?? base_salary, si_salary_cap)
11. bhxh_emp = si_base × 8%, bhyt_emp = si_base × 1.5%, bhtn_emp = min(si_base, bhtn_cap) × 1%
12. total_si_emp = bhxh + bhyt + bhtn
13. taxable_net = taxable_gross - total_si_emp - personal_deduction - dependent_deduction × num_dep
14. pit = calculate_pit_2026(max(0, taxable_net))
    Biểu 5 bậc:  ≤10M → 5% | ≤30M → 10% | ≤60M → 20% | ≤100M → 30% | >100M → 35%
15. net_salary = gross - total_si_emp - pit - other_deductions
```

---

## Thứ tự thực hiện

1. Tạo app skeleton (apps.py, __init__.py, migrations/__init__.py)
2. Viết `models.py` + `calculator.py`
3. `python manage.py makemigrations payroll` → `migrate`
4. Viết `forms.py`
5. Viết `urls.py` (app_name = 'payroll')
6. Viết `views.py` (từng nhóm: config → period → payslip → dashboard)
7. Tạo 18 templates (mỗi nhóm theo views)
8. Kết nối settings.py, urls.py, home.html
9. Thêm `{% include 'employees/includes/auto_logout.html' %}` vào tất cả templates
10. `python manage.py check`

---

## File thay đổi

**Tạo mới:**
- `payroll/` (toàn bộ app — ~8 Python files + 18 templates)

**Sửa:**
- `myproject/settings.py` — thêm 'payroll' vào INSTALLED_APPS
- `myproject/urls.py` — include payroll.urls
- `employees/templates/employees/home.html` — cập nhật href card Tính lương

**Không cần sửa** (đã có sẵn):
- `employees/models.py` — app_payroll đã có
- `employees/helpers.py` — get_user_features đã trả về app_payroll
- `system_settings/models.py` — app_payroll_active đã có
- `system_settings/views.py` — toggle_app đã xử lý payroll
- `settings_home.html` — toggle card đã có

---

## Kiểm tra sau khi hoàn thành

1. `python manage.py check` — 0 lỗi
2. `python manage.py migrate` — migrate thành công
3. Vào `/settings/` → Kích hoạt "Tính lương"
4. Truy cập `/payroll/` từ trang chủ → hiển thị đúng
5. Vào `/payroll/config/` → thiết lập SalaryConfig năm 2026
6. Thêm loại phụ cấp + gán cho NV
7. Tạo kỳ lương tháng 5/2026 → Tính lương → xem phiếu lương NV có AttendanceRecord
8. Kiểm tra gross/net/thuế với công thức thủ công bên ngoài → khớp nhau
9. Duyệt kỳ lương → Đánh dấu đã trả → Xuất Excel
10. NV thường vào `/payroll/payslips/` → chỉ thấy phiếu của mình
