from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from employees.models import Employee


# ─────────────────────────────────────────────
# MODULE 1: CHẤM CÔNG
# ─────────────────────────────────────────────

class WorkShift(models.Model):
    name           = models.CharField('Tên ca', max_length=100)
    start_time     = models.TimeField('Giờ bắt đầu')
    end_time       = models.TimeField('Giờ kết thúc')
    break_minutes  = models.IntegerField('Phút nghỉ giữa ca', default=60)
    standard_hours = models.DecimalField('Giờ chuẩn/ngày', max_digits=4, decimal_places=2, default=8.00)
    is_active      = models.BooleanField('Đang dùng', default=True)

    class Meta:
        verbose_name = 'Ca làm việc'
        ordering = ['start_time']

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')}–{self.end_time.strftime('%H:%M')})"


class PublicHoliday(models.Model):
    name = models.CharField('Tên ngày lễ', max_length=200)
    date = models.DateField('Ngày', unique=True)
    year = models.IntegerField('Năm', editable=False)

    class Meta:
        verbose_name = 'Ngày lễ'
        ordering = ['date']

    def __str__(self):
        return f"{self.name} ({self.date.strftime('%d/%m/%Y')})"

    def save(self, *args, **kwargs):
        self.year = self.date.year
        super().save(*args, **kwargs)


class AttendanceRecord(models.Model):
    STATUS_PRESENT  = 'present'
    STATUS_ABSENT   = 'absent'
    STATUS_HALF_DAY = 'half_day'
    STATUS_LATE     = 'late'
    STATUS_ON_LEAVE = 'on_leave'
    STATUS_HOLIDAY  = 'holiday'

    class OTType(models.TextChoices):
        NORMAL  = 'normal',  'Bình thường (1.5x)'
        NIGHT   = 'night',   'Ban đêm (2.0x)'
        WEEKEND = 'weekend', 'Cuối tuần (2.0x)'
        HOLIDAY = 'holiday', 'Ngày lễ (3.0x)'

    STATUS_CHOICES = [
        ('present',  'Đi làm'),
        ('absent',   'Vắng không phép'),
        ('half_day', 'Nửa ngày'),
        ('late',     'Đi muộn/về sớm'),
        ('on_leave', 'Nghỉ phép'),
        ('holiday',  'Nghỉ lễ'),
    ]

    SOURCE_CHOICES = [
        ('manual',      'Nhập tay'),
        ('import_file', 'Import file'),
        ('system',      'Hệ thống'),
    ]

    employee     = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records', verbose_name='Nhân viên')
    date         = models.DateField('Ngày')
    shift        = models.ForeignKey(WorkShift, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Ca làm việc')
    check_in     = models.TimeField('Giờ vào', null=True, blank=True)
    check_out    = models.TimeField('Giờ ra', null=True, blank=True)
    actual_hours  = models.DecimalField('Giờ làm thực tế', max_digits=5, decimal_places=2, default=0)
    ot_hours      = models.DecimalField('Giờ OT', max_digits=5, decimal_places=2, default=0)
    ot_type       = models.CharField('Loại OT', max_length=20, choices=OTType.choices, null=True, blank=True)
    ot_multiplier = models.DecimalField('Hệ số OT', max_digits=3, decimal_places=1, null=True, blank=True)
    status        = models.CharField('Trạng thái', max_length=20, choices=STATUS_CHOICES, default='present')
    source       = models.CharField('Nguồn', max_length=20, choices=SOURCE_CHOICES, default='manual')
    note         = models.TextField('Ghi chú', blank=True)
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Người tạo')
    created_at   = models.DateTimeField('Thời điểm tạo', auto_now_add=True)

    class Meta:
        verbose_name = 'Bản ghi chấm công'
        unique_together = ('employee', 'date')
        ordering = ['-date', 'employee__employee_code']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date.strftime('%d/%m/%Y')}"

    def calculate_hours(self):
        if self.check_in and self.check_out and self.shift:
            from datetime import datetime, date as date_cls
            d = date_cls.today()
            dt_in  = datetime.combine(d, self.check_in)
            dt_out = datetime.combine(d, self.check_out)
            if dt_out <= dt_in:
                return
            raw_minutes = (dt_out - dt_in).seconds // 60
            worked = max(0, raw_minutes - self.shift.break_minutes)
            self.actual_hours = round(worked / 60, 2)
            self.ot_hours = max(0, round(float(self.actual_hours) - float(self.shift.standard_hours), 2))

    def _determine_ot_type(self):
        """Xác định loại OT dựa trên ngày: lễ > cuối tuần > bình thường."""
        is_holiday = PublicHoliday.objects.filter(date=self.date).exists()
        is_weekend = self.date.weekday() >= 5  # 5=Thứ 7, 6=Chủ nhật
        if is_holiday:
            return self.OTType.HOLIDAY, Decimal('3.0')
        elif is_weekend:
            return self.OTType.WEEKEND, Decimal('2.0')
        else:
            return self.OTType.NORMAL, Decimal('1.5')

    def save(self, *args, **kwargs):
        self.calculate_hours()
        if self.ot_hours and float(self.ot_hours) > 0 and self.date:
            self.ot_type, self.ot_multiplier = self._determine_ot_type()
        else:
            self.ot_type = None
            self.ot_multiplier = None
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
# MODULE 2: NGHỈ PHÉP
# ─────────────────────────────────────────────

class LeaveType(models.Model):
    GENDER_CHOICES = [
        ('all',    'Tất cả'),
        ('female', 'Nữ'),
        ('male',   'Nam'),
    ]

    name               = models.CharField('Tên loại nghỉ', max_length=100)
    code               = models.CharField('Mã loại', max_length=20, default='other')
    max_days_per_year  = models.IntegerField('Số ngày tối đa/năm', default=0, help_text='0 = không giới hạn')
    is_paid            = models.BooleanField('Hưởng lương', default=True)
    requires_approval  = models.BooleanField('Cần duyệt', default=True)
    allow_half_day     = models.BooleanField('Cho nghỉ nửa ngày', default=True)
    document_required  = models.BooleanField('Cần giấy tờ', default=False)
    carry_over         = models.BooleanField('Chuyển năm sau', default=False)
    gender_restriction = models.CharField('Giới tính áp dụng', max_length=10, choices=GENDER_CHOICES, default='all')
    is_active          = models.BooleanField('Đang dùng', default=True)

    class Meta:
        verbose_name = 'Loại nghỉ phép'
        ordering = ['name']

    def __str__(self):
        return self.name


class LeavePolicy(models.Model):
    name             = models.CharField('Tên chính sách', max_length=200)
    base_annual_days = models.IntegerField('Số ngày cơ bản/năm', default=12)
    increment_years  = models.IntegerField('Cứ mỗi X năm thâm niên', default=5)
    increment_days   = models.IntegerField('Cộng thêm X ngày', default=1)
    is_default       = models.BooleanField('Chính sách mặc định', default=False)

    class Meta:
        verbose_name = 'Chính sách phép năm'

    def __str__(self):
        return self.name

    def calculate_days(self, employee, year):
        from datetime import date
        if not employee.start_date:
            return self.base_annual_days
        end_of_year = date(year, 12, 31)
        years_of_service = (end_of_year - employee.start_date).days / 365
        bonus = int(years_of_service / self.increment_years) * self.increment_days
        return self.base_annual_days + bonus

    def save(self, *args, **kwargs):
        if self.is_default:
            LeavePolicy.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class LeaveBalance(models.Model):
    employee       = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances', verbose_name='Nhân viên')
    leave_type     = models.ForeignKey(LeaveType, on_delete=models.CASCADE, verbose_name='Loại nghỉ')
    year           = models.IntegerField('Năm')
    allocated_days = models.DecimalField('Ngày được cấp', max_digits=5, decimal_places=1, default=0)
    used_days      = models.DecimalField('Đã dùng', max_digits=5, decimal_places=1, default=0)
    pending_days   = models.DecimalField('Đang chờ duyệt', max_digits=5, decimal_places=1, default=0)
    carried_days   = models.DecimalField('Chuyển từ năm trước', max_digits=5, decimal_places=1, default=0)
    note           = models.TextField('Ghi chú', blank=True)

    class Meta:
        verbose_name = 'Số dư ngày phép'
        unique_together = ('employee', 'leave_type', 'year')
        ordering = ['-year', 'employee__employee_code']

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name} ({self.year})"

    @property
    def remaining_days(self):
        return float(self.allocated_days) + float(self.carried_days) - float(self.used_days) - float(self.pending_days)


class LeaveRequest(models.Model):
    STATUS_DRAFT      = 'draft'
    STATUS_PENDING    = 'pending'
    STATUS_WAITING_HR = 'waiting_hr'
    STATUS_APPROVED   = 'approved'
    STATUS_REJECTED   = 'rejected'
    STATUS_CANCELLED  = 'cancelled'

    STATUS_CHOICES = [
        ('draft',      'Nháp'),
        ('pending',    'Chờ duyệt cấp 1'),
        ('waiting_hr', 'Chờ HR duyệt'),
        ('approved',   'Đã duyệt'),
        ('rejected',   'Từ chối'),
        ('cancelled',  'Đã hủy'),
    ]

    HALF_DAY_CHOICES = [
        ('morning',   'Buổi sáng'),
        ('afternoon', 'Buổi chiều'),
    ]

    employee        = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests', verbose_name='Nhân viên')
    leave_type      = models.ForeignKey(LeaveType, on_delete=models.PROTECT, verbose_name='Loại nghỉ')
    start_date      = models.DateField('Ngày bắt đầu')
    end_date        = models.DateField('Ngày kết thúc')
    total_days      = models.DecimalField('Số ngày nghỉ', max_digits=5, decimal_places=1, default=0)
    half_day        = models.BooleanField('Nghỉ nửa ngày', default=False)
    half_day_period = models.CharField('Buổi nghỉ', max_length=20, choices=HALF_DAY_CHOICES, blank=True)
    reason          = models.TextField('Lý do')
    document        = models.FileField('Giấy tờ đính kèm', upload_to='leaves/documents/', null=True, blank=True)
    status          = models.CharField('Trạng thái', max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at      = models.DateTimeField('Ngày tạo', auto_now_add=True)
    updated_at      = models.DateTimeField('Cập nhật', auto_now=True)
    approved_at     = models.DateTimeField('Ngày duyệt', null=True, blank=True)

    class Meta:
        verbose_name = 'Đơn xin nghỉ'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name} ({self.start_date.strftime('%d/%m/%Y')})"

    def calculate_total_days(self):
        if not self.start_date or not self.end_date:
            return 0
        if self.half_day:
            return 0.5
        from datetime import timedelta
        holiday_dates = set(
            PublicHoliday.objects.filter(
                date__gte=self.start_date, date__lte=self.end_date
            ).values_list('date', flat=True)
        )
        count = 0
        current = self.start_date
        while current <= self.end_date:
            if current.weekday() < 5 and current not in holiday_dates:
                count += 1
            current += timedelta(days=1)
        return count

    def save(self, *args, **kwargs):
        self.total_days = self.calculate_total_days()
        super().save(*args, **kwargs)


class LeaveApproval(models.Model):
    ACTION_CHOICES = [
        ('approved',  'Đã duyệt'),
        ('rejected',  'Từ chối'),
        ('forwarded', 'Chuyển tiếp'),
    ]

    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='approvals', verbose_name='Đơn xin nghỉ')
    approver      = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Người duyệt')
    level         = models.IntegerField('Cấp duyệt')
    action        = models.CharField('Hành động', max_length=20, choices=ACTION_CHOICES)
    comment       = models.TextField('Nhận xét', blank=True)
    acted_at      = models.DateTimeField('Thời điểm duyệt', auto_now_add=True)

    class Meta:
        verbose_name = 'Lịch sử duyệt đơn'
        ordering = ['acted_at']

    def __str__(self):
        return f"Cấp {self.level}: {self.approver.get_full_name()} → {self.get_action_display()}"
