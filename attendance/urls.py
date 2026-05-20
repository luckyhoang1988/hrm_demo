from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # ── Trang chủ ────────────────────────────────────────
    path('', views.attendance_home, name='attendance_home'),

    # ── Ca làm việc ──────────────────────────────────────
    path('shifts/', views.shift_list, name='shift_list'),
    path('shifts/create/', views.shift_create, name='shift_create'),
    path('shifts/<int:pk>/edit/', views.shift_update, name='shift_update'),
    path('shifts/<int:pk>/delete/', views.shift_delete, name='shift_delete'),

    # ── Ngày lễ ──────────────────────────────────────────
    path('holidays/', views.holiday_manage, name='holiday_manage'),
    path('holidays/<int:pk>/delete/', views.holiday_delete, name='holiday_delete'),

    # ── Bản ghi chấm công ────────────────────────────────
    path('records/', views.attendance_list, name='attendance_list'),
    path('records/create/', views.attendance_create, name='attendance_create'),
    path('records/<int:pk>/edit/', views.attendance_update, name='attendance_update'),
    path('records/<int:pk>/delete/', views.attendance_delete, name='attendance_delete'),
    path('records/import/', views.attendance_import, name='attendance_import'),
    path('records/export/', views.attendance_export, name='attendance_export'),

    # ── Dashboard ────────────────────────────────────────
    path('dashboard/', views.attendance_dashboard, name='attendance_dashboard'),
    path('dashboard/export/', views.attendance_dashboard_export, name='attendance_dashboard_export'),

    # ── Loại nghỉ phép ───────────────────────────────────
    path('leave-types/', views.leave_type_list, name='leave_type_list'),
    path('leave-types/create/', views.leave_type_create, name='leave_type_create'),
    path('leave-types/<int:pk>/edit/', views.leave_type_update, name='leave_type_update'),
    path('leave-types/<int:pk>/delete/', views.leave_type_delete, name='leave_type_delete'),

    # ── Chính sách phép năm ──────────────────────────────
    path('policy/', views.leave_policy_manage, name='leave_policy_manage'),

    # ── Đơn xin nghỉ ─────────────────────────────────────
    path('leaves/', views.leave_request_list, name='leave_request_list'),
    path('leaves/create/', views.leave_request_create, name='leave_request_create'),
    path('leaves/<int:pk>/', views.leave_request_detail, name='leave_request_detail'),
    path('leaves/<int:pk>/cancel/', views.leave_request_cancel, name='leave_request_cancel'),
    path('leaves/<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    path('leaves/<int:pk>/reject/', views.leave_reject, name='leave_reject'),

    # ── Số dư ngày phép ──────────────────────────────────
    path('balance/', views.leave_balance_list, name='leave_balance_list'),
    path('balance/init/', views.leave_balance_init, name='leave_balance_init'),
    path('balance/<int:pk>/edit/', views.leave_balance_edit, name='leave_balance_edit'),
]
