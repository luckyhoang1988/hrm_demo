from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date
from employees.models import Employee
from departments.models import Department

PRIORITY_CHOICES = [
    ('low', 'Thấp'),
    ('normal', 'Bình thường'),
    ('high', 'Cao'),
    ('urgent', 'Khẩn cấp'),
]
RECOMMENDATION_CHOICES = [
    ('strong_yes', 'Rất đồng ý tuyển'),
    ('yes', 'Đồng ý tuyển'),
    ('maybe', 'Cân nhắc'),
    ('no', 'Không đồng ý'),
]
NEED_STATUS = [
    ('pending', 'Chờ duyệt'),
    ('approved', 'Đã duyệt'),
    ('rejected', 'Từ chối'),
    ('enrolled', 'Đã đăng ký học'),
]
PLAN_STATUS = [
    ('not_started', 'Chưa bắt đầu'),
    ('in_progress', 'Đang học'),
    ('completed', 'Hoàn thành'),
    ('overdue', 'Quá hạn'),
]
PLAN_APPROVAL_STATUS = [
    ('pending',  'Chờ duyệt'),
    ('approved', 'Đã duyệt'),
    ('rejected', 'Từ chối'),
]
JOB_APPROVAL_STATUS = [
    ('pending',  'Chờ duyệt'),
    ('approved', 'Đã duyệt'),
    ('rejected', 'Từ chối'),
]

EMPLOYMENT_TYPE = [
    ('full_time', 'Toàn thời gian'),
    ('part_time', 'Bán thời gian'),
    ('internship', 'Thực tập'),
    ('seasonal', 'Thời vụ'),
]
JOB_STATUS = [
    ('draft', 'Nháp'),
    ('open', 'Đang tuyển'),
    ('interviewing', 'Đang PV'),
    ('filled', 'Đã tuyển đủ'),
    ('cancelled', 'Đã hủy'),
]
STAGE_CHOICES = [
    ('new', 'Mới nộp'),
    ('screening', 'Sàng lọc'),
    ('interview', 'Phỏng vấn'),
    ('offer', 'Đề nghị'),
    ('hired', 'Đã tuyển'),
    ('rejected', 'Loại'),
]
SOURCE_CHOICES = [
    ('topcv', 'TopCV'),
    ('vietnamworks', 'VietnamWorks'),
    ('linkedin', 'LinkedIn'),
    ('facebook', 'Facebook'),
    ('website', 'Website công ty'),
    ('referral', 'Giới thiệu nội bộ'),
    ('direct', 'Nộp trực tiếp'),
    ('other', 'Khác'),
]
INTERVIEW_TYPE = [
    ('phone', 'Điện thoại'),
    ('online', 'Online'),
    ('in_person', 'Trực tiếp'),
    ('technical', 'Chuyên môn'),
]
INTERVIEW_STATUS = [
    ('scheduled', 'Đã lên lịch'),
    ('completed', 'Đã hoàn thành'),
    ('cancelled', 'Đã hủy'),
    ('no_show', 'Vắng mặt'),
]
OFFER_STATUS = [
    ('draft', 'Nháp'),
    ('sent', 'Đã gửi'),
    ('accepted', 'Đã chấp nhận'),
    ('rejected', 'Từ chối'),
    ('expired', 'Hết hạn'),
]
CATEGORY = [
    ('soft_skill', 'Kỹ năng mềm'),
    ('technical', 'Chuyên môn'),
    ('safety', 'An toàn lao động'),
    ('compliance', 'Tuân thủ quy định'),
    ('onboarding', 'Hội nhập'),
]
DELIVERY = [
    ('classroom', 'Tập trung tại lớp'),
    ('online', 'Trực tuyến'),
    ('on_job', 'Thực chiến tại chỗ'),
    ('blended', 'Kết hợp'),
]
ENROLLMENT_STATUS = [
    ('registered', 'Đã đăng ký'),
    ('attended', 'Đã tham dự'),
    ('absent', 'Vắng mặt'),
    ('cancelled', 'Đã hủy'),
]
RESULT = [
    ('pending', 'Chưa có kết quả'),
    ('pass', 'Đạt'),
    ('fail', 'Không đạt'),
]
SESSION_STATUS = [
    ('planned', 'Đã lên kế hoạch'),
    ('ongoing', 'Đang diễn ra'),
    ('completed', 'Đã hoàn thành'),
    ('cancelled', 'Đã hủy'),
]

# Constants để dùng thay magic strings trong views/tasks
APPROVAL_PENDING  = 'pending'
APPROVAL_APPROVED = 'approved'
APPROVAL_REJECTED = 'rejected'

STAGE_NEW      = 'new'
STAGE_HIRED    = 'hired'
STAGE_REJECTED = 'rejected'

OFFER_SENT    = 'sent'
OFFER_EXPIRED = 'expired'

PLAN_NOT_STARTED = 'not_started'
PLAN_IN_PROGRESS = 'in_progress'
PLAN_COMPLETED   = 'completed'
PLAN_OVERDUE     = 'overdue'

RESULT_PASS    = 'pass'
RESULT_FAIL    = 'fail'
RESULT_PENDING = 'pending'


class JobPosition(models.Model):
    title = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='job_positions')
    headcount = models.PositiveIntegerField(default=1)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE, default='full_time')
    salary_min = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    location = models.CharField(max_length=200, default='Văn phòng chính')
    open_date = models.DateField()
    close_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=JOB_STATUS, default='draft')
    hiring_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_jobs')
    source_channels = models.CharField(max_length=500, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='requested_jobs')
    approval_status = models.CharField(max_length=20, choices=JOB_APPROVAL_STATUS, default='approved')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_jobs')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_note = models.TextField('Ghi chú duyệt', blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status'], name='talent_job_status_idx'),
            models.Index(fields=['status', 'created_at'], name='talent_job_status_date_idx'),
        ]

    def __str__(self):
        return self.title

    @property
    def days_open(self):
        return (date.today() - self.open_date).days

    @property
    def is_overdue(self):
        return self.close_date and self.close_date < date.today() and self.status == 'open'

    @property
    def filled_count(self):
        return self.applicants.filter(stage='hired').count()


class Applicant(models.Model):
    job_position = models.ForeignKey(JobPosition, on_delete=models.CASCADE, related_name='applicants')
    full_name = models.CharField(max_length=200)
    email = models.CharField(max_length=254)
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=500, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='other')
    referrer = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    cv_file = models.FileField(upload_to='recruitment/cv/', null=True, blank=True)
    cover_letter = models.TextField(blank=True)
    linkedin_url = models.URLField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='new')
    reject_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    converted_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='converted_from')
    hired_at = models.DateTimeField(null=True, blank=True, help_text='Tự động set khi stage chuyển sang hired')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='applicants_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('job_position', 'email')
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['stage'], name='talent_applicant_stage_idx'),
            models.Index(fields=['applied_at'], name='talent_app_applied_at_idx'),
            models.Index(fields=['stage', 'applied_at'], name='talent_app_stage_date_idx'),
        ]

    def __str__(self):
        return f"{self.full_name} — {self.job_position.title}"

    @property
    def has_offer(self):
        return hasattr(self, 'joboffer')


class Interview(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='interviews')
    round_number = models.PositiveIntegerField(default=1)
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPE, default='in_person')
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    location = models.CharField(max_length=200, blank=True)
    interviewers = models.ManyToManyField(User, blank=True, related_name='interviews')
    meeting_url = models.URLField(blank=True, help_text='Link Zoom/Google Meet/Teams')
    status = models.CharField(max_length=20, choices=INTERVIEW_STATUS, default='scheduled')
    score = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    score_technical = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    score_communication = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    score_culture_fit = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='interviews_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_date', 'scheduled_time']

    def __str__(self):
        return f"PV vòng {self.round_number} — {self.applicant.full_name}"

    @property
    def average_score(self):
        scores = [s for s in [self.score_technical, self.score_communication, self.score_culture_fit] if s is not None]
        if scores:
            return round(sum(scores) / len(scores), 1)
        return self.score


class JobOffer(models.Model):
    applicant = models.OneToOneField(Applicant, on_delete=models.CASCADE, related_name='joboffer')
    offered_salary = models.DecimalField(max_digits=15, decimal_places=0)
    start_date = models.DateField()
    probation_months = models.PositiveIntegerField(default=2)
    benefits_note = models.TextField(blank=True)
    offer_letter_file = models.FileField(upload_to='recruitment/offers/', null=True, blank=True)
    deadline_response = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=OFFER_STATUS, default='draft')
    rejection_reason = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='offers_created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer — {self.applicant.full_name}"

    @property
    def is_expired(self):
        return self.deadline_response and self.deadline_response < date.today() and self.status == 'sent'


class TrainingCourse(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY, default='technical')
    delivery_method = models.CharField(max_length=20, choices=DELIVERY, default='classroom')
    duration_hours = models.DecimalField(max_digits=6, decimal_places=1)
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=False)
    provider = models.CharField(max_length=200, default='Nội bộ')
    cost_per_person = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    certificate_validity_months = models.PositiveIntegerField(null=True, blank=True)
    target_departments = models.ManyToManyField(Department, blank=True, related_name='training_courses')
    learning_objectives = models.TextField(blank=True, help_text='Học viên đạt được gì sau khóa học (mỗi dòng 1 mục tiêu)')
    prerequisites = models.TextField(blank=True, help_text='Yêu cầu trước khi tham gia')
    passing_score = models.PositiveIntegerField(default=60, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text='Điểm tối thiểu để đạt (%)')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"[{self.code}] {self.name}"


class TrainingSession(models.Model):
    course = models.ForeignKey(TrainingCourse, on_delete=models.PROTECT, related_name='sessions')
    session_code = models.CharField(max_length=50, unique=True)
    trainer_name = models.CharField(max_length=200)
    trainer_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='training_sessions')
    location = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    online_meeting_url = models.URLField(blank=True, help_text='Link Zoom/Meet/Teams nếu học online')
    recording_url = models.URLField(blank=True, help_text='Link video ghi lại buổi học')
    materials_file = models.FileField(upload_to='training/materials/', null=True, blank=True, help_text='Tài liệu đào tạo (PDF, PPT...)')
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='planned')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['status', 'start_date'], name='talent_session_status_date_idx'),
        ]

    def __str__(self):
        return f"[{self.session_code}] {self.course.name}"

    @property
    def enrolled_count(self):
        return self.enrollments.exclude(status='cancelled').count()

    @property
    def available_slots(self):
        if self.max_participants is None:
            return None
        return self.max_participants - self.enrolled_count


def _add_months(d, months):
    """Thêm số tháng vào ngày d, thuần Python không cần dateutil."""
    import calendar
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def generate_cert_number():
    today = date.today().strftime('%Y%m%d')
    prefix = f"CERT-{today}-"
    count = TrainingCertificate.objects.filter(certificate_number__startswith=prefix).count()
    candidate = f"{prefix}{count + 1:04d}"
    while TrainingCertificate.objects.filter(certificate_number=candidate).exists():
        count += 1
        candidate = f"{prefix}{count + 1:04d}"
    return candidate


class TrainingEnrollment(models.Model):
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='enrollments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments_created')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS, default='registered')
    score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    result = models.CharField(max_length=20, choices=RESULT, default='pending')
    feedback_rating = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    feedback_comment = models.TextField(blank=True)

    class Meta:
        unique_together = ('session', 'employee')
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['result'], name='talent_enrollment_result_idx'),
            models.Index(fields=['status'], name='talent_enrollment_status_idx'),
        ]

    def __str__(self):
        return f"{self.employee.full_name} — {self.session.session_code}"

    def save(self, *args, **kwargs):
        if self.score is not None and self.result == 'pending':
            passing = self.session.course.passing_score
            self.result = 'pass' if self.score >= passing else 'fail'
        super().save(*args, **kwargs)
        if self.result == 'pass' and not TrainingCertificate.objects.filter(enrollment=self).exists():
            course = self.session.course
            expiry = None
            if course.certificate_validity_months:
                expiry = _add_months(date.today(), course.certificate_validity_months)
            TrainingCertificate.objects.create(
                enrollment=self,
                employee=self.employee,
                course=course,
                certificate_number=generate_cert_number(),
                issued_date=date.today(),
                expiry_date=expiry,
            )


class TrainingCertificate(models.Model):
    enrollment = models.OneToOneField(TrainingEnrollment, on_delete=models.CASCADE, related_name='certificate')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(TrainingCourse, on_delete=models.CASCADE, related_name='certificates')
    certificate_number = models.CharField(max_length=50, unique=True)
    issued_date = models.DateField(default=date.today)
    expiry_date = models.DateField(null=True, blank=True)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='certificates_issued')
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-issued_date']
        indexes = [
            models.Index(fields=['expiry_date', 'is_active'], name='talent_cert_expiry_idx'),
        ]

    def __str__(self):
        return f"[{self.certificate_number}] {self.employee.full_name} — {self.course.name}"

    @property
    def is_expired(self):
        return bool(self.expiry_date and self.expiry_date < date.today())

    @property
    def days_until_expiry(self):
        if not self.expiry_date:
            return None
        return (self.expiry_date - date.today()).days

    @property
    def expiring_soon(self):
        d = self.days_until_expiry
        return d is not None and d <= 30


class ApplicantStageHistory(models.Model):
    """Lịch sử thay đổi stage ứng viên — tự động ghi mỗi khi stage thay đổi."""
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='stage_history')
    from_stage = models.CharField(max_length=20, choices=STAGE_CHOICES)
    to_stage = models.CharField(max_length=20, choices=STAGE_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stage_changes')
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.applicant.full_name}: {self.from_stage} → {self.to_stage}"


class TrainingNeedAssessment(models.Model):
    """Đề xuất nhu cầu đào tạo từ nhân viên hoặc quản lý."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='training_needs')
    course = models.ForeignKey(
        TrainingCourse, on_delete=models.PROTECT, related_name='needs',
        null=True, blank=True, help_text='Khóa học nếu đã có trong danh mục'
    )
    course_name_free = models.CharField(max_length=200, blank=True, help_text='Tên khóa học nếu chưa có trong danh mục')
    reason = models.TextField(help_text='Lý do cần đào tạo, kỹ năng cần nâng cao')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='training_requests')
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=NEED_STATUS, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='training_reviews')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        course_label = self.course.name if self.course else self.course_name_free
        return f"{self.employee.full_name} — {course_label}"


class EmployeeTrainingPlan(models.Model):
    """Kế hoạch đào tạo bắt buộc theo năm cho từng nhân viên."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='training_plans')
    course = models.ForeignKey(TrainingCourse, on_delete=models.PROTECT, related_name='plans')
    year = models.PositiveIntegerField(help_text='Năm kế hoạch, ví dụ 2026')
    deadline = models.DateField(null=True, blank=True, help_text='Hạn hoàn thành')
    status = models.CharField(max_length=20, choices=PLAN_STATUS, default='not_started')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='plans_assigned')
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_enrollment = models.ForeignKey(
        TrainingEnrollment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='fulfills_plans', help_text='Enrollment hoàn thành kế hoạch này'
    )
    notes = models.TextField(blank=True)
    is_employee_request = models.BooleanField('Nhân viên tự đề xuất', default=False)
    approval_status = models.CharField(max_length=20, choices=PLAN_APPROVAL_STATUS, default='approved')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_plans')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_note = models.TextField('Ghi chú duyệt', blank=True)

    class Meta:
        unique_together = ('employee', 'course', 'year')
        ordering = ['year', 'deadline']

    def __str__(self):
        return f"{self.employee.full_name} — {self.course.name} ({self.year})"

    @property
    def is_overdue(self):
        return (
            self.deadline is not None and
            self.deadline < date.today() and
            self.status not in ('completed',)
        )
