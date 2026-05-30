---
name: i18n-plan
description: Kế hoạch triển khai đa ngôn ngữ (i18n) — thêm tiếng Anh vào HRM App. Chưa implement. Dùng khi muốn bắt đầu tính năng này.
---

# Kế hoạch triển khai đa ngôn ngữ (i18n) — Thêm tiếng Anh

## Context

HRM App hiện tại hardcode hoàn toàn tiếng Việt (~750–1060 strings trên 34 templates + Python code). Mục tiêu: thêm tiếng Anh (EN) là ngôn ngữ thứ 2, người dùng chuyển đổi qua nút trên giao diện. Tiếng Việt vẫn là mặc định.

## Quy mô công việc (ước tính)

| Phần | Số strings cần dịch | Ghi chú |
|------|-------------------|---------|
| Templates (34 file HTML) | ~600–800 | Phần lớn nhất |
| models.py (2 file) | ~81 | Choices labels, verbose_name |
| views.py (2 file) | ~150 | messages.success/error, export headers |
| forms.py (2 file) | ~14 | label, error messages |
| **Tổng** | **~850–1050** | |

**Thời gian ước tính toàn bộ: 10–15 ngày dev**

---

## Quyết định kỹ thuật

### Cách chuyển ngôn ngữ: Session-based (không đổi URL)
- **Không dùng** `i18n_patterns()` vì sẽ đổi tất cả URL hiện tại (`/employees/` → `/vi/employees/`)
- **Dùng** Django's built-in `set_language` view + `LocaleMiddleware`
- Ngôn ngữ lưu trong **session** → mọi trang tự áp dụng
- URL giữ nguyên, không ảnh hưởng bookmark hoặc activity log

---

## Tiền đề bắt buộc (cần làm trước)

**Cài gettext tools trên Windows:**
```
choco install gettext
```
Kiểm tra: `xgettext --version` phải trả về output.

---

## Giai đoạn 1 — Hạ tầng Django i18n (1 ngày)

### 1.1 `myproject/settings.py`
```python
from django.utils.translation import gettext_lazy as _

LANGUAGE_CODE = 'vi'
USE_I18N = True

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
    path('i18n/setlang/', set_language, name='set_language'),
]
```

### 1.3 Tạo cấu trúc thư mục locale
```
myproject/locale/
├── vi/LC_MESSAGES/django.po
└── en/LC_MESSAGES/django.po
```

### 1.4 Language switcher — `employees/templates/employees/_language_switcher.html`
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

## Giai đoạn 2 — Python code: models + forms (~2 ngày)

```python
# models.py — dùng gettext_lazy
from django.utils.translation import gettext_lazy as _
('dang_lam', _('Đang làm việc')),

# forms.py — dùng gettext_lazy
empty_label=_('-- Chọn bộ phận --')

# views.py — dùng gettext (không lazy)
from django.utils.translation import gettext as _
messages.success(request, _('Đã xóa {} nhân viên.').format(count))
```

**Không cần dịch:** `log_activity()` detail, tên file export Excel.

---

## Giai đoạn 3 — Templates (~5–7 ngày)

Mỗi template:
1. Thêm `{% load i18n %}` đầu file
2. Thêm `{% include 'employees/_language_switcher.html' %}` vào topbar
3. `{% trans "Nhân viên" %}` cho text đơn giản
4. `{% blocktrans with count=total %}Tổng {{ count }} nhân viên{% endblocktrans %}` cho text có biến

**Thứ tự:** `home.html` → `login.html` → `employee_list.html` → còn lại

---

## Giai đoạn 4 — Tạo file dịch & biên dịch (~2–3 ngày)

```bash
python -X utf8 manage.py makemessages -l en --ignore=".venv"
# Dịch trong: locale/en/LC_MESSAGES/django.po
python -X utf8 manage.py compilemessages
```

Ví dụ bản dịch:
```
msgid "Đang làm việc"    msgstr "Working"
msgid "Thử việc"         msgstr "Probation"
msgid "Thực tập sinh"    msgstr "Intern"
msgid "Nghỉ phép"        msgstr "On Leave"
msgid "Nghỉ thai sản"    msgstr "Maternity Leave"
msgid "Nghỉ không lương" msgstr "Unpaid Leave"
msgid "Nghỉ việc"        msgstr "Terminated"
```

---

## Files cần thay đổi (tổng hợp)

| File | Loại thay đổi |
|------|--------------|
| `myproject/settings.py` | Thêm LANGUAGES, LOCALE_PATHS, LocaleMiddleware |
| `myproject/urls.py` | Thêm `set_language` URL |
| `employees/models.py` | Wrap ~46 strings với `_()` |
| `contracts/models.py` | Wrap ~35 strings với `_()` |
| `employees/views.py` | Wrap ~100 strings |
| `contracts/views.py` | Wrap ~50 strings |
| 34 templates | `{% load i18n %}` + `{% trans %}` + include switcher |
| `locale/en/LC_MESSAGES/django.po` | **Tạo mới** — ~850-1050 dòng dịch |

---

## Lưu ý quan trọng

1. **Dùng `gettext_lazy` trong models/forms** — tránh lỗi khi Django khởi động
2. **Dùng `gettext` trong views** — cần giá trị tức thì tại request time
3. **`-X utf8` khi chạy manage.py trên Windows** — bắt buộc vì có ký tự Unicode
4. **Có thể làm theo từng giai đoạn** — mỗi giai đoạn độc lập
