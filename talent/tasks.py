from celery import shared_task
from datetime import date
from .models import OFFER_SENT, OFFER_EXPIRED, PLAN_NOT_STARTED, PLAN_IN_PROGRESS, PLAN_COMPLETED, PLAN_OVERDUE, RESULT_PASS


@shared_task
def notify_stage_change(applicant_id, old_stage, new_stage, changed_by_id):
    """Gửi email cho hiring manager khi stage ứng viên thay đổi."""
    from django.core.mail import send_mail
    from django.conf import settings
    from .models import Applicant

    stage_labels = dict([
        ('new', 'Mới nộp'), ('screening', 'Sàng lọc'),
        ('interview', 'Phỏng vấn'), ('offer', 'Đề nghị'),
        ('hired', 'Đã tuyển'), ('rejected', 'Loại'),
    ])
    try:
        applicant = Applicant.objects.select_related(
            'job_position', 'job_position__hiring_manager'
        ).get(pk=applicant_id)
    except Applicant.DoesNotExist:
        return

    hiring_manager = applicant.job_position.hiring_manager
    if not hiring_manager or not hiring_manager.email:
        return

    subject = f"[HRM] Ứng viên {applicant.full_name} — {stage_labels.get(new_stage, new_stage)}"
    body = (
        f"Vị trí: {applicant.job_position.title}\n"
        f"Ứng viên: {applicant.full_name}\n"
        f"Giai đoạn mới: {stage_labels.get(new_stage, new_stage)}\n"
        f"(Từ: {stage_labels.get(old_stage, old_stage)})\n"
    )
    send_mail(
        subject, body,
        getattr(settings, 'DEFAULT_FROM_EMAIL', 'hrm@company.com'),
        [hiring_manager.email],
        fail_silently=True,
    )


@shared_task
def check_offer_expiry():
    """Chạy hàng ngày: tự động chuyển offer sang 'expired' khi qua deadline."""
    from .models import JobOffer
    expired_count = JobOffer.objects.filter(
        status=OFFER_SENT,
        deadline_response__lt=date.today(),
    ).update(status=OFFER_EXPIRED)
    return f"Đã expire {expired_count} offers"


@shared_task
def check_certificate_expiry():
    """Chạy hàng ngày: set is_active=False và gửi notification cho chứng chỉ đã hết hạn."""
    from .models import TrainingCertificate
    from core.models import Notification
    from core.notifications import create_notification

    expiring = TrainingCertificate.objects.filter(
        is_active=True,
        expiry_date__lt=date.today(),
    ).select_related('employee__user', 'course')

    expired_count = 0
    for cert in expiring:
        cert.is_active = False
        cert.save(update_fields=['is_active'])
        expired_count += 1
        if cert.employee.user:
            create_notification(
                user=cert.employee.user,
                title='Chứng chỉ hết hạn',
                message=f'Chứng chỉ "{cert.course.name}" của bạn đã hết hạn ngày {cert.expiry_date}.',
                type=Notification.TYPE_WARNING,
                link='',
            )
    return f"Đã vô hiệu hóa {expired_count} chứng chỉ hết hạn"


@shared_task
def sync_training_plan_status():
    """Chạy hàng tuần: cập nhật status EmployeeTrainingPlan."""
    from django.db.models import Prefetch
    from .models import EmployeeTrainingPlan, TrainingEnrollment

    # Prefetch enrollments đã pass: 2 queries thay vì N+1
    plans = EmployeeTrainingPlan.objects.filter(
        status__in=[PLAN_NOT_STARTED, PLAN_IN_PROGRESS]
    ).select_related('employee', 'course').prefetch_related(
        Prefetch(
            'employee__enrollments',
            queryset=TrainingEnrollment.objects.filter(
                result=RESULT_PASS
            ).select_related('session__course'),
            to_attr='passed_enrollments',
        )
    )

    completed_count = 0
    overdue_count = 0
    for plan in plans:
        passed = next(
            (e for e in plan.employee.passed_enrollments
             if e.session.course_id == plan.course_id),
            None
        )
        if passed:
            plan.status = PLAN_COMPLETED
            plan.completed_enrollment = passed
            plan.save(update_fields=['status', 'completed_enrollment'])
            completed_count += 1
        elif plan.deadline and plan.deadline < date.today():
            plan.status = PLAN_OVERDUE
            plan.save(update_fields=['status'])
            overdue_count += 1

    return f"Hoàn thành: {completed_count}, Quá hạn: {overdue_count}"
