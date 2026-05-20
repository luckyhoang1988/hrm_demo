from django.db import models
from django.contrib.auth.models import User


class BaseModel(models.Model):
    """Model cha abstract — tất cả model quan trọng kế thừa để có audit fields."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', editable=False,
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', editable=False,
    )

    class Meta:
        abstract = True


class Notification(models.Model):
    TYPE_INFO    = 'info'
    TYPE_WARNING = 'warning'
    TYPE_DANGER  = 'danger'
    TYPE_SUCCESS = 'success'

    TYPE_CHOICES = [
        ('info',    'Thông tin'),
        ('warning', 'Cảnh báo'),
        ('danger',  'Nguy hiểm'),
        ('success', 'Thành công'),
    ]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title      = models.CharField('Tiêu đề', max_length=200)
    message    = models.TextField('Nội dung')
    type       = models.CharField('Loại', max_length=20, choices=TYPE_CHOICES, default=TYPE_INFO)
    link       = models.CharField('Đường dẫn', max_length=500, blank=True)
    is_read    = models.BooleanField('Đã đọc', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Thông báo'

    def __str__(self):
        return f"[{self.type.upper()}] {self.title} → {self.user.username}"
