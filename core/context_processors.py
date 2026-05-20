from .models import Notification


def notifications(request):
    """Cung cấp số thông báo chưa đọc và 5 thông báo mới nhất cho mọi template."""
    if not request.user.is_authenticated:
        return {}
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    recent = list(Notification.objects.filter(user=request.user).order_by('-created_at')[:5])
    return {
        'notif_unread_count': unread_count,
        'notif_recent': recent,
    }
