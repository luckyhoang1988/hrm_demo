from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import OTRecord


@receiver(pre_save, sender=OTRecord)
def capture_old_ot_status(sender, instance, **kwargs):
    """Lưu trạng thái cũ trước khi save để so sánh."""
    if instance.pk:
        try:
            instance._old_status = OTRecord.objects.get(pk=instance.pk).status
        except OTRecord.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=OTRecord)
def notify_ot_status_changed(sender, instance, created, **kwargs):
    """Gửi thông báo cho nhân viên khi bản ghi tăng ca được duyệt hoặc từ chối."""
    if created:
        return

    old_status = getattr(instance, '_old_status', None)
    if not old_status or old_status == instance.status:
        return

    if instance.status not in ('approved', 'rejected'):
        return

    employee = instance.employee
    if not employee.user_id:
        return

    from core.notifications import create_notification
    from core.models import Notification

    OT_LABELS = dict(OTRecord.OT_CHOICES)
    ot_label = OT_LABELS.get(instance.ot_type, instance.ot_type)

    if instance.status == 'approved':
        create_notification(
            user=employee.user,
            title='Tăng ca được duyệt',
            message=(
                f'Bản ghi tăng ca ngày {instance.date.strftime("%d/%m/%Y")} '
                f'({instance.hours}h, {ot_label}) của bạn đã được duyệt và sẽ được tính vào lương.'
            ),
            type=Notification.TYPE_SUCCESS,
            link=f'/payroll/ot/',
        )
    else:
        create_notification(
            user=employee.user,
            title='Tăng ca bị từ chối',
            message=(
                f'Bản ghi tăng ca ngày {instance.date.strftime("%d/%m/%Y")} '
                f'({instance.hours}h, {ot_label}) của bạn đã bị từ chối.'
                + (f' Lý do: {instance.note}' if instance.note else '')
            ),
            type=Notification.TYPE_WARNING,
            link=f'/payroll/ot/',
        )
