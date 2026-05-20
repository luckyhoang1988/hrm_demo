from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver


def _get_ip(request):
    if not request:
        return None
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')


@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    from .models import ActivityLog
    ActivityLog.objects.create(
        user=user,
        action='login',
        target_type='system',
        target_name=user.username,
        ip=_get_ip(request),
    )


@receiver(user_logged_out)
def on_user_logout(sender, request, user, **kwargs):
    from .models import ActivityLog
    if user:
        ActivityLog.objects.create(
            user=user,
            action='logout',
            target_type='system',
            target_name=user.username,
            ip=_get_ip(request),
        )
