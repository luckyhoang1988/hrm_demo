from rest_framework import serializers
from .models import Payslip, PayslipLine, OTRecord


class PayslipLineSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = PayslipLine
        fields = ['id', 'category', 'category_display', 'name', 'amount', 'note', 'order']
        read_only_fields = ['id', 'category_display']


class PayslipSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    # Dòng chi tiết — chỉ hiển thị, không cho phép sửa qua API
    lines = PayslipLineSerializer(many=True, read_only=True)

    class Meta:
        model = Payslip
        fields = [
            'id', 'employee', 'employee_name', 'employee_code',
            'contract', 'month', 'year',
            # Lương snapshot
            'basic_salary', 'allowances_detail',
            # OT
            'ot_hours', 'ot_pay',
            # Tổng thu nhập
            'other_additions', 'gross_salary',
            # Bảo hiểm
            'bhxh_amount', 'bhyt_amount', 'bhtn_amount', 'total_insurance',
            # Thuế TNCN
            'dependents', 'taxable_income', 'pit_amount',
            # Khấu trừ khác & lương thực nhận
            'other_deductions', 'net_salary',
            # Meta
            'note', 'status', 'status_display', 'calculated_at',
            'lines',
        ]
        # Các trường do calculate() tính tự động — không cho client ghi trực tiếp
        read_only_fields = [
            'id', 'employee_name', 'employee_code', 'status_display',
            'basic_salary', 'allowances_detail',
            'ot_hours', 'ot_pay', 'gross_salary',
            'bhxh_amount', 'bhyt_amount', 'bhtn_amount', 'total_insurance',
            'taxable_income', 'pit_amount', 'net_salary',
            'calculated_at', 'lines',
        ]


class OTRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    ot_type_display = serializers.CharField(source='get_ot_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = OTRecord
        fields = [
            'id', 'employee', 'employee_name', 'employee_code',
            'date', 'hours', 'ot_type', 'ot_type_display',
            'multiplier',  # read-only: auto-set từ ot_type trong model.save()
            'reason', 'status', 'status_display',
            'approved_by', 'approved_by_name', 'approved_at', 'note',
            'created_at',
        ]
        read_only_fields = [
            'id', 'employee_name', 'employee_code',
            'ot_type_display', 'multiplier',
            'status_display', 'approved_by', 'approved_by_name', 'approved_at',
            'created_at',
        ]

    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else None
