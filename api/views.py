from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import filters, status
from drf_spectacular.utils import extend_schema

from employees.models import Employee
from employees.serializers import EmployeeSerializer
from employees.helpers import get_user_perms, get_allowed_departments
from departments.models import Department
from departments.serializers import DepartmentSerializer
from attendance.models import AttendanceRecord, LeaveRequest, LeaveType, LeaveApproval
from attendance.serializers import (
    AttendanceRecordSerializer, LeaveRequestSerializer, LeaveTypeSerializer,
)
from payroll.models import Payslip, OTRecord
from payroll.serializers import PayslipSerializer, OTRecordSerializer
from .permissions import HasEmployeesAppPermission, HasAttendanceAppPermission, HasPayrollAppPermission


class HealthCheckView(APIView):
    """Kiểm tra API đang hoạt động — không cần đăng nhập."""
    permission_classes = [AllowAny]

    @extend_schema(responses={200: {'type': 'object', 'properties': {'status': {'type': 'string'}, 'message': {'type': 'string'}}}})
    def get(self, request):
        return Response({'status': 'ok', 'message': 'HRM API đang hoạt động'})


class DepartmentViewSet(ModelViewSet):
    """
    CRUD phòng ban.
    - GET /api/departments/ — danh sách
    - POST /api/departments/ — tạo mới
    - GET /api/departments/{id}/ — chi tiết
    - PUT/PATCH /api/departments/{id}/ — cập nhật
    - DELETE /api/departments/{id}/ — xóa
    """
    serializer_class = DepartmentSerializer
    permission_classes = [HasEmployeesAppPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'id']
    ordering = ['name']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Department.objects.all()
        return get_allowed_departments(user)


class EmployeeViewSet(ModelViewSet):
    """
    CRUD nhân viên.
    - GET /api/employees/ — danh sách (mặc định ẩn nghỉ việc)
    - POST /api/employees/ — tạo mới
    - GET /api/employees/{id}/ — chi tiết
    - PUT/PATCH /api/employees/{id}/ — cập nhật
    - DELETE /api/employees/{id}/ — xóa

    Query params:
    - ?status=dang_lam — lọc theo trạng thái (all = hiện cả nghỉ việc)
    - ?department=3 — lọc theo phòng ban (ID)
    - ?search=nguyen — tìm theo tên / mã NV / email / phone
    - ?ordering=hire_date — sắp xếp
    """
    serializer_class = EmployeeSerializer
    permission_classes = [HasEmployeesAppPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'employee_code', 'email', 'phone']
    ordering_fields = ['full_name', 'hire_date', 'employee_code', 'department__name']
    ordering = ['full_name']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            qs = Employee.objects.select_related('department').all()
        else:
            allowed_depts = get_allowed_departments(user)
            qs = Employee.objects.select_related('department').filter(department__in=allowed_depts)

        status = self.request.query_params.get('status')
        if status == 'all':
            pass  # hiển thị tất cả kể cả nghỉ việc
        elif status:
            qs = qs.filter(status=status)
        else:
            qs = qs.exclude(status='nghi_viec')  # mặc định ẩn nghỉ việc

        dept_id = self.request.query_params.get('department')
        if dept_id:
            qs = qs.filter(department_id=dept_id)

        return qs

    def perform_create(self, serializer):
        """Kiểm tra quyền can_add trước khi tạo nhân viên."""
        user = self.request.user
        if not user.is_superuser:
            perms = get_user_perms(user)
            if not perms['can_add']:
                raise PermissionDenied('Bạn không có quyền thêm nhân viên.')
        serializer.save()


# ─────────────────────────────────────────────
# ATTENDANCE API
# ─────────────────────────────────────────────

class LeaveTypeViewSet(ReadOnlyModelViewSet):
    """
    Danh sách loại nghỉ phép (chỉ đọc).
    - GET /api/attendance/leave-types/
    - GET /api/attendance/leave-types/{id}/
    """
    queryset = LeaveType.objects.filter(is_active=True).order_by('name')
    serializer_class = LeaveTypeSerializer
    permission_classes = [HasAttendanceAppPermission]


class AttendanceRecordViewSet(ModelViewSet):
    """
    CRUD bản ghi chấm công.
    - GET/POST /api/attendance/records/
    - GET/PUT/PATCH/DELETE /api/attendance/records/{id}/

    Query params:
    - ?employee=3 — lọc theo nhân viên (ID)
    - ?date=2026-05-20 — lọc theo ngày
    - ?month=5&year=2026 — lọc theo tháng/năm
    - ?status=present — lọc theo trạng thái
    - ?search=nguyen — tìm theo tên nhân viên
    """
    serializer_class = AttendanceRecordSerializer
    permission_classes = [HasAttendanceAppPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee__full_name', 'employee__employee_code']
    ordering_fields = ['date', 'employee__full_name', 'actual_hours', 'ot_hours']
    ordering = ['-date']

    def get_queryset(self):
        qs = AttendanceRecord.objects.select_related('employee', 'shift').all()
        params = self.request.query_params

        if emp_id := params.get('employee'):
            qs = qs.filter(employee_id=emp_id)
        if date := params.get('date'):
            qs = qs.filter(date=date)
        if month := params.get('month'):
            qs = qs.filter(date__month=month)
        if year := params.get('year'):
            qs = qs.filter(date__year=year)
        if att_status := params.get('status'):
            qs = qs.filter(status=att_status)

        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, source='manual')


class LeaveRequestViewSet(ModelViewSet):
    """
    CRUD đơn xin nghỉ phép.
    - GET/POST /api/attendance/leave-requests/
    - GET/PUT/PATCH/DELETE /api/attendance/leave-requests/{id}/
    - POST /api/attendance/leave-requests/{id}/approve/ — duyệt đơn
    - POST /api/attendance/leave-requests/{id}/reject/ — từ chối đơn

    Query params:
    - ?status=pending — lọc theo trạng thái
    - ?employee=3 — lọc theo nhân viên (ID)
    - ?year=2026 — lọc theo năm
    - ?search=nguyen — tìm theo tên nhân viên
    """
    serializer_class = LeaveRequestSerializer
    permission_classes = [HasAttendanceAppPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee__full_name', 'employee__employee_code']
    ordering_fields = ['created_at', 'start_date', 'total_days']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = LeaveRequest.objects.select_related('employee', 'leave_type').prefetch_related('approvals')
        params = self.request.query_params

        if leave_status := params.get('status'):
            qs = qs.filter(status=leave_status)
        if emp_id := params.get('employee'):
            qs = qs.filter(employee_id=emp_id)
        if year := params.get('year'):
            qs = qs.filter(start_date__year=year)

        return qs

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Duyệt đơn xin nghỉ.
        Body (tuỳ chọn): {"comment": "Đồng ý"}
        - Đơn đang `pending` → chuyển sang `waiting_hr`
        - Đơn đang `waiting_hr` → chuyển sang `approved`
        - Superuser duyệt thẳng lên `approved` bất kể trạng thái.
        """
        leave = self.get_object()
        if leave.status in ('approved', 'rejected', 'cancelled'):
            raise ValidationError(f'Không thể duyệt đơn đang ở trạng thái "{leave.get_status_display()}".')

        comment = request.data.get('comment', '')
        user = request.user

        if user.is_superuser or leave.status == 'waiting_hr':
            new_status = 'approved'
            level = 2
            leave.approved_at = timezone.now()
        else:
            new_status = 'waiting_hr'
            level = 1

        LeaveApproval.objects.create(
            leave_request=leave,
            approver=user,
            level=level,
            action='approved',
            comment=comment,
        )
        leave.status = new_status
        leave.save(update_fields=['status', 'approved_at'])
        return Response(LeaveRequestSerializer(leave).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Từ chối đơn xin nghỉ.
        Body (bắt buộc): {"comment": "Lý do từ chối"}
        """
        leave = self.get_object()
        if leave.status in ('approved', 'rejected', 'cancelled'):
            raise ValidationError(f'Không thể từ chối đơn đang ở trạng thái "{leave.get_status_display()}".')

        comment = request.data.get('comment', '')
        level = 2 if leave.status == 'waiting_hr' else 1

        LeaveApproval.objects.create(
            leave_request=leave,
            approver=request.user,
            level=level,
            action='rejected',
            comment=comment,
        )
        leave.status = 'rejected'
        leave.save(update_fields=['status'])
        return Response(LeaveRequestSerializer(leave).data)


# ─────────────────────────────────────────────
# PAYROLL API
# ─────────────────────────────────────────────

class OTRecordViewSet(ModelViewSet):
    """
    CRUD bản ghi tăng ca (OT).
    - GET/POST /api/payroll/ot-records/
    - GET/PUT/PATCH/DELETE /api/payroll/ot-records/{id}/
    - POST /api/payroll/ot-records/{id}/approve/ — duyệt OT
    - POST /api/payroll/ot-records/{id}/reject/ — từ chối OT

    Query params:
    - ?status=pending — lọc theo trạng thái
    - ?employee=3 — lọc theo nhân viên (ID)
    - ?month=5&year=2026 — lọc theo tháng/năm
    - ?search=nguyen — tìm theo tên nhân viên
    """
    serializer_class = OTRecordSerializer
    permission_classes = [HasPayrollAppPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee__full_name', 'employee__employee_code']
    ordering_fields = ['date', 'hours', 'employee__full_name']
    ordering = ['-date']

    def get_queryset(self):
        qs = OTRecord.objects.select_related('employee', 'approved_by').all()
        params = self.request.query_params

        if emp_id := params.get('employee'):
            qs = qs.filter(employee_id=emp_id)
        if month := params.get('month'):
            qs = qs.filter(date__month=month)
        if year := params.get('year'):
            qs = qs.filter(date__year=year)
        if ot_status := params.get('status'):
            qs = qs.filter(status=ot_status)

        return qs

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Duyệt bản ghi OT.
        Body (tuỳ chọn): {"note": "OK"}
        """
        ot = self.get_object()
        if ot.status != OTRecord.STATUS_PENDING:
            raise ValidationError(f'Không thể duyệt OT đang ở trạng thái "{ot.get_status_display()}".')

        ot.status = OTRecord.STATUS_APPROVED
        ot.approved_by = request.user
        ot.approved_at = timezone.now()
        ot.note = request.data.get('note', '')
        ot.save(update_fields=['status', 'approved_by', 'approved_at', 'note'])
        return Response(OTRecordSerializer(ot).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Từ chối bản ghi OT.
        Body (tuỳ chọn): {"note": "Lý do từ chối"}
        """
        ot = self.get_object()
        if ot.status != OTRecord.STATUS_PENDING:
            raise ValidationError(f'Không thể từ chối OT đang ở trạng thái "{ot.get_status_display()}".')

        ot.status = OTRecord.STATUS_REJECTED
        ot.note = request.data.get('note', '')
        ot.save(update_fields=['status', 'note'])
        return Response(OTRecordSerializer(ot).data)


class PayslipViewSet(ModelViewSet):
    """
    CRUD phiếu lương.
    - GET/POST /api/payroll/payslips/
    - GET/PUT/PATCH/DELETE /api/payroll/payslips/{id}/
    - POST /api/payroll/payslips/{id}/recalculate/ — tính lại phiếu lương
    - POST /api/payroll/payslips/{id}/confirm/ — xác nhận phiếu lương

    Query params:
    - ?month=5&year=2026 — lọc theo kỳ lương
    - ?employee=3 — lọc theo nhân viên (ID)
    - ?status=draft — lọc theo trạng thái (draft/confirmed)
    - ?search=nguyen — tìm theo tên nhân viên
    """
    serializer_class = PayslipSerializer
    permission_classes = [HasPayrollAppPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee__full_name', 'employee__employee_code']
    ordering_fields = ['year', 'month', 'employee__full_name', 'net_salary', 'gross_salary']
    ordering = ['-year', '-month']

    def get_queryset(self):
        qs = Payslip.objects.select_related('employee', 'contract').prefetch_related('lines').all()
        params = self.request.query_params

        if month := params.get('month'):
            qs = qs.filter(month=month)
        if year := params.get('year'):
            qs = qs.filter(year=year)
        if emp_id := params.get('employee'):
            qs = qs.filter(employee_id=emp_id)
        if slip_status := params.get('status'):
            qs = qs.filter(status=slip_status)

        return qs

    def perform_create(self, serializer):
        """Tạo phiếu lương → tự động chạy calculate() + generate_lines()."""
        payslip = serializer.save()
        payslip.calculate()
        payslip.save()
        payslip.generate_lines()

    @action(detail=True, methods=['post'])
    def recalculate(self, request, pk=None):
        """
        Tính lại phiếu lương (chỉ áp dụng khi status=draft).
        Không cần body.
        """
        payslip = self.get_object()
        if payslip.status == Payslip.STATUS_CONFIRMED:
            raise ValidationError('Không thể tính lại phiếu lương đã xác nhận.')

        payslip.calculate()
        payslip.save()
        payslip.generate_lines()
        return Response(PayslipSerializer(payslip).data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Xác nhận phiếu lương — chuyển từ draft → confirmed.
        Không cần body.
        """
        payslip = self.get_object()
        if payslip.status == Payslip.STATUS_CONFIRMED:
            raise ValidationError('Phiếu lương đã được xác nhận rồi.')

        payslip.status = Payslip.STATUS_CONFIRMED
        payslip.save(update_fields=['status'])
        return Response(PayslipSerializer(payslip).data)
