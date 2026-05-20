from django.db import models
from django.contrib.auth.models import User
from departments.models import Department, EmployeeGroup


class UserProfile(models.Model):
    user               = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # Quyền theo ứng dụng
    app_employees      = models.BooleanField(default=False)
    app_contracts      = models.BooleanField(default=False)
    app_attendance     = models.BooleanField(default=False)
    app_payroll        = models.BooleanField(default=False)
    app_talent         = models.BooleanField(default=False)
    # Quyền theo chức năng
    can_export         = models.BooleanField(default=False)
    can_import         = models.BooleanField(default=False)
    can_view_dashboard = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def get_allowed_departments(self):
        group_ids = self.group_perms.values_list('group_id', flat=True)
        return Department.objects.filter(employeegroup__in=group_ids).distinct()


class UserGroupPermission(models.Model):
    """Quyền của 1 user trên 1 nhóm bộ phận cụ thể."""
    profile    = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='group_perms')
    group      = models.ForeignKey(EmployeeGroup, on_delete=models.CASCADE, related_name='user_perms')
    can_add    = models.BooleanField(default=False)
    can_edit   = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        unique_together = ('profile', 'group')
        ordering = ['group__name']

    def __str__(self):
        return f"{self.profile.user.username} – {self.group.name}"


class StaffGroup(models.Model):
    """Nhóm người dùng để phân quyền theo nhóm."""
    name        = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True)
    members     = models.ManyToManyField(User, blank=True, related_name='staff_groups')
    # Quyền ứng dụng
    app_employees      = models.BooleanField(default=False)
    app_contracts      = models.BooleanField(default=False)
    app_attendance     = models.BooleanField(default=False)
    app_payroll        = models.BooleanField(default=False)
    app_talent         = models.BooleanField(default=False)
    # Quyền chức năng
    can_export         = models.BooleanField(default=False)
    can_import         = models.BooleanField(default=False)
    can_view_dashboard = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class StaffGroupDeptPerm(models.Model):
    """Quyền của StaffGroup trên từng nhóm bộ phận (EmployeeGroup)."""
    staff_group = models.ForeignKey(StaffGroup, on_delete=models.CASCADE, related_name='dept_perms')
    emp_group   = models.ForeignKey(EmployeeGroup, on_delete=models.CASCADE, related_name='staff_perms')
    can_add     = models.BooleanField(default=False)
    can_edit    = models.BooleanField(default=False)
    can_delete  = models.BooleanField(default=False)

    class Meta:
        unique_together = ('staff_group', 'emp_group')
        ordering = ['emp_group__name']

    def __str__(self):
        return f"{self.staff_group.name} → {self.emp_group.name}"


class Employee(models.Model):
    STATUS_CHOICES = [
        ('dang_lam',         'Đang làm việc'),
        ('thu_viec',         'Thử việc'),
        ('thuc_tap_sinh',    'Thực tập sinh'),
        ('nghi_phep',        'Nghỉ phép'),
        ('nghi_sinh',        'Nghỉ thai sản'),
        ('nghi_khong_luong', 'Nghỉ không lương'),
        ('nghi_om',          'Nghỉ ốm dài ngày'),
        ('nghi_viec',        'Nghỉ việc'),
    ]
    MARITAL_CHOICES = [
        ('doc_than',    'Độc thân'),
        ('da_ket_hon',  'Đã kết hôn'),
        ('ly_hon',      'Ly hôn'),
        ('goa',         'Góa'),
    ]
    DEGREE_CHOICES = [
        ('trung_hoc',   'Trung học'),
        ('trung_cap',   'Trung cấp'),
        ('cao_dang',    'Cao đẳng'),
        ('dai_hoc',     'Đại học'),
        ('thac_si',     'Thạc sĩ'),
        ('tien_si',     'Tiến sĩ'),
    ]

    user               = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee')
    employee_code      = models.CharField(max_length=20, unique=True, blank=True, null=True)
    photo              = models.ImageField(upload_to='employees/', blank=True, null=True)
    full_name          = models.CharField(max_length=100)
    status             = models.CharField(max_length=20, choices=STATUS_CHOICES, default='dang_lam')
    phone              = models.CharField(max_length=15, blank=True)
    address            = models.CharField(max_length=255, blank=True)
    id_card            = models.CharField(max_length=20, blank=True)
    marital_status     = models.CharField(max_length=20, choices=MARITAL_CHOICES, blank=True)
    degree             = models.CharField(max_length=20, choices=DEGREE_CHOICES, blank=True)
    email              = models.EmailField(unique=True)
    department         = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='employees')
    position           = models.CharField(max_length=100)
    salary             = models.DecimalField(max_digits=10, decimal_places=2)
    hire_date          = models.DateField()
    termination_date            = models.DateField(null=True, blank=True)
    termination_reason          = models.TextField(blank=True)
    scheduled_termination_date  = models.DateField(null=True, blank=True)
    status_note                 = models.TextField(blank=True)
    status_start_date           = models.DateField(null=True, blank=True)
    status_end_date             = models.DateField(null=True, blank=True)

    @staticmethod
    def generate_employee_code(hire_date=None):
        """Auto-generate mã NV theo format NV-YY#### (ví dụ: NV-260001)."""
        from datetime import date
        year = (hire_date or date.today()).strftime('%y')  # "26"
        last = Employee.objects.filter(
            employee_code__startswith=f'NV-{year}'
        ).order_by('-employee_code').first()
        seq = int(last.employee_code[-4:]) + 1 if last else 1
        return f'NV-{year}{seq:04d}'

    def __str__(self):
        return self.full_name

    @property
    def is_active(self):
        return self.status != 'nghi_viec'

    @property
    def days_until_status_end(self):
        """Số ngày còn lại đến status_end_date. None nếu không có ngày kết thúc."""
        if not self.status_end_date:
            return None
        from datetime import date
        return (self.status_end_date - date.today()).days

    @property
    def status_expiring_soon(self):
        """True nếu còn ≤ 15 ngày đến ngày kết thúc trạng thái (hoặc đã quá hạn)."""
        days = self.days_until_status_end
        return days is not None and days <= 15

    @property
    def days_until_termination(self):
        """Số ngày còn lại đến scheduled_termination_date. None nếu không có lịch."""
        if not self.scheduled_termination_date:
            return None
        from datetime import date
        return (self.scheduled_termination_date - date.today()).days


class ActivityLog(models.Model):
    """Ghi lại mọi hành động của user trong hệ thống."""
    ACTION_CHOICES = [
        ('create',        'Tạo mới'),
        ('edit',          'Chỉnh sửa'),
        ('delete',        'Xóa'),
        ('status_change', 'Đổi trạng thái'),
        ('login',         'Đăng nhập'),
        ('logout',        'Đăng xuất'),
        ('import',        'Import dữ liệu'),
        ('export',        'Xuất file'),
    ]
    TARGET_CHOICES = [
        ('employee',    'Nhân viên'),
        ('department',  'Phòng ban'),
        ('emp_group',   'Nhóm bộ phận'),
        ('staff_group', 'Nhóm người dùng'),
        ('user',        'Tài khoản'),
        ('permission',  'Phân quyền'),
        ('contract',    'Hợp đồng'),
        ('talent',      'Tuyển dụng & Đào tạo'),
        ('attendance',  'Chấm công'),
        ('leave',       'Nghỉ phép'),
        ('system',      'Hệ thống'),
    ]
    user        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action      = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES)
    target_name = models.CharField(max_length=200, blank=True)
    detail      = models.TextField(blank=True)
    ip          = models.GenericIPAddressField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} | {self.action} | {self.target_name}"


class StatusLog(models.Model):
    """Lịch sử thay đổi trạng thái nhân viên."""
    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='status_logs')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='status_changes')
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    note       = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    def get_old_status_display(self):
        return dict(Employee.STATUS_CHOICES).get(self.old_status, self.old_status)

    def get_new_status_display(self):
        return dict(Employee.STATUS_CHOICES).get(self.new_status, self.new_status)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.employee} | {self.old_status} → {self.new_status}"
