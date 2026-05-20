from django.db import models


class AppStatus(models.Model):
    app_contracts_active = models.BooleanField(default=False)
    app_attendance_active = models.BooleanField(default=False)
    app_payroll_active = models.BooleanField(default=False)
    app_talent_active = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Trạng thái ứng dụng'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
