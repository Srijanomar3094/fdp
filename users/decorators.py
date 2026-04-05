from functools import wraps
from django.http import JsonResponse


def login_required_json(view_func):
    """Require authenticated session; return 401 JSON instead of redirect."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {'error': 'Authentication required', 'code': 'UNAUTHENTICATED'},
                status=401,
            )
        return view_func(request, *args, **kwargs)

    return wrapper


def role_required(*roles):
    """
    Require the user to have one of the specified roles.
    Also enforces authentication — no separate @login_required_json needed.

    Usage:
        @role_required('admin')
        @role_required('admin', 'analyst')
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse(
                    {'error': 'Authentication required', 'code': 'UNAUTHENTICATED'},
                    status=401,
                )
            if request.user.role not in roles:
                return JsonResponse(
                    {
                        'error': 'You do not have permission to perform this action.',
                        'code': 'FORBIDDEN',
                        'required_roles': list(roles),
                        'your_role': request.user.role,
                    },
                    status=403,
                )
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
