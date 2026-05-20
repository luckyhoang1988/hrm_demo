import os
from django.db import models
from django.utils import timezone
from employees.models import Employee
from departments.models import Department


class Contract(models.Model):
    TYPE_CHOICES = [
        ('thu_viec',  'Thử việc'),
        ('xd_1_nam',  'HĐLĐ xác định thời hạn 1 năm'),
        ('xd_3_nam',  'HĐLĐ xác định thời hạn 3 năm'),
        ('khong_xd',  'HĐLĐ không xác định thời hạn'),
        ('thuc_tap',  'Hợp đồng thực tập'),
    ]
    STATUS_CHOICES = [
        ('hieu_luc',    'Còn hiệu lực'),
        ('sap_het_han', 'Sắp hết hạn'),
        ('het_han',     'Hết hạn'),
        ('gia_han',     'Đã gia hạn'),
        ('cham_dut',    'Đã chấm dứt'),
    ]
    TERMINATION_REASON_CHOICES = [
        ('het_hop_dong', 'Hết hạn hợp đồng'),
        ('tu_nghi',      'Nhân viên tự nghỉ'),
        ('sa_thai',      'Sa thải'),
        ('thoa_thuan',   'Thỏa thuận hai bên'),
        ('khac',         'Khác'),
    ]

    contract_number    = models.CharField('Số hợp đồng', max_length=50, unique=True)
    employee           = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='contracts', verbose_name='Nhân viên')
    department         = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='contracts', verbose_name='Phòng ban')
    contract_type      = models.CharField('Loại hợp đồng', max_length=20, choices=TYPE_CHOICES)
    status             = models.CharField('Trạng thái', max_length=20, choices=STATUS_CHOICES, default='hieu_luc')
    start_date         = models.DateField('Ngày bắt đầu')
    end_date           = models.DateField('Ngày kết thúc', null=True, blank=True)
    position           = models.CharField('Chức vụ', max_length=100, blank=True)
    salary             = models.DecimalField('Lương theo HĐ', max_digits=12, decimal_places=2, null=True, blank=True)
    basic_salary       = models.DecimalField('Lương cơ bản', max_digits=15, decimal_places=0, null=True, blank=True)
    allowances         = models.JSONField('Phụ cấp', default=dict, blank=True,
                                          help_text='VD: {"housing": 2000000, "transport": 500000}')
    renewed_from       = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='renewals', verbose_name='Gia hạn từ HĐ')
    termination_date   = models.DateField('Ngày chấm dứt', null=True, blank=True)
    termination_reason = models.CharField('Lý do chấm dứt', max_length=20, choices=TERMINATION_REASON_CHOICES, blank=True)
    termination_note   = models.TextField('Ghi chú chấm dứt', blank=True)
    signed_date        = models.DateField('Ngày ký hợp đồng', null=True, blank=True)
    notice_period_days = models.PositiveSmallIntegerField('Thời hạn báo trước (ngày)', default=30)
    note               = models.TextField('Ghi chú', blank=True)
    contract_file      = models.FileField('File hợp đồng', upload_to='contracts/files/', null=True, blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Hợp đồng'
        verbose_name_plural = 'Hợp đồng'

    def __str__(self):
        return f"{self.contract_number} — {self.employee.full_name}"

    @property
    def gross_salary(self):
        """Tổng lương = lương cơ bản + tổng phụ cấp."""
        if not self.basic_salary:
            return self.salary
        return self.basic_salary + sum(self.allowances.values())

    @property
    def days_until_expiry(self):
        if not self.end_date:
            return None
        return (self.end_date - timezone.localdate()).days

    @property
    def is_expiring_soon(self):
        d = self.days_until_expiry
        return d is not None and 0 <= d <= 30

    @property
    def is_expired(self):
        if not self.end_date:
            return False
        return self.end_date < timezone.localdate() and self.status not in ('gia_han', 'cham_dut')

    @property
    def is_indefinite(self):
        return self.contract_type == 'khong_xd'

    @property
    def contract_file_name(self):
        if self.contract_file:
            return os.path.basename(self.contract_file.name)
        return None
