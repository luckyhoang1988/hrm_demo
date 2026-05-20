"""
Management command: seed_talent
Tạo dữ liệu mẫu cho app Tuyển dụng & Đào tạo.

Cách dùng:
    python manage.py seed_talent
    python manage.py seed_talent --clear    # Xóa dữ liệu cũ rồi tạo lại
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from departments.models import Department
from talent.models import JobPosition, Applicant, Interview, JobOffer


JOBS = [
    {
        'title': 'Kế toán viên',
        'dept': 'Kế toán',
        'headcount': 2,
        'type': 'full_time',
        'salary_min': 10_000_000,
        'salary_max': 15_000_000,
        'status': 'open',
        'description': 'Thực hiện công việc kế toán tổng hợp, lập báo cáo tài chính.',
        'requirements': 'Tốt nghiệp ĐH Kế toán/Tài chính, ít nhất 1 năm kinh nghiệm.',
        'open_date': date.today() - timedelta(days=20),
    },
    {
        'title': 'Lập trình viên Backend Python',
        'dept': 'Công nghệ thông tin',
        'headcount': 3,
        'type': 'full_time',
        'salary_min': 15_000_000,
        'salary_max': 25_000_000,
        'status': 'open',
        'description': 'Phát triển API và hệ thống backend bằng Python/Django.',
        'requirements': 'Thành thạo Python, Django/FastAPI, PostgreSQL. Ưu tiên có kinh nghiệm Docker.',
        'open_date': date.today() - timedelta(days=15),
    },
    {
        'title': 'Nhân viên Kinh doanh',
        'dept': 'Kinh doanh',
        'headcount': 5,
        'type': 'full_time',
        'salary_min': 8_000_000,
        'salary_max': 20_000_000,
        'status': 'interviewing',
        'description': 'Tìm kiếm và phát triển khách hàng mới, duy trì quan hệ khách hàng.',
        'requirements': 'Kỹ năng giao tiếp tốt, chịu được áp lực, ưu tiên có kinh nghiệm B2B.',
        'open_date': date.today() - timedelta(days=30),
    },
    {
        'title': 'Nhân viên Hành chính Nhân sự',
        'dept': 'Hành chính',
        'headcount': 1,
        'type': 'full_time',
        'salary_min': 9_000_000,
        'salary_max': 13_000_000,
        'status': 'open',
        'description': 'Hỗ trợ công tác tuyển dụng, đào tạo và hành chính văn phòng.',
        'requirements': 'Tốt nghiệp ĐH ngành QTNL/Hành chính. Thành thạo tin học văn phòng.',
        'open_date': date.today() - timedelta(days=10),
    },
]

APPLICANTS = [
    # ── Kế toán viên (idx 0) ──────────────────────────────────────────
    {
        'job': 0, 'full_name': 'Nguyễn Thị Lan Anh',
        'email': 'lananh.kt@gmail.com', 'phone': '0901234567',
        'source': 'topcv', 'stage': 'hired',
        'notes': 'Ứng viên xuất sắc, nhận việc từ 01/06/2026',
        'cover_letter': 'Tôi có 3 năm kinh nghiệm kế toán tổng hợp, thành thạo MISA.',
    },
    {
        'job': 0, 'full_name': 'Trần Minh Khoa',
        'email': 'minhkhoa.finance@yahoo.com', 'phone': '0912345678',
        'source': 'vietnamworks', 'stage': 'interview',
        'notes': 'Hẹn phỏng vấn vòng 2 tuần tới',
        'cover_letter': 'Tốt nghiệp loại giỏi khoa Kế toán, có kinh nghiệm audit 2 năm.',
    },
    {
        'job': 0, 'full_name': 'Lê Thị Thu Hương',
        'email': 'thuhuong88@gmail.com', 'phone': '0923456789',
        'source': 'facebook', 'stage': 'screening',
        'notes': 'CV khá, cần xem xét thêm kinh nghiệm thực tế',
    },
    {
        'job': 0, 'full_name': 'Phạm Văn Đức',
        'email': 'phamvanduc.kt@gmail.com', 'phone': '0934567890',
        'source': 'direct', 'stage': 'rejected',
        'reject_reason': 'Thiếu kinh nghiệm thực tế, chỉ mới ra trường.',
    },

    # ── Lập trình viên Backend (idx 1) ───────────────────────────────
    {
        'job': 1, 'full_name': 'Hoàng Tuấn Anh',
        'email': 'tuananh.dev@gmail.com', 'phone': '0945678901',
        'source': 'linkedin', 'stage': 'offer',
        'notes': 'Đã gửi offer, đang chờ phản hồi',
        'cover_letter': 'Senior Python Developer 5 năm, thành thạo Django/FastAPI/Docker.',
    },
    {
        'job': 1, 'full_name': 'Võ Thị Mỹ Linh',
        'email': 'mylinh.python@gmail.com', 'phone': '0956789012',
        'source': 'topcv', 'stage': 'interview',
        'notes': 'Phỏng vấn kỹ thuật sắp diễn ra',
        'cover_letter': '3 năm kinh nghiệm Django, đã build 2 dự án production.',
    },
    {
        'job': 1, 'full_name': 'Nguyễn Hữu Phúc',
        'email': 'huuphuc.be@outlook.com', 'phone': '0967890123',
        'source': 'referral', 'stage': 'screening',
        'notes': 'Được giới thiệu bởi anh Tuấn – team Backend cũ',
    },
    {
        'job': 1, 'full_name': 'Đặng Quốc Bảo',
        'email': 'quocbao.tech@gmail.com', 'phone': '0978901234',
        'source': 'website', 'stage': 'new',
        'cover_letter': 'Junior Python developer, tìm cơ hội phát triển bản thân.',
    },
    {
        'job': 1, 'full_name': 'Lý Văn Thành',
        'email': 'vanthanh.code@gmail.com', 'phone': '0989012345',
        'source': 'topcv', 'stage': 'hired',
        'notes': 'Nhận việc 15/05/2026',
    },
    {
        'job': 1, 'full_name': 'Bùi Thị Ngọc Hân',
        'email': 'ngochan.fullstack@gmail.com', 'phone': '0990123456',
        'source': 'linkedin', 'stage': 'rejected',
        'reject_reason': 'Yêu cầu lương vượt ngân sách 40%, không thương lượng được.',
    },

    # ── Nhân viên Kinh doanh (idx 2) ─────────────────────────────────
    {
        'job': 2, 'full_name': 'Phan Thị Hồng Nhung',
        'email': 'hongnhung.sales@gmail.com', 'phone': '0901111222',
        'source': 'topcv', 'stage': 'offer',
        'notes': 'Offer gửi ngày 15/05, deadline phản hồi 22/05',
        'cover_letter': 'Kinh nghiệm 4 năm kinh doanh B2B, đạt 120% target liên tục 2 năm.',
    },
    {
        'job': 2, 'full_name': 'Trịnh Văn Hùng',
        'email': 'vanhung.biz@gmail.com', 'phone': '0912222333',
        'source': 'vietnamworks', 'stage': 'hired',
        'notes': 'Đã ký hợp đồng, bắt đầu 01/05/2026',
    },
    {
        'job': 2, 'full_name': 'Ngô Thị Thanh Tâm',
        'email': 'thanhtam.kd@gmail.com', 'phone': '0923333444',
        'source': 'facebook', 'stage': 'interview',
        'cover_letter': '2 năm sales B2C, muốn chuyển sang B2B.',
    },
    {
        'job': 2, 'full_name': 'Đinh Quang Minh',
        'email': 'quangminh.sales@yahoo.com', 'phone': '0934444555',
        'source': 'direct', 'stage': 'interview',
        'notes': 'Phỏng vấn vòng 1 qua, đặt lịch vòng 2',
    },
    {
        'job': 2, 'full_name': 'Cao Thị Bảo Châu',
        'email': 'baochau.vn@gmail.com', 'phone': '0945555666',
        'source': 'referral', 'stage': 'screening',
    },
    {
        'job': 2, 'full_name': 'Lưu Minh Tiến',
        'email': 'minhtien.biz@gmail.com', 'phone': '0956666777',
        'source': 'other', 'stage': 'new',
    },
    {
        'job': 2, 'full_name': 'Hà Thị Kim Oanh',
        'email': 'kimoanh.sales@gmail.com', 'phone': '0967777888',
        'source': 'topcv', 'stage': 'rejected',
        'reject_reason': 'Không phù hợp văn hóa công ty sau vòng phỏng vấn cuối.',
    },

    # ── Nhân viên Hành chính Nhân sự (idx 3) ─────────────────────────
    {
        'job': 3, 'full_name': 'Dương Thị Lan',
        'email': 'duonglan.hr@gmail.com', 'phone': '0978888999',
        'source': 'topcv', 'stage': 'offer',
        'notes': 'Ứng viên tiềm năng nhất, offer đang chờ ký',
        'cover_letter': 'Tốt nghiệp QTNL, 2 năm kinh nghiệm tại công ty 500 nhân sự.',
    },
    {
        'job': 3, 'full_name': 'Vũ Thanh Tùng',
        'email': 'thanhtung.admin@gmail.com', 'phone': '0989999000',
        'source': 'vietnamworks', 'stage': 'screening',
        'cover_letter': 'Có kinh nghiệm hành chính, muốn phát triển sang mảng nhân sự.',
    },
    {
        'job': 3, 'full_name': 'Trần Thị Phương Thảo',
        'email': 'phuongthao.hc@gmail.com', 'phone': '0900000111',
        'source': 'website', 'stage': 'new',
        'cover_letter': 'Sinh viên mới ra trường ngành Hành chính văn phòng.',
    },
]

# Dữ liệu phỏng vấn mẫu (chỉ tạo cho applicant đang ở stage interview/offer/hired)
INTERVIEWS = [
    # (applicant_email, round, type, days_offset, status, score, notes)
    ('minhkhoa.finance@yahoo.com', 1, 'in_person', -5, 'completed', 4, 'Kiến thức tốt, cần kiểm tra thêm kỹ năng thực hành'),
    ('tuananh.dev@gmail.com', 1, 'online', -10, 'completed', 5, 'Xuất sắc, xử lý bài test nhanh và chính xác'),
    ('tuananh.dev@gmail.com', 2, 'technical', -5, 'completed', 5, 'Kiến trúc hệ thống rất tốt'),
    ('mylinh.python@gmail.com', 1, 'phone', -7, 'completed', 3, 'Ổn, cần PV kỹ thuật thêm'),
    ('mylinh.python@gmail.com', 2, 'technical', 3, 'scheduled', None, 'Đặt lịch PV kỹ thuật'),
    ('hongnhung.sales@gmail.com', 1, 'in_person', -8, 'completed', 4, 'Kỹ năng bán hàng tốt'),
    ('hongnhung.sales@gmail.com', 2, 'in_person', -3, 'completed', 5, 'Rất phù hợp vị trí'),
    ('thanhtam.kd@gmail.com', 1, 'phone', -4, 'completed', 3, 'Cần gặp trực tiếp đánh giá thêm'),
    ('quangminh.sales@yahoo.com', 1, 'in_person', -6, 'completed', 4, 'Tốt, đặt lịch vòng 2'),
    ('quangminh.sales@yahoo.com', 2, 'in_person', 2, 'scheduled', None, 'Phỏng vấn Ban Giám đốc'),
    ('duonglan.hr@gmail.com', 1, 'in_person', -5, 'completed', 5, 'Ứng viên xuất sắc, phù hợp 100%'),
]

# Dữ liệu offer mẫu
OFFERS = [
    # (applicant_email, salary, start_date_offset, probation, status)
    ('tuananh.dev@gmail.com', 22_000_000, 20, 2, 'sent'),
    ('hongnhung.sales@gmail.com', 12_000_000, 15, 2, 'sent'),
    ('duonglan.hr@gmail.com', 11_000_000, 10, 2, 'accepted'),
]


class Command(BaseCommand):
    help = 'Tạo dữ liệu mẫu: vị trí tuyển dụng + 20 ứng viên'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Xóa toàn bộ dữ liệu tuyển dụng cũ trước khi tạo mới',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Đang xóa dữ liệu cũ...')
            JobOffer.objects.all().delete()
            Interview.objects.all().delete()
            Applicant.objects.all().delete()
            JobPosition.objects.all().delete()
            self.stdout.write(self.style.WARNING('  Đã xóa toàn bộ dữ liệu tuyển dụng.'))

        admin_user = User.objects.filter(is_superuser=True).first()

        # ── Bước 1: Tạo vị trí tuyển dụng ──────────────────────────────
        self.stdout.write('\n[1/3] Tạo vị trí tuyển dụng...')
        job_objects = []
        for jd in JOBS:
            dept, _ = Department.objects.get_or_create(name=jd['dept'])
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
                    'created_by': admin_user,
                },
            )
            job_objects.append(job)
            status_icon = '✓ Tạo mới' if created else '→ Đã tồn tại'
            self.stdout.write(f'  {status_icon}: [{dept.name}] {job.title}')

        # ── Bước 2: Tạo ứng viên ────────────────────────────────────────
        self.stdout.write('\n[2/3] Tạo ứng viên...')
        applicant_map = {}  # email → Applicant object
        created_count = 0
        skipped_count = 0
        for ad in APPLICANTS:
            job = job_objects[ad['job']]
            applicant, created = Applicant.objects.get_or_create(
                job_position=job,
                email=ad['email'],
                defaults={
                    'full_name': ad['full_name'],
                    'phone': ad.get('phone', ''),
                    'source': ad.get('source', 'other'),
                    'stage': ad.get('stage', 'new'),
                    'notes': ad.get('notes', ''),
                    'cover_letter': ad.get('cover_letter', ''),
                    'reject_reason': ad.get('reject_reason', ''),
                    'created_by': admin_user,
                },
            )
            applicant_map[ad['email']] = applicant
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ {applicant.full_name} → [{job.title}] stage={applicant.stage}')
            else:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(f'  → Bỏ qua (đã có): {applicant.full_name}'))

        # ── Bước 3a: Tạo phỏng vấn ──────────────────────────────────────
        self.stdout.write('\n[3/3] Tạo phỏng vấn & offer mẫu...')
        iv_created = 0
        for (email, rnd, itype, day_offset, status, score, notes) in INTERVIEWS:
            applicant = applicant_map.get(email)
            if not applicant:
                continue
            iv, created = Interview.objects.get_or_create(
                applicant=applicant,
                round_number=rnd,
                defaults={
                    'interview_type': itype,
                    'scheduled_date': date.today() + timedelta(days=day_offset),
                    'duration_minutes': 60,
                    'status': status,
                    'score': score,
                    'notes': notes,
                    'created_by': admin_user,
                },
            )
            if created:
                iv_created += 1

        # ── Bước 3b: Tạo offer ───────────────────────────────────────────
        offer_created = 0
        for (email, salary, start_offset, probation, status) in OFFERS:
            applicant = applicant_map.get(email)
            if not applicant:
                continue
            offer, created = JobOffer.objects.get_or_create(
                applicant=applicant,
                defaults={
                    'offered_salary': salary,
                    'start_date': date.today() + timedelta(days=start_offset),
                    'probation_months': probation,
                    'status': status,
                    'deadline_response': date.today() + timedelta(days=7),
                    'created_by': admin_user,
                },
            )
            if created:
                offer_created += 1

        # ── Tổng kết ─────────────────────────────────────────────────────
        self.stdout.write('\n' + '─' * 50)
        self.stdout.write(self.style.SUCCESS(
            f'Hoàn thành! Đã tạo:\n'
            f'  • {len(job_objects)} vị trí tuyển dụng\n'
            f'  • {created_count} ứng viên mới (bỏ qua {skipped_count} đã có)\n'
            f'  • {iv_created} lịch phỏng vấn\n'
            f'  • {offer_created} offer'
        ))
        self.stdout.write('\nTruy cập: http://127.0.0.1:8000/talent/')
