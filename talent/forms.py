from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from .models import (
    JobPosition, Applicant, Interview, JobOffer,
    TrainingCourse, TrainingSession, TrainingEnrollment,
    TrainingNeedAssessment, EmployeeTrainingPlan,
    STAGE_CHOICES,
)
from employees.models import Employee
from departments.models import Department


class JobPositionForm(forms.ModelForm):
    class Meta:
        model = JobPosition
        fields = ['title', 'department', 'headcount', 'employment_type',
                  'salary_min', 'salary_max', 'description', 'requirements',
                  'benefits', 'location', 'open_date', 'close_date', 'status',
                  'priority', 'hiring_manager', 'source_channels', 'notes']
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

    def clean(self):
        cleaned = super().clean()
        stage = cleaned.get('stage')
        reject_reason = cleaned.get('reject_reason')
        if stage == 'rejected' and not reject_reason:
            self.add_error('reject_reason', 'Bắt buộc nhập lý do từ chối.')
        return cleaned


class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ['round_number', 'interview_type', 'scheduled_date', 'scheduled_time',
                  'duration_minutes', 'location', 'meeting_url', 'interviewers',
                  'status', 'score', 'score_technical', 'score_communication',
                  'score_culture_fit', 'recommendation', 'notes']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'scheduled_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'interviewers': forms.CheckboxSelectMultiple(),
            'meeting_url': forms.URLInput(attrs={'placeholder': 'https://meet.google.com/...'}),
        }

    def clean_scheduled_date(self):
        scheduled_date = self.cleaned_data.get('scheduled_date')
        if scheduled_date and scheduled_date < date.today():
            raise forms.ValidationError('Ngày phỏng vấn không được trong quá khứ.')
        return scheduled_date


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

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        deadline = cleaned.get('deadline_response')
        if start and deadline and deadline < start:
            self.add_error('deadline_response', 'Hạn phản hồi phải sau ngày bắt đầu làm việc.')
        return cleaned


class TrainingCourseForm(forms.ModelForm):
    class Meta:
        model = TrainingCourse
        fields = ['code', 'name', 'category', 'delivery_method', 'duration_hours',
                  'description', 'learning_objectives', 'prerequisites',
                  'is_mandatory', 'passing_score', 'provider', 'cost_per_person',
                  'certificate_validity_months', 'target_departments', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'learning_objectives': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Mỗi dòng 1 mục tiêu'}),
            'prerequisites': forms.Textarea(attrs={'rows': 2}),
            'target_departments': forms.CheckboxSelectMultiple(),
        }


class TrainingSessionForm(forms.ModelForm):
    class Meta:
        model = TrainingSession
        fields = ['course', 'session_code', 'trainer_name', 'trainer_employee',
                  'location', 'online_meeting_url', 'start_date', 'end_date',
                  'max_participants', 'materials_file', 'status', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'online_meeting_url': forms.URLInput(attrs={'placeholder': 'https://zoom.us/j/...'}),
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

    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score is not None and not (0 <= score <= 100):
            raise forms.ValidationError('Điểm phải từ 0 đến 100.')
        return score


class EnrollmentAddForm(forms.Form):
    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(status__in=[
            'dang_lam', 'thu_viec', 'thuc_tap_sinh'
        ]).select_related('department').order_by('full_name'),
        widget=forms.CheckboxSelectMultiple(),
        label='Chọn nhân viên',
    )


class TrainingNeedForm(forms.ModelForm):
    class Meta:
        model = TrainingNeedAssessment
        fields = ['employee', 'course', 'course_name_free', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Lý do cần đào tạo, kỹ năng cần nâng cao...'}),
            'course_name_free': forms.TextInput(attrs={'placeholder': 'Tên khóa học nếu chưa có trong danh mục'}),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('course') and not cleaned.get('course_name_free'):
            raise forms.ValidationError('Phải chọn khóa học có sẵn hoặc nhập tên khóa học mới.')
        return cleaned


class TrainingNeedReviewForm(forms.ModelForm):
    class Meta:
        model = TrainingNeedAssessment
        fields = ['status', 'review_note']
        widgets = {
            'review_note': forms.Textarea(attrs={'rows': 2}),
        }


class EmployeeTrainingPlanForm(forms.ModelForm):
    class Meta:
        model = EmployeeTrainingPlan
        fields = ['employee', 'course', 'year', 'deadline', 'notes']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < date.today():
            raise forms.ValidationError('Hạn hoàn thành không được trong quá khứ.')
        return deadline


class PlanRequestForm(forms.ModelForm):
    """Nhân viên tự đề xuất kế hoạch học — không cần chọn employee (lấy từ user hiện tại)."""
    class Meta:
        model = EmployeeTrainingPlan
        fields = ['course', 'year', 'deadline', 'notes']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Lý do muốn học khóa này...'}),
        }

    def clean_year(self):
        year = self.cleaned_data.get('year')
        if year and year < date.today().year:
            raise forms.ValidationError('Năm kế hoạch không được nhỏ hơn năm hiện tại.')
        return year

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < date.today():
            raise forms.ValidationError('Hạn hoàn thành không được trong quá khứ.')
        return deadline


class PlanApproveForm(forms.Form):
    approval_note = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ghi chú (không bắt buộc)'}),
        required=False,
        label='Ghi chú',
    )


class PlanRejectForm(forms.Form):
    approval_note = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Lý do từ chối...'}),
        required=True,
        label='Lý do từ chối',
        error_messages={'required': 'Phải nhập lý do từ chối.'},
    )


class JobApproveForm(forms.Form):
    approval_note = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ghi chú (không bắt buộc)'}),
        required=False,
        label='Ghi chú',
    )


class JobRejectForm(forms.Form):
    approval_note = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Lý do từ chối...'}),
        required=True,
        label='Lý do từ chối',
        error_messages={'required': 'Phải nhập lý do từ chối.'},
    )


class ApplicantConvertForm(forms.Form):
    """Form chuyển ứng viên thành nhân viên — thay thế validation thủ công trong view."""
    employee_code = forms.CharField(
        max_length=20, label='Mã nhân viên',
        widget=forms.TextInput(attrs={'placeholder': 'VD: NV25001'}),
    )
    position = forms.CharField(
        max_length=200, label='Chức vụ',
        widget=forms.TextInput(attrs={'placeholder': 'VD: Nhân viên kinh doanh'}),
    )
    salary = forms.DecimalField(
        max_digits=15, decimal_places=0, min_value=0, label='Lương cơ bản',
        widget=forms.NumberInput(attrs={'placeholder': '0'}),
    )
    hire_date = forms.DateField(
        label='Ngày vào làm',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def __init__(self, *args, applicant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.applicant = applicant

    def clean_employee_code(self):
        code = self.cleaned_data['employee_code'].strip().upper()
        if Employee.objects.filter(employee_code=code).exists():
            raise ValidationError(f'Mã nhân viên "{code}" đã tồn tại.')
        return code

    def clean(self):
        cleaned = super().clean()
        if self.applicant and Employee.objects.filter(email=self.applicant.email).exists():
            raise ValidationError(
                f'Email "{self.applicant.email}" đã tồn tại trong hệ thống nhân viên.'
            )
        return cleaned
