"""
Management command: seed_full_pipeline
Mô phỏng luồng tuyển dụng đầy đủ:
  50 ứng viên → 30 pass → Employee + Contract

Cách dùng:
    python manage.py seed_full_pipeline
    python manage.py seed_full_pipeline --clear
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import date
from departments.models import Department
from talent.models import JobPosition, Applicant
from employees.models import Employee
from contracts.models import Contract


EMAIL_DOMAIN = '@pipeline.hrm'

DEPARTMENTS = [
    'Công nghệ thông tin',
    'Kế toán',
    'Kinh doanh',
    'Hành chính',
    'Marketing',
    'Vận hành',
]

JOBS = [
    {
        'title': 'Lập trình viên Backend Python',
        'dept': 'Công nghệ thông tin',
        'headcount': 8, 'type': 'full_time',
        'salary_min': 13_000_000, 'salary_max': 25_000_000,
        'status': 'closed',
        'description': 'Phát triển API và hệ thống backend bằng Python/Django.',
        'requirements': 'Thành thạo Python, Django, PostgreSQL.',
        'open_date': date(2025, 11, 1),
    },
    {
        'title': 'Kế toán tổng hợp',
        'dept': 'Kế toán',
        'headcount': 5, 'type': 'full_time',
        'salary_min': 10_000_000, 'salary_max': 18_000_000,
        'status': 'closed',
        'description': 'Thực hiện công việc kế toán tổng hợp, lập báo cáo tài chính.',
        'requirements': 'Tốt nghiệp ĐH Kế toán/Tài chính.',
        'open_date': date(2025, 10, 15),
    },
    {
        'title': 'Nhân viên Kinh doanh',
        'dept': 'Kinh doanh',
        'headcount': 7, 'type': 'full_time',
        'salary_min': 9_000_000, 'salary_max': 30_000_000,
        'status': 'interviewing',
        'description': 'Tìm kiếm và phát triển khách hàng.',
        'requirements': 'Kỹ năng giao tiếp tốt, chịu được áp lực.',
        'open_date': date(2025, 10, 1),
    },
    {
        'title': 'Chuyên viên Hành chính Nhân sự',
        'dept': 'Hành chính',
        'headcount': 4, 'type': 'full_time',
        'salary_min': 9_000_000, 'salary_max': 20_000_000,
        'status': 'offer',
        'description': 'Hỗ trợ công tác tuyển dụng, đào tạo và hành chính văn phòng.',
        'requirements': 'Tốt nghiệp ĐH ngành QTNL/Hành chính.',
        'open_date': date(2025, 11, 15),
    },
    {
        'title': 'Chuyên viên Marketing Digital',
        'dept': 'Marketing',
        'headcount': 4, 'type': 'full_time',
        'salary_min': 10_000_000, 'salary_max': 20_000_000,
        'status': 'offer',
        'description': 'Lên kế hoạch và triển khai các chiến dịch marketing online.',
        'requirements': 'Am hiểu SEO/SEM, Social Media, có kinh nghiệm chạy ads.',
        'open_date': date(2025, 12, 1),
    },
    {
        'title': 'Nhân viên Vận hành & Logistics',
        'dept': 'Vận hành',
        'headcount': 2, 'type': 'full_time',
        'salary_min': 10_000_000, 'salary_max': 13_000_000,
        'status': 'offer',
        'description': 'Quản lý kho, vận chuyển và các hoạt động vận hành.',
        'requirements': 'Kinh nghiệm logistics/chuỗi cung ứng là lợi thế.',
        'open_date': date(2025, 12, 15),
    },
]

# Mỗi ứng viên: job (index), stage, thông tin cá nhân.
# Nếu stage='hired' → có key 'hired' chứa thông tin Employee + Contract.
APPLICANTS = [
    # ── IT: 12 UV, 8 hired ───────────────────────────────────────────────────
    {
        'job': 0, 'stage': 'hired',
        'full_name': 'Nguyễn Văn Hoàng', 'email': f'van.hoang.it{EMAIL_DOMAIN}',
        'phone': '0901100001', 'source': 'linkedin',
        'notes': 'Senior developer 5 năm, nhận việc 01/11/2025',
        'cover_letter': 'Thành thạo Django/FastAPI, kiến trúc microservices.',
        'hired': {
            'position': 'Senior Backend Developer', 'salary': 22_000_000,
            'hire_date': date(2025, 11, 1), 'contract_type': 'xd_3_nam',
            'end_date': date(2028, 10, 31),
        },
    },
    {
        'job': 0, 'stage': 'hired',
        'full_name': 'Trần Thị Minh Châu', 'email': f'minh.chau.it{EMAIL_DOMAIN}',
        'phone': '0901100002', 'source': 'topcv',
        'cover_letter': 'Có kinh nghiệm xây dựng REST API với Django DRF.',
        'hired': {
            'position': 'Backend Developer', 'salary': 18_000_000,
            'hire_date': date(2025, 11, 15), 'contract_type': 'xd_1_nam',
            'end_date': date(2026, 11, 14),
        },
    },
    {
        'job': 0, 'stage': 'hired',
        'full_name': 'Lê Tuấn Kiệt', 'email': f'tuan.kiet.it{EMAIL_DOMAIN}',
        'phone': '0901100003', 'source': 'vietnamworks',
        'cover_letter': '4 năm backend Python, thành thạo PostgreSQL và Redis.',
        'hired': {
            'position': 'Backend Developer', 'salary': 16_000_000,
            'hire_date': date(2025, 12, 1), 'contract_type': 'xd_1_nam',
            'end_date': date(2026, 11, 30),
        },
    },
    {
        'job': 0, 'stage': 'hired',
        'full_name': 'Phạm Thị Thu Hà', 'email': f'thu.ha.it{EMAIL_DOMAIN}',
        'phone': '0901100004', 'source': 'topcv',
        'cover_letter': 'Junior developer mới tốt nghiệp, đam mê học hỏi.',
        'hired': {
            'position': 'Junior Backend Developer', 'salary': 13_000_000,
            'hire_date': date(2026, 1, 3), 'contract_type': 'thu_viec',
            'end_date': date(2026, 3, 2),
        },
    },
    {
        'job': 0, 'stage': 'hired',
        'full_name': 'Võ Minh Đức', 'email': f'minh.duc.it{EMAIL_DOMAIN}',
        'phone': '0901100005', 'source': 'referral',
        'cover_letter': 'Developer 3 năm, thành thạo Docker và CI/CD.',
        'hired': {
            'position': 'Backend Developer', 'salary': 17_000_000,
            'hire_date': date(2026, 1, 15), 'contract_type': 'xd_1_nam',
            'end_date': date(2027, 1, 14),
        },
    },
    {
        'job': 0, 'stage': 'hired',
        'full_name': 'Bùi Thị Lan Phương', 'email': f'lan.phuong.it{EMAIL_DOMAIN}',
        'phone': '0901100006', 'source': 'linkedin',
        'cover_letter': 'Backend developer 2 năm, có kinh nghiệm AWS.',
        'hired': {
            'position': 'Backend Developer', 'salary': 15_000_000,
            'hire_date': date(2026, 2, 1), 'contract_type': 'xd_1_nam',
            'end_date': date(2027, 1, 31),
        },
    },
    {
        'job': 0, 'stage': 'hired',
        'full_name': 'Đỗ Quốc Huy', 'email': f'quoc.huy.it{EMAIL_DOMAIN}',
        'phone': '0901100007', 'source': 'direct',
        'notes': 'Tech Lead, vào không thời hạn',
        'hired': {
            'position': 'Tech Lead Backend', 'salary': 25_000_000,
            'hire_date': date(2025, 10, 1), 'contract_type': 'khong_xd',
            'end_date': None,
        },
    },
    {
        'job': 0, 'stage': 'hired',
        'full_name': 'Hoàng Thị Ngọc Ánh', 'email': f'ngoc.anh.it{EMAIL_DOMAIN}',
        'phone': '0901100008', 'source': 'topcv',
        'cover_letter': 'Developer 2 năm, tốt nghiệp loại giỏi ĐH Bách Khoa.',
        'hired': {
            'position': 'Backend Developer', 'salary': 15_000_000,
            'hire_date': date(2026, 3, 1), 'contract_type': 'xd_1_nam',
            'end_date': date(2027, 2, 28),
        },
    },
    {
        'job': 0, 'stage': 'offer',
        'full_name': 'Nguyễn Đình Lâm', 'email': f'dinh.lam.it{EMAIL_DOMAIN}',
        'phone': '0901100009', 'source': 'linkedin',
        'notes': 'Đang chờ phản hồi offer lương 19M',
    },
    {
        'job': 0, 'stage': 'interview',
        'full_name': 'Phan Thị Kim Thoa', 'email': f'kim.thoa.it{EMAIL_DOMAIN}',
        'phone': '0901100010', 'source': 'topcv',
        'notes': 'PV kỹ thuật vòng 2 vào tuần tới',
    },
    {
        'job': 0, 'stage': 'rejected',
        'full_name': 'Trịnh Công Sơn', 'email': f'cong.son.it{EMAIL_DOMAIN}',
        'phone': '0901100011', 'source': 'website',
        'reject_reason': 'Kinh nghiệm không phù hợp, chủ yếu làm frontend.',
    },
    {
        'job': 0, 'stage': 'rejected',
        'full_name': 'Lý Thị Bảo Yến', 'email': f'bao.yen.it{EMAIL_DOMAIN}',
        'phone': '0901100012', 'source': 'other',
        'reject_reason': 'Lương yêu cầu vượt ngân sách 50%.',
    },

    # ── Kế toán: 8 UV, 5 hired ───────────────────────────────────────────────
    {
        'job': 1, 'stage': 'hired',
        'full_name': 'Đinh Thị Hương Giang', 'email': f'huong.giang.kt{EMAIL_DOMAIN}',
        'phone': '0901200001', 'source': 'topcv',
        'cover_letter': 'Kế toán tổng hợp 4 năm, thành thạo MISA và SAP.',
        'hired': {
            'position': 'Kế toán tổng hợp', 'salary': 14_000_000,
            'hire_date': date(2025, 11, 15), 'contract_type': 'xd_1_nam',
            'end_date': date(2026, 11, 14),
        },
    },
    {
        'job': 1, 'stage': 'hired',
        'full_name': 'Đặng Văn Thắng', 'email': f'van.thang.kt{EMAIL_DOMAIN}',
        'phone': '0901200002', 'source': 'vietnamworks',
        'cover_letter': '3 năm kế toán thuế, thành thạo lập tờ khai thuế GTGT, TNCN.',
        'hired': {
            'position': 'Kế toán thuế', 'salary': 12_000_000,
            'hire_date': date(2025, 12, 1), 'contract_type': 'xd_1_nam',
            'end_date': date(2026, 11, 30),
        },
    },
    {
        'job': 1, 'stage': 'hired',
        'full_name': 'Cao Thị Mỹ Duyên', 'email': f'my.duyen.kt{EMAIL_DOMAIN}',
        'phone': '0901200003', 'source': 'facebook',
        'cover_letter': 'Sinh viên mới ra trường ngành Kế toán, điểm GPA 3.4.',
        'hired': {
            'position': 'Kế toán viên', 'salary': 11_000_000,
            'hire_date': date(2026, 2, 1), 'contract_type': 'thu_viec',
            'end_date': date(2026, 3, 31),
        },
    },
    {
        'job': 1, 'stage': 'hired',
        'full_name': 'Ngô Quang Vinh', 'email': f'quang.vinh.kt{EMAIL_DOMAIN}',
        'phone': '0901200004', 'source': 'referral',
        'notes': 'Trưởng nhóm KT từ công ty lớn, vào không thời hạn',
        'hired': {
            'position': 'Trưởng nhóm Kế toán', 'salary': 18_000_000,
            'hire_date': date(2025, 10, 15), 'contract_type': 'khong_xd',
            'end_date': None,
        },
    },
    {
        'job': 1, 'stage': 'hired',
        'full_name': 'Tô Thị Lan Anh', 'email': f'lan.anh.kt{EMAIL_DOMAIN}',
        'phone': '0901200005', 'source': 'topcv',
        'cover_letter': '2 năm kế toán công nợ và thanh toán.',
        'hired': {
            'position': 'Kế toán viên', 'salary': 12_000_000,
            'hire_date': date(2026, 3, 15), 'contract_type': 'xd_1_nam',
            'end_date': date(2027, 3, 14),
        },
    },
    {
        'job': 1, 'stage': 'offer',
        'full_name': 'Dương Minh Quân', 'email': f'minh.quan.kt{EMAIL_DOMAIN}',
        'phone': '0901200006', 'source': 'linkedin',
        'notes': 'Offer gửi ngày 10/05, đang chờ phản hồi',
    },
    {
        'job': 1, 'stage': 'interview',
        'full_name': 'Lưu Thị Thu Thủy', 'email': f'thu.thuy.kt{EMAIL_DOMAIN}',
        'phone': '0901200007', 'source': 'vietnamworks',
        'notes': 'PV vòng 2 với CFO',
    },
    {
        'job': 1, 'stage': 'rejected',
        'full_name': 'Hồ Văn Phước', 'email': f'van.phuoc.kt{EMAIL_DOMAIN}',
        'phone': '0901200008', 'source': 'direct',
        'reject_reason': 'Không có kinh nghiệm phần mềm kế toán phù hợp.',
    },

    # ── Kinh doanh: 10 UV, 7 hired ───────────────────────────────────────────
    {
        'job': 2, 'stage': 'hired',
        'full_name': 'Trần Thị Kiều Oanh', 'email': f'kieu.oanh.kd{EMAIL_DOMAIN}',
        'phone': '0901300001', 'source': 'topcv',
        'cover_letter': '4 năm kinh doanh B2B, đạt 120% target liên tiếp.',
        'hired': {
            'position': 'Senior Sales Executive', 'salary': 15_000_000,
            'hire_date': date(2025, 10, 1), 'contract_type': 'xd_3_nam',
            'end_date': date(2028, 9, 30),
        },
    },
    {
        'job': 2, 'stage': 'hired',
        'full_name': 'Nguyễn Thanh Bình', 'email': f'thanh.binh.kd{EMAIL_DOMAIN}',
        'phone': '0901300002', 'source': 'linkedin',
        'notes': 'Sales Manager kỳ cựu, vào không thời hạn',
        'hired': {
            'position': 'Sales Manager', 'salary': 22_000_000,
            'hire_date': date(2025, 10, 15), 'contract_type': 'khong_xd',
            'end_date': None,
        },
    },
    {
        'job': 2, 'stage': 'hired',
        'full_name': 'Lê Thị Hồng Vân', 'email': f'hong.van.kd{EMAIL_DOMAIN}',
        'phone': '0901300003', 'source': 'vietnamworks',
        'cover_letter': '2 năm kinh doanh, thành thạo CRM Salesforce.',
        'hired': {
            'position': 'Sales Executive', 'salary': 10_000_000,
            'hire_date': date(2025, 11, 1), 'contract_type': 'xd_1_nam',
            'end_date': date(2026, 10, 31),
        },
    },
    {
        'job': 2, 'stage': 'hired',
        'full_name': 'Phạm Quốc Dũng', 'email': f'quoc.dung.kd{EMAIL_DOMAIN}',
        'phone': '0901300004', 'source': 'facebook',
        'cover_letter': 'Fresh graduate chuyên ngành Marketing, nhiệt huyết.',
        'hired': {
            'position': 'Sales Executive', 'salary': 9_000_000,
            'hire_date': date(2026, 1, 6), 'contract_type': 'thu_viec',
            'end_date': date(2026, 3, 5),
        },
    },
    {
        'job': 2, 'stage': 'hired',
        'full_name': 'Vũ Thị Thu Trang', 'email': f'thu.trang.kd{EMAIL_DOMAIN}',
        'phone': '0901300005', 'source': 'referral',
        'notes': 'Sales Director level, vào không thời hạn',
        'hired': {
            'position': 'Sales Director', 'salary': 30_000_000,
            'hire_date': date(2025, 9, 1), 'contract_type': 'khong_xd',
            'end_date': None,
        },
    },
    {
        'job': 2, 'stage': 'hired',
        'full_name': 'Bùi Công Minh', 'email': f'cong.minh.kd{EMAIL_DOMAIN}',
        'phone': '0901300006', 'source': 'topcv',
        'cover_letter': '3 năm B2B sales, mảng phần mềm doanh nghiệp.',
        'hired': {
            'position': 'Sales Executive', 'salary': 11_000_000,
            'hire_date': date(2025, 12, 15), 'contract_type': 'xd_1_nam',
            'end_date': date(2026, 12, 14),
        },
    },
    {
        'job': 2, 'stage': 'hired',
        'full_name': 'Đỗ Thị Xuân Hoa', 'email': f'xuan.hoa.kd{EMAIL_DOMAIN}',
        'phone': '0901300007', 'source': 'website',
        'cover_letter': '2 năm sales, có mạng lưới khách hàng rộng.',
        'hired': {
            'position': 'Sales Executive', 'salary': 10_500_000,
            'hire_date': date(2026, 2, 15), 'contract_type': 'xd_1_nam',
            'end_date': date(2027, 2, 14),
        },
    },
    {
        'job': 2, 'stage': 'offer',
        'full_name': 'Hoàng Văn Toàn', 'email': f'van.toan.kd{EMAIL_DOMAIN}',
        'phone': '0901300008', 'source': 'direct',
        'notes': 'Offer lương 14M, đang thương lượng',
    },
    {
        'job': 2, 'stage': 'interview',
        'full_name': 'Nguyễn Thị Kim Loan', 'email': f'kim.loan.kd{EMAIL_DOMAIN}',
        'phone': '0901300009', 'source': 'topcv',
        'notes': 'PV vòng 1 xong, đặt lịch vòng 2',
    },
    {
        'job': 2, 'stage': 'rejected',
        'full_name': 'Trần Minh Tuấn', 'email': f'minh.tuan.kd{EMAIL_DOMAIN}',
        'phone': '0901300010', 'source': 'other',
        'reject_reason': 'Không phù hợp với văn hóa công ty.',
    },

    # ── Hành chính: 8 UV, 4 hired ────────────────────────────────────────────
    {
        'job': 3, 'stage': 'hired',
        'full_name': 'Lê Thị Phương Dung', 'email': f'phuong.dung.hc{EMAIL_DOMAIN}',
        'phone': '0901400001', 'source': 'topcv',
        'cover_letter': '3 năm nhân sự, thành thạo quy trình tuyển dụng và đào tạo.',
        'hired': {
            'position': 'Chuyên viên Nhân sự', 'salary': 11_000_000,
            'hire_date': date(2025, 11, 1), 'contract_type': 'xd_1_nam',
            'end_date': date(2026, 10, 31),
        },
    },
    {
        'job': 3, 'stage': 'hired',
        'full_name': 'Phạm Ngọc Hải', 'email': f'ngoc.hai.hc{EMAIL_DOMAIN}',
        'phone': '0901400002', 'source': 'vietnamworks',
        'cover_letter': '2 năm hành chính văn phòng, thành thạo Word/Excel.',
        'hired': {
            'position': 'Chuyên viên Hành chính', 'salary': 10_000_000,
            'hire_date': date(2025, 12, 1), 'contract_type': 'xd_1_nam',
            'end_date': date(2026, 11, 30),
        },
    },
    {
        'job': 3, 'stage': 'hired',
        'full_name': 'Võ Thị Thu Hằng', 'email': f'thu.hang.hc{EMAIL_DOMAIN}',
        'phone': '0901400003', 'source': 'website',
        'cover_letter': 'Mới ra trường, chuyên ngành Quản trị nhân lực.',
        'hired': {
            'position': 'Trợ lý Hành chính', 'salary': 9_000_000,
            'hire_date': date(2026, 2, 1), 'contract_type': 'thu_viec',
            'end_date': date(2026, 3, 31),
        },
    },
    {
        'job': 3, 'stage': 'hired',
        'full_name': 'Bùi Thanh Long', 'email': f'thanh.long.hc{EMAIL_DOMAIN}',
        'phone': '0901400004', 'source': 'referral',
        'notes': 'HR Manager với 8 năm kinh nghiệm',
        'hired': {
            'position': 'HR Manager', 'salary': 20_000_000,
            'hire_date': date(2025, 10, 1), 'contract_type': 'xd_3_nam',
            'end_date': date(2028, 9, 30),
        },
    },
    {
        'job': 3, 'stage': 'offer',
        'full_name': 'Đinh Thị Bích Hạnh', 'email': f'bich.hanh.hc{EMAIL_DOMAIN}',
        'phone': '0901400005', 'source': 'topcv',
        'notes': 'Offer gửi 12/05, chờ phản hồi đến 19/05',
    },
    {
        'job': 3, 'stage': 'interview',
        'full_name': 'Đặng Văn Sơn', 'email': f'van.son.hc{EMAIL_DOMAIN}',
        'phone': '0901400006', 'source': 'facebook',
        'notes': 'PV với HR Director lần 2',
    },
    {
        'job': 3, 'stage': 'screening',
        'full_name': 'Cao Thị Diệu Linh', 'email': f'dieu.linh.hc{EMAIL_DOMAIN}',
        'phone': '0901400007', 'source': 'linkedin',
        'notes': 'CV ấn tượng, đang lên lịch PV',
    },
    {
        'job': 3, 'stage': 'rejected',
        'full_name': 'Ngô Minh Khải', 'email': f'minh.khai.hc{EMAIL_DOMAIN}',
        'phone': '0901400008', 'source': 'other',
        'reject_reason': 'Không phù hợp yêu cầu kinh nghiệm tối thiểu 2 năm.',
    },

    # ── Marketing: 7 UV, 4 hired ─────────────────────────────────────────────
    {
        'job': 4, 'stage': 'hired',
        'full_name': 'Tô Thị Ánh Hồng', 'email': f'anh.hong.mkt{EMAIL_DOMAIN}',
        'phone': '0901500001', 'source': 'topcv',
        'cover_letter': '3 năm digital marketing, thành thạo Google/Meta Ads.',
        'hired': {
            'position': 'Digital Marketing Executive', 'salary': 13_000_000,
            'hire_date': date(2026, 1, 2), 'contract_type': 'xd_1_nam',
            'end_date': date(2027, 1, 1),
        },
    },
    {
        'job': 4, 'stage': 'hired',
        'full_name': 'Dương Quang Hưng', 'email': f'quang.hung.mkt{EMAIL_DOMAIN}',
        'phone': '0901500002', 'source': 'linkedin',
        'cover_letter': 'Content creator 2 năm, kênh YouTube 50K subscribers.',
        'hired': {
            'position': 'Content Marketing', 'salary': 10_000_000,
            'hire_date': date(2026, 2, 1), 'contract_type': 'xd_1_nam',
            'end_date': date(2027, 1, 31),
        },
    },
    {
        'job': 4, 'stage': 'hired',
        'full_name': 'Lưu Thị Ngọc Trinh', 'email': f'ngoc.trinh.mkt{EMAIL_DOMAIN}',
        'phone': '0901500003', 'source': 'vietnamworks',
        'cover_letter': 'SEO Specialist 3 năm, tăng organic traffic 300%.',
        'hired': {
            'position': 'SEO/SEM Specialist', 'salary': 12_000_000,
            'hire_date': date(2026, 1, 15), 'contract_type': 'xd_1_nam',
            'end_date': date(2027, 1, 14),
        },
    },
    {
        'job': 4, 'stage': 'hired',
        'full_name': 'Hồ Văn Nam', 'email': f'van.nam.mkt{EMAIL_DOMAIN}',
        'phone': '0901500004', 'source': 'referral',
        'notes': 'Marketing Manager với 6 năm kinh nghiệm',
        'hired': {
            'position': 'Marketing Manager', 'salary': 20_000_000,
            'hire_date': date(2025, 11, 1), 'contract_type': 'xd_3_nam',
            'end_date': date(2028, 10, 31),
        },
    },
    {
        'job': 4, 'stage': 'offer',
        'full_name': 'Trần Thị Mai Linh', 'email': f'mai.linh.mkt{EMAIL_DOMAIN}',
        'phone': '0901500005', 'source': 'topcv',
        'notes': 'Offer lương 11M, đang cân nhắc',
    },
    {
        'job': 4, 'stage': 'interview',
        'full_name': 'Nguyễn Hoàng Phi', 'email': f'hoang.phi.mkt{EMAIL_DOMAIN}',
        'phone': '0901500006', 'source': 'facebook',
        'notes': 'PV kỹ năng design và content',
    },
    {
        'job': 4, 'stage': 'rejected',
        'full_name': 'Lê Thị Khánh Ly', 'email': f'khanh.ly.mkt{EMAIL_DOMAIN}',
        'phone': '0901500007', 'source': 'other',
        'reject_reason': 'Portfolio không đủ mạnh so với yêu cầu.',
    },

    # ── Vận hành: 5 UV, 2 hired ──────────────────────────────────────────────
    {
        'job': 5, 'stage': 'hired',
        'full_name': 'Phạm Thị Thuỳ Dương', 'email': f'thuy.duong.vhd{EMAIL_DOMAIN}',
        'phone': '0901600001', 'source': 'topcv',
        'cover_letter': '3 năm quản lý kho và chuỗi cung ứng.',
        'hired': {
            'position': 'Chuyên viên Vận hành', 'salary': 11_000_000,
            'hire_date': date(2026, 3, 1), 'contract_type': 'xd_1_nam',
            'end_date': date(2027, 2, 28),
        },
    },
    {
        'job': 5, 'stage': 'hired',
        'full_name': 'Võ Văn Phúc', 'email': f'van.phuc.vhd{EMAIL_DOMAIN}',
        'phone': '0901600002', 'source': 'vietnamworks',
        'cover_letter': '5 năm logistics, thành thạo quản lý vận chuyển và kho bãi.',
        'hired': {
            'position': 'Logistics Coordinator', 'salary': 12_000_000,
            'hire_date': date(2026, 2, 15), 'contract_type': 'xd_1_nam',
            'end_date': date(2027, 2, 14),
        },
    },
    {
        'job': 5, 'stage': 'offer',
        'full_name': 'Bùi Thị Xuân Mai', 'email': f'xuan.mai.vhd{EMAIL_DOMAIN}',
        'phone': '0901600003', 'source': 'referral',
        'notes': 'Offer lương 11M, chờ phản hồi',
    },
    {
        'job': 5, 'stage': 'screening',
        'full_name': 'Đỗ Minh Nhật', 'email': f'minh.nhat.vhd{EMAIL_DOMAIN}',
        'phone': '0901600004', 'source': 'direct',
        'notes': 'CV đang xem xét',
    },
    {
        'job': 5, 'stage': 'rejected',
        'full_name': 'Hoàng Thị Thanh Tú', 'email': f'thanh.tu.vhd{EMAIL_DOMAIN}',
        'phone': '0901600005', 'source': 'facebook',
        'reject_reason': 'Không có kinh nghiệm logistics, chỉ làm bán lẻ.',
    },
]


class Command(BaseCommand):
    help = 'Tạo 50 ứng viên → 30 pass → Employee + Contract (full pipeline)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Xóa dữ liệu seed cũ (email @pipeline.hrm) trước khi tạo',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self._clear_data()

        admin = User.objects.filter(is_superuser=True).first()
        today = date.today()

        # ── Bước 1: Phòng ban ─────────────────────────────────────────────────
        self.stdout.write('\n[1/4] Tạo phòng ban...')
        dept_map = {}
        for name in DEPARTMENTS:
            dept, created = Department.objects.get_or_create(name=name)
            dept_map[name] = dept
            self.stdout.write(f'  {"✓" if created else "→"} {name}')

        # ── Bước 2: Vị trí tuyển dụng ────────────────────────────────────────
        self.stdout.write('\n[2/4] Tạo vị trí tuyển dụng...')
        job_objects = []
        for jd in JOBS:
            dept = dept_map[jd['dept']]
            job, created = JobPosition.objects.get_or_create(
                title=jd['title'],
                department=dept,
                defaults={
                    'headcount': jd['headcount'],
                    'employment_type': jd['type'],
                    'salary_min': jd['salary_min'],
                    'salary_max': jd['salary_max'],
                    'status': jd['status'],
                    'description': jd.get('description', ''),
                    'requirements': jd.get('requirements', ''),
                    'open_date': jd['open_date'],
                    'created_by': admin,
                },
            )
            job_objects.append(job)
            label = 'Tạo mới' if created else 'Đã có'
            self.stdout.write(f'  {"✓" if created else "→"} [{label}] {job.title}')

        # ── Bước 3: Ứng viên → Employee → Contract ───────────────────────────
        self.stdout.write('\n[3/4] Xử lý 50 ứng viên...')
        app_created = app_skipped = emp_created = contract_created = 0
        contract_num = self._next_contract_num()

        for ad in APPLICANTS:
            job = job_objects[ad['job']]

            # Idempotent: bỏ qua nếu email đã có
            if Applicant.objects.filter(email=ad['email']).exists():
                app_skipped += 1
                self.stdout.write(
                    self.style.WARNING(f'  → Bỏ qua (đã có): {ad["full_name"]}')
                )
                continue

            applicant = Applicant.objects.create(
                job_position=job,
                full_name=ad['full_name'],
                email=ad['email'],
                phone=ad.get('phone', ''),
                source=ad.get('source', 'other'),
                stage=ad['stage'],
                notes=ad.get('notes', ''),
                cover_letter=ad.get('cover_letter', ''),
                reject_reason=ad.get('reject_reason', ''),
                created_by=admin,
            )
            app_created += 1

            if ad['stage'] != 'hired' or 'hired' not in ad:
                self.stdout.write(f'  ✓ [{ad["stage"].upper():10}] {ad["full_name"]}')
                continue

            # Kiểm tra email chưa tồn tại trong Employee
            if Employee.objects.filter(email=ad['email']).exists():
                self.stdout.write(
                    self.style.WARNING(f'  ! {ad["full_name"]}: email đã có trong Employee, bỏ qua')
                )
                continue

            h = ad['hired']

            # Tạo Employee (employee_code tự sinh trong model.save())
            emp = Employee.objects.create(
                employee_code=Employee.generate_employee_code(h['hire_date']),
                full_name=ad['full_name'],
                email=ad['email'],
                phone=ad.get('phone', ''),
                department=job.department,
                position=h['position'],
                salary=h['salary'],
                hire_date=h['hire_date'],
                status='dang_lam',
            )
            emp_created += 1

            # Link applicant → employee
            applicant.converted_employee = emp
            applicant.save()

            # Tính trạng thái hợp đồng dựa theo ngày
            end_date = h['end_date']
            if end_date is None:
                ct_status = 'hieu_luc'
            elif end_date < today:
                ct_status = 'het_han'
            elif (end_date - today).days <= 30:
                ct_status = 'sap_het_han'
            else:
                ct_status = 'hieu_luc'

            contract_number = f'HD-PL-2026-{contract_num:03d}'
            Contract.objects.create(
                contract_number=contract_number,
                employee=emp,
                department=job.department,
                contract_type=h['contract_type'],
                status=ct_status,
                start_date=h['hire_date'],
                end_date=end_date,
                position=h['position'],
                salary=h['salary'],
                signed_date=h['hire_date'],
            )
            contract_num += 1
            contract_created += 1

            self.stdout.write(
                f'  ✓ [HIRED     ] {ad["full_name"]} '
                f'→ NV {emp.employee_code} '
                f'→ HĐ {contract_number} [{ct_status}]'
            )

        # ── Bước 4: Tổng kết ─────────────────────────────────────────────────
        self.stdout.write('\n' + '─' * 65)
        hired_count = sum(1 for a in APPLICANTS if a['stage'] == 'hired')
        other_count = len(APPLICANTS) - hired_count
        self.stdout.write(self.style.SUCCESS(
            f'[4/4] Hoàn thành!\n'
            f'  • {app_created} ứng viên tạo mới (bỏ qua {app_skipped} đã tồn tại)\n'
            f'    - {hired_count} ứng viên hired  |  {other_count} ứng viên các stage khác\n'
            f'  • {emp_created} nhân viên được tạo (Employee)\n'
            f'  • {contract_created} hợp đồng được tạo (Contract)\n'
        ))
        self.stdout.write('Kiểm tra tại:')
        self.stdout.write('  Tuyển dụng : http://127.0.0.1:8000/talent/applicants/')
        self.stdout.write('  Nhân viên  : http://127.0.0.1:8000/employees/')
        self.stdout.write('  Hợp đồng   : http://127.0.0.1:8000/contracts/')

    def _clear_data(self):
        self.stdout.write('Đang xóa dữ liệu pipeline seed cũ...')
        c = Contract.objects.filter(employee__email__endswith=EMAIL_DOMAIN).count()
        Contract.objects.filter(employee__email__endswith=EMAIL_DOMAIN).delete()

        e = Employee.objects.filter(email__endswith=EMAIL_DOMAIN).count()
        Employee.objects.filter(email__endswith=EMAIL_DOMAIN).delete()

        a = Applicant.objects.filter(email__endswith=EMAIL_DOMAIN).count()
        Applicant.objects.filter(email__endswith=EMAIL_DOMAIN).delete()

        self.stdout.write(self.style.WARNING(
            f'  Đã xóa: {c} hợp đồng | {e} nhân viên | {a} ứng viên'
        ))

    def _next_contract_num(self):
        """Tìm số thứ tự HĐ pipeline tiếp theo để tránh trùng contract_number."""
        import re
        nums = [
            int(m.group(1))
            for num in Contract.objects.filter(
                contract_number__startswith='HD-PL-2026-'
            ).values_list('contract_number', flat=True)
            if (m := re.search(r'HD-PL-2026-(\d+)', num))
        ]
        return max(nums, default=0) + 1
