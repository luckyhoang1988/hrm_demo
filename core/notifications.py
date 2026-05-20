from .models import Notification


def create_notification(user, title, message, type=Notification.TYPE_INFO, link=''):
    """Tạo 1 thông báo trong hệ thống cho user."""
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=type,
        link=link,
    )


def create_notification_bulk(users, title, message, type=Notification.TYPE_INFO, link=''):
    """Tạo thông báo cùng lúc cho nhiều user."""
    objs = [
        Notification(user=u, title=title, message=message, type=type, link=link)
        for u in users
    ]
    Notification.objects.bulk_create(objs)
