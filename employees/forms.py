from django import forms
from .models import Employee
from departments.models import Department


class EmployeeForm(forms.ModelForm):
    # to_field_name='name': template gửi tên phòng ban (không gửi PK)
    # → template hiện tại dùng value="{{ dept.name }}" không cần sửa
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        to_field_name='name',
        empty_label='-- Chọn bộ phận --',
    )

    class Meta:
        model = Employee
        fields = [
            'employee_code', 'photo', 'full_name', 'status', 'phone', 'address', 'id_card',
            'marital_status', 'degree', 'email', 'department', 'position', 'salary', 'hire_date',
            'status_start_date', 'status_end_date',
        ]
        widgets = {
            'hire_date':         forms.DateInput(attrs={'type': 'date'}),
            'status_start_date': forms.DateInput(attrs={'type': 'date'}),
            'status_end_date':   forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_employee_code(self):
        value = self.cleaned_data.get('employee_code', '')
        return value.upper() if value else value

    def clean(self):
        cleaned    = super().clean()
        status     = cleaned.get('status')
        start_date = cleaned.get('status_start_date')
        end_date   = cleaned.get('status_end_date')
        if status in ('thu_viec', 'thuc_tap_sinh'):
            if not start_date:
                self.add_error('status_start_date', 'Vui lòng nhập ngày bắt đầu.')
            if not end_date:
                self.add_error('status_end_date', 'Vui lòng nhập ngày kết thúc.')
            if start_date and end_date and end_date <= start_date:
                self.add_error('status_end_date', 'Ngày kết thúc phải sau ngày bắt đầu.')
        return cleaned
