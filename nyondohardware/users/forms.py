from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import UserProfile


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name  = forms.CharField(max_length=50, required=True)
    email      = forms.EmailField(required=True)
    phone      = forms.CharField(max_length=20, required=True)
    role       = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES)

    class Meta:
        model  = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
            'role',
            'password1',
            'password2',
        ]

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        import re
        if not re.match(r'^(\+?256|0)[7][0-9]{8}$', phone):
            raise forms.ValidationError('Enter a valid Ugandan phone number.')
        return phone


class UserEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name  = forms.CharField(max_length=50, required=True)
    email      = forms.EmailField(required=True)

    class Meta:
        model  = UserProfile
        fields = ['role', 'phone', 'is_active']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        import re
        if not re.match(r'^(\+?256|0)[7][0-9]{8}$', phone):
            raise forms.ValidationError('Enter a valid Ugandan phone number.')
        return phone


class CustomPasswordChangeForm(PasswordChangeForm):
    pass