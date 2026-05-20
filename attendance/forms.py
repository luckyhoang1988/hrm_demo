from django import forms
from .models import (
    WorkShift, PublicHoliday, AttendanceRecord,
    LeaveType, LeavePolicy, LeaveBalance, LeaveRequest,
)


class WorkShiftForm(forms.ModelForm):
    class Meta:
        model  = WorkShift
        fields = ['name', 'start_time', 'end_time', 'break_minutes', 'standard_hours', 'is_active']
        widgets = {
            'start_time':     forms.TimeInput(attrs={'type': 'time'}),
            'end_time':       forms.TimeInput(attrs={'type': 'time'}),
            'break_minutes':  forms.NumberInput(attrs={'min': 0, 'max': 120}),
            'standard_hours': forms.NumberInput(attrs={'step': '0.5', 'min': 1, 'max': 24}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_time')
        end   = cleaned.get('end_time')
        if start and end and end <= start:
            raise forms.ValidationError('Giờ kết thúc phải sau giờ bắt đầu.')
        return cleaned


class PublicHolidayForm(forms.ModelForm):
    class Meta:
        model  = PublicHoliday
        fields = ['name', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class AttendanceRecordForm(forms.ModelForm):
    class Meta:
        model  = AttendanceRecord
        fields = ['employee', 'date', 'shift', 'check_in', 'check_out', 'status', 'note']
        widgets = {
            'date':      forms.DateInput(attrs={'type': 'date'}),
            'check_in':  forms.TimeInput(attrs={'type': 'time'}),
            'check_out': forms.TimeInput(attrs={'type': 'time'}),
            'note':      forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned   = super().clean()
        check_in  = cleaned.get('check_in')
        check_out = cleaned.get('check_out')
        if check_in and check_out and check_out <= check_in:
            raise forms.ValidationError('Giờ ra phải sau giờ vào.')
        return cleaned


class AttendanceImportForm(forms.Form):
    file = forms.FileField(
        label='File Excel (.xlsx)',
        help_text='Cột: Mã NV | Ngày (dd/mm/yyyy) | Giờ vào (HH:MM) | Giờ ra (HH:MM) | Ghi chú'
    )

    def clean_file(self):
        f = self.cleaned_data['file']
        if not f.name.endswith('.xlsx'):
            raise forms.ValidationError('Chỉ chấp nhận file .xlsx.')
        if f.size > 10 * 1024 * 1024:
            raise forms.ValidationError('File quá lớn (tối đa 10MB).')
        return f


class LeaveTypeForm(forms.ModelForm):
    class Meta:
        model  = LeaveType
        fields = ['name', 'code', 'max_days_per_year', 'is_paid', 'requires_approval',
                  'allow_half_day', 'document_required', 'carry_over', 'gender_restriction', 'is_active']
        widgets = {
            'max_days_per_year': forms.NumberInput(attrs={'min': 0}),
        }


class LeavePolicyForm(forms.ModelForm):
    class Meta:
        model  = LeavePolicy
        fields = ['name', 'base_annual_days', 'increment_years', 'increment_days']
        widgets = {
            'base_annual_days': forms.NumberInput(attrs={'min': 1}),
            'increment_years':  forms.NumberInput(attrs={'min': 1}),
            'increment_days':   forms.NumberInput(attrs={'min': 0}),
        }


class LeaveBalanceForm(forms.ModelForm):
    class Meta:
        model  = LeaveBalance
        fields = ['allocated_days', 'carried_days', 'note']
        widgets = {
            'allocated_days': forms.NumberInput(attrs={'step': '0.5', 'min': 0}),
            'carried_days':   forms.NumberInput(attrs={'step': '0.5', 'min': 0}),
            'note':           forms.Textarea(attrs={'rows': 2}),
        }


class LeaveBalanceInitForm(forms.Form):
    from datetime import date as _date
    year = forms.IntegerField(
        label='Năm',
        min_value=2020,
        max_value=2030,
        initial=_date.today().year,
    )
    leave_type = forms.ModelChoiceField(
        queryset=LeaveType.objects.filter(is_active=True),
        label='Loại nghỉ phép',
    )


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model  = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'half_day', 'half_day_period', 'reason', 'document']
        widgets = {
            'start_date':      forms.DateInput(attrs={'type': 'date'}),
            'end_date':        forms.DateInput(attrs={'type': 'date'}),
            'reason':          forms.Textarea(attrs={'rows': 3}),
            'half_day_period': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)
        self.fields['leave_type'].queryset = LeaveType.objects.filter(is_active=True)
        self.fields['document'].required = False

    def clean(self):
        cleaned    = super().clean()
        start      = cleaned.get('start_date')
        end        = cleaned.get('end_date')
        half_day   = cleaned.get('half_day')
        half_period = cleaned.get('half_day_period')

        if start and end:
            if end < start:
                raise forms.ValidationError('Ngày kết thúc phải từ ngày bắt đầu trở đi.')
        if half_day and not half_period:
            self.add_error('half_day_period', 'Vui lòng chọn buổi nghỉ nửa ngày.')
        return cleaned

    def clean_document(self):
        doc = self.cleaned_data.get('document')
        if doc:
            allowed = ('.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png')
            if not any(doc.name.lower().endswith(ext) for ext in allowed):
                raise forms.ValidationError('Chỉ chấp nhận PDF, DOC, DOCX, JPG, PNG.')
            if doc.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File quá lớn (tối đa 10MB).')
        return doc


class LeaveApproveForm(forms.Form):
    comment = forms.CharField(
        label='Nhận xét (tùy chọn)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Nhận xét khi duyệt...'}),
    )


class LeaveRejectForm(forms.Form):
    comment = forms.CharField(
        label='Lý do từ chối',
        required=True,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Nêu rõ lý do từ chối...'}),
    )
