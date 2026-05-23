from django import forms
from .models import SchemeCustomer, Deposit, Pickup
from .utils import get_customer_balance, get_scheme_products
import re


def style_fields(form):
    for name, field in form.fields.items():
        widget_type = field.widget.__class__.__name__
        if widget_type == 'Select':
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white cursor-pointer'
            })
        elif widget_type == 'Textarea':
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm',
                'rows': '3'
            })
        else:
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'
            })


class SchemeCustomerRegistrationForm(forms.ModelForm):

    class Meta:
        model  = SchemeCustomer
        fields = [
            'full_name', 'nin', 'phone',
            'employer', 'employer_address'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_nin(self):
        nin = self.cleaned_data.get('nin')
        if not re.match(r'^[A-Z0-9]{14}$', nin):
            raise forms.ValidationError(
                'NIN must be exactly 14 uppercase letters and numbers.'
            )
        if SchemeCustomer.objects.filter(nin=nin).exclude(
                pk=self.instance.pk).exists():
            raise forms.ValidationError('This NIN is already registered.')
        return nin

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^(\+?256|0)[7][0-9]{8}$', phone):
            raise forms.ValidationError('Enter a valid Ugandan phone number.')
        return phone


class SchemeCustomerEditForm(forms.ModelForm):

    class Meta:
        model  = SchemeCustomer
        fields = ['phone', 'employer', 'employer_address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^(\+?256|0)[7][0-9]{8}$', phone):
            raise forms.ValidationError('Enter a valid Ugandan phone number.')
        return phone


class DepositForm(forms.ModelForm):

    class Meta:
        model   = Deposit
        fields  = ['amount', 'payment_date', 'payment_method']
        widgets = {
            'payment_date': forms.DateInput(
                attrs={'type': 'date',
                       'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        # Re-apply date input after style_fields
        self.fields['payment_date'].widget = forms.DateInput(
            attrs={'type': 'date',
                   'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}
        )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount


class PickupForm(forms.ModelForm):

    class Meta:
        model   = Pickup
        fields  = ['product', 'quantity', 'unit_price', 'pickup_date']
        widgets = {
            'pickup_date': forms.DateInput(
                attrs={'type': 'date',
                       'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.customer = kwargs.pop('customer', None)
        super().__init__(*args, **kwargs)
        style_fields(self)
        # Re-apply date input after style_fields
        self.fields['pickup_date'].widget = forms.DateInput(
            attrs={'type': 'date',
                   'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm'}
        )
        self.fields['product'].queryset = get_scheme_products()

    def clean(self):
        cleaned_data = super().clean()
        quantity     = cleaned_data.get('quantity')
        unit_price   = cleaned_data.get('unit_price')

        if quantity and unit_price and self.customer:
            total_value = quantity * unit_price
            balance     = get_customer_balance(self.customer)
            if total_value > balance:
                raise forms.ValidationError(
                    f'Total value (UGX {total_value:,.0f}) exceeds '
                    f'customer balance (UGX {balance:,.0f}).'
                )
        return cleaned_data