from rest_framework.permissions import BasePermission
from employees.helpers import get_user_features, get_user_perms


class HasEmployeesAppPermission(BasePermission):
    """Kiểm tra user có quyền truy cập module Nhân viên không."""
    message = 'Bạn không có quyền truy cập module Nhân viên.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return get_user_features(request.user).get('app_employees', False)

    def has_object_permission(self, request, view, obj):
        """Kiểm tra quyền sửa/xóa theo phòng ban của nhân viên."""
        if request.user.is_superuser:
            return True
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        perms = get_user_perms(request.user)
        dept_name = obj.department.name
        if request.method in ('PUT', 'PATCH'):
            return perms['editable_depts'] is None or dept_name in perms['editable_depts']
        if request.method == 'DELETE':
            return perms['deletable_depts'] is None or dept_name in perms['deletable_depts']
        return True


class HasAttendanceAppPermission(BasePermission):
    """Kiểm tra user có quyền truy cập module Chấm công không."""
    message = 'Bạn không có quyền truy cập module Chấm công.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return get_user_features(request.user).get('app_attendance', False)


class HasPayrollAppPermission(BasePermission):
    """Kiểm tra user có quyền truy cập module Lương không."""
    message = 'Bạn không có quyền truy cập module Lương.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return get_user_features(request.user).get('app_payroll', False)
