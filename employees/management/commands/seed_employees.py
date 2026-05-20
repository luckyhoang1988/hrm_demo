"""
Management command: seed_employees
Xóa toàn bộ nhân viên hiện tại và tạo 500 nhân viên mẫu NV0001–NV0500.

Cách dùng:
    python -X utf8 manage.py seed_employees
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from decimal import Decimal
from employees.models import Employee, StatusLog, ActivityLog
from departments.models import Department

HO = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ',
      'Võ', 'Đặng', 'Bùi', 'Đỗ', 'Hồ', 'Ngô', 'Dương', 'Lý', 'Đinh',
      'Trịnh', 'Cao', 'Tô']

DEM_NAM  = ['Văn', 'Hữu', 'Đình', 'Quốc', 'Minh', 'Tuấn', 'Thanh', 'Đức', 'Anh', 'Công']
DEM_NU   = ['Thị', 'Thùy', 'Thanh', 'Ngọc', 'Phương', 'Lan', 'Kim', 'Thu', 'Mai', 'Bảo']

TEN_NAM = ['An', 'Bảo', 'Cường', 'Dũng', 'Đức', 'Hùng', 'Khoa', 'Long',
           'Minh', 'Nam', 'Phúc', 'Quân', 'Sơn', 'Tài', 'Tuấn', 'Vinh',
           'Hoàng', 'Nhật', 'Trung', 'Khải']
TEN_NU  = ['Anh', 'Chi', 'Duyên', 'Giang', 'Hoa', 'Hương', 'Lan', 'Linh',
           'Mai', 'Ngân', 'Nhi', 'Oanh', 'Phương', 'Quỳnh', 'Thảo',
           'Trang', 'Vy', 'Yến', 'Châu', 'Như']

DEPARTMENTS = [
    ('Kế toán',                ['Kế toán viên', 'Kế toán tổng hợp', 'Trưởng phòng Kế toán'], 10_000_000, 20_000_000),
    ('Công nghệ thông tin',    ['Lập trình viên', 'Kỹ sư hệ thống', 'Trưởng nhóm Backend', 'Kỹ sư QA'], 15_000_000, 30_000_000),
    ('Kinh doanh',             ['Nhân viên Kinh doanh', 'Chuyên viên KD', 'Trưởng phòng Kinh doanh'], 8_000_000, 20_000_000),
    ('Hành chính',             ['Nhân viên Hành chính', 'Chuyên viên Hành chính', 'Thư ký'], 8_000_000, 14_000_000),
    ('Nhân sự',                ['Chuyên viên Nhân sự', 'Tuyển dụng viên', 'Trưởng phòng Nhân sự'], 10_000_000, 18_000_000),
    ('Sản xuất',               ['Công nhân sản xuất', 'Tổ trưởng sản xuất', 'Giám sát sản xuất'], 7_000_000, 15_000_000),
    ('Marketing',              ['Chuyên viên Marketing', 'Content Creator', 'Trưởng phòng Marketing'], 10_000_000, 22_000_000),
    ('Kho vận',                ['Nhân viên kho', 'Thủ kho', 'Trưởng kho'], 7_500_000, 14_000_000),
    ('Pháp lý',                ['Chuyên viên Pháp lý', 'Luật sư nội bộ', 'Trưởng phòng Pháp lý'], 15_000_000, 30_000_000),
    ('Ban Giám Đốc',           ['Trợ lý Giám đốc', 'Phó Giám đốc', 'Giám đốc điều hành'], 20_000_000, 50_000_000),
]

# Phân bổ trạng thái: 500 NV
# dang_lam: 380, thu_viec: 40, thuc_tap_sinh: 30,
# nghi_phep: 15, nghi_sinh: 10, nghi_khong_luong: 8, nghi_om: 7, nghi_viec: 10
STATUS_DIST = (
    ['dang_lam']         * 380 +
    ['thu_viec']         * 40  +
    ['thuc_tap_sinh']    * 30  +
    ['nghi_phep']        * 15  +
    ['nghi_sinh']        * 10  +
    ['nghi_khong_luong'] * 8   +
    ['nghi_om']          * 7   +
    ['nghi_viec']        * 10
)  # tổng 500

DEGREES = ['dai_hoc', 'cao_dang', 'thac_si', 'trung_cap', 'tien_si', 'trung_hoc']
MARITAL = ['doc_than', 'da_ket_hon', 'ly_hon', 'doc_than', 'da_ket_hon']

LEAVE_STATUSES     = {'nghi_phep', 'nghi_sinh', 'nghi_khong_luong', 'nghi_om'}
DATE_STATUSES      = {'thu_viec', 'thuc_tap_sinh'}
TERMINATION_STATUS = 'nghi_viec'


class Command(BaseCommand):
    help = 'Xóa toàn bộ nhân viên và tạo 500 nhân viên mẫu NV0001–NV0500'

    def handle(self, *args, **options):
        self.stdout.write('=' * 55)
        self.stdout.write('  SEED 500 NHÂN VIÊN MẪU')
        self.stdout.write('=' * 55)

        with transaction.atomic():
            self._delete_all()
            depts = self._ensure_departments()
            self._create_employees(depts)

        self.stdout.write(self.style.SUCCESS('\nHoàn thành! Truy cập: http://127.0.0.1:8000/employees/'))

    # ── Bước 1: Xóa dữ liệu cũ ──────────────────────────────────────────
    def _delete_all(self):
        self.stdout.write('\n[1/3] Xóa dữ liệu nhân viên cũ...')

        # Phải xóa contracts trước vì on_delete=PROTECT
        try:
            from contracts.models import Contract
            n = Contract.objects.all().delete()[0]
            self.stdout.write(f'  • Đã xóa {n} hợp đồng')
        except Exception:
            pass

        # Các bảng CASCADE sẽ tự xóa khi employee bị xóa,
        # nhưng xóa tường minh để in số liệu rõ hơn
        try:
            from attendance.models import AttendanceRecord, LeaveRequest, LeaveBalance
            AttendanceRecord.objects.all().delete()
            LeaveRequest.objects.all().delete()
            LeaveBalance.objects.all().delete()
        except Exception:
            pass

        try:
            from talent.models import TrainingCertificate, TrainingEnrollment
            TrainingCertificate.objects.all().delete()
            TrainingEnrollment.objects.all().delete()
        except Exception:
            pass

        n_log  = StatusLog.objects.all().delete()[0]
        n_emp  = Employee.objects.all().delete()[0]
        self.stdout.write(f'  • Đã xóa {n_emp} nhân viên, {n_log} status log')

    # ── Bước 2: Đảm bảo các phòng ban tồn tại ────────────────────────────
    def _ensure_departments(self):
        self.stdout.write('\n[2/3] Chuẩn bị phòng ban...')
        dept_objects = []
        for (name, _, _, _) in DEPARTMENTS:
            dept, created = Department.objects.get_or_create(name=name)
            icon = '✓ Tạo mới' if created else '→ Đã có'
            self.stdout.write(f'  {icon}: {name}')
            dept_objects.append(dept)
        return dept_objects

    # ── Bước 3: Tạo 500 nhân viên ─────────────────────────────────────────
    def _create_employees(self, depts):
        self.stdout.write('\n[3/3] Tạo 500 nhân viên...')
        today = date.today()
        employees = []

        for i in range(500):
            n = i + 1  # 1 → 500

            # Giới tính: chẵn = nam, lẻ = nữ
            is_male = (n % 2 == 0)

            # Họ tên
            ho  = HO[i % len(HO)]
            dem = DEM_NAM[i % len(DEM_NAM)] if is_male else DEM_NU[i % len(DEM_NU)]
            ten = TEN_NAM[i % len(TEN_NAM)] if is_male else TEN_NU[i % len(TEN_NU)]
            full_name = f'{ho} {dem} {ten}'

            # Mã nhân viên
            employee_code = f'NV{n:04d}'

            # Email (dùng ten+ho+n để đảm bảo unique)
            email = f'{_slug(ten)}.{_slug(ho)}{n}@company.vn'

            # Phòng ban & chức vụ
            dept_idx   = i % len(DEPARTMENTS)
            dept_name, positions, sal_min, sal_max = DEPARTMENTS[dept_idx]
            dept       = depts[dept_idx]
            position   = positions[i % len(positions)]

            # Lương (phân tầng trong khoảng min–max của phòng ban)
            sal_range = sal_max - sal_min
            salary    = Decimal(sal_min + (sal_range * (i % 5)) // 4)

            # Ngày vào làm (trải đều 5 năm gần nhất)
            days_ago  = (i * 3) % (5 * 365)
            hire_date = today - timedelta(days=days_ago)

            # Trạng thái
            status = STATUS_DIST[i]

            # Thông tin thêm tùy trạng thái
            status_start_date = status_end_date = None
            status_note       = ''
            termination_date  = None
            termination_reason = ''

            if status in DATE_STATUSES:
                status_start_date = today - timedelta(days=30)
                status_end_date   = today + timedelta(days=60)

            elif status in LEAVE_STATUSES:
                status_start_date = today - timedelta(days=10)
                status_end_date   = today + timedelta(days=20)
                status_note       = 'Nghỉ theo đơn đã được duyệt'

            elif status == TERMINATION_STATUS:
                termination_date   = today - timedelta(days=(i % 30) + 1)
                termination_reason = 'Hết hợp đồng'

            # CCCD (12 số)
            id_card = f'{(n * 7 + 100000000000) % 900000000000 + 100000000000}'[:12]

            employees.append(Employee(
                employee_code      = employee_code,
                full_name          = full_name,
                email              = email,
                phone              = f'09{n:08d}'[:10],
                department         = dept,
                position           = position,
                salary             = salary,
                hire_date          = hire_date,
                status             = status,
                marital_status     = MARITAL[i % len(MARITAL)],
                degree             = DEGREES[i % len(DEGREES)],
                id_card            = id_card,
                status_start_date  = status_start_date,
                status_end_date    = status_end_date,
                status_note        = status_note,
                termination_date   = termination_date,
                termination_reason = termination_reason,
            ))

        Employee.objects.bulk_create(employees)
        self.stdout.write(f'  ✓ Đã tạo {len(employees)} nhân viên (NV0001 – NV0500)')

        # In phân bổ trạng thái
        self.stdout.write('\n  Phân bổ trạng thái:')
        from django.db.models import Count
        for row in Employee.objects.values('status').annotate(n=Count('id')).order_by('-n'):
            label = dict(Employee.STATUS_CHOICES).get(row['status'], row['status'])
            self.stdout.write(f'    {label:<25} {row["n"]:>3} người')

        # In phân bổ phòng ban
        self.stdout.write('\n  Phân bổ phòng ban:')
        for row in Employee.objects.values('department__name').annotate(n=Count('id')).order_by('department__name'):
            self.stdout.write(f'    {row["department__name"]:<30} {row["n"]:>3} người')


def _slug(s):
    """Chuyển tên tiếng Việt thành slug không dấu."""
    table = str.maketrans(
        'àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ'
        'ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ',
        'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd'
        'AAAAAAAAAAAAAAAAAEEEEEEEEEEEIIIIIOOOOOOOOOOOOOOOOOUUUUUUUUUUUYYYYYD',
    )
    return s.lower().translate(table)
