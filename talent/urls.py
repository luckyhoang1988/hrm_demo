from django.urls import path
from . import views

app_name = 'talent'

urlpatterns = [
    # Home
    path('', views.talent_home, name='talent_home'),

    # Job Positions
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/edit/', views.job_update, name='job_update'),
    path('jobs/<int:pk>/delete/', views.job_delete, name='job_delete'),

    # Applicants
    path('applicants/', views.applicant_list, name='applicant_list'),
    path('kanban/', views.applicant_kanban, name='applicant_kanban'),
    path('applicants/create/', views.applicant_create, name='applicant_create'),
    path('applicants/generate-code/', views.generate_employee_code, name='generate_employee_code'),
    path('applicants/<int:pk>/', views.applicant_detail, name='applicant_detail'),
    path('applicants/<int:pk>/edit/', views.applicant_update, name='applicant_update'),
    path('applicants/<int:pk>/delete/', views.applicant_delete, name='applicant_delete'),
    path('applicants/<int:pk>/stage/', views.applicant_change_stage, name='applicant_change_stage'),
    path('applicants/<int:pk>/convert/', views.applicant_convert, name='applicant_convert'),

    # Interviews
    path('applicants/<int:applicant_pk>/interview/create/', views.interview_create, name='interview_create'),
    path('interviews/<int:pk>/edit/', views.interview_update, name='interview_update'),
    path('interviews/<int:pk>/delete/', views.interview_delete, name='interview_delete'),

    # Offers
    path('applicants/<int:applicant_pk>/offer/create/', views.offer_create, name='offer_create'),
    path('offers/<int:pk>/edit/', views.offer_update, name='offer_update'),

    # Recruitment Dashboard & Export
    path('recruitment/dashboard/', views.recruitment_dashboard, name='recruitment_dashboard'),
    path('recruitment/export/', views.recruitment_export, name='recruitment_export'),

    # Training Courses
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/edit/', views.course_update, name='course_update'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),

    # Training Sessions
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/', views.session_create, name='session_create'),
    path('sessions/<int:pk>/', views.session_detail, name='session_detail'),
    path('sessions/<int:pk>/edit/', views.session_update, name='session_update'),
    path('sessions/<int:pk>/delete/', views.session_delete, name='session_delete'),

    # Enrollments
    path('sessions/<int:session_pk>/enroll/', views.enrollment_add, name='enrollment_add'),
    path('sessions/<int:session_pk>/bulk-score/', views.bulk_score_update, name='bulk_score_update'),
    path('enrollments/<int:pk>/update/', views.enrollment_update, name='enrollment_update'),
    path('enrollments/<int:pk>/delete/', views.enrollment_delete, name='enrollment_delete'),

    # Certificates
    path('certificates/', views.certificate_list, name='certificate_list'),
    path('certificates/<int:pk>/', views.certificate_detail, name='certificate_detail'),
    path('certificates/<int:pk>/print/', views.certificate_print, name='certificate_print'),

    # Training Dashboard & Export
    path('training/dashboard/', views.training_dashboard, name='training_dashboard'),
    path('training/export/', views.training_export, name='training_export'),
]
