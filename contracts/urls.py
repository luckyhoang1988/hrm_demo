from django.urls import path
from . import views

app_name = 'contracts'

urlpatterns = [
    path('',                    views.contract_list,         name='contract_list'),
    path('create/',             views.contract_create,       name='contract_create'),
    path('<int:pk>/',           views.contract_detail,       name='contract_detail'),
    path('<int:pk>/edit/',      views.contract_update,       name='contract_update'),
    path('<int:pk>/delete/',    views.contract_delete,       name='contract_delete'),
    path('<int:pk>/renew/',     views.contract_renew,        name='contract_renew'),
    path('<int:pk>/terminate/', views.contract_terminate,    name='contract_terminate'),
    path('<int:pk>/print/',     views.contract_print,        name='contract_print'),
    path('dashboard/',                views.contract_dashboard,               name='contract_dashboard'),
    path('dashboard/export/excel/',   views.contract_dashboard_export_excel,  name='contract_dashboard_export_excel'),
    path('export/excel/',             views.contract_export_excel,            name='contract_export_excel'),
]
