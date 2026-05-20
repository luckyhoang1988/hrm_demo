# Kế hoạch Triển khai App `contracts` — Quản lý Hợp đồng Lao động

## Context

Project HRM hiện tại đã có `app_contracts: BooleanField` trong `UserProfile` và `StaffGroup` — tức là hệ thống phân quyền đã sẵn sàng nhận app contracts. Cần xây dựng app mới `contracts` theo đúng pattern của `employees` (FBV, standalone template, inline CSS/JS, log_activity, base_filter_qs, Paginator 50/trang).

---

## Cấu trúc thư mục app `contracts`

```
myproject/
└── contracts/
    ├── __init__.py
    ├── apps.py
    ├── admin.py
    ├── models.py
    ├── forms.py
    ├── views.py
    ├── urls.py
    ├── migrations/
    │   └── __init__.py
    └── templates/contracts/
        ├── contract_list.html
        ├── contract_form.html
        ├── contract_detail.html
        ├── contract_confirm_delete.html
        ├── contract_renew.html
        └── contract_dashboard.html
```

---

## Phase 1 — Foundation

### Bước 1: Tạo app skeleton
```
python manage.py startapp contracts
```

### Bước 2: Đăng ký app và URL

**`myproject/settings.py`** — thêm `'contracts'` vào `INSTALLED_APPS`.

**`myproject/urls.py`** — thêm:
```python
path('contracts/', include('contracts.urls')),
```

### Bước 3: `contracts/models.py`

#### Model `Contract`

| Field | Type | Mô tả |
|---|---|---|
| `contract_number` | CharField(50, unique) | Số HĐ — tự uppercase |
| `employee` | FK → Employee (PROTECT) | Nhân viên |
| `department` | FK → Department (PROTECT) | Phòng ban tại thời điểm ký |
| `contract_type` | CharField choices | 5 loại (xem bên dưới) |
| `status` | CharField choices | 5 trạng thái (xem bên dưới) |
| `start_date` | DateField | Ngày bắt đầu |
| `end_date` | DateField (null/blank) | Ngày kết thúc — null với HĐ không XĐ thời hạn |
| `position` | CharField(100, blank) | Chức vụ khi ký |
| `salary` | DecimalField(12,2, null/blank) | Lương theo HĐ |
| `renewed_from` | FK → self (null, SET_NULL) | Gia hạn từ HĐ nào |
| `termination_date` | DateField (null/blank) | Ngày chấm dứt |
| `termination_reason` | CharField choices | Lý do chấm dứt |
| `termination_note` | TextField(blank) | Ghi chú chấm dứt |
| `note` | TextField(blank) | Ghi chú chung |
| `created_at` | DateTimeField(auto_now_add) | |
| `updated_at` | DateTimeField(auto_now) | |

**TYPE_CHOICES (5 loại):**
```python
('thu_viec',   'Thử việc')
('xd_1_nam',   'HDLĐ xác định thời hạn 1 năm')
('xd_3_nam',   'HDLĐ xác định thời hạn 3 năm')
('khong_xd',   'HDLĐ không xác định thời hạn')
('thuc_tap',   'Hợp đồng thực tập')
```

**STATUS_CHOICES (5 trạng thái):**
```python
('hieu_luc',    'Còn hiệu lực')
('sap_het_han', 'Sắp hết hạn')   # ≤ 30 ngày, tính tự động
('het_han',     'Hết hạn')
('gia_han',     'Đã gia hạn')
('cham_dut',    'Đã chấm dứt')
```

**Properties trên Contract:**
- `days_until_expiry` → số ngày đến `end_date` (None nếu không có)
- `is_expiring_soon` → True nếu 0 ≤ days_until_expiry ≤ 30
- `is_expired` → True nếu qua `end_date`
- `is_indefinite` → True nếu `contract_type == 'khong_xd'`

**Lưu ý migration:** Migration 0001 của contracts cần `dependencies = [('employees', '0020_activitylog')]` vì có FK sang `Employee` và `Department`.

### Bước 4: Tạo và chạy migration
```
python manage.py makemigrations contracts
python manage.py migrate
python manage.py check
```

### Bước 5: `contracts/admin.py`
```python
@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['contract_number', 'employee', 'contract_type', 'status', 'start_date', 'end_date']
    list_filter  = ['status', 'contract_type']
    search_fields = ['contract_number', 'employee__full_name']
```

---

## Phase 2 — Forms + Views

### Bước 6: `contracts/forms.py`

**`ContractForm`** (ModelForm — dùng cho create/update):
- Fields: contract_number, employee, department, contract_type, start_date, end_date, position, salary, note
- `employee`: ModelChoiceField lọc `status__in=['dang_lam','thu_viec','thuc_tap_sinh']`
- `department`: ModelChoiceField `to_field_name='name'` (nhất quán với EmployeeForm)
- Widgets: DateInput type=date cho start_date, end_date
- `clean_contract_number()`: uppercase + strip
- `clean()`: bắt buộc `end_date` nếu không phải `khong_xd`; validate end_date > start_date; check trùng số HĐ

**`ContractRenewForm`** (ModelForm — dùng riêng cho view gia hạn):
- Fields: contract_number, contract_type, start_date, end_date, position, salary, note
- Cùng validation logic, không có employee/department (lấy từ HĐ cũ)

**`ContractTerminateForm`** (Form — dùng cho view chấm dứt):
- Fields: termination_date (DateInput), termination_reason (ChoiceField), termination_note (Textarea)

### Bước 7: `contracts/views.py`

**Imports từ employees:**
```python
from employees.views import get_user_features, log_activity, _get_client_ip
```

**Utility function — `auto_update_contract_statuses()`:**
- Bulk update `status='het_han'` khi `end_date < today` và status chưa terminal
- Bulk update `status='sap_het_han'` khi `end_date` trong 30 ngày tới
- Gọi ở đầu `contract_list` (tương tự `auto_terminate_employees()`)

**Danh sách views:**

| View | Method | Quyền |
|---|---|---|
| `contract_list` | GET + auto_update | `app_contracts` |
| `contract_create` | GET/POST | `app_contracts` |
| `contract_detail` | GET | `app_contracts` |
| `contract_update` | GET/POST | `app_contracts` |
| `contract_delete` | GET/POST | `app_contracts` |
| `contract_renew` | GET/POST | `app_contracts` |
| `contract_terminate` | GET/POST | `app_contracts` |
| `contract_dashboard` | GET | `app_contracts` + `can_view_dashboard` |
| `contract_export_excel` | GET | `app_contracts` + `can_export` |

**Pattern phân quyền:**
```python
features = get_user_features(request.user)
if not features['app_contracts']:
    return redirect('home')
```

**`contract_list` — Filter fields:** employee (text, search full_name + employee_code + contract_number), department (dropdown), contract_type (select), status (select), date_from/date_to (start_date range), expiring=true

**`contract_list` — Sort fields:** contract_number, employee__full_name, department__name, contract_type, status, start_date, end_date

**`contract_renew` logic:**
1. Lấy HĐ cũ, pre-fill form (contract_type, position, salary, start_date=old.end_date)
2. Khi POST: tạo HĐ mới với `renewed_from=old_contract`
3. Cập nhật HĐ cũ `status='gia_han'`
4. log_activity với detail="Gia hạn từ HĐ {old_number}"

**`contract_dashboard` — Context:**
- status_counts: `qs.values('status').annotate(cnt=Count('id'))`
- type_counts: `qs.values('contract_type').annotate(cnt=Count('id'))`
- expiring_soon: HĐ hết hạn ≤ 30 ngày
- overdue: HĐ đã hết hạn chưa xử lý
- dept_stats: thống kê theo phòng ban

**Log activity cho mọi write operation:**
```python
log_activity(user, action, 'contract', contract_number, detail, ip)
```

### Bước 8: `contracts/urls.py`
```python
urlpatterns = [
    path('',                    views.contract_list,          name='contract_list'),
    path('create/',             views.contract_create,        name='contract_create'),
    path('<int:pk>/',           views.contract_detail,        name='contract_detail'),
    path('<int:pk>/edit/',      views.contract_update,        name='contract_update'),
    path('<int:pk>/delete/',    views.contract_delete,        name='contract_delete'),
    path('<int:pk>/renew/',     views.contract_renew,         name='contract_renew'),
    path('<int:pk>/terminate/', views.contract_terminate,     name='contract_terminate'),
    path('dashboard/',          views.contract_dashboard,     name='contract_dashboard'),
    path('export/excel/',       views.contract_export_excel,  name='contract_export_excel'),
]
```

---

## Phase 3 — Templates

**Nguyên tắc:** standalone HTML, không extend base, inline CSS + JS, màu `#1565C0`/`#4CAF50`/`#c62828`/`#FF9800`, icons emoji.

### `contract_list.html`
- Topbar xanh `#1565C0`, breadcrumb: `🏠 > 📄 Hợp đồng`
- Filter box (employee text, phòng ban dropdown, loại HĐ, trạng thái, ngày từ–đến)
- Alert banner cam nếu có HĐ sắp hết hạn
- Bảng sortable, badge màu theo status (xanh/cam/đỏ/tím/xám)
- Pagination 50/trang dùng `base_filter_qs`
- Nút "Thêm HĐ mới" + "Export Excel" (tuỳ quyền)

**Status badge colors:**
```
hieu_luc    → #4CAF50 (xanh)
sap_het_han → #FF9800 (cam)
het_han     → #c62828 (đỏ)
gia_han     → #7B1FA2 (tím)
cham_dut    → #607D8B (xám)
```

### `contract_form.html`
- Layout 2 cột: form trái, info card nhân viên phải
- JS auto-fill: khi chọn NV → fill department, position, salary (dùng inline JSON dict từ context `employee_data_json`)
- JS toggle: ẩn/hiện `end_date` khi chọn `khong_xd`
- Hiển thị lỗi form nhất quán

### `contract_detail.html`
- Layout 2 cột: sidebar (thông tin HĐ + buttons) + main (lịch sử gia hạn)
- Alert đỏ/cam nếu `is_expiring_soon` hoặc `is_expired`
- Timeline gia hạn qua `renewals.all()` + link `renewed_from`
- Link sang `employee_detail` nhân viên liên quan

### `contract_confirm_delete.html`, `contract_renew.html`, `contract_dashboard.html`
- Confirm delete: card cảnh báo, hiện số HĐ + tên NV
- Renew: thông tin HĐ cũ readonly + form HĐ mới bên dưới
- Dashboard: KPI cards, alert sắp hết hạn, donut chart (Chart.js CDN), bảng theo phòng ban

---

## Phase 4 — Tích hợp giao diện

### Bước 13: `employees/views.py` — sửa view `home`
Thêm `features` vào context:
```python
@login_required
def home(request):
    features = get_user_features(request.user)
    return render(request, 'employees/home.html', {'features': features})
```

### Bước 14: `employees/templates/employees/home.html`
Đổi card "Hợp đồng Lao động" từ disabled → active có điều kiện:
```html
{% if features.app_contracts %}
<a href="{% url 'contract_list' %}" class="app-card">...📄 Hợp đồng Lao động...</a>
{% else %}
<div class="app-card disabled">...
{% endif %}
```

---

## Files cần thay đổi / tạo mới

**Tạo mới:**
- `contracts/__init__.py`, `apps.py`, `admin.py`, `models.py`, `forms.py`, `views.py`, `urls.py`
- `contracts/migrations/__init__.py` + `0001_initial.py` (generate tự động)
- `contracts/templates/contracts/` — 6 template files

**Sửa đổi:**
- `myproject/settings.py` — thêm `'contracts'` vào INSTALLED_APPS
- `myproject/urls.py` — thêm `path('contracts/', include('contracts.urls'))`
- `employees/views.py` — sửa view `home` để truyền `features` context
- `employees/templates/employees/home.html` — kích hoạt card Hợp đồng

---

## Hàm tái dụng từ `employees`

| Hàm | File | Dùng trong contracts |
|---|---|---|
| `get_user_features(user)` | `employees/views.py:131` | Kiểm tra `app_contracts`, `can_export`, `can_view_dashboard` |
| `log_activity(...)` | `employees/views.py:32` | Log mọi thao tác CRUD |
| `_get_client_ip(request)` | `employees/views.py:27` | Lấy IP cho log_activity |

---

## Xác minh sau khi hoàn thành

1. `python manage.py check` — không có lỗi
2. `python manage.py migrate` — migration thành công
3. Vào Django Admin, tạo thử 1 Contract
4. Truy cập `/contracts/` — hiện danh sách
5. Tạo HĐ mới: chọn NV → auto-fill phòng ban/chức vụ/lương; chọn loại → ẩn/hiện end_date
6. Gia hạn HĐ: HĐ cũ chuyển sang "Đã gia hạn", HĐ mới có link `renewed_from`
7. Chấm dứt HĐ: status → "Đã chấm dứt", có termination_date + reason
8. Export Excel: file tải về có màu theo trạng thái
9. Dashboard: KPI cards + biểu đồ hiển thị đúng
10. Trang chủ: user có `app_contracts=True` thấy card Hợp đồng active; user không có quyền thấy disabled
11. ActivityLog: kiểm tra `/employees/activity-log/` ghi đúng các action contracts
