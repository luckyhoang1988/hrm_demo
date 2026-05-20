# Kế hoạch Triển khai: App Tuyển dụng & Đào tạo (HRM)

## Context

HRM app hiện có 3 app: `employees`, `contracts`, `system_settings`. Người dùng yêu cầu thêm **1 app mới duy nhất** gộp cả tuyển dụng và đào tạo:

- **Django app name**: `talent` (Python identifier hợp lệ)
- **Hiển thị (verbose_name)**: `Tuyển dụng & Đào tạo`
- **URL prefix**: `/talent/`
- **Namespace**: `talent:`
- **Phân khu bên trong**: `/talent/recruitment/` (tuyển dụng) + `/talent/training/` (đào tạo)
- **Home page**: `/talent/` → trang tổng quan 2 section (tuyển dụng + đào tạo)

**Quyết định thiết kế:**
- Pipeline tuyển dụng: **5 giai đoạn cố định** (đơn giản, phù hợp SME)
- Chứng chỉ: **tự động tạo khi nhân viên được đánh dấu Pass**
- Scope MVP — loại bỏ: AI parsing, e-signature, approval workflow, gamification

---

## Tích hợp với hệ thống hiện tại

Vì gộp thành 1 app, tất cả đều dùng **1 quyền** và **1 toggle** duy nhất:

| Điểm tích hợp | Cần thay đổi | File |
|---|---|---|
| **AppStatus** | Thêm `app_talent_active = BooleanField(default=False)` | `system_settings/models.py` |
| **UserProfile** | Thêm `app_talent = BooleanField(default=False)` | `employees/models.py` → migration |
| **StaffGroup** | Thêm `app_talent = BooleanField(default=False)` | `employees/models.py` → migration |
| **get_user_features()** | Thêm `'app_talent': profile.app_talent or any(sg.app_talent ...)` | `employees/helpers.py` |
| **ActivityLog TARGET_CHOICES** | Thêm `('talent', 'Tuyển dụng & Đào tạo')` | `employees/models.py` → migration |
| **home.html** | Thêm **1 card** "Tuyển dụng & Đào tạo" | `employees/templates/employees/home.html` |
| **settings_home.html** | Thêm **1 toggle card** Tuyển dụng & Đào tạo | `system_settings/templates/system_settings/settings_home.html` |
| **settings.py** | Thêm `'talent'` vào INSTALLED_APPS | `myproject/settings.py` |
| **myproject/urls.py** | Thêm `path('talent/', include('talent.urls'))` | `myproject/urls.py` |
| **permission_manage.html**, **staff_group_form.html** | Thêm checkbox `app_talent` | templates system_settings |
| **auto_logout include** | Script PowerShell thêm vào tất cả template mới | PowerShell (cuối cùng) |

---

## Phase 1: Cập nhật Core (làm đầu tiên)

### Bước 1.1 — `employees/models.py`
- Thêm vào `ActivityLog.TARGET_CHOICES`: `('talent', 'Tuyển dụng & Đào tạo')`
- Thêm vào `UserProfile`: `app_talent = BooleanField(default=False)`
- Thêm vào `StaffGroup`: `app_talent = BooleanField(default=False)`
- **Chạy migration**: `python manage.py makemigrations employees`

### Bước 1.2 — `system_settings/models.py`
- Thêm vào `AppStatus`: `app_talent_active = BooleanField(default=False)`
- **Chạy migration**: `python manage.py makemigrations system_settings`

### Bước 1.3 — `employees/helpers.py` — hàm `get_user_features()`
Cập nhật dict trả về — thêm 1 dòng bên trong logic tổng hợp quyền:
```python
'app_talent': profile.app_talent or any(sg.app_talent for sg in staff_groups),
```

### Bước 1.4 — `python manage.py migrate`

---

## Phase 2: App `talent` — Section Tuyển dụng

### 2.1 Cấu trúc thư mục (toàn bộ app `talent`)
```
talent/
├── __init__.py
├── apps.py                    ← verbose_name = 'Tuyển dụng & Đào tạo'
├── models.py                  ← TẤT CẢ models tuyển dụng + đào tạo
├── forms.py                   ← TẤT CẢ forms
├── views.py                   ← TẤT CẢ views (có thể chia views_recruitment + views_training)
├── urls.py                    ← app_name='talent', /recruitment/* + /training/*
├── admin.py
├── migrations/
│   └── 0001_initial.py
└── templates/talent/
    ├── home.html              ← Trang tổng quan 2 section (tuyển dụng + đào tạo)
    │
    ├── [TUYỂN DỤNG]
    ├── job_list.html
    ├── job_form.html
    ├── job_detail.html
    ├── job_confirm_delete.html
    ├── applicant_list.html
    ├── applicant_form.html
    ├── applicant_detail.html
    ├── applicant_confirm_delete.html
    ├── applicant_change_stage.html
    ├── applicant_convert.html
    ├── interview_form.html
    ├── interview_confirm_delete.html
    ├── offer_form.html
    ├── recruitment_dashboard.html
    │
    └── [ĐÀO TẠO]
    ├── course_list.html
    ├── course_form.html
    ├── course_detail.html
    ├── course_confirm_delete.html
    ├── session_list.html
    ├── session_form.html
    ├── session_detail.html
    ├── session_confirm_delete.html
    ├── enrollment_form.html
    ├── certificate_list.html
    ├── certificate_detail.html
    └── training_dashboard.html
```

**`talent/apps.py`:**
```python
class TalentConfig(AppConfig):
    name = 'talent'
    verbose_name = 'Tuyển dụng & Đào tạo'
```

### 2.2 Models (`talent/models.py`) — Section Tuyển dụng

#### `JobPosition` — Vị trí tuyển dụng
```python
EMPLOYMENT_TYPE = [('full_time','Toàn thời gian'),('part_time','Bán thời gian'),('internship','Thực tập'),('seasonal','Thời vụ')]
JOB_STATUS = [('draft','Nháp'),('open','Đang tuyển'),('interviewing','Đang PV'),('filled','Đã tuyển đủ'),('cancelled','Đã hủy')]

class JobPosition(models.Model):
    title              # CharField — chức danh cần tuyển
    department         # FK → Department, on_delete=PROTECT
    headcount          # PositiveIntegerField — số lượng cần tuyển
    employment_type    # CharField choices=EMPLOYMENT_TYPE
    salary_min / salary_max  # DecimalField nullable
    description        # TextField
    requirements       # TextField
    benefits           # TextField blank=True
    location           # CharField default='Văn phòng chính'
    open_date          # DateField
    close_date         # DateField nullable — deadline nhận hồ sơ
    status             # CharField choices=JOB_STATUS default='draft'
    hiring_manager     # FK User SET_NULL nullable — người phụ trách
    source_channels    # CharField blank=True — ghi chú kênh đăng tin
    notes              # TextField blank=True
    created_by         # FK User SET_NULL nullable related_name='jobs_created'
    created_at         # auto_now_add

    @property days_open    → (today - open_date).days
    @property is_overdue   → close_date and close_date < today and status == 'open'
    @property filled_count → số Applicant có status='hired' cho job này
```

#### `Applicant` — Ứng viên (pipeline cố định 5 stage)
```python
STAGE_CHOICES = [
    ('new',        'Mới nộp'),
    ('screening',  'Sàng lọc'),
    ('interview',  'Phỏng vấn'),
    ('offer',      'Đề nghị'),
    ('hired',      'Đã tuyển'),
    ('rejected',   'Loại'),
]
SOURCE_CHOICES = [('topcv','TopCV'),('vietnamworks','VietnamWorks'),('linkedin','LinkedIn'),
                  ('facebook','Facebook'),('website','Website công ty'),('referral','Giới thiệu nội bộ'),
                  ('direct','Nộp trực tiếp'),('other','Khác')]

class Applicant(models.Model):
    job_position       # FK → JobPosition, on_delete=CASCADE
    full_name          # CharField
    email              # CharField (không unique toàn bảng — cùng người có thể apply nhiều vị trí)
    phone              # CharField blank=True
    address            # CharField blank=True
    source             # CharField choices=SOURCE_CHOICES
    referrer           # FK → Employee SET_NULL nullable — người giới thiệu
    cv_file            # FileField upload_to='recruitment/cv/' nullable
    cover_letter       # TextField blank=True
    linkedin_url       # URLField blank=True
    applied_at         # auto_now_add
    stage              # CharField choices=STAGE_CHOICES default='new'
    reject_reason      # TextField blank=True
    notes              # TextField blank=True — ghi chú nội bộ của HR
    converted_employee # FK → Employee SET_NULL nullable — sau khi convert
    created_by         # FK User SET_NULL nullable

    class Meta: unique_together = ('job_position', 'email')  # 1 email, 1 vị trí

    @property stage_display → tên stage tiếng Việt
    @property has_offer    → JobOffer.objects.filter(applicant=self).exists()
```

#### `Interview` — Lịch phỏng vấn
```python
INTERVIEW_TYPE = [('phone','Điện thoại'),('online','Online'),('in_person','Trực tiếp'),('technical','Chuyên môn')]
INTERVIEW_STATUS = [('scheduled','Đã lên lịch'),('completed','Đã hoàn thành'),('cancelled','Đã hủy'),('no_show','Vắng mặt')]

class Interview(models.Model):
    applicant          # FK → Applicant, on_delete=CASCADE
    round_number       # PositiveIntegerField default=1
    interview_type     # CharField choices=INTERVIEW_TYPE
    scheduled_date     # DateField
    scheduled_time     # TimeField nullable
    duration_minutes   # PositiveIntegerField default=60
    location           # CharField blank=True — địa điểm hoặc link meet
    interviewers       # ManyToManyField User blank=True
    status             # CharField choices=INTERVIEW_STATUS default='scheduled'
    score              # IntegerField validators=[1-5] nullable — điểm tổng
    notes              # TextField blank=True — feedback sau phỏng vấn
    created_by         # FK User SET_NULL nullable
    created_at         # auto_now_add
```

#### `JobOffer` — Đề nghị việc làm
```python
OFFER_STATUS = [('draft','Nháp'),('sent','Đã gửi'),('accepted','Đã chấp nhận'),('rejected','Từ chối'),('expired','Hết hạn')]

class JobOffer(models.Model):
    applicant          # OneToOneField → Applicant, on_delete=CASCADE
    offered_salary     # DecimalField
    start_date         # DateField — ngày bắt đầu dự kiến
    probation_months   # PositiveIntegerField default=2
    benefits_note      # TextField blank=True
    offer_letter_file  # FileField upload_to='recruitment/offers/' nullable
    deadline_response  # DateField nullable — hạn phản hồi
    status             # CharField choices=OFFER_STATUS default='draft'
    rejection_reason   # TextField blank=True
    sent_at            # DateTimeField nullable
    accepted_at        # DateTimeField nullable
    created_by         # FK User SET_NULL nullable
    created_at         # auto_now_add

    @property is_expired → deadline_response and deadline_response < today and status == 'sent'
```

### 2.3 Views (`talent/views.py`) — Section Tuyển dụng

Import từ `employees.helpers`: `get_user_features`, `log_activity`, `_get_client_ip`

Feature gate dùng chung cho cả 2 section: `if not get_user_features(request.user)['app_talent']: redirect('home')`

| View | URL | Method | Mô tả |
|---|---|---|---|
| `talent_home` | `/talent/` | GET | Trang tổng quan 2 section: tuyển dụng + đào tạo |
| `job_list` | `/talent/recruitment/` | GET | Danh sách vị trí, filter theo status/dept, phân trang 20 |
| `job_create` | `/talent/recruitment/jobs/create/` | GET/POST | Tạo vị trí mới |
| `job_detail` | `/talent/recruitment/jobs/<pk>/` | GET | Chi tiết + danh sách ứng viên phân theo stage |
| `job_update` | `/talent/recruitment/jobs/<pk>/edit/` | GET/POST | Sửa vị trí |
| `job_delete` | `/talent/recruitment/jobs/<pk>/delete/` | GET/POST | Xóa vị trí (PROTECT nếu có ứng viên) |
| `applicant_list` | `/talent/recruitment/applicants/` | GET | Tất cả ứng viên, filter job/stage/source |
| `applicant_create` | `/talent/recruitment/applicants/create/` | GET/POST | Thêm ứng viên (job chọn từ dropdown) |
| `applicant_detail` | `/talent/recruitment/applicants/<pk>/` | GET | Chi tiết + timeline phỏng vấn + offer |
| `applicant_update` | `/talent/recruitment/applicants/<pk>/edit/` | GET/POST | Sửa thông tin ứng viên |
| `applicant_delete` | `/talent/recruitment/applicants/<pk>/delete/` | GET/POST | Xóa ứng viên |
| `applicant_change_stage` | `/talent/recruitment/applicants/<pk>/stage/` | POST | Chuyển stage (AJAX-friendly, redirect back) |
| `applicant_convert` | `/talent/recruitment/applicants/<pk>/convert/` | GET/POST | Convert ứng viên → Employee (prefill form) |
| `interview_create` | `/talent/recruitment/applicants/<pk>/interview/` | GET/POST | Thêm lịch PV cho ứng viên |
| `interview_update` | `/talent/recruitment/interviews/<pk>/edit/` | GET/POST | Sửa lịch PV |
| `interview_delete` | `/talent/recruitment/interviews/<pk>/delete/` | POST | Xóa lịch PV |
| `offer_create` | `/talent/recruitment/applicants/<pk>/offer/` | GET/POST | Tạo offer cho ứng viên |
| `offer_update` | `/talent/recruitment/offers/<pk>/edit/` | GET/POST | Sửa offer |
| `recruitment_dashboard` | `/talent/recruitment/dashboard/` | GET | KPIs + biểu đồ pipeline |
| `recruitment_export` | `/talent/recruitment/export/excel/` | GET | Xuất danh sách ứng viên Excel |

**`applicant_convert` — logic quan trọng:**
1. Kiểm tra stage phải là `'offer'` và offer có status `'accepted'`
2. Pre-fill form tạo Employee với thông tin từ Applicant + JobOffer
3. Khi submit: tạo Employee, set `applicant.converted_employee = employee`, `applicant.stage = 'hired'`
4. Log activity: `log_activity(..., 'create', 'employee', f'Tuyển dụng từ: {applicant.full_name}')`
5. Redirect đến employee_detail

### 2.4 URLs (`talent/urls.py`)
```python
app_name = 'talent'
urlpatterns = [
    # Trang tổng quan
    path('', views.talent_home, name='talent_home'),

    # === TUYỂN DỤNG ===
    path('recruitment/', views.job_list, name='job_list'),
    path('recruitment/jobs/create/', views.job_create, name='job_create'),
    path('recruitment/jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('recruitment/jobs/<int:pk>/edit/', views.job_update, name='job_update'),
    path('recruitment/jobs/<int:pk>/delete/', views.job_delete, name='job_delete'),
    path('recruitment/applicants/', views.applicant_list, name='applicant_list'),
    path('recruitment/applicants/create/', views.applicant_create, name='applicant_create'),
    path('recruitment/applicants/<int:pk>/', views.applicant_detail, name='applicant_detail'),
    path('recruitment/applicants/<int:pk>/edit/', views.applicant_update, name='applicant_update'),
    path('recruitment/applicants/<int:pk>/delete/', views.applicant_delete, name='applicant_delete'),
    path('recruitment/applicants/<int:pk>/stage/', views.applicant_change_stage, name='applicant_change_stage'),
    path('recruitment/applicants/<int:pk>/convert/', views.applicant_convert, name='applicant_convert'),
    path('recruitment/applicants/<int:pk>/interview/', views.interview_create, name='interview_create'),
    path('recruitment/interviews/<int:pk>/edit/', views.interview_update, name='interview_update'),
    path('recruitment/interviews/<int:pk>/delete/', views.interview_delete, name='interview_delete'),
    path('recruitment/applicants/<int:pk>/offer/', views.offer_create, name='offer_create'),
    path('recruitment/offers/<int:pk>/edit/', views.offer_update, name='offer_update'),
    path('recruitment/dashboard/', views.recruitment_dashboard, name='recruitment_dashboard'),
    path('recruitment/export/excel/', views.recruitment_export, name='recruitment_export'),

    # === ĐÀO TẠO ===
    path('training/', views.course_list, name='course_list'),
    path('training/courses/create/', views.course_create, name='course_create'),
    path('training/courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('training/courses/<int:pk>/edit/', views.course_update, name='course_update'),
    path('training/courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    path('training/sessions/', views.session_list, name='session_list'),
    path('training/sessions/create/', views.session_create, name='session_create'),
    path('training/sessions/<int:pk>/', views.session_detail, name='session_detail'),
    path('training/sessions/<int:pk>/edit/', views.session_update, name='session_update'),
    path('training/sessions/<int:pk>/delete/', views.session_delete, name='session_delete'),
    path('training/sessions/<int:pk>/enroll/', views.enrollment_add, name='enrollment_add'),
    path('training/enrollments/<int:pk>/delete/', views.enrollment_delete, name='enrollment_delete'),
    path('training/enrollments/<int:pk>/update/', views.enrollment_update, name='enrollment_update'),
    path('training/certificates/', views.certificate_list, name='certificate_list'),
    path('training/certificates/<int:pk>/', views.certificate_detail, name='certificate_detail'),
    path('training/dashboard/', views.training_dashboard, name='training_dashboard'),
    path('training/export/excel/', views.training_export, name='training_export'),
]
```

### 2.5 Dashboard Tuyển dụng

**KPIs hiển thị:**
- Tổng vị trí đang tuyển / đã tuyển đủ / đã hủy
- Tổng ứng viên đang active / bị loại / đã tuyển
- Offer acceptance rate (% offer được chấp nhận)
- Biểu đồ: số ứng viên theo stage (bar chart — Chart.js)
- Biểu đồ: nguồn ứng viên (donut chart — theo source)
- Bảng: top vị trí có nhiều ứng viên nhất
- Alert: vị trí đã quá hạn close_date mà chưa filled

---

## Phase 3: App `talent` — Section Đào tạo

*(Cùng app `talent`, tiếp tục thêm vào `talent/models.py` và `talent/views.py`)*

### 3.1 Models (`talent/models.py`) — Section Đào tạo

#### `TrainingCourse` — Khóa đào tạo
```python
CATEGORY = [('soft_skill','Kỹ năng mềm'),('technical','Chuyên môn'),('safety','An toàn lao động'),
            ('compliance','Tuân thủ quy định'),('onboarding','Hội nhập')]
DELIVERY = [('classroom','Tập trung tại lớp'),('online','Trực tuyến'),('on_job','Thực chiến tại chỗ'),('blended','Kết hợp')]

class TrainingCourse(models.Model):
    code               # CharField unique — mã khóa học (tự sinh hoặc nhập tay)
    name               # CharField
    category           # CharField choices=CATEGORY
    delivery_method    # CharField choices=DELIVERY
    duration_hours     # DecimalField — số giờ đào tạo
    description        # TextField blank=True
    is_mandatory       # BooleanField default=False
    provider           # CharField — 'Nội bộ' hoặc tên đơn vị ngoài
    cost_per_person    # DecimalField nullable — chi phí/người
    certificate_validity_months  # PositiveIntegerField nullable — None = không hết hạn
    target_departments # ManyToManyField Department blank=True — phòng ban mục tiêu
    is_active          # BooleanField default=True
    created_by         # FK User SET_NULL nullable
    created_at         # auto_now_add
```

#### `TrainingSession` — Lớp/Buổi đào tạo
```python
SESSION_STATUS = [('planned','Đã lên kế hoạch'),('ongoing','Đang diễn ra'),('completed','Đã hoàn thành'),('cancelled','Đã hủy')]

class TrainingSession(models.Model):
    course             # FK → TrainingCourse, on_delete=PROTECT
    session_code       # CharField unique (auto-gen: COURSE_CODE-YYYYMM-01)
    trainer_name       # CharField — tên giảng viên (text, linh hoạt)
    trainer_employee   # FK → Employee SET_NULL nullable — nếu là NV nội bộ
    location           # CharField
    start_date         # DateField
    end_date           # DateField
    max_participants   # PositiveIntegerField nullable
    status             # CharField choices=SESSION_STATUS default='planned'
    notes              # TextField blank=True
    created_by         # FK User SET_NULL nullable
    created_at         # auto_now_add

    @property enrolled_count → TrainingEnrollment.objects.filter(session=self).exclude(status='cancelled').count()
    @property available_slots → max_participants - enrolled_count (None nếu max_participants là None)
```

#### `TrainingEnrollment` — Đăng ký đào tạo
```python
ENROLLMENT_STATUS = [('registered','Đã đăng ký'),('attended','Đã tham dự'),('absent','Vắng mặt'),('cancelled','Đã hủy')]
RESULT = [('pending','Chưa có kết quả'),('pass','Đạt'),('fail','Không đạt')]

class TrainingEnrollment(models.Model):
    session            # FK → TrainingSession, on_delete=CASCADE
    employee           # FK → Employee, on_delete=CASCADE
    enrolled_by        # FK User SET_NULL nullable
    enrolled_at        # auto_now_add
    status             # CharField choices=ENROLLMENT_STATUS default='registered'
    score              # DecimalField nullable — điểm (0-100)
    result             # CharField choices=RESULT default='pending'
    feedback_rating    # PositiveIntegerField nullable — 1-5 sao
    feedback_comment   # TextField blank=True

    class Meta: unique_together = ('session', 'employee')

    # Override save(): khi result='pass' và chưa có certificate → tự tạo TrainingCertificate
```

#### `TrainingCertificate` — Chứng chỉ
```python
class TrainingCertificate(models.Model):
    enrollment         # OneToOneField → TrainingEnrollment, on_delete=CASCADE
    employee           # FK → Employee, on_delete=CASCADE (denormalized để query nhanh)
    course             # FK → TrainingCourse, on_delete=CASCADE (denormalized)
    certificate_number # CharField unique — auto-gen: CERT-YYYYMMDD-XXXX
    issued_date        # DateField default=today
    expiry_date        # DateField nullable — tính từ issued_date + validity_months
    issued_by          # FK User SET_NULL nullable
    notes              # TextField blank=True
    is_active          # BooleanField default=True

    @property is_expired    → expiry_date and expiry_date < today
    @property days_until_expiry → (expiry_date - today).days nếu có expiry_date
    @property expiring_soon → days_until_expiry is not None and days_until_expiry <= 30
```

**Logic tự động cấp chứng chỉ (trong `TrainingEnrollment.save()`):**
```python
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    if self.result == 'pass' and not hasattr(self, 'trainingcertificate'):
        course = self.session.course
        expiry = None
        if course.certificate_validity_months:
            expiry = date.today() + relativedelta(months=course.certificate_validity_months)
        TrainingCertificate.objects.create(
            enrollment=self,
            employee=self.employee,
            course=course,
            certificate_number=generate_cert_number(),  # CERT-YYYYMMDD-XXXX
            issued_date=date.today(),
            expiry_date=expiry,
        )
```

### 3.2 Views (`talent/views.py`) — Section Đào tạo

| View | URL | Method | Mô tả |
|---|---|---|---|
| `course_list` | `/talent/training/` | GET | Danh sách khóa học, filter theo category/active |
| `course_create` | `/talent/training/courses/create/` | GET/POST | Tạo khóa học |
| `course_detail` | `/talent/training/courses/<pk>/` | GET | Chi tiết khóa + danh sách lớp |
| `course_update` | `/talent/training/courses/<pk>/edit/` | GET/POST | Sửa khóa học |
| `course_delete` | `/talent/training/courses/<pk>/delete/` | GET/POST | Xóa (PROTECT nếu có session) |
| `session_list` | `/talent/training/sessions/` | GET | Tất cả lớp học, filter theo course/status/date |
| `session_create` | `/talent/training/sessions/create/` | GET/POST | Tạo lớp mới |
| `session_detail` | `/talent/training/sessions/<pk>/` | GET | Chi tiết lớp + bảng enrollment + form thêm NV |
| `session_update` | `/talent/training/sessions/<pk>/edit/` | GET/POST | Sửa lớp |
| `session_delete` | `/talent/training/sessions/<pk>/delete/` | GET/POST | Xóa lớp |
| `enrollment_add` | `/talent/training/sessions/<pk>/enroll/` | GET/POST | HR thêm NV vào lớp (multi-select) |
| `enrollment_delete` | `/talent/training/enrollments/<pk>/delete/` | POST | Xóa đăng ký |
| `enrollment_update` | `/talent/training/enrollments/<pk>/update/` | POST | Cập nhật attendance + điểm + kết quả (form inline) |
| `certificate_list` | `/talent/training/certificates/` | GET | Tất cả chứng chỉ, filter nhân viên/khóa/sắp hết hạn |
| `certificate_detail` | `/talent/training/certificates/<pk>/` | GET | Chi tiết chứng chỉ |
| `training_dashboard` | `/talent/training/dashboard/` | GET | KPIs + biểu đồ |
| `training_export` | `/talent/training/export/excel/` | GET | Xuất danh sách enrollment/chứng chỉ |

**`enrollment_add` — logic:**
- Form có multi-select danh sách Employee (filter theo `allowed_departments`)
- Bỏ qua những NV đã đăng ký (unique_together constraint)
- Log: `log_activity(..., 'create', 'talent', f'Đăng ký {count} NV vào lớp {session_code}')`

**`enrollment_update` — logic:**
- Nhận: `status` (attended/absent), `score`, `result`, `feedback_rating`, `feedback_comment`
- Gọi `enrollment.save()` → nếu result=pass, chứng chỉ tự tạo
- Log: `log_activity(..., 'edit', 'talent', f'Cập nhật kết quả {employee.full_name}')`

### 3.3 Dashboard Đào tạo

**KPIs hiển thị:**
- Tổng khóa học active / lớp trong tháng này
- Tổng lượt đăng ký / completion rate (% attended + pass)
- Chứng chỉ sắp hết hạn ≤ 30 ngày (alert card đỏ nếu > 0)
- Biểu đồ: số lượng đào tạo theo tháng (6 tháng gần nhất — line chart)
- Biểu đồ: tỷ lệ kết quả pass/fail/pending (donut chart)
- Bảng: nhân viên có nhiều chứng chỉ sắp hết hạn nhất

---

## Phase 4: Cập nhật UI tổng thể

### 4.1 `employees/templates/employees/home.html`
Thêm **1 card duy nhất** "Tuyển dụng & Đào tạo" vào section "Đang hoạt động":
- Icon: 👥🎓, link `{% url 'talent:talent_home' %}`
- Hiện khi `app_status.app_talent_active and features.app_talent`
- Thêm vào section "Sắp ra mắt" khi chưa active

### 4.2 `system_settings/templates/system_settings/settings_home.html`
Thêm **1 toggle card** "Tuyển dụng & Đào tạo" (cùng pattern với Hợp đồng):
- Toggle `app_talent_active`

### 4.3 `system_settings/views.py` — view `toggle_app`
Thêm `'talent': 'app_talent_active'` vào dict mapping

### 4.4 `system_settings/templates/system_settings/permission_manage.html` + `staff_group_form.html`
Thêm **1 checkbox** `app_talent` — "Tuyển dụng & Đào tạo" (cùng pattern với `app_contracts`)

### 4.5 Thêm auto_logout include vào tất cả template mới
```powershell
# Dùng script PowerShell tương tự v23 đã có sẵn
# Thêm {% include 'employees/includes/auto_logout.html' %} trước </body>
# trong tất cả 28 template mới của app talent
```

---

## Thứ tự thực thi

| Bước | Việc cần làm | File thay đổi |
|---|---|---|
| 1 | Sửa `employees/models.py` (UserProfile + StaffGroup + ActivityLog — thêm `app_talent`) | `employees/models.py` |
| 2 | Sửa `system_settings/models.py` (AppStatus — thêm `app_talent_active`) | `system_settings/models.py` |
| 3 | Sửa `employees/helpers.py` (get_user_features — thêm `app_talent`) | `employees/helpers.py` |
| 4 | `makemigrations employees system_settings && migrate` | — |
| 5 | Tạo app `talent/` — `apps.py`, `models.py` (tất cả 7 models), `forms.py`, `views.py`, `urls.py`, `admin.py` | `talent/` |
| 6 | Tạo 28 templates trong `talent/templates/talent/` | `talent/templates/talent/` |
| 7 | Thêm `'talent'` vào `INSTALLED_APPS` | `myproject/settings.py` |
| 8 | Thêm `path('talent/', include('talent.urls'))` | `myproject/urls.py` |
| 9 | `makemigrations talent && migrate` | — |
| 10 | Cập nhật `home.html` (1 card Tuyển dụng & Đào tạo) | `employees/templates/employees/home.html` |
| 11 | Cập nhật `settings_home.html` (1 toggle Talent) | `system_settings/templates/system_settings/settings_home.html` |
| 12 | Cập nhật `toggle_app` view (thêm `'talent'`) | `system_settings/views.py` |
| 13 | Cập nhật `permission_manage.html` + `staff_group_form.html` (1 checkbox `app_talent`) | system_settings templates |
| 14 | Thêm auto_logout include vào 28 template mới (PowerShell — cùng script v23) | 28 templates mới |
| 15 | `python manage.py check` + test thủ công | — |

---

## Hàm tái dụng từ hệ thống hiện tại

| Hàm | File | Dùng trong |
|---|---|---|
| `log_activity(user, action, target_type, target_name, detail, ip)` | `employees/helpers.py` | Mọi view ghi dữ liệu |
| `_get_client_ip(request)` | `employees/helpers.py` | Mọi view ghi log |
| `get_user_features(user)` | `employees/helpers.py` | Feature gate ở đầu mỗi view |
| `get_allowed_departments(user)` | `employees/helpers.py` | Filter theo phòng ban được phép |
| `AppStatus.get()` | `system_settings/models.py` | Check toggle trong home view |
| `openpyxl` | đã cài | Export Excel |

---

## Kiểm tra sau khi hoàn thành

1. **`python manage.py check`** — không lỗi
2. **`python manage.py runserver`** → http://127.0.0.1:8000/
3. **Superuser test flow Tuyển dụng:**
   - Vào Settings → kích hoạt app "Tuyển dụng & Đào tạo"
   - Home → 1 card "Tuyển dụng & Đào tạo" xuất hiện → click vào → trang tổng quan talent_home
   - Click "Tuyển dụng" → Tạo vị trí → tạo ứng viên → chuyển stage → thêm lịch PV → tạo offer → convert → kiểm tra Employee được tạo
4. **Superuser test flow Đào tạo:**
   - Click "Đào tạo" từ talent_home
   - Tạo khóa học → tạo lớp → đăng ký NV → điểm danh + nhập điểm Pass → kiểm tra chứng chỉ tự tạo
   - Dashboard: KPIs hiển thị đúng, biểu đồ không lỗi
5. **Test phân quyền:** user không phải superuser — chỉ thấy app được gán quyền
6. **ActivityLog:** Mọi thao tác CRUD được ghi vào `/settings/activity-log/`
7. **Export Excel:** Tải file từ trang danh sách ứng viên và danh sách chứng chỉ
