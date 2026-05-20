from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    HealthCheckView,
    EmployeeViewSet, DepartmentViewSet,
    AttendanceRecordViewSet, LeaveRequestViewSet, LeaveTypeViewSet,
    PayslipViewSet, OTRecordViewSet,
)

router = DefaultRouter()

# Employees
router.register('employees', EmployeeViewSet, basename='employee')
router.register('departments', DepartmentViewSet, basename='department')

# Attendance
router.register('attendance/records', AttendanceRecordViewSet, basename='attendance-record')
router.register('attendance/leave-requests', LeaveRequestViewSet, basename='leave-request')
router.register('attendance/leave-types', LeaveTypeViewSet, basename='leave-type')

# Payroll
router.register('payroll/payslips', PayslipViewSet, basename='payslip')
router.register('payroll/ot-records', OTRecordViewSet, basename='ot-record')

urlpatterns = [
    # Lấy token: POST /api/token/ với body {"username": "...", "password": "..."}
    path('token/', obtain_auth_token, name='api-token'),
    path('health/', HealthCheckView.as_view(), name='api-health'),
    path('', include(router.urls)),
]
