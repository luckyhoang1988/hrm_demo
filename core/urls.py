from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', views.mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.mark_all_read, name='notification_mark_all_read'),
]
