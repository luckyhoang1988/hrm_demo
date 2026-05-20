# Kế hoạch triển khai đa ngôn ngữ (i18n) — Thêm tiếng Anh

## Context

HRM App hiện tại hardcode hoàn toàn tiếng Việt (~750–1060 strings trên 34 templates + Python code). Mục tiêu: thêm tiếng Anh (EN) là ngôn ngữ thứ 2, người dùng chuyển đổi qua nút trên giao diện. Tiếng Việt vẫn là mặc định.

---

## Quy mô công việc (ước tính)

| Phần | Số strings cần dịch | Ghi chú |
|------|-------------------|---------|
| Templates (34 file HTML) | ~600–800 | Phần lớn nhất |
| models.py (2 file) | ~81 | Choices labels, verbose_name |
| views.py (2 file) | ~150 | messages.success/error, export headers |
| forms.py (2 file) | ~14 | label, error messages |
| **Tổng** | **~850–1050** | |

**Thời gian ước tính toàn bộ: 10–15 ngày dev** (phần nhiều là dịch + wrap từng template)

---

## Quyết định kỹ thuật

### Cách chuyển ngôn ngữ: Session-based (không đổi URL)
- **Không dùng** `i18n_patterns()` vì sẽ đổi tất cả URL hiện tại (`/employees/` → `/vi/employees/`)
- **Dùng** Django's built-in `set_language` view + `LocaleMiddleware`
- Ngôn ngữ lưu trong **session** → mọi trang tự áp dụng
- URL giữ nguyên, không ảnh hưởng bookmark hoặc activity log

### Language switcher: Include template tái sử dụng
- Tạo file `_language_switcher.html` — component nút 🇻🇳/🇺🇸
- Mỗi template chỉ cần thêm `{% include 'employees/_language_switcher.html' %}` vào topbar
- Tránh lặp code trên 34 file

---

## Tiền đề bắt buộc (cần làm trước)

**Cài gettext tools trên Windows** — bắt buộc để chạy `makemessages`:
```
choco install gettext
# HOẶC tải tại: https://mlocalization.github.io/
```
Kiểm tra: `xgettext --version` phải trả về output.

---

## Giai đoạn 1 — Hạ tầng Django i18n (1 ngày)

### 1.1 `myproject/settings.py`
```python
from django.utils.translation import gettext_lazy as _

LANGUAGE_CODE = 'vi'          # đổi từ 'en-us'
USE_I18N = True               # đã có

LANGUAGES = [
    ('vi', _('Tiếng Việt')),
    ('en', _('English')),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

MIDDLEWARE = [
    ...
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',   # THÊM — sau SessionMiddleware
    'django.middleware.common.CommonMiddleware',
    ...
]
```

### 1.2 `myproject/urls.py`
```python
from django.conf.urls.i18n import set_language
urlpatterns = [
    ...
    path('i18n/setlang/', set_language, name='set_language'),  # THÊM
]
```

### 1.3 Tạo cấu trúc thư mục locale
```
myproject/locale/
├── vi/LC_MESSAGES/django.po  (tiếng Việt — nguồn)
└── en/LC_MESSAGES/django.po  (tiếng Anh — cần dịch)
```

### 1.4 Tạo `employees/templates/employees/_language_switcher.html`
```html
{% load i18n %}
<form method="post" action="{% url 'set_language' %}" style="display:inline;">
    {% csrf_token %}
    <input type="hidden" name="next" value="{{ request.get_full_path }}">
    <select name="language" onchange="this.form.submit()"
            style="background:rgba(255,255,255,0.15); color:white; border:1px solid rgba(255,255,255,0.3);
                   border-radius:5px; padding:4px 8px; font-size:13px; cursor:pointer;">
        {% get_current_language as LANGUAGE_CODE %}
        <option value="vi" {% if LANGUAGE_CODE == 'vi' %}selected{% endif %}>🇻🇳 Tiếng Việt</option>
        <option value="en" {% if LANGUAGE_CODE == 'en' %}selected{% endif %}>🇺🇸 English</option>
    </select>
</form>
```

---

## Giai đoạn 2 — Python code (models + forms) (~2 ngày)

### 2.1 `employees/models.py` và `contracts/models.py`
Thêm `from django.utils.translation import gettext_lazy as _` và wrap:
```python
# Trước:
('dang_lam', 'Đang làm việc'),
# Sau:
('dang_lam', _('Đang làm việc')),
```
Áp dụng cho: STATUS_CHOICES, MARITAL_CHOICES, DEGREE_CHOICES, ACTION_CHOICES, TARGET_CHOICES, TYPE_CHOICES, STATUS_CHOICES (contracts), TERMINATION_REASON_CHOICES, tất cả verbose_name.

### 2.2 `employees/forms.py` và `contracts/forms.py`
```python
from django.utils.translation import gettext_lazy as _
empty_label=_('-- Chọn bộ phận --')
raise forms.ValidationError(_('Chỉ hỗ trợ file PDF, DOC, DOCX.'))
self.add_error('end_date', _('Ngày kết thúc phải sau ngày bắt đầu.'))
```

---

## Giai đoạn 3 — Views (~2 ngày)

Wrap các strings quan trọng hiển thị cho user (messages.success/error):
```python
from django.utils.translation import gettext as _
messages.success(request, _('Đã xóa {} nhân viên.').format(count))
```

**Không cần dịch:**
- `log_activity()` detail — đây là log nội bộ, giữ tiếng Việt OK
- Tên file export Excel (`danh_sach_hop_dong.xlsx`) — giữ nguyên

**Cần dịch (headers Excel hiển thị cho user):**
```python
headers = [_('Số HĐ'), _('Nhân viên'), _('Mã NV'), ...]
```

---

## Giai đoạn 4 — Templates (~5–7 ngày)

### Mỗi template cần:
1. Thêm `{% load i18n %}` đầu file
2. Thêm language switcher vào topbar: `{% include 'employees/_language_switcher.html' %}`
3. Wrap text: `{% trans "Nhân viên" %}`, `{% trans "Đăng xuất" %}`
4. Với text có biến: `{% blocktrans with count=total %}Tổng {{ count }} nhân viên{% endblocktrans %}`

### Thứ tự ưu tiên (làm trước):
1. `home.html` — trang chủ, entry point
2. `login.html` — trang đăng nhập
3. `employee_list.html` — trang dùng nhiều nhất
4. `contract_list.html`
5. Còn lại theo thứ tự sử dụng

---

## Giai đoạn 5 — Tạo file dịch & biên dịch (~2–3 ngày)

```bash
# Tạo/cập nhật file .po (tiếng Anh)
python -X utf8 manage.py makemessages -l en --ignore=".venv"

# Dịch strings trong file: locale/en/LC_MESSAGES/django.po
# msgid "Đang làm việc"
# msgstr "Working"

# Biên dịch
python -X utf8 manage.py compilemessages
```

### Ví dụ nội dung `locale/en/LC_MESSAGES/django.po`:
```
msgid "Đang làm việc"    msgstr "Working"
msgid "Thử việc"         msgstr "Probation"
msgid "Thực tập sinh"    msgstr "Intern"
msgid "Nghỉ phép"        msgstr "On Leave"
msgid "Nghỉ thai sản"    msgstr "Maternity Leave"
msgid "Nghỉ không lương" msgstr "Unpaid Leave"
msgid "Nghỉ ốm dài ngày" msgstr "Sick Leave"
msgid "Nghỉ việc"        msgstr "Terminated"
msgid "Nhân viên"        msgstr "Employee"
msgid "Phòng ban"        msgstr "Department"
... (850–1050 entries)
```

---

## Files cần thay đổi (tổng hợp)

| File | Loại thay đổi |
|------|--------------|
| `myproject/settings.py` | Thêm LANGUAGES, LOCALE_PATHS, LocaleMiddleware |
| `myproject/urls.py` | Thêm `set_language` URL |
| `employees/models.py` | Wrap ~46 strings với `_()` |
| `contracts/models.py` | Wrap ~35 strings với `_()` |
| `employees/forms.py` | Wrap ~4 strings |
| `contracts/forms.py` | Wrap ~10 strings |
| `employees/views.py` | Wrap ~100 strings |
| `contracts/views.py` | Wrap ~50 strings |
| 34 templates | `{% load i18n %}` + `{% trans %}` + include switcher |
| `locale/en/LC_MESSAGES/django.po` | **Tạo mới** — ~850-1050 dòng dịch |
| `locale/vi/LC_MESSAGES/django.po` | **Tạo mới** — identity map (msgstr = msgid) |
| `employees/templates/employees/_language_switcher.html` | **Tạo mới** |

---

## Kiểm thử (Verification)

1. Khởi động server → truy cập trang chủ → chọn 🇺🇸 English → toàn bộ UI chuyển sang tiếng Anh
2. Chuyển lại 🇻🇳 Tiếng Việt → UI quay về tiếng Việt
3. Reload trang → ngôn ngữ vẫn giữ (lưu trong session)
4. Đăng xuất/đăng nhập lại → ngôn ngữ giữ nguyên
5. Kiểm tra Admin Django (`/admin/`) → choices labels hiển thị đúng ngôn ngữ

---

## Lưu ý triển khai

1. **Bắt đầu từ Giai đoạn 1 trước** — setup hạ tầng để test sớm, dù chưa có bản dịch
2. **Dùng `gettext_lazy` trong models/forms** — quan trọng, dùng lazy để tránh lỗi khi Django khởi động
3. **Dùng `gettext` (không lazy) trong views** — vì cần giá trị tức thì tại request time
4. **Tiếng Việt file `.po`** — sau khi chạy `makemessages`, file `locale/vi/...` để msgstr trống → Django tự dùng msgid (bản gốc tiếng Việt)
5. **`-X utf8` khi chạy manage.py trên Windows** — bắt buộc vì có ký tự Unicode
6. **Có thể làm theo từng giai đoạn** — mỗi giai đoạn độc lập, không cần làm xong hết mới test được
