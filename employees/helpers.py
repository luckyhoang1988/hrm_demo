from departments.models import Department, EmployeeGroup
from employees.models import (
    UserProfile, StaffGroup,
    ActivityLog, UserGroupPermission, StaffGroupDeptPerm,
)


def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')


def log_activity(user, action, target_type, target_name='', detail='', ip=None):
    ActivityLog.objects.create(
        user=user if (user and user.is_authenticated) else None,
        action=action,
        target_type=target_type,
        target_name=target_name,
        detail=detail,
        ip=ip,
    )


def get_allowed_departments(user):
    if user.is_superuser:
        return Department.objects.all()
    profile, _ = UserProfile.objects.get_or_create(user=user)
    individual_ids = set(profile.group_perms.values_list('group_id', flat=True))
    staff_ids = set(
        StaffGroupDeptPerm.objects
        .filter(staff_group__members=user)
        .values_list('emp_group_id', flat=True)
    )
    all_ids = individual_ids | staff_ids
    return Department.objects.filter(employeegroup__in=all_ids).distinct()


def get_user_perms(user):
    """Quyền thêm/sửa/xóa theo bộ phận — cộng dồn cá nhân + StaffGroup."""
    if user.is_superuser:
        return {'can_add': True, 'editable_depts': None, 'deletable_depts': None}
    profile, _ = UserProfile.objects.get_or_create(user=user)

    gp = profile.group_perms.select_related('group')
    can_add  = gp.filter(can_add=True).exists()
    edit_ids = set(gp.filter(can_edit=True).values_list('group_id', flat=True))
    del_ids  = set(gp.filter(can_delete=True).values_list('group_id', flat=True))

    for dp in StaffGroupDeptPerm.objects.filter(staff_group__members=user).select_related('emp_group'):
        if dp.can_add:    can_add = True
        if dp.can_edit:   edit_ids.add(dp.emp_group_id)
        if dp.can_delete: del_ids.add(dp.emp_group_id)

    editable_depts  = set(Department.objects.filter(employeegroup__in=edit_ids).values_list('name', flat=True))
    deletable_depts = set(Department.objects.filter(employeegroup__in=del_ids).values_list('name', flat=True))
    return {'can_add': can_add, 'editable_depts': editable_depts, 'deletable_depts': deletable_depts}


def get_user_features(user):
    """Quyền app + chức năng — cộng dồn cá nhân + StaffGroup."""
    if user.is_superuser:
        return {
            'app_employees': True, 'app_contracts': True,
            'app_attendance': True, 'app_payroll': True,
            'app_talent': True,
            'can_export': True, 'can_import': True, 'can_view_dashboard': True,
        }
    profile, _ = UserProfile.objects.get_or_create(user=user)
    f = {
        'app_employees':      profile.app_employees,
        'app_contracts':      profile.app_contracts,
        'app_attendance':     profile.app_attendance,
        'app_payroll':        profile.app_payroll,
        'app_talent':         profile.app_talent,
        'can_export':         profile.can_export,
        'can_import':         profile.can_import,
        'can_view_dashboard': profile.can_view_dashboard,
    }
    for sg in user.staff_groups.all():
        if sg.app_employees:      f['app_employees']      = True
        if sg.app_contracts:      f['app_contracts']      = True
        if sg.app_attendance:     f['app_attendance']     = True
        if sg.app_payroll:        f['app_payroll']        = True
        if sg.app_talent:         f['app_talent']         = True
        if sg.can_export:         f['can_export']         = True
        if sg.can_import:         f['can_import']         = True
        if sg.can_view_dashboard: f['can_view_dashboard'] = True
    return f
