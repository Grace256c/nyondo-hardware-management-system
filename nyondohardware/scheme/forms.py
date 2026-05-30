from django import forms
from .models import SchemeCustomer, Deposit, Pickup
from .utils import get_customer_balance, get_scheme_products
import re


def style_fields(form):
    for name, field in form.fields.items():
        widget_type = field.widget.__class__.__name__
        if widget_type == 'Select':
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-transparent'
            })
        elif widget_type == 'Textarea':
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-transparent',
                'rows' : '3'
            })
        elif widget_type == 'DateInput':
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-transparent',
                'type' : 'date'
            })
        else:
            field.widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-transparent'
            })


# ── SCHEME CUSTOMER REGISTRATION FORM ─────────────────────────
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
        self.fields['full_name'].widget.attrs['placeholder']        = 'As it appears on National ID'
        self.fields['nin'].widget.attrs['placeholder']              = 'e.g. CM12345678901A'
        self.fields['phone'].widget.attrs['placeholder']            = '0712345678 or +256712345678'
        self.fields['employer'].widget.attrs['placeholder']         = 'e.g. Ministry of Education'
        self.fields['employer_address'].widget.attrs['placeholder'] = 'Employer physical address'
        self.fields['employer'].required                            = False
        self.fields['employer_address'].required                    = False

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '').strip()
        if not name:
            raise forms.ValidationError('Full name is required.')
        if len(name) < 3:
            raise forms.ValidationError('Full name must be at least 3 characters.')
        if len(name) > 100:
            raise forms.ValidationError('Full name cannot exceed 100 characters.')
        # Must contain at least two words (first and last name)
        if len(name.split()) < 2:
            raise forms.ValidationError(
                'Please enter both first and last name as they appear on your National ID.'
            )
        # Only letters and spaces
        if not re.match(r'^[A-Za-z\s\-]+$', name):
            raise forms.ValidationError(
                'Full name can only contain letters, spaces and hyphens.'
            )
        return name

    def clean_nin(self):
        nin = self.cleaned_data.get('nin', '').strip().upper()
        if not nin:
            raise forms.ValidationError('NIN is required.')
        if not re.match(r'^[A-Z0-9]{14}$', nin):
            raise forms.ValidationError(
                'NIN must be exactly 14 uppercase letters and numbers. '
                'Example: CM12345678901A'
            )
        if SchemeCustomer.objects.filter(nin=nin).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(
                'A customer with this NIN is already registered.'
            )
        return nin

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

    def clean_employer(self):
        employer = self.cleaned_data.get('employer', '').strip()
        if employer and len(employer) < 2:
            raise forms.ValidationError('Employer name must be at least 2 characters.')
        return employer


# ── SCHEME CUSTOMER EDIT FORM ─────────────────────────────────
class SchemeCustomerEditForm(forms.ModelForm):

    class Meta:
        model  = SchemeCustomer
        fields = ['phone', 'employer', 'employer_address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['phone'].widget.attrs['placeholder']            = '0712345678 or +256712345678'
        self.fields['employer'].widget.attrs['placeholder']         = 'e.g. Ministry of Education'
        self.fields['employer_address'].widget.attrs['placeholder'] = 'Employer physical address'
        self.fields['employer'].required                            = False
        self.fields['employer_address'].required                    = False

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

    def clean_employer(self):
        employer = self.cleaned_data.get('employer', '').strip()
        if employer and len(employer) < 2:
            raise forms.ValidationError('Employer name must be at least 2 characters.')
        return employer


# ── DEPOSIT FORM ──────────────────────────────────────────────
class DepositForm(forms.ModelForm):

    class Meta:
        model   = Deposit
        fields  = ['amount', 'payment_date', 'payment_method']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['amount'].widget.attrs['placeholder'] = 'e.g. 500000'
        self.fields['payment_date'].widget = forms.DateInput(
            attrs={
                'type' : 'date',
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400'
            }
        )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None:
            raise forms.ValidationError('Deposit amount is required.')
        if amount <= 0:
            raise forms.ValidationError('Deposit amount must be greater than zero.')
        if amount < 1000:
            raise forms.ValidationError(
                'Minimum deposit amount is UGX 1,000.'
            )
        if amount > 100000000:
            raise forms.ValidationError(
                'Deposit amount seems too large. Please verify.'
            )
        return amount

    def clean_payment_date(self):
        from django.utils import timezone
        date = self.cleaned_data.get('payment_date')
        if not date:
            raise forms.ValidationError('Payment date is required.')
        if date > timezone.now().date():
            raise forms.ValidationError('Payment date cannot be in the future.')
        return date

    def clean_payment_method(self):
        method = self.cleaned_data.get('payment_method')
        if not method:
            raise forms.ValidationError('Please select a payment method.')
        return method


# ── PICKUP FORM ───────────────────────────────────────────────
class PickupForm(forms.ModelForm):

    class Meta:
        model   = Pickup
        fields  = ['product', 'quantity', 'unit_price', 'pickup_date']
        widgets = {
            'pickup_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.customer = kwargs.pop('customer', None)
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['quantity'].widget.attrs['placeholder']   = 'e.g. 10'
        self.fields['unit_price'].widget.attrs['placeholder'] = 'Auto-filled from product'
        self.fields['product'].queryset                       = get_scheme_products()
        self.fields['pickup_date'].widget = forms.DateInput(
            attrs={
                'type' : 'date',
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400'
            }
        )

    def clean_product(self):
        product = self.cleaned_data.get('product')
        if not product:
            raise forms.ValidationError('Please select a product.')
        # Verify product is in allowed scheme categories
        allowed = ['Cement', 'Iron Bars', 'Iron Sheets']
        if product.category.name not in allowed:
            raise forms.ValidationError(
                f'{product.name} is not available under the scheme. '
                f'Only Cement, Iron Bars and Iron Sheets are allowed.'
            )
        return product

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is None:
            raise forms.ValidationError('Quantity is required.')
        if quantity <= 0:
            raise forms.ValidationError('Quantity must be greater than zero.')
        return quantity

    def clean_unit_price(self):
        price = self.cleaned_data.get('unit_price')
        if price is None:
            raise forms.ValidationError('Unit price is required.')
        if price <= 0:
            raise forms.ValidationError('Unit price must be greater than zero.')
        return price

    def clean_pickup_date(self):
        from django.utils import timezone
        date = self.cleaned_data.get('pickup_date')
        if not date:
            raise forms.ValidationError('Pickup date is required.')
        if date > timezone.now().date():
            raise forms.ValidationError('Pickup date cannot be in the future.')
        return date

    def clean(self):
        cleaned_data = super().clean()
        product      = cleaned_data.get('product')
        quantity     = cleaned_data.get('quantity')
        unit_price   = cleaned_data.get('unit_price')

        if product and quantity:
            # Check stock availability
            if quantity > product.quantity:
                self.add_error(
                    'quantity',
                    f'Not enough stock for {product.name}. '
                    f'Available: {product.quantity:,.0f} {product.get_unit_display()}.'
                )

        if quantity and unit_price and self.customer:
            total_value = quantity * unit_price
            balance     = get_customer_balance(self.customer)

            if total_value > balance:
                raise forms.ValidationError(
                    f'Total value (UGX {total_value:,.0f}) exceeds the '
                    f'customer\'s available balance (UGX {balance:,.0f}). '
                    f'The customer needs to make a deposit first.'
                )

        return cleaned_data