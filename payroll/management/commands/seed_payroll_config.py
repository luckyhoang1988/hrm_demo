"""
Seed dữ liệu InsuranceConfig và PITBracket cho các năm 2024, 2025, 2026.

Chạy:
    python manage.py seed_payroll_config
    python manage.py seed_payroll_config --year 2026    # chỉ seed năm cụ thể
    python manage.py seed_payroll_config --force        # ghi đè nếu đã tồn tại
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from payroll.models import InsuranceConfig, PITBracket


# ─────────────────────────────────────────────────────────────────────────────
# DỮ LIỆU THEO NĂM
# ─────────────────────────────────────────────────────────────────────────────

INSURANCE_DATA = {
    2024: {
        'si_employee_rate':    Decimal('8.00'),
        'hi_employee_rate':    Decimal('1.50'),
        'ui_employee_rate':    Decimal('1.00'),
        'si_employer_rate':    Decimal('17.50'),
        'hi_employer_rate':    Decimal('3.00'),
        'ui_employer_rate':    Decimal('1.00'),
        'salary_cap':          Decimal('36000000'),   # 20 × 1,800,000
        'personal_deduction':  Decimal('11000000'),
        'dependent_deduction': Decimal('4400000'),
    },
    2025: {
        'si_employee_rate':    Decimal('8.00'),
        'hi_employee_rate':    Decimal('1.50'),
        'ui_employee_rate':    Decimal('1.00'),
        'si_employer_rate':    Decimal('17.50'),
        'hi_employer_rate':    Decimal('3.00'),
        'ui_employer_rate':    Decimal('1.00'),
        'salary_cap':          Decimal('46800000'),   # 20 × 2,340,000
        'personal_deduction':  Decimal('11000000'),
        'dependent_deduction': Decimal('4400000'),
    },
    2026: {
        'si_employee_rate':    Decimal('8.00'),
        'hi_employee_rate':    Decimal('1.50'),
        'ui_employee_rate':    Decimal('1.00'),
        'si_employer_rate':    Decimal('17.50'),
        'hi_employer_rate':    Decimal('3.00'),
        'ui_employer_rate':    Decimal('1.00'),
        'salary_cap':          Decimal('46800000'),   # cập nhật khi có thông tư mới
        # Resolution 110/2025 — hiệu lực từ 2026
        'personal_deduction':  Decimal('15500000'),
        'dependent_deduction': Decimal('6200000'),
    },
}

# Bậc thuế TNCN: (min_income, max_income_or_None, rate)
# 2024-2025: theo Nghị quyết cũ
PIT_BRACKETS_OLD = [
    (Decimal('0'),          Decimal('5000000'),   Decimal('0.05')),
    (Decimal('5000000'),    Decimal('10000000'),  Decimal('0.10')),
    (Decimal('10000000'),   Decimal('18000000'),  Decimal('0.15')),
    (Decimal('18000000'),   Decimal('32000000'),  Decimal('0.20')),
    (Decimal('32000000'),   Decimal('52000000'),  Decimal('0.25')),
    (Decimal('52000000'),   Decimal('80000000'),  Decimal('0.30')),
    (Decimal('80000000'),   None,                 Decimal('0.35')),
]

# 2026+: theo Resolution 110/2025
PIT_BRACKETS_2026 = [
    (Decimal('0'),          Decimal('5000000'),   Decimal('0.05')),
    (Decimal('5000000'),    Decimal('10000000'),  Decimal('0.10')),
    (Decimal('10000000'),   Decimal('18000000'),  Decimal('0.15')),
    (Decimal('18000000'),   Decimal('32000000'),  Decimal('0.20')),
    (Decimal('32000000'),   Decimal('52000000'),  Decimal('0.25')),
    (Decimal('52000000'),   Decimal('80000000'),  Decimal('0.30')),
    (Decimal('80000000'),   None,                 Decimal('0.35')),
]

PIT_DATA = {
    2024: PIT_BRACKETS_OLD,
    2025: PIT_BRACKETS_OLD,
    2026: PIT_BRACKETS_2026,
}


class Command(BaseCommand):
    help = 'Seed InsuranceConfig + PITBracket cho các năm 2024, 2025, 2026'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, help='Chỉ seed năm cụ thể')
        parser.add_argument('--force', action='store_true', help='Ghi đè dữ liệu đã tồn tại')

    def handle(self, *args, **options):
        target_year = options.get('year')
        force       = options.get('force', False)

        years = [target_year] if target_year else [2024, 2025, 2026]

        for year in years:
            if year not in INSURANCE_DATA:
                self.stdout.write(self.style.WARNING(f'Không có dữ liệu cho năm {year}, bỏ qua.'))
                continue

            # InsuranceConfig
            cfg, created = InsuranceConfig.objects.get_or_create(year=year)
            if created or force:
                for field, value in INSURANCE_DATA[year].items():
                    setattr(cfg, field, value)
                cfg.save()
                verb = 'Tạo mới' if created else 'Cập nhật'
                self.stdout.write(self.style.SUCCESS(f'  [{verb}] InsuranceConfig năm {year}'))
            else:
                self.stdout.write(f'  [Bỏ qua] InsuranceConfig năm {year} đã tồn tại (dùng --force để ghi đè)')

            # PITBracket
            existing_count = PITBracket.objects.filter(year=year).count()
            if existing_count == 0 or force:
                PITBracket.objects.filter(year=year).delete()
                brackets = []
                for order, (min_inc, max_inc, rate) in enumerate(PIT_DATA[year], start=1):
                    brackets.append(PITBracket(
                        year=year,
                        order=order,
                        min_income=min_inc,
                        max_income=max_inc,
                        rate=rate,
                    ))
                PITBracket.objects.bulk_create(brackets)
                verb = 'Tạo mới' if existing_count == 0 else 'Ghi đè'
                self.stdout.write(self.style.SUCCESS(
                    f'  [{verb}] {len(brackets)} PITBracket cho năm {year}'
                ))
            else:
                self.stdout.write(f'  [Bỏ qua] PITBracket năm {year} đã tồn tại (dùng --force để ghi đè)')

        self.stdout.write(self.style.SUCCESS('\nHoàn thành seed dữ liệu cấu hình payroll!'))
        self.stdout.write('Chạy lại với --force để cập nhật nếu đã có dữ liệu cũ.')
