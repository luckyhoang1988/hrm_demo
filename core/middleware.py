import threading

_thread_local = threading.local()


def get_current_user():
    """Trả về user đang thực hiện request trong thread hiện tại."""
    return getattr(_thread_local, 'user', None)


class CurrentUserMiddleware:
    """Lưu request.user vào thread local để BaseModel auto-fill created_by/updated_by."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            _thread_local.user = request.user
        else:
            _thread_local.user = None
        return self.get_response(request)
