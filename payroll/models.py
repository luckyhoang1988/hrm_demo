from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from employees.models import Employee
from contracts.models import Contract

User = get_user_model()


# ─────────────────────────────────────────────
# CẤU HÌNH TOÀN HỆ THỐNG (fallback)
# ─────────────────────────────────────────────

class PayrollConfig(models.Model):
    """Singleton — cấu hình mặc định khi chưa có InsuranceConfig theo năm."""
    bhxh_rate           = models.DecimalField('Tỷ lệ BHXH NV đóng (%)', max_digits=5, decimal_places=2, default=Decimal('8.00'))
    bhyt_rate           = models.DecimalField('Tỷ lệ BHYT NV đóng (%)', max_digits=5, decimal_places=2, default=Decimal('1.50'))
    bhtn_rate           = models.DecimalField('Tỷ lệ BHTN NV đóng (%)', max_digits=5, decimal_places=2, default=Decimal('1.00'))
    personal_deduction  = models.DecimalField('Giảm trừ bản thân (đ/tháng)', max_digits=15, decimal_places=0, default=Decimal('11000000'))
    dependent_deduction = models.DecimalField('Giảm trừ mỗi người phụ thuộc (đ/tháng)', max_digits=15, decimal_places=0, default=Decimal('4400000'))
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cấu hình bảng lương'

    def __str__(self):
        return 'Cấu hình bảng lương'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ─────────────────────────────────────────────
# CẤU HÌNH BẢO HIỂM THEO NĂM
# ─────────────────────────────────────────────

class InsuranceConfig(models.Model):
    """Cấu hình tỷ lệ BHXH/BHYT/BHTN và mức trần theo từng năm."""
    year                 = models.IntegerField('Năm', unique=True)
    # NV đóng
    si_employee_rate     = models.DecimalField('BHXH NV (%)', max_digits=5, decimal_places=2, default=Decimal('8.00'))
    hi_employee_rate     = models.DecimalField('BHYT NV (%)', max_digits=5, decimal_places=2, default=Decimal('1.50'))
    ui_employee_rate     = models.DecimalField('BHTN NV (%)', max_digits=5, decimal_places=2, default=Decimal('1.00'))
    # Chủ sử dụng lao động đóng (để tham khảo / báo cáo chi phí)
    si_employer_rate     = models.DecimalField('BHXH Chủ (%)', max_digits=5, decimal_places=2, default=Decimal('17.50'))
    hi_employer_rate     = models.DecimalField('BHYT Chủ (%)', max_digits=5, decimal_places=2, default=Decimal('3.00'))
    ui_employer_rate     = models.DecimalField('BHTN Chủ (%)', max_digits=5, decimal_places=2, default=Decimal('1.00'))
    # Mức trần đóng BHXH (= 20 × lương cơ sở)
    salary_cap           = models.DecimalField('Mức trần đóng BH (đ/tháng)', max_digits=15, decimal_places=0, default=Decimal('46800000'))
    # Giảm trừ gia cảnh (thuế TNCN) — thay đổi theo nghị quyết
    personal_deduction   = models.DecimalField('Giảm trừ bản thân (đ/tháng)', max_digits=15, decimal_places=0, default=Decimal('15500000'))
    dependent_deduction  = models.DecimalField('Giảm trừ người phụ thuộc (đ/người/tháng)', max_digits=15, decimal_places=0, default=Decimal('6200000'))

    class Meta:
        verbose_name = 'Cấu hình bảo hiểm theo năm'
        ordering = ['-year']

    def __str__(self):
        return f'Cấu hình BH năm {self.year}'

    @property
    def total_employee_rate(self):
        return self.si_employee_rate + self.hi_employee_rate + self.ui_employee_rate

    @property
    def total_employer_rate(self):
        return self.si_employer_rate + self.hi_employer_rate + self.ui_employer_rate


# ─────────────────────────────────────────────
# BẬC THUẾ TNCN THEO NĂM
# ─────────────────────────────────────────────

class PITBracket(models.Model):
    """Bậc thuế TNCN lũy tiến — cập nhật khi Nhà nước ban hành nghị quyết mới."""
    year        = models.IntegerField('Năm')
    order       = models.PositiveSmallIntegerField('Thứ tự bậc')
    min_income  = models.DecimalField('Thu nhập từ (đ/tháng)', max_digits=15, decimal_places=0, default=0)
    max_income  = models.DecimalField('Thu nhập đến (đ/tháng, để trống = không giới hạn)', max_digits=15, decimal_places=0, null=True, blank=True)
    rate        = models.DecimalField('Thuế suất (VD: 0.05 = 5%)', max_digits=4, decimal_places=2)

    class Meta:
        verbose_name = 'Bậc thuế TNCN'
        unique_together = ('year', 'order')
        ordering = ['year', 'order']

    def __str__(self):
        return f'Bậc {self.order} ({self.year}) — {int(self.rate * 100)}%'

    @property
    def rate_percent(self):
        return self.rate * 100


# ─────────────────────────────────────────────
# CẤU HÌNH LƯƠNG RIÊNG TỪNG NHÂN VIÊN
# ─────────────────────────────────────────────

class SalaryConfig(models.Model):
    """Config lương riêng từng NV — ưu tiên hơn dữ liệu từ Contract khi tính lương."""
    employee        = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='salary_configs', verbose_name='Nhân viên')
    contract        = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True, related_name='salary_configs', verbose_name='Hợp đồng liên kết')
    effective_from  = models.DateField('Hiệu lực từ ngày')
    effective_to    = models.DateField('Hiệu lực đến ngày', null=True, blank=True)
    basic_salary    = models.DecimalField('Lương cơ bản (đ/tháng)', max_digits=15, decimal_places=0)
    allowances      = models.JSONField('Phụ cấp chi tiết', default=dict, blank=True,
                                       help_text='VD: {"Phụ cấp nhà ở": 2000000, "Phụ cấp xăng xe": 500000}')
    dependents      = models.IntegerField('Số người phụ thuộc', default=0)
    is_active       = models.BooleanField('Đang áp dụng', default=True)
    note            = models.TextField('Ghi chú', blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cấu hình lương NV'
        ordering = ['-effective_from']

    def __str__(self):
        return f'{self.employee.full_name} — {self.basic_salary:,.0f} đ (từ {self.effective_from})'

    @property
    def allowances_total(self):
        return sum(Decimal(str(v)) for v in self.allowances.values()) if self.allowances else Decimal('0')

    @property
    def gross_salary(self):
        return Decimal(str(self.basic_salary)) + self.allowances_total


# ─────────────────────────────────────────────
# BẢN GHI OT (TĂNG CA) — CẦN DUYỆT
# ─────────────────────────────────────────────

class OTRecord(models.Model):
    """Yêu cầu tăng ca — HR nhập, quản lý duyệt → mới được tính vào lương."""
    STATUS_PENDING  = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        ('pending',  'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
    ]

    OT_NORMAL  = 'normal'
    OT_NIGHT   = 'night'
    OT_WEEKEND = 'weekend'
    OT_HOLIDAY = 'holiday'
    OT_CHOICES = [
        ('normal',  'Bình thường (1.5×)'),
        ('night',   'Ban đêm (2.0×)'),
        ('weekend', 'Cuối tuần (2.0×)'),
        ('holiday', 'Ngày lễ (3.0×)'),
    ]

    OT_MULTIPLIERS = {
        'normal':  Decimal('1.5'),
        'night':   Decimal('2.0'),
        'weekend': Decimal('2.0'),
        'holiday': Decimal('3.0'),
    }

    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='ot_records', verbose_name='Nhân viên')
    date        = models.DateField('Ngày tăng ca')
    hours       = models.DecimalField('Số giờ OT', max_digits=4, decimal_places=1)
    ot_type     = models.CharField('Loại OT', max_length=20, choices=OT_CHOICES, default='normal')
    multiplier  = models.DecimalField('Hệ số lương', max_digits=3, decimal_places=1, default=Decimal('1.5'))
    reason      = models.TextField('Lý do tăng ca', blank=True)
    status      = models.CharField('Trạng thái', max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_ot_records', verbose_name='Người duyệt')
    approved_at = models.DateTimeField('Thời điểm duyệt', null=True, blank=True)
    note        = models.TextField('Ghi chú duyệt', blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bản ghi tăng ca'
        ordering = ['-date', 'employee__employee_code']

    def __str__(self):
        return f'OT {self.employee.full_name} — {self.date} ({self.hours}h)'

    def save(self, *args, **kwargs):
        # Auto-fill multiplier theo ot_type nếu chưa set hoặc thay đổi type
        self.multiplier = self.OT_MULTIPLIERS.get(self.ot_type, Decimal('1.5'))
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
# HÀM TÍNH THUẾ TNCN
# ─────────────────────────────────────────────

def _calculate_pit(taxable_income, year=None):
    """Tính thuế TNCN lũy tiến. Ưu tiên PITBracket từ DB; fallback hardcoded 2024-2025."""
    if taxable_income <= 0:
        return Decimal('0')

    # Thử lấy từ database
    if year:
        db_brackets = list(PITBracket.objects.filter(year=year).order_by('order'))
        if db_brackets:
            tax = Decimal('0')
            remaining = taxable_income
            for b in db_brackets:
                if remaining <= 0:
                    break
                bracket_size = (b.max_income - b.min_income) if b.max_income is not None else remaining
                chunk = min(remaining, bracket_size)
                tax += chunk * b.rate
                remaining -= chunk
            return tax.quantize(Decimal('1'))

    # Hardcoded fallback (theo luật 2024-2025)
    brackets = [
        (Decimal('5000000'),  Decimal('0.05')),
        (Decimal('5000000'),  Decimal('0.10')),
        (Decimal('8000000'),  Decimal('0.15')),
        (Decimal('14000000'), Decimal('0.20')),
        (Decimal('20000000'), Decimal('0.25')),
        (Decimal('28000000'), Decimal('0.30')),
        (None,                Decimal('0.35')),
    ]
    tax = Decimal('0')
    remaining = taxable_income
    for limit, rate in brackets:
        if limit is None:
            tax += remaining * rate
            break
        chunk = min(remaining, limit)
        tax += chunk * rate
        remaining -= chunk
        if remaining <= 0:
            break
    return tax.quantize(Decimal('1'))


# ─────────────────────────────────────────────
# PHIẾU LƯƠNG
# ─────────────────────────────────────────────

class Payslip(models.Model):
    STATUS_DRAFT     = 'draft'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CHOICES = [
        ('draft',     'Nháp'),
        ('confirmed', 'Đã xác nhận'),
    ]

    employee          = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='payslips', verbose_name='Nhân viên')
    contract          = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True, related_name='payslips', verbose_name='Hợp đồng')
    month             = models.PositiveSmallIntegerField('Tháng')
    year              = models.PositiveSmallIntegerField('Năm')

    # Snapshot lương tại thời điểm tính
    basic_salary      = models.DecimalField('Lương cơ bản', max_digits=15, decimal_places=0, default=0)
    allowances_detail = models.JSONField('Chi tiết phụ cấp', default=dict, blank=True)

    # OT
    ot_hours          = models.DecimalField('Tổng giờ OT', max_digits=7, decimal_places=2, default=0)
    ot_pay            = models.DecimalField('Tiền OT', max_digits=15, decimal_places=0, default=0)

    # Tổng thu nhập
    other_additions   = models.DecimalField('Thưởng / Phụ cấp khác', max_digits=15, decimal_places=0, default=0)
    gross_salary      = models.DecimalField('Tổng thu nhập (Gross)', max_digits=15, decimal_places=0, default=0)

    # Bảo hiểm NV đóng
    bhxh_amount       = models.DecimalField('BHXH', max_digits=15, decimal_places=0, default=0)
    bhyt_amount       = models.DecimalField('BHYT', max_digits=15, decimal_places=0, default=0)
    bhtn_amount       = models.DecimalField('BHTN', max_digits=15, decimal_places=0, default=0)
    total_insurance   = models.DecimalField('Tổng bảo hiểm', max_digits=15, decimal_places=0, default=0)

    # Thuế TNCN
    dependents        = models.PositiveSmallIntegerField('Số người phụ thuộc', default=0)
    taxable_income    = models.DecimalField('Thu nhập chịu thuế', max_digits=15, decimal_places=0, default=0)
    pit_amount        = models.DecimalField('Thuế TNCN', max_digits=15, decimal_places=0, default=0)

    # Khấu trừ khác và lương thực nhận
    other_deductions  = models.DecimalField('Khấu trừ khác', max_digits=15, decimal_places=0, default=0)
    net_salary        = models.DecimalField('Lương thực nhận (Net)', max_digits=15, decimal_places=0, default=0)

    note              = models.TextField('Ghi chú', blank=True)
    status            = models.CharField('Trạng thái', max_length=20, choices=STATUS_CHOICES, default='draft')
    calculated_at     = models.DateTimeField('Thời điểm tính', auto_now=True)

    class Meta:
        verbose_name = 'Phiếu lương'
        unique_together = ('employee', 'month', 'year')
        ordering = ['-year', '-month', 'employee__employee_code']

    def __str__(self):
        return f"Phiếu lương {self.employee.full_name} — {self.month:02d}/{self.year}"

    def calculate(self, config=None, insurance_config=None):
        """Tính toán lại toàn bộ phiếu lương."""
        from attendance.models import AttendanceRecord

        if config is None:
            config = PayrollConfig.get()

        # Thử lấy InsuranceConfig theo năm
        if insurance_config is None:
            try:
                insurance_config = InsuranceConfig.objects.get(year=self.year)
            except InsuranceConfig.DoesNotExist:
                insurance_config = None

        # 1. Lấy thông tin lương: SalaryConfig ưu tiên, fallback Contract
        salary_cfg = (
            SalaryConfig.objects
            .filter(employee=self.employee, is_active=True)
            .order_by('-effective_from')
            .first()
        )
        if salary_cfg:
            self.basic_salary = salary_cfg.basic_salary
            self.allowances_detail = salary_cfg.allowances or {}
            self.dependents = salary_cfg.dependents
        elif self.contract and self.contract.basic_salary:
            self.basic_salary = self.contract.basic_salary
            self.allowances_detail = self.contract.allowances or {}

        allowances_total = (
            sum(Decimal(str(v)) for v in self.allowances_detail.values())
            if self.allowances_detail else Decimal('0')
        )
        basic = Decimal(str(self.basic_salary)) if self.basic_salary else Decimal('0')

        # 2. OT: ưu tiên OTRecord approved trong tháng, fallback AttendanceRecord
        ot_pay = Decimal('0')
        total_ot_hours = Decimal('0')

        approved_ots = OTRecord.objects.filter(
            employee=self.employee,
            date__month=self.month,
            date__year=self.year,
            status=OTRecord.STATUS_APPROVED,
        )
        if approved_ots.exists():
            if basic:
                hourly_rate = basic / 26 / 8
                for rec in approved_ots:
                    total_ot_hours += rec.hours
                    ot_pay += (rec.hours * hourly_rate * rec.multiplier).quantize(Decimal('1'))
        else:
            att_records = AttendanceRecord.objects.filter(
                employee=self.employee,
                date__month=self.month,
                date__year=self.year,
                ot_hours__gt=0,
            )
            if basic:
                hourly_rate = basic / 26 / 8
                for rec in att_records:
                    total_ot_hours += rec.ot_hours
                    multiplier = rec.ot_multiplier if rec.ot_multiplier else Decimal('1.5')
                    ot_pay += (rec.ot_hours * hourly_rate * multiplier).quantize(Decimal('1'))

        self.ot_hours = total_ot_hours
        self.ot_pay = ot_pay

        # 3. Gross
        other_add = Decimal(str(self.other_additions)) if self.other_additions else Decimal('0')
        gross = (basic + allowances_total + ot_pay + other_add).quantize(Decimal('1'))
        self.gross_salary = gross

        # 4. Bảo hiểm với mức trần (tính trên basic_salary)
        if insurance_config:
            bh_base = min(basic, insurance_config.salary_cap)
            self.bhxh_amount = (bh_base * insurance_config.si_employee_rate / 100).quantize(Decimal('1'))
            self.bhyt_amount = (bh_base * insurance_config.hi_employee_rate / 100).quantize(Decimal('1'))
            self.bhtn_amount = (bh_base * insurance_config.ui_employee_rate / 100).quantize(Decimal('1'))
            personal_ded  = insurance_config.personal_deduction
            dependent_ded = insurance_config.dependent_deduction
        else:
            bh_base = basic
            self.bhxh_amount = (bh_base * config.bhxh_rate / 100).quantize(Decimal('1'))
            self.bhyt_amount = (bh_base * config.bhyt_rate / 100).quantize(Decimal('1'))
            self.bhtn_amount = (bh_base * config.bhtn_rate / 100).quantize(Decimal('1'))
            personal_ded  = config.personal_deduction
            dependent_ded = config.dependent_deduction

        self.total_insurance = self.bhxh_amount + self.bhyt_amount + self.bhtn_amount

        # 5. Thu nhập chịu thuế và PIT
        deduction = personal_ded + dependent_ded * self.dependents
        taxable = gross - self.total_insurance - deduction
        self.taxable_income = max(Decimal('0'), taxable).quantize(Decimal('1'))
        self.pit_amount = _calculate_pit(self.taxable_income, year=self.year)

        # 6. Net
        other_ded = Decimal(str(self.other_deductions)) if self.other_deductions else Decimal('0')
        self.net_salary = (gross - self.total_insurance - self.pit_amount - other_ded).quantize(Decimal('1'))

    def generate_lines(self):
        """Tạo PayslipLine chi tiết. Gọi sau save() để có pk."""
        self.lines.all().delete()
        lines = []
        basic = Decimal(str(self.basic_salary)) if self.basic_salary else Decimal('0')

        # Thu nhập
        order = 1
        lines.append(PayslipLine(payslip=self, category='earning', name='Lương cơ bản', amount=basic, order=order))
        for key, val in (self.allowances_detail or {}).items():
            order += 1
            lines.append(PayslipLine(payslip=self, category='earning', name=f'Phụ cấp: {key}', amount=Decimal(str(val)), order=order))
        if self.ot_pay:
            order += 1
            lines.append(PayslipLine(payslip=self, category='earning',
                                     name=f'Làm thêm giờ ({self.ot_hours}h)', amount=self.ot_pay, order=order))
        if self.other_additions:
            order += 1
            lines.append(PayslipLine(payslip=self, category='earning',
                                     name='Thưởng / Phụ cấp khác', amount=Decimal(str(self.other_additions)), order=order))

        # Khấu trừ bảo hiểm
        lines.append(PayslipLine(payslip=self, category='deduction', name='BHXH (NV đóng)', amount=self.bhxh_amount, order=1))
        lines.append(PayslipLine(payslip=self, category='deduction', name='BHYT (NV đóng)', amount=self.bhyt_amount, order=2))
        lines.append(PayslipLine(payslip=self, category='deduction', name='BHTN (NV đóng)', amount=self.bhtn_amount, order=3))
        if self.other_deductions:
            lines.append(PayslipLine(payslip=self, category='deduction',
                                     name='Khấu trừ khác', amount=Decimal(str(self.other_deductions)), order=4))

        # Thuế TNCN
        if self.pit_amount:
            lines.append(PayslipLine(payslip=self, category='tax', name='Thuế TNCN lũy tiến', amount=self.pit_amount, order=1))

        PayslipLine.objects.bulk_create(lines)


# ─────────────────────────────────────────────
# CHI TIẾT DÒNG PHIẾU LƯƠNG
# ─────────────────────────────────────────────

class PayslipLine(models.Model):
    """Dòng chi tiết trong phiếu lương — tạo tự động qua Payslip.generate_lines()."""
    CATEGORY_EARNING   = 'earning'
    CATEGORY_DEDUCTION = 'deduction'
    CATEGORY_TAX       = 'tax'
    CATEGORY_CHOICES = [
        ('earning',   'Thu nhập'),
        ('deduction', 'Khấu trừ'),
        ('tax',       'Thuế'),
    ]

    payslip  = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='lines', verbose_name='Phiếu lương')
    category = models.CharField('Loại', max_length=20, choices=CATEGORY_CHOICES)
    name     = models.CharField('Mô tả', max_length=200)
    amount   = models.DecimalField('Số tiền', max_digits=15, decimal_places=0)
    note     = models.CharField('Ghi chú', max_length=500, blank=True)
    order    = models.PositiveSmallIntegerField('Thứ tự', default=0)

    class Meta:
        ordering = ['category', 'order']

    def __str__(self):
        return f'{self.name}: {self.amount:,.0f} đ'
