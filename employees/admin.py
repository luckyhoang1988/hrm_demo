from django.contrib import admin
from .models import Employee, Department, EmployeeGroup, UserProfile

admin.site.register(Employee)
admin.site.register(Department)
admin.site.register(EmployeeGroup)
admin.site.register(UserProfile)
