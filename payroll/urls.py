from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    # ── Phiếu lương ──────────────────────────────────────
    path('',                          views.payslip_list,         name='payslip_list'),
    path('bulk-create/',              views.payslip_bulk_create,  name='payslip_bulk_create'),
    path('<int:pk>/',                 views.payslip_detail,       name='payslip_detail'),
    path('<int:pk>/edit/',            views.payslip_update,       name='payslip_update'),
    path('<int:pk>/delete/',          views.payslip_delete,       name='payslip_delete'),
    path('<int:pk>/print/',           views.payslip_print,        name='payslip_print'),

    # ── Cấu hình toàn hệ thống (fallback) ────────────────
    path('config/',                   views.payroll_config,       name='payroll_config'),

    # ── Cấu hình bảo hiểm theo năm + bậc thuế TNCN ───────
    path('insurance/',                views.insurance_config_list,   name='insurance_config_list'),
    path('insurance/create/',         views.insurance_config_create, name='insurance_config_create'),
    path('insurance/<int:pk>/delete/', views.insurance_config_delete, name='insurance_config_delete'),

    # ── Cấu hình lương riêng từng NV ─────────────────────
    path('salary-config/',            views.salary_config_list,   name='salary_config_list'),
    path('salary-config/create/',     views.salary_config_create, name='salary_config_create'),
    path('salary-config/<int:pk>/edit/',   views.salary_config_update, name='salary_config_update'),
    path('salary-config/<int:pk>/delete/', views.salary_config_delete, name='salary_config_delete'),

    # ── Bản ghi tăng ca (OT) ─────────────────────────────
    path('ot/',                       views.ot_list,    name='ot_list'),
    path('ot/create/',                views.ot_create,  name='ot_create'),
    path('ot/<int:pk>/approve/',      views.ot_approve, name='ot_approve'),
    path('ot/<int:pk>/reject/',       views.ot_reject,  name='ot_reject'),
    path('ot/<int:pk>/delete/',       views.ot_delete,  name='ot_delete'),
]
