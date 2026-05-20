from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    # Đánh dấu tất cả là đã đọc khi mở trang
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'core/notification_list.html', {'notifications': notifications})


@login_required
@require_POST
def mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'ok': True, 'count': 0})
