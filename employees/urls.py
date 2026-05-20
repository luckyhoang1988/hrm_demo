from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('create/', views.employee_create, name='employee_create'),
    path('edit/<int:pk>/', views.employee_update, name='employee_update'),
    path('delete/<int:pk>/', views.employee_delete, name='employee_delete'),
    path('terminate/<int:pk>/', views.employee_terminate, name='employee_terminate'),
    path('reactivate/<int:pk>/', views.employee_reactivate, name='employee_reactivate'),
    path('change-status/<int:pk>/', views.employee_change_status, name='employee_change_status'),
    path('<int:pk>/', views.employee_detail, name='employee_detail'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/export-status/', views.export_status_excel, name='export_status_excel'),
    path('change-password/', views.change_password, name='change_password'),
    path('check-code/', views.check_employee_code, name='check_employee_code'),
    path('import/', views.import_excel, name='import_excel'),
    path('import/template/', views.download_import_template, name='download_import_template'),
]
