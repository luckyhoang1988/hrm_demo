from rest_framework import serializers
from .models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_code', 'full_name',
            'department', 'department_name',
            'status', 'status_display', 'is_active',
            'position', 'phone', 'email', 'address',
            'id_card', 'marital_status', 'degree',
            'salary', 'hire_date',
            'status_start_date', 'status_end_date', 'status_note',
            'scheduled_termination_date',
            'termination_date', 'termination_reason',
        ]
        read_only_fields = ['id', 'is_active', 'status_display', 'department_name']

    def validate_employee_code(self, value):
        return value.upper() if value else value

    def create(self, validated_data):
        if not validated_data.get('employee_code'):
            hire_date = validated_data.get('hire_date')
            validated_data['employee_code'] = Employee.generate_employee_code(hire_date)
        return super().create(validated_data)
