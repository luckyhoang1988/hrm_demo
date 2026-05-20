from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import LeaveRequest


@receiver(pre_save, sender=LeaveRequest)
def capture_old_leave_status(sender, instance, **kwargs):
    """Lưu trạng thái cũ trước khi save để so sánh."""
    if instance.pk:
        try:
            instance._old_status = LeaveRequest.objects.get(pk=instance.pk).status
        except LeaveRequest.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=LeaveRequest)
def notify_leave_status_changed(sender, instance, created, **kwargs):
    """Gửi thông báo cho nhân viên khi đơn nghỉ phép được duyệt hoặc từ chối."""
    if created:
        return

    old_status = getattr(instance, '_old_status', None)
    if not old_status or old_status == instance.status:
        return

    # Chỉ notify khi chuyển sang approved hoặc rejected
    if instance.status not in ('approved', 'rejected'):
        return

    # Tìm user được liên kết với nhân viên này
    employee = instance.employee
    if not employee.user_id:
        return

    from core.notifications import create_notification
    from core.models import Notification

    period = f'{instance.start_date.strftime("%d/%m/%Y")}'
    if instance.start_date != instance.end_date:
        period += f' – {instance.end_date.strftime("%d/%m/%Y")}'

    if instance.status == 'approved':
        create_notification(
            user=employee.user,
            title='Đơn nghỉ phép được duyệt',
            message=(
                f'Đơn xin nghỉ {instance.leave_type.name} '
                f'({period}, {instance.total_days} ngày) của bạn đã được duyệt.'
            ),
            type=Notification.TYPE_SUCCESS,
            link=f'/attendance/leaves/{instance.pk}/',
        )
    else:
        create_notification(
            user=employee.user,
            title='Đơn nghỉ phép bị từ chối',
            message=(
                f'Đơn xin nghỉ {instance.leave_type.name} '
                f'({period}, {instance.total_days} ngày) của bạn đã bị từ chối.'
            ),
            type=Notification.TYPE_DANGER,
            link=f'/attendance/leaves/{instance.pk}/',
        )
