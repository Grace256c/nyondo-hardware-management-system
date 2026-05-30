from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile
from .forms import UserRegistrationForm, UserEditForm, CustomPasswordChangeForm, ProfileUpdateForm
from .decorators import admin_required, sales_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # Backend validation
        if not username:
            messages.error(request, 'Username is required.')
            return render(request, 'users/login.html')

        if not password:
            messages.error(request, 'Password is required.')
            return render(request, 'users/login.html')

        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters.')
            return render(request, 'users/login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, 'Your account has been deactivated. Contact the admin.')
                return render(request, 'users/login.html')
            if not user.userprofile.is_active:
                messages.error(request, 'Your account has been deactivated. Contact the admin.')
                return render(request, 'users/login.html')
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'users/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('users:login')


@admin_required
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user            = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name  = form.cleaned_data['last_name']
            user.email      = form.cleaned_data['email']
            user.save()
            user.userprofile.role  = form.cleaned_data['role']
            user.userprofile.phone = form.cleaned_data['phone']
            user.userprofile.save()
            messages.success(request, f'User {user.get_full_name()} created successfully.')
            return redirect('users:user-list')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})


@admin_required
def user_list_view(request):
    users = User.objects.all().order_by('first_name')
    return render(request, 'users/user_list.html', {'users': users})


@admin_required
def user_detail_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, 'users/user_detail.html', {'user': user})


@admin_required
def user_edit_view(request, pk):
    user    = get_object_or_404(User, pk=pk)
    profile = user.userprofile

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=profile)
        if form.is_valid():
            user.first_name = form.cleaned_data['first_name']
            user.last_name  = form.cleaned_data['last_name']
            user.email      = form.cleaned_data['email']
            user.save()
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('users:user-list')
    else:
        form = UserEditForm(instance=profile, initial={
            'first_name': user.first_name,
            'last_name' : user.last_name,
            'email'     : user.email,
        })

    return render(request, 'users/user_edit_form.html', {
        'form': form,
        'user': user,
    })


@admin_required
def user_deactivate_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.userprofile.is_active = False
        user.userprofile.save()
        user.is_active = False
        user.save()
        messages.success(request, f'{user.get_full_name()} has been deactivated.')
        return redirect('users:user-list')
    return render(request, 'users/user_confirm_deactivate.html', {'user': user})


@admin_required
def user_delete_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('users:user-list')
    return render(request, 'users/user_confirm_delete.html', {'user': user})


@sales_required
def profile_view(request):
    if request.method == 'POST':
        profile_form  = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user.userprofile
        )
        password_form = CustomPasswordChangeForm(request.user, request.POST)

        if 'update_profile' in request.POST:
            if profile_form.is_valid():
                request.user.first_name = profile_form.cleaned_data['first_name']
                request.user.last_name  = profile_form.cleaned_data['last_name']
                request.user.save()
                profile_form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('users:profile')

        elif 'change_password' in request.POST:
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully.')
                return redirect('users:profile')
    else:
        profile_form  = ProfileUpdateForm(
            instance=request.user.userprofile,
            initial={
                'first_name': request.user.first_name,
                'last_name' : request.user.last_name,
            }
        )
        password_form = CustomPasswordChangeForm(request.user)

    return render(request, 'users/profile.html', {
        'profile_form' : profile_form,
        'password_form': password_form,
    })