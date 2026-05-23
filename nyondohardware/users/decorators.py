from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def sales_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not hasattr(request.user, 'userprofile'):
            raise PermissionDenied
        if request.user.userprofile.role not in ['sales_attendant', 'store_manager', 'admin']:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not hasattr(request.user, 'userprofile'):
            raise PermissionDenied
        if request.user.userprofile.role not in ['store_manager', 'admin']:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not hasattr(request.user, 'userprofile'):
            raise PermissionDenied
        if request.user.userprofile.role != 'admin':
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper