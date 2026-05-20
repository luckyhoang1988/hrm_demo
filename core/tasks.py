from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User


def _get_hr_users():
    """Lấy danh sách user có quyền xem nhân viên (HR + superuser)."""
    from employees.models import UserProfile, StaffGroup
    superusers = list(User.objects.filter(is_superuser=True))
    profile_ids = UserProfile.objects.filter(app_employees=True).values_list('user_id', flat=True)
    group_ids = StaffGroup.objects.filter(app_employees=True).values_list('members__id', flat=True)
    allowed_ids = set(profile_ids) | set(group_ids)
    extra = list(User.objects.filter(id__in=allowed_ids).exclude(is_superuser=True))
    return superusers + extra


def _get_contract_users():
    """Lấy danh sách user có quyền xem hợp đồng."""
    from employees.models import UserProfile, StaffGroup
    superusers = list(User.objects.filter(is_superuser=True))
    profile_ids = UserProfile.objects.filter(app_contracts=True).values_list('user_id', flat=True)
    group_ids = StaffGroup.objects.filter(app_contracts=True).values_list('members__id', flat=True)
    allowed_ids = set(profile_ids) | set(group_ids)
    extra = list(User.objects.filter(id__in=allowed_ids).exclude(is_superuser=True))
    return superusers + extra


@shared_task(name='core.tasks.check_contract_expiry')
def check_contract_expiry():
    """Kiểm tra hợp đồng sắp hết hạn và tạo thông báo cho HR."""
    from datetime import date, timedelta
    from contracts.models import Contract
    from core.notifications import create_notification_bulk
    from core.models import Notification

    today = date.today()
    recipients = _get_contract_users()
    if not recipients:
        return 'Không có user HR nào để thông báo.'

    count = 0
    for days_left, label in [(7, '7 ngày'), (15, '15 ngày'), (30, '30 ngày')]:
        target_date = today + timedelta(days=days_left)
        contracts = Contract.objects.filter(
            end_date=target_date,
            status__in=['hieu_luc', 'sap_het_han'],
        ).select_related('employee')

        for contract in contracts:
            title = f'Hợp đồng sắp hết hạn ({label})'
            message = (
                f'Hợp đồng {contract.contract_number} của {contract.employee.full_name} '
                f'sẽ hết hạn vào {contract.end_date.strftime("%d/%m/%Y")} '
                f'(còn {days_left} ngày). Cần gia hạn hoặc chấm dứt.'
            )
            notif_type = Notification.TYPE_DANGER if days_left <= 7 else (
                Notification.TYPE_WARNING if days_left <= 15 else Notification.TYPE_INFO
            )
            link = f'/contracts/{contract.pk}/'
            create_notification_bulk(recipients, title, message, type=notif_type, link=link)
            count += 1

    return f'Đã kiểm tra, tạo thông báo cho {count} hợp đồng sắp hết hạn.'


@shared_task(name='core.tasks.check_employee_status_expiry')
def check_employee_status_expiry():
    """Kiểm tra nhân viên có trạng thái sắp hết hạn (<= 7 ngày) và tạo thông báo."""
    from datetime import date, timedelta
    from employees.models import Employee
    from core.notifications import create_notification_bulk
    from core.models import Notification

    today = date.today()
    threshold = today + timedelta(days=7)
    recipients = _get_hr_users()
    if not recipients:
        return 'Không có user HR nào để thông báo.'

    STATUS_LABELS = dict(Employee.STATUS_CHOICES)
    expiring = Employee.objects.filter(
        status_end_date__lte=threshold,
        status_end_date__gte=today,
    ).exclude(status='nghi_viec')

    count = 0
    for emp in expiring:
        days_left = (emp.status_end_date - today).days
        title = f'Trạng thái NV sắp hết hạn ({days_left} ngày)'
        message = (
            f'{emp.full_name} đang ở trạng thái "{STATUS_LABELS.get(emp.status, emp.status)}", '
            f'kết thúc vào {emp.status_end_date.strftime("%d/%m/%Y")}. Cần cập nhật trạng thái.'
        )
        notif_type = Notification.TYPE_DANGER if days_left <= 2 else Notification.TYPE_WARNING
        link = f'/employees/{emp.pk}/'
        create_notification_bulk(recipients, title, message, type=notif_type, link=link)
        count += 1

    return f'Đã kiểm tra {count} nhân viên có trạng thái sắp hết hạn.'


@shared_task(name='core.tasks.auto_terminate_employees_task')
def auto_terminate_employees_task():
    """Tự động chuyển nhân viên sang nghỉ việc khi đến scheduled_termination_date."""
    from datetime import date
    from employees.models import Employee, StatusLog
    from core.notifications import create_notification_bulk
    from core.models import Notification

    today = date.today()
    to_terminate = Employee.objects.filter(
        scheduled_termination_date__lte=today,
    ).exclude(status='nghi_viec')

    count = 0
    hr_users = _get_hr_users()

    for emp in to_terminate:
        old_status = emp.status
        StatusLog.objects.create(
            employee=emp,
            old_status=old_status,
            new_status='nghi_viec',
            note='Tự động nghỉ việc theo lịch đã đặt (Celery task)',
        )
        emp.status = 'nghi_viec'
        emp.termination_date = emp.scheduled_termination_date
        emp.scheduled_termination_date = None
        emp.save()

        if hr_users:
            create_notification_bulk(
                hr_users,
                title=f'Nhân viên tự động nghỉ việc: {emp.full_name}',
                message=(
                    f'{emp.full_name} ({emp.employee_code}) đã được hệ thống chuyển sang '
                    f'"Nghỉ việc" theo lịch đặt sẵn ngày {today.strftime("%d/%m/%Y")}.'
                ),
                type=Notification.TYPE_INFO,
                link=f'/employees/{emp.pk}/',
            )
        count += 1

    return f'Đã tự động chuyển {count} nhân viên sang nghỉ việc.'
