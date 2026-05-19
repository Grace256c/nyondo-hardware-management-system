from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile
from .forms import UserRegistrationForm, UserEditForm, CustomPasswordChangeForm
from .decorators import admin_required, sales_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        from django.contrib.auth import authenticate
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
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
            user = form.save(commit=False)
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
    user = get_object_or_404(User, pk=pk)
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

    return render(request, 'users/user_edit_form.html', {'form': form, 'user': user})


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
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('users:profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'users/profile.html', {'form': form})