from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def admin_required(view_func):
    """
    Decorator to ensure the logged-in user has the Admin role or is a superuser.
    Non-admin users are redirected to the home dashboard with a warning message.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('accounts:login')}?next={request.path}")
        
        if not request.user.is_admin_role:
            messages.error(request, "Access denied. Administrator privileges are required to view that page.")
            return redirect('home')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view
