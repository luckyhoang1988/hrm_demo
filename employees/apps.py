from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    name = 'employees'

    def ready(self):
        import employees.signals  # noqa: F401 — kết nối signal login/logout
