from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from contracts.models import Contract
from employees.helpers import get_user_features, log_activity, _get_client_ip
from employees.models import Employee
from system_settings.models import AppStatus

from .models import (
    InsuranceConfig, OTRecord, PITBracket,
    PayrollConfig, Payslip, SalaryConfig,
)


def _require_payroll(request):
    """Trả về None nếu được phép, hoặc HttpResponse redirect nếu không."""
    if not AppStatus.get().app_payroll_active:
        messages.error(request, 'Ứng dụng Bảng lương chưa được kích hoạt.')
        return redirect('home')
    if not request.user.is_superuser:
        feats = get_user_features(request.user)
        if not feats.get('app_payroll'):
            messages.error(request, 'Bạn không có quyền truy cập Bảng lương.')
            return redirect('home')
    return None


# ─────────────────────────────────────────────
# DANH SÁCH PHIẾU LƯƠNG
# ─────────────────────────────────────────────

@login_required
def payslip_list(request):
    guard = _require_payroll(request)
    if guard:
        return guard

    today = date.today()
    month = int(request.GET.get('month', today.month))
    year  = int(request.GET.get('year',  today.year))
    dept  = request.GET.get('dept', '')
    status_filter = request.GET.get('status', '')

    qs = (
        Payslip.objects
        .filter(month=month, year=year)
        .select_related('employee', 'employee__department')
        .order_by('employee__employee_code')
    )
    if dept:
        qs = qs.filter(employee__department__name=dept)
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 50)
    page_obj  = paginator.get_page(request.GET.get('page'))

    from departments.models import Department
    departments = Department.objects.all().order_by('name')

    # tạo list tháng cho dropdown
    months = list(range(1, 13))
    years  = list(range(today.year - 2, today.year + 2))

    return render(request, 'payroll/payslip_list.html', {
        'page_obj':    page_obj,
        'month':       month,
        'year':        year,
        'dept':        dept,
        'status_filter': status_filter,
        'departments': departments,
        'months':      months,
        'years':       years,
        'total_net':   sum(p.net_salary for p in page_obj.object_list),
        'total_gross': sum(p.gross_salary for p in page_obj.object_list),
    })


# ─────────────────────────────────────────────
# TẠO HÀNG LOẠT
# ─────────────────────────────────────────────

@login_required
def payslip_bulk_create(request):
    guard = _require_payroll(request)
    if guard:
        return guard

    if not request.user.is_superuser:
        messages.error(request, 'Chỉ quản trị viên mới có thể tạo bảng lương hàng loạt.')
        return redirect('payroll:payslip_list')

    today = date.today()
    if request.method == 'POST':
        month = int(request.POST.get('month', today.month))
        year  = int(request.POST.get('year',  today.year))

        # Lấy tất cả NV active (không nghi_viec)
        active_employees = (
            Employee.objects
            .exclude(status='nghi_viec')
            .select_related('department')
        )

        config = PayrollConfig.get()
        created_count = 0
        skipped_count = 0

        for emp in active_employees:
            # Tìm hợp đồng còn hiệu lực
            contract = (
                Contract.objects
                .filter(employee=emp, status__in=['hieu_luc', 'sap_het_han'])
                .order_by('-start_date')
                .first()
            )

            try:
                payslip, created = Payslip.objects.get_or_create(
                    employee=emp,
                    month=month,
                    year=year,
                    defaults={'contract': contract, 'status': 'draft'},
                )
                if created:
                    payslip.calculate(config=config)
                    payslip.save()
                    payslip.generate_lines()
                    created_count += 1
                else:
                    skipped_count += 1
            except IntegrityError:
                skipped_count += 1

        log_activity(
            request.user, 'create', 'Phiếu lương',
            f'Tháng {month:02d}/{year}',
            f'Tạo {created_count} phiếu, bỏ qua {skipped_count} phiếu đã tồn tại',
            ip=_get_client_ip(request),
        )
        messages.success(request, f'Đã tạo {created_count} phiếu lương. Bỏ qua {skipped_count} phiếu đã tồn tại.')
        return redirect(f"{reverse('payroll:payslip_list')}?month={month}&year={year}")

    months = list(range(1, 13))
    years  = list(range(today.year - 2, today.year + 2))
    return render(request, 'payroll/payslip_bulk_create.html', {
        'month':  today.month,
        'year':   today.year,
        'months': months,
        'years':  years,
    })


# ─────────────────────────────────────────────
# CHI TIẾT PHIẾU LƯƠNG
# ─────────────────────────────────────────────

@login_required
def payslip_detail(request, pk):
    guard = _require_payroll(request)
    if guard:
        return guard

    payslip = get_object_or_404(
        Payslip.objects.select_related('employee', 'employee__department', 'contract'),
        pk=pk,
    )
    return render(request, 'payroll/payslip_detail.html', {'payslip': payslip})


# ─────────────────────────────────────────────
# CẬP NHẬT PHIẾU LƯƠNG (thủ công)
# ─────────────────────────────────────────────

@login_required
def payslip_update(request, pk):
    guard = _require_payroll(request)
    if guard:
        return guard

    payslip = get_object_or_404(Payslip, pk=pk)
    if payslip.status == Payslip.STATUS_CONFIRMED and not request.user.is_superuser:
        messages.error(request, 'Không thể sửa phiếu lương đã xác nhận.')
        return redirect('payroll:payslip_detail', pk=pk)

    if request.method == 'POST':
        try:
            payslip.dependents      = int(request.POST.get('dependents', 0))
            payslip.other_additions = int(request.POST.get('other_additions', 0))
            payslip.other_deductions = int(request.POST.get('other_deductions', 0))
            payslip.note            = request.POST.get('note', '')
            new_status              = request.POST.get('status', payslip.status)
            if new_status in (Payslip.STATUS_DRAFT, Payslip.STATUS_CONFIRMED):
                payslip.status = new_status
            # Tính lại sau khi cập nhật
            payslip.calculate()
            payslip.save()
            payslip.generate_lines()
            log_activity(
                request.user, 'edit', 'Phiếu lương',
                str(payslip),
                ip=_get_client_ip(request),
            )
            messages.success(request, 'Đã cập nhật và tính lại phiếu lương.')
        except Exception as e:
            messages.error(request, f'Lỗi: {e}')
        return redirect('payroll:payslip_detail', pk=pk)

    return render(request, 'payroll/payslip_update.html', {'payslip': payslip})


# ─────────────────────────────────────────────
# XÓA PHIẾU LƯƠNG
# ─────────────────────────────────────────────

@login_required
def payslip_delete(request, pk):
    guard = _require_payroll(request)
    if guard:
        return guard

    if not request.user.is_superuser:
        messages.error(request, 'Chỉ quản trị viên mới có thể xóa phiếu lương.')
        return redirect('payroll:payslip_list')

    payslip = get_object_or_404(Payslip, pk=pk)
    if request.method == 'POST':
        label = str(payslip)
        payslip.delete()
        log_activity(
            request.user, 'delete', 'Phiếu lương', label,
            ip=_get_client_ip(request),
        )
        messages.success(request, f'Đã xóa {label}.')
        return redirect('payroll:payslip_list')

    return render(request, 'payroll/payslip_confirm_delete.html', {'payslip': payslip})


# ─────────────────────────────────────────────
# IN PHIẾU LƯƠNG
# ─────────────────────────────────────────────

@login_required
def payslip_print(request, pk):
    guard = _require_payroll(request)
    if guard:
        return guard

    payslip = get_object_or_404(
        Payslip.objects.select_related('employee', 'employee__department', 'contract'),
        pk=pk,
    )
    return render(request, 'payroll/payslip_print.html', {'payslip': payslip})


# ─────────────────────────────────────────────
# CẤU HÌNH BẢNG LƯƠNG
# ─────────────────────────────────────────────

@login_required
def payroll_config(request):
    if not request.user.is_superuser:
        messages.error(request, 'Chỉ quản trị viên mới có thể chỉnh cấu hình.')
        return redirect('home')

    config = PayrollConfig.get()
    if request.method == 'POST':
        try:
            from decimal import Decimal as D
            config.bhxh_rate           = D(request.POST.get('bhxh_rate', '8.00'))
            config.bhyt_rate           = D(request.POST.get('bhyt_rate', '1.50'))
            config.bhtn_rate           = D(request.POST.get('bhtn_rate', '1.00'))
            config.personal_deduction  = D(request.POST.get('personal_deduction', '11000000'))
            config.dependent_deduction = D(request.POST.get('dependent_deduction', '4400000'))
            config.save()
            log_activity(
                request.user, 'edit', 'Cấu hình bảng lương',
                ip=_get_client_ip(request),
            )
            messages.success(request, 'Đã lưu cấu hình bảng lương.')
        except Exception as e:
            messages.error(request, f'Lỗi: {e}')
        return redirect('payroll:payroll_config')

    return render(request, 'payroll/payroll_config.html', {'config': config})


# ─────────────────────────────────────────────
# CẤU HÌNH BẢO HIỂM THEO NĂM (InsuranceConfig + PITBracket)
# ─────────────────────────────────────────────

@login_required
def insurance_config_list(request):
    guard = _require_payroll(request)
    if guard:
        return guard
    if not request.user.is_superuser:
        messages.error(request, 'Chỉ quản trị viên mới có thể xem cấu hình bảo hiểm.')
        return redirect('payroll:payslip_list')

    configs = InsuranceConfig.objects.all()
    return render(request, 'payroll/insurance_config_list.html', {'configs': configs})


@login_required
def insurance_config_create(request):
    if not request.user.is_superuser:
        messages.error(request, 'Chỉ quản trị viên mới có thể thêm cấu hình.')
        return redirect('payroll:insurance_config_list')

    if request.method == 'POST':
        try:
            D = __import__('decimal').Decimal
            year = int(request.POST['year'])
            cfg, created = InsuranceConfig.objects.get_or_create(year=year)
            cfg.si_employee_rate    = D(request.POST.get('si_employee_rate', '8.00'))
            cfg.hi_employee_rate    = D(request.POST.get('hi_employee_rate', '1.50'))
            cfg.ui_employee_rate    = D(request.POST.get('ui_employee_rate', '1.00'))
            cfg.si_employer_rate    = D(request.POST.get('si_employer_rate', '17.50'))
            cfg.hi_employer_rate    = D(request.POST.get('hi_employer_rate', '3.00'))
            cfg.ui_employer_rate    = D(request.POST.get('ui_employer_rate', '1.00'))
            cfg.salary_cap          = D(request.POST.get('salary_cap', '46800000'))
            cfg.personal_deduction  = D(request.POST.get('personal_deduction', '15500000'))
            cfg.dependent_deduction = D(request.POST.get('dependent_deduction', '6200000'))
            cfg.save()

            # Lưu PITBracket cho năm này
            _save_pit_brackets(year, request.POST)

            action = 'create' if created else 'edit'
            log_activity(request.user, action, 'Cấu hình BH', f'Năm {year}',
                         ip=_get_client_ip(request))
            verb = 'Đã tạo' if created else 'Đã cập nhật'
            messages.success(request, f'{verb} cấu hình bảo hiểm năm {year}.')
            return redirect('payroll:insurance_config_list')
        except Exception as e:
            messages.error(request, f'Lỗi: {e}')

    year_prefill = int(request.GET.get('year', date.today().year))
    existing = None
    pit_brackets = []
    try:
        existing = InsuranceConfig.objects.get(year=year_prefill)
        pit_brackets = list(PITBracket.objects.filter(year=year_prefill).order_by('order'))
    except InsuranceConfig.DoesNotExist:
        pass

    return render(request, 'payroll/insurance_config_form.html', {
        'existing': existing,
        'year_prefill': year_prefill,
        'pit_brackets': pit_brackets,
    })


@login_required
def insurance_config_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Chỉ quản trị viên mới có thể xóa cấu hình.')
        return redirect('payroll:insurance_config_list')

    cfg = get_object_or_404(InsuranceConfig, pk=pk)
    if request.method == 'POST':
        year = cfg.year
        PITBracket.objects.filter(year=year).delete()
        cfg.delete()
        log_activity(request.user, 'delete', 'Cấu hình BH', f'Năm {year}',
                     ip=_get_client_ip(request))
        messages.success(request, f'Đã xóa cấu hình bảo hiểm năm {year}.')
        return redirect('payroll:insurance_config_list')

    return render(request, 'payroll/insurance_config_confirm_delete.html', {'cfg': cfg})


def _save_pit_brackets(year, post_data):
    """Lưu danh sách PITBracket từ POST data."""
    PITBracket.objects.filter(year=year).delete()
    brackets = []
    order = 1
    while True:
        rate_key = f'pit_rate_{order}'
        min_key  = f'pit_min_{order}'
        max_key  = f'pit_max_{order}'
        if rate_key not in post_data:
            break
        rate = post_data[rate_key].strip()
        if not rate:
            break
        D = __import__('decimal').Decimal
        max_val = post_data.get(max_key, '').strip()
        brackets.append(PITBracket(
            year=year,
            order=order,
            min_income=D(post_data.get(min_key, '0') or '0'),
            max_income=D(max_val) if max_val else None,
            rate=D(rate),
        ))
        order += 1
    if brackets:
        PITBracket.objects.bulk_create(brackets)


# ─────────────────────────────────────────────
# CẤU HÌNH LƯƠNG RIÊNG TỪNG NV (SalaryConfig)
# ─────────────────────────────────────────────

@login_required
def salary_config_list(request):
    guard = _require_payroll(request)
    if guard:
        return guard

    emp_id = request.GET.get('employee', '')
    qs = SalaryConfig.objects.select_related('employee', 'employee__department', 'contract')
    if emp_id:
        qs = qs.filter(employee_id=emp_id)

    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    employees = Employee.objects.exclude(status='nghi_viec').select_related('department').order_by('full_name')
    return render(request, 'payroll/salary_config_list.html', {
        'page_obj': page_obj,
        'employees': employees,
        'emp_id': emp_id,
    })


@login_required
def salary_config_create(request):
    guard = _require_payroll(request)
    if guard:
        return guard
    if not request.user.is_superuser:
        messages.error(request, 'Chỉ quản trị viên mới có thể tạo cấu hình lương.')
        return redirect('payroll:salary_config_list')

    if request.method == 'POST':
        try:
            D = __import__('decimal').Decimal
            import json
            emp = get_object_or_404(Employee, pk=request.POST['employee'])
            contract_id = request.POST.get('contract') or None
            contract = get_object_or_404(Contract, pk=contract_id) if contract_id else None

            # Parse allowances từ textarea JSON
            allowances_raw = request.POST.get('allowances', '{}').strip()
            try:
                allowances = json.loads(allowances_raw) if allowances_raw else {}
            except json.JSONDecodeError:
                allowances = {}

            cfg = SalaryConfig.objects.create(
                employee=emp,
                contract=contract,
                effective_from=request.POST['effective_from'],
                effective_to=request.POST.get('effective_to') or None,
                basic_salary=D(request.POST['basic_salary']),
                allowances=allowances,
                dependents=int(request.POST.get('dependents', 0)),
                is_active='is_active' in request.POST,
                note=request.POST.get('note', ''),
            )
            log_activity(request.user, 'create', 'Cấu hình lương', str(cfg),
                         ip=_get_client_ip(request))
            messages.success(request, f'Đã tạo cấu hình lương cho {emp.full_name}.')
            return redirect('payroll:salary_config_list')
        except Exception as e:
            messages.error(request, f'Lỗi: {e}')

    emp_prefill = request.GET.get('employee')
    employees = Employee.objects.exclude(status='nghi_viec').select_related('department').order_by('full_name')
    contracts = Contract.objects.filter(status__in=['hieu_luc', 'sap_het_han']).select_related('employee')
    return render(request, 'payroll/salary_config_form.html', {
        'employees': employees,
        'contracts': contracts,
        'emp_prefill': emp_prefill,
        'is_create': True,
    })


@login_required
def salary_config_update(request, pk):
    guard = _require_payroll(request)
    if guard:
        return guard
    if not request.user.is_superuser:
        messages.error(request, 'Chỉ quản trị viên mới có thể sửa cấu hình lương.')
        return redirect('payroll:salary_config_list')

    cfg = get_object_or_404(SalaryConfig, pk=pk)
    if request.method == 'POST':
        try:
            D = __import__('decimal').Decimal
            import json
            allowances_raw = request.POST.get('allowances', '{}').strip()
            try:
                allowances = json.loads(allowances_raw) if allowances_raw else {}
            except json.JSONDecodeError:
                allowances = {}

            contract_id = request.POST.get('contract') or None
            cfg.contract       = get_object_or_404(Contract, pk=contract_id) if contract_id else None
            cfg.effective_from = request.POST['effective_from']
            cfg.effective_to   = request.POST.get('effective_to') or None
            cfg.basic_salary   = D(request.POST['basic_salary'])
            cfg.allowances     = allowances
            cfg.dependents     = int(request.POST.get('dependents', 0))
            cfg.is_active      = 'is_active' in request.POST
            cfg.note           = request.POST.get('note', '')
            cfg.save()
            log_activity(request.user, 'edit', 'Cấu hình lương', str(cfg),
                         ip=_get_client_ip(request))
            messages.success(request, 'Đã cập nhật cấu hình lương.')
            return redirect('payroll:salary_config_list')
        except Exception as e:
            messages.error(request, f'Lỗi: {e}')

    contracts = Contract.objects.filter(
        employee=cfg.employee, status__in=['hieu_luc', 'sap_het_han']
    )
    import json
    return render(request, 'payroll/salary_config_form.html', {
        'cfg': cfg,
        'contracts': contracts,
        'allowances_json': json.dumps(cfg.allowances, ensure_ascii=False),
        'is_create': False,
    })


@login_required
def salary_config_delete(request, pk):
    guard = _require_payroll(request)
    if guard:
        return guard
    if not request.user.is_superuser:
        messages.error(request, 'Chỉ quản trị viên mới có thể xóa cấu hình lương.')
        return redirect('payroll:salary_config_list')

    cfg = get_object_or_404(SalaryConfig, pk=pk)
    if request.method == 'POST':
        label = str(cfg)
        cfg.delete()
        log_activity(request.user, 'delete', 'Cấu hình lương', label,
                     ip=_get_client_ip(request))
        messages.success(request, f'Đã xóa cấu hình lương: {label}.')
        return redirect('payroll:salary_config_list')

    return render(request, 'payroll/salary_config_confirm_delete.html', {'cfg': cfg})


# ─────────────────────────────────────────────
# BẢN GHI OT (OTRecord)
# ─────────────────────────────────────────────

@login_required
def ot_list(request):
    guard = _require_payroll(request)
    if guard:
        return guard

    today = date.today()
    month  = int(request.GET.get('month', today.month))
    year   = int(request.GET.get('year',  today.year))
    status = request.GET.get('status', '')
    emp_id = request.GET.get('employee', '')

    qs = (
        OTRecord.objects
        .filter(date__month=month, date__year=year)
        .select_related('employee', 'employee__department', 'approved_by')
        .order_by('-date', 'employee__employee_code')
    )
    if status:
        qs = qs.filter(status=status)
    if emp_id:
        qs = qs.filter(employee_id=emp_id)

    paginator = Paginator(qs, 50)
    page_obj  = paginator.get_page(request.GET.get('page'))

    from departments.models import Department
    employees = Employee.objects.exclude(status='nghi_viec').select_related('department').order_by('full_name')
    return render(request, 'payroll/ot_list.html', {
        'page_obj':  page_obj,
        'month':     month,
        'year':      year,
        'status':    status,
        'emp_id':    emp_id,
        'employees': employees,
        'months':    list(range(1, 13)),
        'years':     list(range(today.year - 2, today.year + 2)),
        'status_choices': OTRecord.STATUS_CHOICES,
        'total_hours': sum(r.hours for r in page_obj.object_list),
    })


@login_required
def ot_create(request):
    guard = _require_payroll(request)
    if guard:
        return guard

    if request.method == 'POST':
        try:
            D = __import__('decimal').Decimal
            emp = get_object_or_404(Employee, pk=request.POST['employee'])
            ot_type = request.POST.get('ot_type', 'normal')
            rec = OTRecord.objects.create(
                employee=emp,
                date=request.POST['date'],
                hours=D(request.POST['hours']),
                ot_type=ot_type,
                reason=request.POST.get('reason', ''),
                status='pending',
            )
            log_activity(request.user, 'create', 'Bản ghi OT', str(rec),
                         ip=_get_client_ip(request))
            messages.success(request, f'Đã tạo bản ghi OT cho {emp.full_name}.')
            return redirect('payroll:ot_list')
        except Exception as e:
            messages.error(request, f'Lỗi: {e}')

    employees = Employee.objects.exclude(status='nghi_viec').select_related('department').order_by('full_name')
    return render(request, 'payroll/ot_form.html', {
        'employees': employees,
        'ot_choices': OTRecord.OT_CHOICES,
        'today': date.today().isoformat(),
    })


@login_required
def ot_approve(request, pk):
    guard = _require_payroll(request)
    if guard:
        return guard
    if not request.user.is_superuser:
        messages.error(request, 'Chỉ quản trị viên mới có thể duyệt OT.')
        return redirect('payroll:ot_list')

    rec = get_object_or_404(OTRecord, pk=pk)
    if request.method == 'POST':
        from django.utils import timezone
        rec.status      = OTRecord.STATUS_APPROVED
        rec.approved_by = request.user
        rec.approved_at = timezone.now()
        rec.note        = request.POST.get('note', '')
        rec.save()
        log_activity(request.user, 'edit', 'Bản ghi OT', f'Duyệt: {rec}',
                     ip=_get_client_ip(request))
        messages.success(request, f'Đã duyệt OT cho {rec.employee.full_name}.')
        return redirect('payroll:ot_list')

    return render(request, 'payroll/ot_approve.html', {'rec': rec, 'action': 'approve'})


@login_required
def ot_reject(request, pk):
    guard = _require_payroll(request)
    if guard:
        return guard
    if not request.user.is_superuser:
        messages.error(request, 'Chỉ quản trị viên mới có thể từ chối OT.')
        return redirect('payroll:ot_list')

    rec = get_object_or_404(OTRecord, pk=pk)
    if request.method == 'POST':
        from django.utils import timezone
        rec.status      = OTRecord.STATUS_REJECTED
        rec.approved_by = request.user
        rec.approved_at = timezone.now()
        rec.note        = request.POST.get('note', '')
        rec.save()
        log_activity(request.user, 'edit', 'Bản ghi OT', f'Từ chối: {rec}',
                     ip=_get_client_ip(request))
        messages.success(request, f'Đã từ chối OT của {rec.employee.full_name}.')
        return redirect('payroll:ot_list')

    return render(request, 'payroll/ot_approve.html', {'rec': rec, 'action': 'reject'})


@login_required
def ot_delete(request, pk):
    guard = _require_payroll(request)
    if guard:
        return guard
    if not request.user.is_superuser:
        messages.error(request, 'Chỉ quản trị viên mới có thể xóa bản ghi OT.')
        return redirect('payroll:ot_list')

    rec = get_object_or_404(OTRecord, pk=pk)
    if request.method == 'POST':
        label = str(rec)
        rec.delete()
        log_activity(request.user, 'delete', 'Bản ghi OT', label,
                     ip=_get_client_ip(request))
        messages.success(request, f'Đã xóa: {label}.')
        return redirect('payroll:ot_list')

    return render(request, 'payroll/ot_confirm_delete.html', {'rec': rec})
