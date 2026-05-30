# Quy tắc Template — HRM App

## Cấu trúc template chuẩn

```html
{% extends "base.html" %}
{% block title %}Tiêu đề trang — HRM{% endblock %}

{% block content %}
<div class="container-fluid">
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h4>Tiêu đề</h4>
    {% if can_add %}
    <a href="{% url 'app:create' %}" class="btn btn-primary">Thêm mới</a>
    {% endif %}
  </div>

  <!-- Nội dung chính -->
</div>
{% endblock %}
```

## Quy ước bắt buộc

### Hiển thị ngày
```html
{{ employee.date_of_birth | date:"d/m/Y" }}   <!-- ĐÚNG ✅ -->
{{ employee.date_of_birth }}                   <!-- SAI ❌ — format Mỹ -->
```

### URL — luôn dùng {% url %}, không hardcode
```html
<a href="{% url 'contracts:detail' contract.pk %}">Xem</a>   <!-- ĐÚNG ✅ -->
<a href="/contracts/{{ contract.pk }}/">Xem</a>              <!-- SAI ❌ -->
```

### Kiểm tra quyền trong template
```html
{% if user.is_superuser or can_edit %}
  <a href="{% url 'employee_edit' emp.pk %}">Sửa</a>
{% endif %}

{% if user.is_superuser or can_delete %}
  <a href="{% url 'employee_delete' emp.pk %}">Xóa</a>
{% endif %}
```

### CSRF cho form
```html
<form method="post" action="{% url 'employee_create' %}">
  {% csrf_token %}
  <!-- fields -->
  <button type="submit" class="btn btn-primary">Lưu</button>
</form>
```

### Hiển thị số tiền (lương, phụ cấp)
```html
{{ payslip.gross_salary | floatformat:0 }}    <!-- 15000000 -->
```
Hoặc dùng filter custom nếu có: `| money_format`

## Status badge (pill màu)

```html
<!-- Employee status — xem CSS class trong employee_list.html -->
<span class="badge status-{{ employee.status }}">
  {{ employee.get_status_display }}
</span>
```

## Pagination chuẩn

```html
{% if page_obj.has_other_pages %}
<nav aria-label="Pagination">
  <ul class="pagination justify-content-center">
    {% if page_obj.has_previous %}
      <li class="page-item">
        <a class="page-link" href="?{{ base_filter_qs }}&page={{ page_obj.previous_page_number }}">Trước</a>
      </li>
    {% endif %}
    <li class="page-item active">
      <span class="page-link">{{ page_obj.number }} / {{ page_obj.paginator.num_pages }}</span>
    </li>
    {% if page_obj.has_next %}
      <li class="page-item">
        <a class="page-link" href="?{{ base_filter_qs }}&page={{ page_obj.next_page_number }}">Sau</a>
      </li>
    {% endif %}
  </ul>
</nav>
{% endif %}
```

## Messages (thông báo sau action)

```python
# Trong view
from django.contrib import messages
messages.success(request, 'Đã lưu thành công!')
messages.error(request, 'Có lỗi xảy ra!')
messages.warning(request, 'Cảnh báo: ...')
```

```html
<!-- Trong base.html đã có, nhưng nếu cần hiển thị thủ công -->
{% for message in messages %}
<div class="alert alert-{{ message.tags }}">{{ message }}</div>
{% endfor %}
```

## Không làm trong template

- Không chứa business logic phức tạp (tính toán, query DB)
- Không dùng `{{ var | safe }}` với input người dùng
- Không hardcode URL, text nhạy cảm
- Không lồng quá 4 cấp `{% if %}` — nếu cần, xử lý trong view
