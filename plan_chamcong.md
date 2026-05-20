# Kế hoạch: App Chấm công & Nghỉ phép (`attendance`)

## Context

HRM app đã có 4 app (employees, contracts, system_settings, talent). Cần xây dựng thêm app `attendance` quản lý chấm công và nghỉ phép. Hạ tầng đã sẵn sàng: `AppStatus.app_attendance_active`, `UserProfile.app_attendance`, `StaffGroup.app_attendance`, `get_user_features()` đều đã có sẵn — chỉ cần tạo app mới và kết nối.

**Quyết định thiết kế:**
- 1 app duy nhất `attendance` (gộp chấm công + nghỉ phép) — 2 module tách biệt trong cùng app
- Approval 2 cấp: Trưởng phòng (level 1, có can_edit trên EmployeeGroup) → HR/Admin (level 2, superuser)
- Nhập chấm công: Admin nhập tay + Import Excel/CSV
- Số dư phép: Tự động tính 12 ngày + 1 ngày/5 năm thâm niên, có thể override thủ công

---

## Bước 1 — Tạo app skeleton

```
attendance/
├── __init__.py
├── apps.py
├── admin.py
├── models.py
├── forms.py
├── views.py
├── urls.py             # app_name = 'attendance'
├── migrations/
│   └── __init__.py
└── templates/attendance/
    └── (20 template files)
```

---

## Bước 2 — Models (`attendance/models.py`)

### Module 1: Chấm công

```python
class WorkShift(Model):
    name            # "Ca hành chính", "Ca sáng", "Ca chiều"
    start_time      # TimeField
    end_time        # TimeField
    break_minutes   # IntegerField (phút nghỉ, mặc định 60)
    standard_hours  # DecimalField (giờ chuẩn, mặc định 8.0)
    is_active

class PublicHoliday(Model):
    name    # "Tết Nguyên Đán ngày 1"
    date    # DateField (unique)
    year    # IntegerField

class AttendanceRecord(Model):
    STATUS = [present, absent, half_day, late, on_leave, holiday]
    SOURCE = [manual, import_file, system]

    employee      # FK → Employee (on_delete=CASCADE)
    date          # DateField
    shift         # FK → WorkShift (null=True)
    check_in      # TimeField (null=True)
    check_out     # TimeField (null=True)
    actual_hours  # DecimalField (tính tự động)
    ot_hours      # DecimalField (phần dư sau standard_hours)
    status        # CharField choices
    source        # CharField choices
    note
    created_by    # FK → User (null=True, SET_NULL)
    created_at

    class Meta:
        unique_together = ('employee', 'date')

    def calculate_hours():  # tính actual_hours và ot_hours khi save
```

### Module 2: Nghỉ phép

```python
class LeaveType(Model):
    name                # "Nghỉ phép năm", "Nghỉ ốm", "Nghỉ thai sản"
    code                # annual / sick / maternity / paternity / other
    max_days_per_year   # 0 = không giới hạn
    is_paid
    requires_approval
    allow_half_day
    document_required
    carry_over          # BooleanField (chuyển năm sau)
    gender_restriction  # all / female / male
    is_active

class LeavePolicy(Model):
    name                # "Chính sách mặc định"
    base_annual_days    # 12
    increment_years     # 5 (cứ 5 năm)
    increment_days      # 1 (cộng thêm 1 ngày)
    is_default

class LeaveBalance(Model):
    employee         # FK → Employee
    leave_type       # FK → LeaveType
    year             # IntegerField
    allocated_days   # DecimalField
    used_days        # DecimalField (tự cộng khi approve)
    pending_days     # DecimalField (đang chờ duyệt)
    carried_days     # DecimalField (chuyển từ năm trước)
    note

    class Meta:
        unique_together = ('employee', 'leave_type', 'year')

    @property
    def remaining_days():
        return allocated_days + carried_days - used_days - pending_days

class LeaveRequest(Model):
    STATUS = [
        ('draft',       'Nháp'),
        ('pending',     'Chờ duyệt cấp 1'),
        ('waiting_hr',  'Chờ HR duyệt'),
        ('approved',    'Đã duyệt'),
        ('rejected',    'Từ chối'),
        ('cancelled',   'Đã hủy'),
    ]
    employee        # FK → Employee
    leave_type      # FK → LeaveType
    start_date
    end_date
    total_days      # DecimalField (tính tự động, bỏ qua PublicHoliday)
    half_day        # BooleanField
    half_day_period # morning / afternoon
    reason
    document        # FileField (null=True)
    status
    created_at / updated_at / approved_at

class LeaveApproval(Model):
    leave_request  # FK → LeaveRequest
    approver       # FK → User
    level          # IntegerField (1 hoặc 2)
    action         # approved / rejected / forwarded
    comment
    acted_at
```

---

## Bước 3 — Logic nghiệp vụ quan trọng

### Tính số ngày phép tự động
```python
def calculate_allocated_days(employee, year):
    years_of_service = (date(year, 12, 31) - employee.start_date).days / 365
    policy = LeavePolicy.objects.filter(is_default=True).first()
    base = policy.base_annual_days       # 12
    bonus = int(years_of_service / policy.increment_years) * policy.increment_days
    return base + bonus
```

### Luồng duyệt 2 cấp
```
NV tạo đơn (status=pending)
    → Level 1 (can_edit trên EmployeeGroup của NV): Approve → status=waiting_hr
    → Level 2 (superuser): Approve → status=approved
       • Tự động: LeaveBalance.used_days += total_days, pending_days -= total_days
       • Tự động: tạo AttendanceRecord(status='on_leave') cho từng ngày nghỉ
Reject ở bất kỳ cấp: status=rejected, hoàn pending_days
Hủy đơn (pending/waiting_hr): status=cancelled, hoàn pending_days
```

### Tính giờ làm & OT
```python
def calculate_hours(check_in, check_out, shift):
    raw_minutes = (check_out - check_in).seconds // 60
    worked = raw_minutes - shift.break_minutes
    actual = round(worked / 60, 2)
    ot = max(0, actual - float(shift.standard_hours))
    return actual, ot
```

### Import Excel chấm công
- Cột: Mã NV, Ngày, Giờ vào, Giờ ra, Ghi chú
- Tự match employee_code → Employee, tính actual_hours/ot_hours tự động
- Report: thành công / bỏ qua (trùng) / lỗi

---

## Bước 4 — Views (28 views)

### Chấm công (12 views)
| View | URL | Mô tả |
|---|---|---|
| `attendance_home` | `/attendance/` | Trang chủ module |
| `attendance_list` | `/attendance/records/` | Bảng chấm công, filter tháng/NV/phòng ban |
| `attendance_create` | `/attendance/records/create/` | Thêm bản ghi thủ công |
| `attendance_update` | `/attendance/records/<pk>/edit/` | Sửa bản ghi |
| `attendance_delete` | `/attendance/records/<pk>/delete/` | Xóa bản ghi |
| `attendance_import` | `/attendance/records/import/` | Import Excel từ máy chấm công |
| `attendance_export` | `/attendance/records/export/` | Xuất báo cáo tháng Excel |
| `shift_list` | `/attendance/shifts/` | Danh sách ca làm việc |
| `shift_create` | `/attendance/shifts/create/` | Thêm ca |
| `shift_update` | `/attendance/shifts/<pk>/edit/` | Sửa ca |
| `shift_delete` | `/attendance/shifts/<pk>/delete/` | Xóa ca |
| `holiday_manage` | `/attendance/holidays/` | Quản lý ngày lễ (inline) |

### Nghỉ phép (16 views)
| View | URL | Mô tả |
|---|---|---|
| `leave_request_list` | `/attendance/leaves/` | DS đơn — tab "Của tôi / Chờ duyệt" |
| `leave_request_create` | `/attendance/leaves/create/` | Tạo đơn xin nghỉ |
| `leave_request_detail` | `/attendance/leaves/<pk>/` | Chi tiết + timeline duyệt |
| `leave_request_cancel` | `/attendance/leaves/<pk>/cancel/` | Hủy đơn |
| `leave_approve` | `/attendance/leaves/<pk>/approve/` | Duyệt (level 1 hoặc 2) |
| `leave_reject` | `/attendance/leaves/<pk>/reject/` | Từ chối |
| `leave_balance_list` | `/attendance/balance/` | Số dư ngày phép |
| `leave_balance_edit` | `/attendance/balance/<pk>/edit/` | Điều chỉnh thủ công |
| `leave_balance_init` | `/attendance/balance/init/` | Khởi tạo số dư đầu năm (bulk) |
| `leave_type_list` | `/attendance/leave-types/` | DS loại nghỉ phép |
| `leave_type_create` | `/attendance/leave-types/create/` | Thêm loại |
| `leave_type_update` | `/attendance/leave-types/<pk>/edit/` | Sửa loại |
| `leave_type_delete` | `/attendance/leave-types/<pk>/delete/` | Xóa loại |
| `leave_policy_manage` | `/attendance/policy/` | Sửa chính sách phép năm |
| `attendance_dashboard` | `/attendance/dashboard/` | Dashboard tổng hợp |
| `attendance_dashboard_export` | `/attendance/dashboard/export/` | Xuất báo cáo Excel |

---

## Bước 5 — Templates (20 files)

| File | Dùng cho |
|---|---|
| `attendance_home.html` | Trang chủ — 2 card lớn (Chấm công / Nghỉ phép) + quick stats |
| `attendance_list.html` | Bảng chấm công + filter + sort + pagination |
| `attendance_form.html` | Thêm/sửa bản ghi thủ công |
| `attendance_confirm_delete.html` | Xác nhận xóa |
| `attendance_import.html` | Upload Excel + kết quả import |
| `attendance_dashboard.html` | Dashboard: KPI cards + chart + bảng OT |
| `shift_list.html` | Danh sách ca |
| `shift_form.html` | Form ca làm việc |
| `shift_confirm_delete.html` | Xác nhận xóa ca |
| `holiday_manage.html` | Danh sách + thêm/xóa ngày lễ |
| `leave_request_list.html` | DS đơn + filter + tab |
| `leave_request_form.html` | Form tạo đơn (loại, ngày, lý do, upload) |
| `leave_request_detail.html` | Chi tiết + timeline duyệt + nút approve/reject |
| `leave_request_confirm_cancel.html` | Xác nhận hủy |
| `leave_balance_list.html` | Bảng số dư phép — filter năm/phòng ban |
| `leave_balance_form.html` | Form điều chỉnh số dư |
| `leave_balance_init.html` | Khởi tạo số dư đầu năm |
| `leave_type_list.html` | DS loại nghỉ phép |
| `leave_type_form.html` | Form thêm/sửa loại |
| `leave_policy_form.html` | Form sửa chính sách phép năm |

---

## Bước 6 — Kết nối hệ thống hiện tại

### `employees/models.py`
Thêm vào `ActivityLog.TARGET_CHOICES`:
```python
('attendance', 'Chấm công'),
('leave',      'Nghỉ phép'),
```
→ Migration `employees/migrations/0023_add_attendance_leave_target.py`

### `myproject/settings.py`
```python
INSTALLED_APPS = [..., 'attendance']
```

### `myproject/urls.py`
```python
path('attendance/', include('attendance.urls')),
```

### `employees/templates/employees/home.html`
Card "Chấm công" → active khi `app_status.app_attendance_active and features.app_attendance`

### `system_settings/templates/system_settings/settings_home.html`
Kiểm tra card "Chấm công" — thêm nếu thiếu

---

## Bước 7 — Dữ liệu mặc định (migration 0001)

Tạo sẵn trong migration:
- `WorkShift`: Ca hành chính (8:00–17:00, 60 phút nghỉ, 8h chuẩn)
- `LeavePolicy`: Chính sách mặc định (12 ngày, +1/5 năm, is_default=True)
- `LeaveType` mặc định (7 loại):
  - Nghỉ phép năm (annual, paid, carry_over)
  - Nghỉ ốm (sick, paid, doc_required)
  - Nghỉ thai sản nữ (maternity, paid, female)
  - Nghỉ thai sản nam (paternity, paid, male)
  - Nghỉ kết hôn (other, paid, 3 ngày)
  - Nghỉ tang chế (other, paid, 3 ngày)
  - Nghỉ không lương (other, unpaid)

---

## Thứ tự thực hiện

1. Tạo app skeleton
2. Viết `models.py` → `makemigrations` → `migrate`
3. Update `employees/models.py` + migration 0023
4. Viết `forms.py`
5. Viết `urls.py`
6. Viết `views.py` (nhóm: shift → holiday → attendance → leave)
7. Tạo 20 templates
8. Kết nối `settings.py`, `urls.py`, `home.html`, `settings_home.html`
9. Thêm `auto_logout.html` include vào tất cả templates mới
10. Chạy `python manage.py check`

---

## Kiểm tra sau khi hoàn thành

1. `python manage.py check` — không lỗi
2. Truy cập `/attendance/` → trang chủ app
3. Tạo ca làm việc, thêm ngày lễ
4. Thêm bản ghi chấm công thủ công → actual_hours/ot_hours tính đúng
5. Import file Excel → kết quả đúng
6. Tạo đơn xin nghỉ → duyệt 2 cấp → LeaveBalance.used_days tăng
7. Hủy đơn → LeaveBalance.used_days giảm trở lại
8. Khởi tạo số dư phép năm → thâm niên tính đúng
9. `/settings/` toggle Chấm công → card đổi trạng thái
10. Dashboard: KPI cards, chart hiển thị
11. Xuất Excel báo cáo tháng
