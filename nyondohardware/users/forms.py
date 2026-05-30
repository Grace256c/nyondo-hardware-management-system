from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import UserProfile
import re


def style_fields(form):
    for name, field in form.fields.items():
        widget_type = field.widget.__class__.__name__
        if widget_type == 'Select':
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-orange-400'
            })
        elif widget_type == 'Textarea':
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400',
                'rows' : '3'
            })
        elif widget_type == 'CheckboxInput':
            field.widget.attrs.update({
                'class': 'w-4 h-4 rounded border-gray-300 text-orange-500 focus:ring-orange-400'
            })
        elif widget_type == 'FileInput':
            field.widget.attrs.update({
                'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-orange-50 file:text-orange-600 hover:file:bg-orange-100'
            })
        else:
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400'
            })


# ── USER REGISTRATION FORM ────────────────────────────────────
class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name  = forms.CharField(max_length=50, required=True)
    email      = forms.EmailField(required=False)
    phone      = forms.CharField(max_length=20, required=True)
    role       = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES)

    class Meta:
        model  = User
        fields = [
            'username', 'first_name', 'last_name',
            'email', 'phone', 'role',
            'password1', 'password2',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['username'].widget.attrs['placeholder']   = 'e.g. grace.nakiyemba'
        self.fields['first_name'].widget.attrs['placeholder'] = 'First name'
        self.fields['last_name'].widget.attrs['placeholder']  = 'Last name'
        self.fields['email'].widget.attrs['placeholder']      = 'email@example.com (optional)'
        self.fields['phone'].widget.attrs['placeholder']      = '0712345678 or +256712345678'

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise forms.ValidationError('Username is required.')
        if len(username) < 3:
            raise forms.ValidationError('Username must be at least 3 characters.')
        if len(username) > 50:
            raise forms.ValidationError('Username cannot exceed 50 characters.')
        if not re.match(r'^[a-zA-Z0-9._\-]+$', username):
            raise forms.ValidationError(
                'Username can only contain letters, numbers, dots, underscores and hyphens.'
            )
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_first_name(self):
        name = self.cleaned_data.get('first_name', '').strip()
        if not name:
            raise forms.ValidationError('First name is required.')
        if len(name) < 2:
            raise forms.ValidationError('First name must be at least 2 characters.')
        if not re.match(r'^[A-Za-z\s\-]+$', name):
            raise forms.ValidationError('First name can only contain letters.')
        return name.title()

    def clean_last_name(self):
        name = self.cleaned_data.get('last_name', '').strip()
        if not name:
            raise forms.ValidationError('Last name is required.')
        if len(name) < 2:
            raise forms.ValidationError('Last name must be at least 2 characters.')
        if not re.match(r'^[A-Za-z\s\-]+$', name):
            raise forms.ValidationError('Last name can only contain letters.')
        return name.title()

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise forms.ValidationError('Phone number is required.')
        if not re.match(r'^(\+?256|0)[7][0-9]{8}$', phone):
            raise forms.ValidationError(
                'Enter a valid Ugandan phone number. '
                'Format: 0712345678 or +256712345678'
            )
        return phone

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if not role:
            raise forms.ValidationError('Please select a role.')
        valid_roles = [r[0] for r in UserProfile.ROLE_CHOICES]
        if role not in valid_roles:
            raise forms.ValidationError('Invalid role selected.')
        return role


# ── USER EDIT FORM ────────────────────────────────────────────
class UserEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name  = forms.CharField(max_length=50, required=True)
    email      = forms.EmailField(required=False)

    class Meta:
        model  = UserProfile
        fields = ['role', 'phone', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['first_name'].widget.attrs['placeholder'] = 'First name'
        self.fields['last_name'].widget.attrs['placeholder']  = 'Last name'
        self.fields['email'].widget.attrs['placeholder']      = 'email@example.com (optional)'
        self.fields['phone'].widget.attrs['placeholder']      = '0712345678 or +256712345678'

    def clean_first_name(self):
        name = self.cleaned_data.get('first_name', '').strip()
        if not name:
            raise forms.ValidationError('First name is required.')
        if len(name) < 2:
            raise forms.ValidationError('First name must be at least 2 characters.')
        if not re.match(r'^[A-Za-z\s\-]+$', name):
            raise forms.ValidationError('First name can only contain letters.')
        return name.title()

    def clean_last_name(self):
        name = self.cleaned_data.get('last_name', '').strip()
        if not name:
            raise forms.ValidationError('Last name is required.')
        if len(name) < 2:
            raise forms.ValidationError('Last name must be at least 2 characters.')
        if not re.match(r'^[A-Za-z\s\-]+$', name):
            raise forms.ValidationError('Last name can only contain letters.')
        return name.title()

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise forms.ValidationError('Phone number is required.')
        if not re.match(r'^(\+?256|0)[7][0-9]{8}$', phone):
            raise forms.ValidationError(
                'Enter a valid Ugandan phone number. '
                'Format: 0712345678 or +256712345678'
            )
        return phone


# ── PROFILE UPDATE FORM ───────────────────────────────────────
class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name  = forms.CharField(max_length=50, required=True)

    class Meta:
        model  = UserProfile
        fields = ['phone', 'avatar']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['first_name'].widget.attrs['placeholder'] = 'First name'
        self.fields['last_name'].widget.attrs['placeholder']  = 'Last name'
        self.fields['phone'].widget.attrs['placeholder']      = '0712345678 or +256712345678'

    def clean_first_name(self):
        name = self.cleaned_data.get('first_name', '').strip()
        if not name:
            raise forms.ValidationError('First name is required.')
        if len(name) < 2:
            raise forms.ValidationError('First name must be at least 2 characters.')
        if not re.match(r'^[A-Za-z\s\-]+$', name):
            raise forms.ValidationError('First name can only contain letters.')
        return name.title()

    def clean_last_name(self):
        name = self.cleaned_data.get('last_name', '').strip()
        if not name:
            raise forms.ValidationError('Last name is required.')
        if len(name) < 2:
            raise forms.ValidationError('Last name must be at least 2 characters.')
        if not re.match(r'^[A-Za-z\s\-]+$', name):
            raise forms.ValidationError('Last name can only contain letters.')
        return name.title()

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise forms.ValidationError('Phone number is required.')
        if not re.match(r'^(\+?256|0)[7][0-9]{8}$', phone):
            raise forms.ValidationError(
                'Enter a valid Ugandan phone number. '
                'Format: 0712345678 or +256712345678'
            )
        return phone

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Check file size — max 2MB
            if avatar.size > 2 * 1024 * 1024:
                raise forms.ValidationError(
                    'Image file too large. Maximum size is 2MB.'
                )
            # Check file type
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            import os
            ext = os.path.splitext(avatar.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError(
                    'Invalid file type. Please upload a JPG, PNG or WebP image.'
                )
        return avatar


# ── PASSWORD CHANGE FORM ──────────────────────────────────────
class CustomPasswordChangeForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['old_password'].widget.attrs['placeholder']  = 'Your current password'
        self.fields['new_password1'].widget.attrs['placeholder'] = 'New password'
        self.fields['new_password2'].widget.attrs['placeholder'] = 'Confirm new password'

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1', '')
        if len(password) < 8:
            raise forms.ValidationError(
                'Password must be at least 8 characters long.'
            )
        if password.isdigit():
            raise forms.ValidationError(
                'Password cannot be entirely numeric.'
            )
        if password.lower() == password:
            raise forms.ValidationError(
                'Password must contain at least one uppercase letter.'
            )
        return password