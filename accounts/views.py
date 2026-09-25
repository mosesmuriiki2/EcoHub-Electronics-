from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import User
from .forms import StaffCreationForm, StaffEditForm
from .decorators import admin_required


def user_logout(request):
    """Log out the current user and redirect to login."""
    auth_logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('accounts:login')


@admin_required
def user_list(request):
    """Admin-only list of all shop staff members with search and role filter."""
    query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()
    status_filter = request.GET.get('status', '').strip()

    users = User.objects.all().order_by('-date_joined')

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    if role_filter in [User.Role.ADMIN, User.Role.CASHIER]:
        users = users.filter(role=role_filter)

    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    total_count = User.objects.count()
    admin_count = User.objects.filter(role=User.Role.ADMIN).count()
    cashier_count = User.objects.filter(role=User.Role.CASHIER).count()

    context = {
        'users': users,
        'query': query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'total_count': total_count,
        'admin_count': admin_count,
        'cashier_count': cashier_count,
    }
    return render(request, 'accounts/user_list.html', context)


@admin_required
def user_create(request):
    """Admin-only view to create a new staff member."""
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Staff member '{user.username}' ({user.get_role_display()}) created successfully.")
            return redirect('accounts:user_list')
    else:
        form = StaffCreationForm()

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': 'Add New Staff Member',
        'is_edit': False,
    })


@admin_required
def user_edit(request, pk):
    """Admin-only view to edit staff member details."""
    target_user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = StaffEditForm(request.POST, instance=target_user)
        if form.is_valid():
            # If current logged in admin is editing themselves, ensure they don't deactivate themselves
            if target_user == request.user and not form.cleaned_data.get('is_active'):
                messages.error(request, "You cannot deactivate your own account.")
                return render(request, 'accounts/user_form.html', {
                    'form': form,
                    'title': f'Edit Staff: {target_user.username}',
                    'is_edit': True,
                    'target_user': target_user,
                })

            user = form.save()
            messages.success(request, f"Staff member '{user.username}' updated successfully.")
            return redirect('accounts:user_list')
    else:
        form = StaffEditForm(instance=target_user)

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': f'Edit Staff: {target_user.username}',
        'is_edit': True,
        'target_user': target_user,
    })


@admin_required
@require_POST
def user_toggle_status(request, pk):
    """Admin-only view to activate or deactivate a staff member."""
    target_user = get_object_or_404(User, pk=pk)

    if target_user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('accounts:user_list')

    target_user.is_active = not target_user.is_active
    target_user.save()

    status_str = "activated" if target_user.is_active else "deactivated"
    messages.success(request, f"Staff member '{target_user.username}' has been {status_str}.")
    return redirect('accounts:user_list')
