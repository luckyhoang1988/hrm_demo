from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from django.http import JsonResponse

from departments.models import Department, EmployeeGroup
from employees.models import (
    UserProfile, UserGroupPermission,
    StaffGroup, StaffGroupDeptPerm, ActivityLog, Employee,
)
from employees.helpers import _get_client_ip, log_activity
from system_settings.models import AppStatus


@login_required
def settings_home(request):
    if not request.user.is_superuser:
        return redirect('employee_list')
    app_status = AppStatus.get()
    return render(request, 'system_settings/settings_home.html', {'app_status': app_status})


@login_required
def toggle_app(request, app_name):
    if not request.user.is_superuser:
        return redirect('employee_list')
    if request.method == 'POST':
        allowed = {'contracts', 'attendance', 'payroll', 'talent'}
        if app_name in allowed:
            status = AppStatus.get()
            field = f'app_{app_name}_active'
            new_val = not getattr(status, field)
            setattr(status, field, new_val)
            status.save()
            action = 'Kích hoạt' if new_val else 'Tắt'
            log_activity(request.user, 'edit', 'system', f'{action} app_{app_name}', ip=_get_client_ip(request))
    return redirect('system_settings:settings_home')


# ── Phòng ban ────────────────────────────────────────────────────────────────

@login_required
def department_manage(request):
    if not request.user.is_superuser:
        return redirect('employee_list')
    error = None
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            error = 'Tên bộ phận không được để trống.'
        elif Department.objects.filter(name=name).exists():
            error = f'Bộ phận "{name}" đã tồn tại.'
        else:
            Department.objects.create(name=name)
            log_activity(request.user, 'create', 'department', name, ip=_get_client_ip(request))
            return redirect('system_settings:department_manage')
    departments = Department.objects.all()
    return render(request, 'system_settings/department_manage.html', {
        'departments': departments,
        'error': error,
    })


@login_required
def department_update(request, pk):
    if not request.user.is_superuser:
        return redirect('employee_list')
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name and not Department.objects.filter(name=name).exclude(pk=pk).exists():
            old_name = dept.name
            dept.name = name
            dept.save()
            log_activity(request.user, 'edit', 'department', name,
                         detail=f'{old_name} → {name}', ip=_get_client_ip(request))
    return redirect('system_settings:department_manage')


@login_required
def department_delete(request, pk):
    if not request.user.is_superuser:
        return redirect('employee_list')
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        name = dept.name
        dept.delete()
        log_activity(request.user, 'delete', 'department', name, ip=_get_client_ip(request))
        return redirect('system_settings:department_manage')
    return render(request, 'system_settings/department_confirm_delete.html', {'dept': dept})


# ── Nhóm bộ phận (EmployeeGroup) ─────────────────────────────────────────────

@login_required
def group_list(request):
    if not request.user.is_superuser:
        return redirect('employee_list')
    groups = EmployeeGroup.objects.prefetch_related('departments').all()
    return render(request, 'system_settings/group_list.html', {'groups': groups})


@login_required
def group_create(request):
    if not request.user.is_superuser:
        return redirect('employee_list')
    all_departments = Department.objects.all()
    used_dept_ids = set(EmployeeGroup.objects.values_list('departments', flat=True))
    used_dept_ids.discard(None)
    error = None
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        dept_ids    = request.POST.getlist('departments')
        if not name:
            error = 'Tên nhóm không được để trống.'
        elif EmployeeGroup.objects.filter(name=name).exists():
            error = f'Nhóm "{name}" đã tồn tại.'
        else:
            group = EmployeeGroup.objects.create(name=name, description=description)
            group.departments.set(dept_ids)
            log_activity(request.user, 'create', 'emp_group', name, ip=_get_client_ip(request))
            return redirect('system_settings:group_list')
    return render(request, 'system_settings/group_form.html', {
        'all_departments': all_departments,
        'used_dept_ids': used_dept_ids,
        'error': error,
        'title': 'Tạo nhóm mới',
    })


@login_required
def group_update(request, pk):
    if not request.user.is_superuser:
        return redirect('employee_list')
    group = get_object_or_404(EmployeeGroup, pk=pk)
    all_departments = Department.objects.all()
    used_dept_ids = set(
        EmployeeGroup.objects.exclude(pk=pk).values_list('departments', flat=True)
    )
    used_dept_ids.discard(None)
    error = None
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        dept_ids    = request.POST.getlist('departments')
        if not name:
            error = 'Tên nhóm không được để trống.'
        elif EmployeeGroup.objects.filter(name=name).exclude(pk=pk).exists():
            error = f'Nhóm "{name}" đã tồn tại.'
        else:
            group.name        = name
            group.description = description
            group.save()
            group.departments.set(dept_ids)
            log_activity(request.user, 'edit', 'emp_group', name, ip=_get_client_ip(request))
            return redirect('system_settings:group_list')
    return render(request, 'system_settings/group_form.html', {
        'group': group,
        'all_departments': all_departments,
        'used_dept_ids': used_dept_ids,
        'error': error,
        'title': 'Chỉnh sửa nhóm',
    })


@login_required
def group_delete(request, pk):
    if not request.user.is_superuser:
        return redirect('employee_list')
    group = get_object_or_404(EmployeeGroup, pk=pk)
    if request.method == 'POST':
        name = group.name
        group.delete()
        log_activity(request.user, 'delete', 'emp_group', name, ip=_get_client_ip(request))
        return redirect('system_settings:group_list')
    return render(request, 'system_settings/group_confirm_delete.html', {'group': group})


# ── Tài khoản người dùng ─────────────────────────────────────────────────────

@login_required
def user_list(request):
    if not request.user.is_superuser:
        return redirect('employee_list')
    all_groups = EmployeeGroup.objects.prefetch_related('departments').all()
    users_raw  = User.objects.prefetch_related(
        'profile__group_perms__group',
        'staff_groups',
    ).select_related('profile').order_by('username')

    users_data = []
    for u in users_raw:
        if u.is_superuser:
            users_data.append({'user': u, 'groups_data': [], 'active_groups': []})
            continue
        profile = getattr(u, 'profile', None)
        if profile is None:
            profile = UserProfile.objects.create(user=u)
        existing    = {gp.group_id: gp for gp in profile.group_perms.all()}
        groups_data = []
        for g in all_groups:
            perm = existing.get(g.pk)
            groups_data.append({
                'group':      g,
                'has_access': perm is not None,
                'can_add':    perm.can_add    if perm else False,
                'can_edit':   perm.can_edit   if perm else False,
                'can_delete': perm.can_delete if perm else False,
            })
        active_groups = [gp.group for gp in profile.group_perms.all()]
        users_data.append({
            'user':               u,
            'groups_data':        groups_data,
            'active_groups':      active_groups,
            'app_employees':      profile.app_employees,
            'app_contracts':      profile.app_contracts,
            'app_attendance':     profile.app_attendance,
            'app_payroll':        profile.app_payroll,
            'app_talent':         profile.app_talent,
            'can_export':         profile.can_export,
            'can_import':         profile.can_import,
            'can_view_dashboard': profile.can_view_dashboard,
            'can_approve_talent': profile.can_approve_talent,
        })

    # Thêm thông tin employee liên kết cho mỗi user
    for ud in users_data:
        linked_emp = getattr(ud['user'], 'employee', None)
        ud['linked_employee'] = linked_emp

    all_employees = Employee.objects.filter(status__in=[
        'dang_lam', 'thu_viec', 'thuc_tap_sinh', 'nghi_phep',
        'nghi_sinh', 'nghi_khong_luong', 'nghi_om',
    ]).select_related('department').order_by('full_name')

    staff_groups = StaffGroup.objects.prefetch_related('members', 'dept_perms__emp_group').all()
    return render(request, 'system_settings/user_list.html', {
        'users_data':    users_data,
        'groups':        all_groups,
        'all_groups':    all_groups,
        'staff_groups':  staff_groups,
        'app_status':    AppStatus.get(),
        'all_employees': all_employees,
    })


@login_required
def user_create(request):
    if not request.user.is_superuser:
        return redirect('employee_list')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        is_super = request.POST.get('is_superuser') == 'on'
        if not username or not password:
            error = 'Tên đăng nhập và mật khẩu không được để trống.'
        elif User.objects.filter(username=username).exists():
            error = f'Tên đăng nhập "{username}" đã tồn tại.'
        else:
            if is_super:
                User.objects.create_superuser(username, email, password)
            else:
                User.objects.create_user(username, email, password)
            log_activity(request.user, 'create', 'user', username,
                         detail='Superuser' if is_super else 'User thường',
                         ip=_get_client_ip(request))
            return redirect('system_settings:user_list')
    return render(request, 'system_settings/user_form.html', {'error': error})


@login_required
def user_delete(request, pk):
    if not request.user.is_superuser:
        return redirect('employee_list')
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if user == request.user:
            return redirect('system_settings:user_list')
        username = user.username
        user.delete()
        log_activity(request.user, 'delete', 'user', username, ip=_get_client_ip(request))
        return redirect('system_settings:user_list')
    return render(request, 'system_settings/user_confirm_delete.html', {'target_user': user})


@login_required
def admin_reset_password(request, pk):
    if not request.user.is_superuser:
        return redirect('employee_list')
    target = get_object_or_404(User, pk=pk)
    error = None
    if request.method == 'POST':
        new_pass  = request.POST.get('new_password', '')
        new_pass2 = request.POST.get('new_password2', '')
        if not new_pass:
            error = 'Mật khẩu mới không được để trống.'
        elif new_pass != new_pass2:
            error = 'Mật khẩu xác nhận không khớp.'
        elif len(new_pass) < 6:
            error = 'Mật khẩu phải có ít nhất 6 ký tự.'
        else:
            target.set_password(new_pass)
            target.save()
            log_activity(request.user, 'edit', 'user', target.username,
                         detail='Reset mật khẩu', ip=_get_client_ip(request))
            messages.success(request, f'Đã reset mật khẩu cho tài khoản "{target.username}" thành công.')
            return redirect('system_settings:user_list')
    return render(request, 'system_settings/reset_password.html', {'target': target, 'error': error})


# ── Nhóm người dùng (StaffGroup) ─────────────────────────────────────────────

@login_required
def staff_group_create(request):
    if not request.user.is_superuser:
        return redirect('employee_list')
    all_users      = User.objects.filter(is_superuser=False).order_by('username')
    all_emp_groups = EmployeeGroup.objects.prefetch_related('departments').all()
    error = None
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if not name:
            error = 'Tên nhóm không được để trống.'
        elif StaffGroup.objects.filter(name=name).exists():
            error = f'Nhóm "{name}" đã tồn tại.'
        else:
            sg = StaffGroup.objects.create(
                name=name, description=description,
                app_employees      = 'app_employees'  in request.POST,
                app_contracts      = 'app_contracts'  in request.POST,
                app_attendance     = 'app_attendance' in request.POST,
                app_payroll        = 'app_payroll'    in request.POST,
                app_talent         = 'app_talent'     in request.POST,
                can_export         = 'feat_export'          in request.POST,
                can_import         = 'feat_import'          in request.POST,
                can_view_dashboard = 'feat_dashboard'       in request.POST,
                can_approve_talent = 'feat_approve_talent'  in request.POST,
            )
            sg.members.set(request.POST.getlist('members'))
            for eg in all_emp_groups:
                if f'dg_{eg.pk}' in request.POST:
                    StaffGroupDeptPerm.objects.create(
                        staff_group=sg, emp_group=eg,
                        can_add    = f'dadd_{eg.pk}'  in request.POST,
                        can_edit   = f'dedit_{eg.pk}' in request.POST,
                        can_delete = f'ddel_{eg.pk}'  in request.POST,
                    )
            log_activity(request.user, 'create', 'staff_group', name, ip=_get_client_ip(request))
            messages.success(request, f'Đã tạo nhóm "{name}" thành công.')
            return redirect('system_settings:user_list')
    emp_group_data = [
        {'group': eg, 'has_access': False, 'can_add': False, 'can_edit': False, 'can_delete': False}
        for eg in all_emp_groups
    ]
    return render(request, 'system_settings/staff_group_form.html', {
        'title': 'Tạo nhóm người dùng',
        'all_users': all_users, 'emp_group_data': emp_group_data, 'error': error,
        'app_status': AppStatus.get(),
    })


@login_required
def staff_group_update(request, pk):
    if not request.user.is_superuser:
        return redirect('employee_list')
    sg             = get_object_or_404(StaffGroup, pk=pk)
    all_users      = User.objects.filter(is_superuser=False).order_by('username')
    all_emp_groups = EmployeeGroup.objects.prefetch_related('departments').all()
    existing_depts = {dp.emp_group_id: dp for dp in sg.dept_perms.all()}
    error = None
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if not name:
            error = 'Tên nhóm không được để trống.'
        elif StaffGroup.objects.filter(name=name).exclude(pk=pk).exists():
            error = f'Nhóm "{name}" đã tồn tại.'
        else:
            sg.name               = name
            sg.description        = description
            sg.app_employees      = 'app_employees'  in request.POST
            sg.app_contracts      = 'app_contracts'  in request.POST
            sg.app_attendance     = 'app_attendance' in request.POST
            sg.app_payroll        = 'app_payroll'    in request.POST
            sg.app_talent         = 'app_talent'     in request.POST
            sg.can_export         = 'feat_export'         in request.POST
            sg.can_import         = 'feat_import'         in request.POST
            sg.can_view_dashboard = 'feat_dashboard'      in request.POST
            sg.can_approve_talent = 'feat_approve_talent' in request.POST
            sg.save()
            sg.members.set(request.POST.getlist('members'))
            sg.dept_perms.all().delete()
            for eg in all_emp_groups:
                if f'dg_{eg.pk}' in request.POST:
                    StaffGroupDeptPerm.objects.create(
                        staff_group=sg, emp_group=eg,
                        can_add    = f'dadd_{eg.pk}'  in request.POST,
                        can_edit   = f'dedit_{eg.pk}' in request.POST,
                        can_delete = f'ddel_{eg.pk}'  in request.POST,
                    )
            log_activity(request.user, 'edit', 'staff_group', name, ip=_get_client_ip(request))
            messages.success(request, f'Đã cập nhật nhóm "{name}" thành công.')
            return redirect('system_settings:user_list')
    emp_group_data = []
    for eg in all_emp_groups:
        dp = existing_depts.get(eg.pk)
        emp_group_data.append({
            'group':      eg,
            'has_access': dp is not None,
            'can_add':    dp.can_add    if dp else False,
            'can_edit':   dp.can_edit   if dp else False,
            'can_delete': dp.can_delete if dp else False,
        })
    return render(request, 'system_settings/staff_group_form.html', {
        'title': 'Chỉnh sửa nhóm người dùng',
        'sg': sg, 'all_users': all_users,
        'emp_group_data': emp_group_data, 'error': error,
        'app_status': AppStatus.get(),
    })


@login_required
def staff_group_delete(request, pk):
    if not request.user.is_superuser:
        return redirect('employee_list')
    sg = get_object_or_404(StaffGroup, pk=pk)
    if request.method == 'POST':
        name = sg.name
        sg.delete()
        log_activity(request.user, 'delete', 'staff_group', name, ip=_get_client_ip(request))
        messages.success(request, f'Đã xóa nhóm "{name}".')
        return redirect('system_settings:user_list')
    return render(request, 'system_settings/staff_group_confirm_delete.html', {'sg': sg})


# ── Phân quyền ───────────────────────────────────────────────────────────────

@login_required
def permission_manage(request):
    if not request.user.is_superuser:
        return redirect('employee_list')

    if request.method == 'POST':
        user_id    = request.POST.get('user_id')
        all_groups = EmployeeGroup.objects.all()
        user = get_object_or_404(User, pk=user_id)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.app_employees  = 'app_employees'  in request.POST
        profile.app_contracts  = 'app_contracts'  in request.POST
        profile.app_attendance = 'app_attendance' in request.POST
        profile.app_payroll    = 'app_payroll'    in request.POST
        profile.app_talent     = 'app_talent'     in request.POST
        profile.can_export         = 'feat_export'         in request.POST
        profile.can_import         = 'feat_import'         in request.POST
        profile.can_view_dashboard = 'feat_dashboard'      in request.POST
        profile.can_approve_talent = 'feat_approve_talent' in request.POST
        profile.save()
        profile.group_perms.all().delete()
        for group in all_groups:
            if f'group_{group.pk}' in request.POST:
                UserGroupPermission.objects.create(
                    profile=profile,
                    group=group,
                    can_add=f'add_{group.pk}' in request.POST,
                    can_edit=f'edit_{group.pk}' in request.POST,
                    can_delete=f'del_{group.pk}' in request.POST,
                )
        log_activity(request.user, 'edit', 'permission', user.username,
                     detail='Cập nhật phân quyền cá nhân', ip=_get_client_ip(request))
        messages.success(request, f'Đã cập nhật quyền cho tài khoản "{user.username}" thành công.')

    return redirect('system_settings:user_list')


# ── Nhật ký hoạt động ────────────────────────────────────────────────────────

@login_required
def activity_log(request):
    if not request.user.is_superuser:
        return redirect('employee_list')

    user_filter   = request.GET.get('user', '')
    action_filter = request.GET.get('action', '')
    target_filter = request.GET.get('target_type', '')
    date_from     = request.GET.get('date_from', '')
    date_to       = request.GET.get('date_to', '')
    search        = request.GET.get('search', '')

    qs = ActivityLog.objects.select_related('user').order_by('-created_at')

    if user_filter:
        qs = qs.filter(user__username=user_filter)
    if action_filter:
        qs = qs.filter(action=action_filter)
    if target_filter:
        qs = qs.filter(target_type=target_filter)
    if date_from:
        try:
            from datetime import date as _d
            qs = qs.filter(created_at__date__gte=_d.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import date as _d
            qs = qs.filter(created_at__date__lte=_d.fromisoformat(date_to))
        except ValueError:
            pass
    if search:
        qs = qs.filter(Q(target_name__icontains=search) | Q(detail__icontains=search))

    total = qs.count()
    paginator_log = Paginator(qs, 50)
    page_obj = paginator_log.get_page(request.GET.get('page'))

    all_users_log = User.objects.filter(activitylog__isnull=False).distinct().order_by('username')

    return render(request, 'system_settings/activity_log.html', {
        'page_obj':       page_obj,
        'total':          total,
        'all_users':      all_users_log,
        'user_filter':    user_filter,
        'action_filter':  action_filter,
        'target_filter':  target_filter,
        'date_from':      date_from,
        'date_to':        date_to,
        'search':         search,
        'action_choices': ActivityLog.ACTION_CHOICES,
        'target_choices': ActivityLog.TARGET_CHOICES,
    })


# ── Liên kết User ↔ Employee ─────────────────────────────────────────────────

@login_required
def user_link_employee(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'ok': False, 'error': 'Không có quyền'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)

    target_user = get_object_or_404(User, pk=pk)
    employee_id = request.POST.get('employee_id', '').strip()

    # Hủy liên kết cũ nếu có
    old_emp = getattr(target_user, 'employee', None)
    if old_emp:
        old_emp.user = None
        old_emp.save(update_fields=['user'])

    if employee_id:
        new_emp = get_object_or_404(Employee, pk=employee_id)
        # Hủy liên kết user cũ của employee đó (nếu có)
        if new_emp.user and new_emp.user != target_user:
            new_emp.user = None
        new_emp.user = target_user
        new_emp.save(update_fields=['user'])
        log_activity(request.user, 'edit', 'user', target_user.username,
                     detail=f'Liên kết tài khoản → NV {new_emp.full_name}',
                     ip=_get_client_ip(request))
        return JsonResponse({'ok': True, 'emp_name': new_emp.full_name, 'emp_code': new_emp.employee_code or ''})
    else:
        log_activity(request.user, 'edit', 'user', target_user.username,
                     detail='Hủy liên kết tài khoản khỏi nhân viên',
                     ip=_get_client_ip(request))
        return JsonResponse({'ok': True, 'emp_name': '', 'emp_code': ''})
