from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from employees.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('employees/', include('employees.urls')),
    path('contracts/', include('contracts.urls')),
    path('settings/', include('system_settings.urls')),
    path('talent/', include('talent.urls')),
    path('attendance/', include('attendance.urls')),
    path('payroll/', include('payroll.urls')),
    path('core/', include('core.urls')),
    # REST API
    path('api/', include('api.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
    path('login/', auth_views.LoginView.as_view(template_name='employees/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
