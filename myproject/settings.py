from pathlib import Path
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_celery_beat',
    'django_celery_results',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',
    'api',
    'core',
    'departments',
    'employees',
    'contracts',
    'system_settings',
    'talent',
    'attendance',
    'payroll',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.CurrentUserMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://localhost').split(',')

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Tự động logout sau 15 phút không có request HTTP nào (server-side bảo vệ)
SESSION_COOKIE_AGE = 900          # 15 phút tính bằng giây
SESSION_SAVE_EVERY_REQUEST = True  # Reset timer mỗi lần có request mới

# ── DJANGO REST FRAMEWORK ────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'HRM API',
    'DESCRIPTION': 'API quản lý nhân sự — Employees, Attendance, Payroll',
    'VERSION': '1.0.0',
}

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# ── CELERY ───────────────────────────────────────────────────────────────────
# Docker: dùng Redis broker (service "redis" trong docker-compose)
# Dev local: đặt CELERY_BROKER_URL=filesystem:// trong .env để dùng filesystem
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://redis:6379/0')
if CELERY_BROKER_URL == 'filesystem://':
    import os as _os
    _CELERY_DATA_DIR = str(BASE_DIR / 'celery_data')
    _os.makedirs(_CELERY_DATA_DIR, exist_ok=True)
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        'data_folder_in': _CELERY_DATA_DIR,
        'data_folder_out': _CELERY_DATA_DIR,
    }
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'default'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Cấu hình periodic tasks (chạy tự động theo lịch)
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    # Kiểm tra hợp đồng sắp hết hạn — chạy lúc 8:00 sáng mỗi ngày
    'check-contract-expiry': {
        'task': 'core.tasks.check_contract_expiry',
        'schedule': crontab(hour=8, minute=0),
    },
    # Kiểm tra trạng thái nhân viên sắp hết hạn — chạy lúc 8:05 sáng
    'check-employee-status-expiry': {
        'task': 'core.tasks.check_employee_status_expiry',
        'schedule': crontab(hour=8, minute=5),
    },
    # Tự động chuyển nhân viên nghỉ việc theo lịch — chạy lúc 0:05 sáng
    'auto-terminate-employees': {
        'task': 'core.tasks.auto_terminate_employees_task',
        'schedule': crontab(hour=0, minute=5),
    },
}

# ── LOGGING (ra stdout để Docker logs đọc được) ───────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('DJANGO_LOG_LEVEL', default='WARNING'),
            'propagate': False,
        },
    },
}
