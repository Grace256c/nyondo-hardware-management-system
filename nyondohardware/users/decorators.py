from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def sales_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('users:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('users:login')
        role = request.user.userprofile.role
        if role not in ['store_manager', 'admin']:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('users:login')
        role = request.user.userprofile.role
        if role != 'admin':
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper