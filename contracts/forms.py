from django import forms
from employees.models import Employee
from departments.models import Department
from .models import Contract


class ContractForm(forms.ModelForm):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(
            status__in=['dang_lam', 'thu_viec', 'thuc_tap_sinh']
        ).order_by('full_name'),
        label='Nhân viên',
        empty_label='-- Chọn nhân viên --',
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all().order_by('name'),
        to_field_name='name',
        label='Phòng ban',
        empty_label='-- Chọn phòng ban --',
    )

    class Meta:
        model = Contract
        fields = [
            'contract_number', 'employee', 'department', 'contract_type',
            'start_date', 'end_date', 'signed_date', 'notice_period_days',
            'position', 'salary', 'note', 'contract_file',
        ]
        widgets = {
            'start_date':  forms.DateInput(attrs={'type': 'date'}),
            'end_date':    forms.DateInput(attrs={'type': 'date'}),
            'signed_date': forms.DateInput(attrs={'type': 'date'}),
            'note':        forms.Textarea(attrs={'rows': 3}),
        }

    def clean_contract_number(self):
        return self.cleaned_data.get('contract_number', '').upper().strip()

    def clean_contract_file(self):
        f = self.cleaned_data.get('contract_file')
        if f and hasattr(f, 'name'):
            ext = f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
            if ext not in ('pdf', 'doc', 'docx'):
                raise forms.ValidationError('Chỉ hỗ trợ file PDF, DOC, DOCX.')
            if f.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File không được vượt quá 10MB.')
        return f

    def clean(self):
        cleaned = super().clean()
        contract_type = cleaned.get('contract_type')
        start_date    = cleaned.get('start_date')
        end_date      = cleaned.get('end_date')
        employee      = cleaned.get('employee')

        if contract_type != 'khong_xd':
            if not end_date:
                self.add_error('end_date', 'Loại hợp đồng này yêu cầu ngày kết thúc.')
            elif start_date and end_date and end_date <= start_date:
                self.add_error('end_date', 'Ngày kết thúc phải sau ngày bắt đầu.')

        # Cảnh báo nếu nhân viên đã có hợp đồng đang hiệu lực
        if employee:
            qs = Contract.objects.filter(
                employee=employee,
                status__in=('hieu_luc', 'sap_het_han'),
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                existing = qs.first()
                self.add_error(
                    'employee',
                    f'Nhân viên này đã có hợp đồng đang hiệu lực: {existing.contract_number}. '
                    f'Hãy gia hạn hoặc chấm dứt hợp đồng cũ trước.',
                )
        return cleaned


class ContractRenewForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['contract_number', 'contract_type', 'start_date', 'end_date', 'position', 'salary', 'note']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date':   forms.DateInput(attrs={'type': 'date'}),
            'note':       forms.Textarea(attrs={'rows': 3}),
        }

    def clean_contract_number(self):
        return self.cleaned_data.get('contract_number', '').upper().strip()

    def clean(self):
        cleaned = super().clean()
        contract_type = cleaned.get('contract_type')
        start_date    = cleaned.get('start_date')
        end_date      = cleaned.get('end_date')

        if contract_type != 'khong_xd':
            if not end_date:
                self.add_error('end_date', 'Loại hợp đồng này yêu cầu ngày kết thúc.')
            elif start_date and end_date and end_date <= start_date:
                self.add_error('end_date', 'Ngày kết thúc phải sau ngày bắt đầu.')
        return cleaned


class ContractTerminateForm(forms.Form):
    termination_date = forms.DateField(
        label='Ngày chấm dứt',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    termination_reason = forms.ChoiceField(
        label='Lý do chấm dứt',
        choices=Contract.TERMINATION_REASON_CHOICES,
    )
    termination_note = forms.CharField(
        label='Ghi chú',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
    )
