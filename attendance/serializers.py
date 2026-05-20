from rest_framework import serializers
from .models import AttendanceRecord, LeaveRequest, LeaveType, LeaveApproval


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = [
            'id', 'name', 'code', 'max_days_per_year', 'is_paid',
            'requires_approval', 'allow_half_day', 'document_required',
            'carry_over', 'gender_restriction', 'is_active',
        ]
        read_only_fields = ['id']


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    shift_name = serializers.CharField(source='shift.name', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    ot_type_display = serializers.CharField(source='get_ot_type_display', read_only=True, default=None)

    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'employee', 'employee_name', 'employee_code',
            'date', 'shift', 'shift_name',
            'check_in', 'check_out',
            'actual_hours', 'ot_hours', 'ot_type', 'ot_type_display', 'ot_multiplier',
            'status', 'status_display',
            'source', 'note',
            'created_at',
        ]
        read_only_fields = [
            'id', 'employee_name', 'employee_code', 'shift_name',
            'actual_hours', 'ot_hours', 'ot_type', 'ot_type_display', 'ot_multiplier',
            'status_display', 'created_at',
        ]


class LeaveApprovalSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(source='approver.get_full_name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = LeaveApproval
        fields = ['id', 'level', 'approver_name', 'action', 'action_display', 'comment', 'acted_at']
        read_only_fields = ['id', 'approver_name', 'action_display', 'acted_at']


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    # Lịch sử duyệt — chỉ hiển thị trong detail (nested)
    approvals = LeaveApprovalSerializer(many=True, read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'employee_code',
            'leave_type', 'leave_type_name',
            'start_date', 'end_date', 'total_days',
            'half_day', 'half_day_period',
            'reason', 'status', 'status_display',
            'created_at', 'approved_at',
            'approvals',
        ]
        read_only_fields = [
            'id', 'employee_name', 'employee_code', 'leave_type_name',
            'total_days', 'status_display', 'created_at', 'approved_at',
            'approvals',
        ]
