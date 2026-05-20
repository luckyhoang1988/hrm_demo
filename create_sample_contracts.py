"""
Script tao hop dong mau - 50 HĐ đa dạng.
Chay: python -X utf8 create_sample_contracts.py
"""
import os, random
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from contracts.models import Contract
from employees.models import Employee

TODAY = date.today()
random.seed(99)

# 50 kich ban: (type, status, start_offset, duration_days, notice_days)
# start_offset: so ngay so voi TODAY (am = qua khu, duong = tuong lai)
# duration=0 => khong_xd (end_date=None)
SCENARIOS = [
    # --- HĐLĐ 1 NĂM ---
    ('xd_1_nam', 'hieu_luc',    -30,   365, 30),
    ('xd_1_nam', 'hieu_luc',    -60,   365, 30),
    ('xd_1_nam', 'hieu_luc',   -120,   365, 30),
    ('xd_1_nam', 'hieu_luc',   -180,   365, 30),
    ('xd_1_nam', 'hieu_luc',   -250,   365, 30),
    ('xd_1_nam', 'sap_het_han',-350,   365, 30),
    ('xd_1_nam', 'sap_het_han',-360,   365, 30),
    ('xd_1_nam', 'het_han',    -400,   365, 30),
    ('xd_1_nam', 'het_han',    -450,   365, 30),
    ('xd_1_nam', 'gia_han',    -500,   365, 30),
    ('xd_1_nam', 'cham_dut',   -300,   365, 30),
    ('xd_1_nam', 'cham_dut',   -200,   365, 30),

    # --- HĐLĐ 3 NĂM ---
    ('xd_3_nam', 'hieu_luc',    -90,  1095, 45),
    ('xd_3_nam', 'hieu_luc',   -200,  1095, 45),
    ('xd_3_nam', 'hieu_luc',   -365,  1095, 45),
    ('xd_3_nam', 'hieu_luc',   -500,  1095, 45),
    ('xd_3_nam', 'sap_het_han',-1080, 1095, 45),
    ('xd_3_nam', 'sap_het_han',-1085, 1095, 45),
    ('xd_3_nam', 'het_han',   -1200,  1095, 45),
    ('xd_3_nam', 'het_han',   -1300,  1095, 45),
    ('xd_3_nam', 'gia_han',   -1150,  1095, 45),
    ('xd_3_nam', 'gia_han',   -1250,  1095, 45),
    ('xd_3_nam', 'cham_dut',   -600,  1095, 45),
    ('xd_3_nam', 'cham_dut',   -800,  1095, 45),

    # --- HĐLĐ KHÔNG XĐ ---
    ('khong_xd', 'hieu_luc',   -365,     0, 60),
    ('khong_xd', 'hieu_luc',   -730,     0, 60),
    ('khong_xd', 'hieu_luc',  -1095,     0, 60),
    ('khong_xd', 'hieu_luc',  -1825,     0, 60),
    ('khong_xd', 'hieu_luc',  -2555,     0, 60),
    ('khong_xd', 'cham_dut',   -500,     0, 60),
    ('khong_xd', 'cham_dut',  -1000,     0, 60),

    # --- THỬ VIỆC (6 tháng = 180 ngày) ---
    ('thu_viec', 'hieu_luc',    -10,   180, 15),
    ('thu_viec', 'hieu_luc',    -30,   180, 15),
    ('thu_viec', 'hieu_luc',    -60,   180, 15),
    ('thu_viec', 'sap_het_han', -165,  180, 15),
    ('thu_viec', 'het_han',     -200,  180, 15),
    ('thu_viec', 'het_han',     -250,  180, 15),
    ('thu_viec', 'gia_han',     -200,  180, 15),
    ('thu_viec', 'cham_dut',    -100,  180, 15),

    # --- THỰC TẬP SINH (3 tháng = 90 ngày) ---
    ('thuc_tap', 'hieu_luc',     -5,    90,  7),
    ('thuc_tap', 'hieu_luc',    -20,    90,  7),
    ('thuc_tap', 'hieu_luc',    -45,    90,  7),
    ('thuc_tap', 'sap_het_han', -75,    90,  7),
    ('thuc_tap', 'sap_het_han', -80,    90,  7),
    ('thuc_tap', 'het_han',    -100,    90,  7),
    ('thuc_tap', 'het_han',    -120,    90,  7),
    ('thuc_tap', 'het_han',    -150,    90,  7),
    ('thuc_tap', 'gia_han',    -100,    90,  7),
    ('thuc_tap', 'cham_dut',   -60,     90,  7),
]

TERM_REASONS = ['tu_nghi', 'thoa_thuan', 'sa_thai', 'het_hop_dong', 'khac']

NOTES = {
    'xd_1_nam':  'HĐ 1 nam.',
    'xd_3_nam':  'HĐ 3 nam.',
    'khong_xd':  'HĐ khong xac dinh thoi han.',
    'thu_viec':  'HĐ thu viec 6 thang.',
    'thuc_tap':  'HĐ thuc tap 3 thang.',
}

# Lay nhân vien chua co HĐ
used_ids = list(Contract.objects.values_list('employee_id', flat=True))
pool = list(Employee.objects.exclude(id__in=used_ids).select_related('department'))

if len(pool) < 50:
    print(f'Chi con {len(pool)} NV chua co HĐ, se tao {len(pool)} HĐ.')
    chosen = pool
    SCENARIOS = SCENARIOS[:len(pool)]
else:
    chosen = random.sample(pool, 50)

existing_nums = set(Contract.objects.values_list('contract_number', flat=True))

created = 0
start_num = Contract.objects.count() + 1

print(f'\n=== TAO {len(chosen)} HOP DONG MAU ===\n')

for idx, (emp, scenario) in enumerate(zip(chosen, SCENARIOS)):
    ctype, status, start_off, duration, notice = scenario

    start_date = TODAY + timedelta(days=start_off)

    if ctype == 'khong_xd' or duration == 0:
        end_date = None
    else:
        end_date = start_date + timedelta(days=duration)

    # Tao so HĐ unique
    seq = start_num + idx
    num = f'HD-{start_date.year}-{seq:04d}'
    while num in existing_nums:
        seq += 1
        num = f'HD-{start_date.year}-{seq:04d}'
    existing_nums.add(num)

    signed = start_date - timedelta(days=random.randint(2, 7))

    kwargs = dict(
        contract_number    = num,
        employee           = emp,
        department         = emp.department,
        contract_type      = ctype,
        status             = status,
        start_date         = start_date,
        end_date           = end_date,
        position           = emp.position,
        salary             = emp.salary,
        signed_date        = signed,
        notice_period_days = notice,
        note               = NOTES.get(ctype, ''),
    )

    if status == 'cham_dut':
        kwargs['termination_reason'] = random.choice(TERM_REASONS)
        kwargs['termination_date']   = TODAY - timedelta(days=random.randint(10, 60))
        kwargs['termination_note']   = 'Da hoan tat thu tuc.'

    c = Contract.objects.create(**kwargs)
    end_str = c.end_date.strftime('%d/%m/%Y') if c.end_date else 'Khong XD'
    status_label = c.get_status_display().ljust(15)
    type_label   = c.get_contract_type_display().ljust(35)
    print(f'  [{idx+1:02d}] {c.contract_number:<18} | {emp.full_name:<28} | {type_label} | {status_label} | {end_str}')
    created += 1

# Thong ke
print(f'\n=== THONG KE ===')
from django.db.models import Count
stats = Contract.objects.values('status').annotate(n=Count('id')).order_by('status')
status_map = dict(Contract.STATUS_CHOICES)
for s in stats:
    print(f'  {status_map.get(s["status"], s["status"]):<18}: {s["n"]} HĐ')
print(f'\n  Tong cong : {Contract.objects.count()} hop dong trong DB')
print(f'  Vua tao   : {created} hop dong moi')
