from django import forms
from .models import (
    JobPosition, Applicant, Interview, JobOffer,
    TrainingCourse, TrainingSession, TrainingEnrollment
)
from employees.models import Employee
from departments.models import Department


class JobPositionForm(forms.ModelForm):
    class Meta:
        model = JobPosition
        fields = ['title', 'department', 'headcount', 'employment_type',
                  'salary_min', 'salary_max', 'description', 'requirements',
                  'benefits', 'location', 'open_date', 'close_date', 'status',
                  'hiring_manager', 'source_channels', 'notes']
        widgets = {
            'open_date': forms.DateInput(attrs={'type': 'date'}),
            'close_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'requirements': forms.Textarea(attrs={'rows': 4}),
            'benefits': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        sal_min = cleaned.get('salary_min')
        sal_max = cleaned.get('salary_max')
        if sal_min and sal_max and sal_max < sal_min:
            raise forms.ValidationError('Lương tối đa phải lớn hơn lương tối thiểu.')
        open_date = cleaned.get('open_date')
        close_date = cleaned.get('close_date')
        if open_date and close_date and close_date < open_date:
            raise forms.ValidationError('Ngày đóng hồ sơ phải sau ngày mở.')
        return cleaned


class ApplicantForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = ['job_position', 'full_name', 'email', 'phone', 'address',
                  'source', 'referrer', 'cv_file', 'cover_letter', 'linkedin_url',
                  'stage', 'notes']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ApplicantStageForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = ['stage', 'reject_reason']
        widgets = {
            'reject_reason': forms.Textarea(attrs={'rows': 3}),
        }


class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ['round_number', 'interview_type', 'scheduled_date', 'scheduled_time',
                  'duration_minutes', 'location', 'interviewers', 'status', 'score', 'notes']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'scheduled_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'interviewers': forms.CheckboxSelectMultiple(),
        }


class JobOfferForm(forms.ModelForm):
    class Meta:
        model = JobOffer
        fields = ['offered_salary', 'start_date', 'probation_months',
                  'benefits_note', 'offer_letter_file', 'deadline_response',
                  'status', 'rejection_reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'deadline_response': forms.DateInput(attrs={'type': 'date'}),
            'benefits_note': forms.Textarea(attrs={'rows': 3}),
            'rejection_reason': forms.Textarea(attrs={'rows': 2}),
        }


class TrainingCourseForm(forms.ModelForm):
    class Meta:
        model = TrainingCourse
        fields = ['code', 'name', 'category', 'delivery_method', 'duration_hours',
                  'description', 'is_mandatory', 'provider', 'cost_per_person',
                  'certificate_validity_months', 'target_departments', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'target_departments': forms.CheckboxSelectMultiple(),
        }


class TrainingSessionForm(forms.ModelForm):
    class Meta:
        model = TrainingSession
        fields = ['course', 'session_code', 'trainer_name', 'trainer_employee',
                  'location', 'start_date', 'end_date', 'max_participants', 'status', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        if start and end and end < start:
            raise forms.ValidationError('Ngày kết thúc phải sau ngày bắt đầu.')
        return cleaned


class EnrollmentUpdateForm(forms.ModelForm):
    class Meta:
        model = TrainingEnrollment
        fields = ['status', 'score', 'result', 'feedback_rating', 'feedback_comment']
        widgets = {
            'feedback_comment': forms.Textarea(attrs={'rows': 2}),
        }


class EnrollmentAddForm(forms.Form):
    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(status__in=[
            'dang_lam', 'thu_viec', 'thuc_tap_sinh'
        ]).select_related('department').order_by('full_name'),
        widget=forms.CheckboxSelectMultiple(),
        label='Chọn nhân viên',
    )
