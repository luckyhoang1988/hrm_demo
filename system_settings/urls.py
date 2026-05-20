from django.urls import path
from . import views

app_name = 'system_settings'

urlpatterns = [
    path('', views.settings_home, name='settings_home'),

    # Phòng ban
    path('departments/', views.department_manage, name='department_manage'),
    path('departments/edit/<int:pk>/', views.department_update, name='department_update'),
    path('departments/delete/<int:pk>/', views.department_delete, name='department_delete'),

    # Nhóm bộ phận (EmployeeGroup)
    path('employee-groups/', views.group_list, name='group_list'),
    path('employee-groups/create/', views.group_create, name='group_create'),
    path('employee-groups/edit/<int:pk>/', views.group_update, name='group_update'),
    path('employee-groups/delete/<int:pk>/', views.group_delete, name='group_delete'),

    # Tài khoản người dùng
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/delete/<int:pk>/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/reset-password/', views.admin_reset_password, name='admin_reset_password'),
    path('users/<int:pk>/link-employee/', views.user_link_employee, name='user_link_employee'),

    # Nhóm người dùng (StaffGroup)
    path('staff-groups/create/', views.staff_group_create, name='staff_group_create'),
    path('staff-groups/<int:pk>/edit/', views.staff_group_update, name='staff_group_update'),
    path('staff-groups/<int:pk>/delete/', views.staff_group_delete, name='staff_group_delete'),

    # Phân quyền
    path('permissions/', views.permission_manage, name='permission_manage'),

    # Nhật ký hoạt động
    path('activity-log/', views.activity_log, name='activity_log'),

    # Toggle trạng thái app
    path('toggle-app/<str:app_name>/', views.toggle_app, name='toggle_app'),
]
