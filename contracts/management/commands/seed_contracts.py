"""
Management command: seed_contracts
Tạo 100 hợp đồng mẫu cho nhân viên NV0001–NV0100.

Cách dùng:
    python -X utf8 manage.py seed_contracts
    python -X utf8 manage.py seed_contracts --clear    # Xóa HĐ cũ rồi tạo lại
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from decimal import Decimal
from employees.models import Employee
from contracts.models import Contract

TODAY = date.today()

# Phân bổ 100 hợp đồng theo trạng thái & loại
# idx 0–49   : hieu_luc  (còn hiệu lực)   — xd_1_nam / xd_3_nam / khong_xd
# idx 50–64  : sap_het_han (sắp hết hạn)  — end_date trong 30 ngày tới
# idx 65–74  : het_han    (đã hết hạn)    — end_date trong quá khứ
# idx 75–84  : gia_han    (đã gia hạn)    — có renewed_from
# idx 85–94  : cham_dut   (đã chấm dứt)  — có termination_date
# idx 95–99  : thu_viec / thuc_tap        — hieu_luc, thời hạn ngắn


def _make_number(n):
    """HD-2025-001 … HD-2025-100"""
    return f'HD-2025-{n:03d}'


def _salary_for(emp):
    return emp.salary or Decimal('10000000')


class Command(BaseCommand):
    help = 'Tạo 100 hợp đồng mẫu cho NV0001–NV0100'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Xóa toàn bộ hợp đồng trước khi tạo')

    def handle(self, *args, **options):
        self.stdout.write('=' * 55)
        self.stdout.write('  SEED 100 HỢP ĐỒNG MẪU')
        self.stdout.write('=' * 55)

        if options['clear']:
            n = Contract.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'\n  Đã xóa {n} hợp đồng cũ.'))

        # Lấy NV0001–NV0100, đảm bảo đúng thứ tự
        employees = list(
            Employee.objects.filter(
                employee_code__in=[f'NV{i:04d}' for i in range(1, 101)]
            ).select_related('department').order_by('employee_code')
        )

        if len(employees) < 100:
            self.stdout.write(self.style.ERROR(
                f'\nChỉ tìm thấy {len(employees)} nhân viên NV0001–NV0100. '
                'Hãy chạy seed_employees trước.'
            ))
            return

        with transaction.atomic():
            contracts, renewed_pairs = self._build_contracts(employees)
            created = Contract.objects.bulk_create(contracts)

            # Gán renewed_from sau khi có PK (bulk_create trả về objects có pk)
            if renewed_pairs:
                self._set_renewed_from(created, renewed_pairs)

        self._print_summary()

    # ─────────────────────────────────────────────────────────────────────
    def _build_contracts(self, employees):
        contracts    = []
        renewed_pairs = []  # list of (contract_idx, source_idx)

        for i, emp in enumerate(employees):
            n   = i + 1   # 1 → 100
            sal = _salary_for(emp)

            # ── 0–49: Còn hiệu lực ──────────────────────────────────────
            if i < 50:
                c_type = ['xd_1_nam', 'xd_3_nam', 'khong_xd'][i % 3]
                if c_type == 'xd_1_nam':
                    start = TODAY - timedelta(days=180)
                    end   = TODAY + timedelta(days=185)
                elif c_type == 'xd_3_nam':
                    start = TODAY - timedelta(days=365)
                    end   = TODAY + timedelta(days=730)
                else:  # khong_xd
                    start = TODAY - timedelta(days=500)
                    end   = None

                contracts.append(Contract(
                    contract_number = _make_number(n),
                    employee        = emp,
                    department      = emp.department,
                    contract_type   = c_type,
                    status          = 'hieu_luc',
                    start_date      = start,
                    end_date        = end,
                    position        = emp.position,
                    salary          = sal,
                    signed_date     = start,
                ))

            # ── 50–64: Sắp hết hạn (end_date trong 30 ngày tới) ────────
            elif i < 65:
                days_left = (i - 50) * 2 + 1   # 1, 3, 5 … 29
                start = TODAY - timedelta(days=335)
                end   = TODAY + timedelta(days=days_left)
                contracts.append(Contract(
                    contract_number = _make_number(n),
                    employee        = emp,
                    department      = emp.department,
                    contract_type   = 'xd_1_nam',
                    status          = 'sap_het_han',
                    start_date      = start,
                    end_date        = end,
                    position        = emp.position,
                    salary          = sal,
                    signed_date     = start,
                ))

            # ── 65–74: Đã hết hạn ───────────────────────────────────────
            elif i < 75:
                days_ago = (i - 64) * 15        # 15, 30, … 150 ngày trước
                start = TODAY - timedelta(days=365 + days_ago)
                end   = TODAY - timedelta(days=days_ago)
                contracts.append(Contract(
                    contract_number = _make_number(n),
                    employee        = emp,
                    department      = emp.department,
                    contract_type   = 'xd_1_nam',
                    status          = 'het_han',
                    start_date      = start,
                    end_date        = end,
                    position        = emp.position,
                    salary          = sal,
                    signed_date     = start,
                ))

            # ── 75–84: Đã gia hạn ───────────────────────────────────────
            elif i < 85:
                # HĐ gốc (đã hết hạn → status=gia_han)
                old_start = TODAY - timedelta(days=730)
                old_end   = TODAY - timedelta(days=30)
                old_contract = Contract(
                    contract_number = _make_number(n) + '-A',
                    employee        = emp,
                    department      = emp.department,
                    contract_type   = 'xd_1_nam',
                    status          = 'gia_han',
                    start_date      = old_start,
                    end_date        = old_end,
                    position        = emp.position,
                    salary          = sal,
                    signed_date     = old_start,
                )
                contracts.append(old_contract)
                old_idx = len(contracts) - 1

                # HĐ gia hạn mới (còn hiệu lực)
                new_start = old_end + timedelta(days=1)
                new_end   = new_start + timedelta(days=365)
                new_contract = Contract(
                    contract_number = _make_number(n),
                    employee        = emp,
                    department      = emp.department,
                    contract_type   = 'xd_1_nam',
                    status          = 'hieu_luc',
                    start_date      = new_start,
                    end_date        = new_end,
                    position        = emp.position,
                    salary          = sal + Decimal('1000000'),
                    signed_date     = new_start,
                )
                contracts.append(new_contract)
                new_idx = len(contracts) - 1
                renewed_pairs.append((new_idx, old_idx))

            # ── 85–94: Đã chấm dứt ──────────────────────────────────────
            elif i < 95:
                reasons = ['het_hop_dong', 'tu_nghi', 'sa_thai', 'thoa_thuan', 'khac']
                start = TODAY - timedelta(days=500)
                end   = TODAY - timedelta(days=60)
                term  = end + timedelta(days=5)
                contracts.append(Contract(
                    contract_number    = _make_number(n),
                    employee           = emp,
                    department         = emp.department,
                    contract_type      = 'xd_1_nam',
                    status             = 'cham_dut',
                    start_date         = start,
                    end_date           = end,
                    position           = emp.position,
                    salary             = sal,
                    signed_date        = start,
                    termination_date   = term,
                    termination_reason = reasons[i % len(reasons)],
                    termination_note   = 'Chấm dứt theo thỏa thuận.',
                ))

            # ── 95–99: Thử việc / Thực tập ──────────────────────────────
            else:
                c_type = 'thu_viec' if i % 2 == 0 else 'thuc_tap'
                start  = TODAY - timedelta(days=30)
                end    = TODAY + timedelta(days=60)
                contracts.append(Contract(
                    contract_number = _make_number(n),
                    employee        = emp,
                    department      = emp.department,
                    contract_type   = c_type,
                    status          = 'hieu_luc',
                    start_date      = start,
                    end_date        = end,
                    position        = emp.position,
                    salary          = sal * Decimal('0.85'),
                    signed_date     = start,
                ))

        return contracts, renewed_pairs

    def _set_renewed_from(self, created, renewed_pairs):
        """Gán renewed_from sau khi bulk_create đã có PK."""
        for new_idx, old_idx in renewed_pairs:
            new_obj = created[new_idx]
            old_obj = created[old_idx]
            new_obj.renewed_from_id = old_obj.pk
            new_obj.save(update_fields=['renewed_from'])

    def _print_summary(self):
        from django.db.models import Count
        total = Contract.objects.count()
        self.stdout.write(f'\n  ✓ Tổng cộng: {total} hợp đồng\n')
        self.stdout.write('  Phân bổ trạng thái:')
        for row in Contract.objects.values('status').annotate(n=Count('id')).order_by('-n'):
            label = dict(Contract.STATUS_CHOICES).get(row['status'], row['status'])
            self.stdout.write(f'    {label:<25} {row["n"]:>3} HĐ')

        self.stdout.write('\n  Phân bổ loại hợp đồng:')
        for row in Contract.objects.values('contract_type').annotate(n=Count('id')).order_by('-n'):
            label = dict(Contract.TYPE_CHOICES).get(row['contract_type'], row['contract_type'])
            self.stdout.write(f'    {label:<40} {row["n"]:>3} HĐ')

        self.stdout.write(self.style.SUCCESS('\nHoàn thành! Truy cập: http://127.0.0.1:8000/contracts/'))
