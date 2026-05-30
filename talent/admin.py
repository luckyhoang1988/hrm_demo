from django.contrib import admin
from .models import (
    JobPosition, Applicant, Interview, JobOffer,
    TrainingCourse, TrainingSession, TrainingEnrollment, TrainingCertificate,
    ApplicantStageHistory, TrainingNeedAssessment, EmployeeTrainingPlan,
)


@admin.register(JobPosition)
class JobPositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'status', 'approval_status', 'employment_type', 'open_date', 'close_date']
    list_filter = ['status', 'approval_status', 'employment_type', 'department', 'priority']
    search_fields = ['title', 'location']
    date_hierarchy = 'open_date'


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'job_position', 'stage', 'source', 'applied_at']
    list_filter = ['stage', 'source', 'job_position__department']
    search_fields = ['full_name', 'email', 'phone']
    date_hierarchy = 'applied_at'


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'round_number', 'interview_type', 'scheduled_date', 'status', 'recommendation']
    list_filter = ['status', 'interview_type', 'recommendation']
    search_fields = ['applicant__full_name']


@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'offered_salary', 'start_date', 'deadline_response', 'status']
    list_filter = ['status']
    search_fields = ['applicant__full_name']


@admin.register(TrainingCourse)
class TrainingCourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'delivery_method', 'is_mandatory', 'passing_score', 'is_active']
    list_filter = ['category', 'delivery_method', 'is_mandatory', 'is_active']
    search_fields = ['code', 'name', 'provider']
    filter_horizontal = ['target_departments']


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ['session_code', 'course', 'trainer_name', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'course']
    search_fields = ['session_code', 'trainer_name', 'course__name']
    date_hierarchy = 'start_date'


@admin.register(TrainingEnrollment)
class TrainingEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'session', 'status', 'score', 'result', 'enrolled_at']
    list_filter = ['status', 'result', 'session__course']
    search_fields = ['employee__full_name', 'session__session_code']


@admin.register(TrainingCertificate)
class TrainingCertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_number', 'employee', 'course', 'issued_date', 'expiry_date', 'is_active']
    list_filter = ['is_active', 'course']
    search_fields = ['certificate_number', 'employee__full_name', 'course__name']
    date_hierarchy = 'issued_date'


@admin.register(ApplicantStageHistory)
class ApplicantStageHistoryAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'from_stage', 'to_stage', 'changed_by', 'changed_at']
    list_filter = ['from_stage', 'to_stage']
    search_fields = ['applicant__full_name']
    date_hierarchy = 'changed_at'


@admin.register(TrainingNeedAssessment)
class TrainingNeedAssessmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'course', 'course_name_free', 'status', 'requested_by', 'requested_at']
    list_filter = ['status']
    search_fields = ['employee__full_name', 'course__name', 'course_name_free']


@admin.register(EmployeeTrainingPlan)
class EmployeeTrainingPlanAdmin(admin.ModelAdmin):
    list_display = ['employee', 'course', 'year', 'deadline', 'status', 'approval_status', 'is_employee_request']
    list_filter = ['status', 'approval_status', 'year', 'is_employee_request']
    search_fields = ['employee__full_name', 'course__name']
