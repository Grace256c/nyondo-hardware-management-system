from django import forms
from .models import Customer, Invoice, InvoiceItem, Receivable, CustomerPayment
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
        elif widget_type == 'CheckboxInput':
            field.widget.attrs.update({
                'class': 'w-4 h-4 rounded border-gray-300 text-orange-500 focus:ring-orange-400'
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


# ── CUSTOMER FORM ─────────────────────────────────────────────
class CustomerForm(forms.ModelForm):

    class Meta:
        model  = Customer
        fields = ['name', 'phone', 'customer_type', 'address', 'distance_km']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['name'].widget.attrs['placeholder']        = 'e.g. Kato Building Supplies'
        self.fields['phone'].widget.attrs['placeholder']       = '0712345678 or +256712345678'
        self.fields['address'].widget.attrs['placeholder']     = 'Physical address or area'
        self.fields['distance_km'].widget.attrs['placeholder'] = 'e.g. 5.5'
        self.fields['address'].required                        = False
        self.fields['distance_km'].required                    = False

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Customer name is required.')
        if len(name) < 2:
            raise forms.ValidationError('Customer name must be at least 2 characters.')
        if len(name) > 100:
            raise forms.ValidationError('Customer name cannot exceed 100 characters.')
        return name

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

    def clean_customer_type(self):
        customer_type = self.cleaned_data.get('customer_type')
        if not customer_type:
            raise forms.ValidationError('Please select a customer type.')
        valid_types = ['retail', 'wholesale', 'walk_in']
        if customer_type not in valid_types:
            raise forms.ValidationError('Invalid customer type selected.')
        return customer_type

    def clean_distance_km(self):
        distance = self.cleaned_data.get('distance_km')
        if distance is not None:
            if distance < 0:
                raise forms.ValidationError('Distance cannot be negative.')
            if distance > 9999:
                raise forms.ValidationError('Distance value is too large.')
        return distance


# ── INVOICE FORM ──────────────────────────────────────────────
class InvoiceForm(forms.ModelForm):

    class Meta:
        model  = Invoice
        fields = [
            'customer', 'customer_name', 'customer_type',
            'payment_method', 'payment_status',
            'amount_paid', 'notes'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['customer'].required      = False
        self.fields['customer_name'].required = False
        self.fields['amount_paid'].required   = False
        self.fields['notes'].required         = False
        self.fields['customer_name'].widget.attrs['placeholder'] = 'Walk-in customer name'
        self.fields['amount_paid'].widget.attrs['placeholder']   = '0'
        self.fields['notes'].widget.attrs['placeholder']         = 'Optional notes'

    def clean_customer_name(self):
        name       = self.cleaned_data.get('customer_name', '').strip()
        customer   = self.cleaned_data.get('customer')
        if not customer and name and len(name) < 2:
            raise forms.ValidationError(
                'Customer name must be at least 2 characters.'
            )
        if name and len(name) > 100:
            raise forms.ValidationError(
                'Customer name cannot exceed 100 characters.'
            )
        return name

    def clean_payment_method(self):
        method = self.cleaned_data.get('payment_method')
        if not method:
            raise forms.ValidationError('Please select a payment method.')
        return method

    def clean_payment_status(self):
        status = self.cleaned_data.get('payment_status')
        if not status:
            raise forms.ValidationError('Please select a payment status.')
        return status

    def clean_amount_paid(self):
        amount = self.cleaned_data.get('amount_paid')
        if amount is None:
            return 0
        if amount < 0:
            raise forms.ValidationError('Amount paid cannot be negative.')
        return amount

    def clean(self):
        cleaned_data   = super().clean()
        customer       = cleaned_data.get('customer')
        customer_name  = cleaned_data.get('customer_name', '').strip()
        payment_status = cleaned_data.get('payment_status')
        amount_paid    = cleaned_data.get('amount_paid', 0)

        # Must have either a registered customer or a walk-in name
        if not customer and not customer_name:
            raise forms.ValidationError(
                'Please select an existing customer or enter a walk-in customer name.'
            )

        # Credit sales must have a registered customer (for receivables tracking)
        if payment_status == 'credit' and not customer:
            raise forms.ValidationError(
                'Credit sales require a registered customer. '
                'Please register the customer first or change payment status to Cash.'
            )

        # Partial payment must have amount paid
        if payment_status == 'partial' and (not amount_paid or amount_paid <= 0):
            self.add_error(
                'amount_paid',
                'Please enter the amount paid for a partial payment.'
            )

        return cleaned_data


# ── INVOICE ITEM FORM ─────────────────────────────────────────
class InvoiceItemForm(forms.ModelForm):

    class Meta:
        model  = InvoiceItem
        fields = ['product', 'quantity', 'unit_price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

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

    def clean(self):
        cleaned_data = super().clean()
        product      = cleaned_data.get('product')
        quantity     = cleaned_data.get('quantity')

        if product and quantity:
            if quantity > product.quantity:
                raise forms.ValidationError(
                    f'Not enough stock for {product.name}. '
                    f'Available: {product.quantity:,.0f} {product.get_unit_display()}.'
                )
        return cleaned_data


# ── RECEIVABLE EDIT FORM ──────────────────────────────────────
class ReceivableEditForm(forms.ModelForm):

    class Meta:
        model   = Receivable
        fields  = ['due_date', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['due_date'].widget = forms.DateInput(
            attrs={
                'type' : 'date',
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400'
            }
        )
        self.fields['due_date'].required                         = False
        self.fields['notes'].widget.attrs['placeholder']         = 'Optional notes'

    def clean_due_date(self):
        from django.utils import timezone
        date = self.cleaned_data.get('due_date')
        if date and date < timezone.now().date():
            raise forms.ValidationError(
                'Due date is already in the past. Please set a future date.'
            )
        return date


# ── CUSTOMER PAYMENT FORM ─────────────────────────────────────
class CustomerPaymentForm(forms.ModelForm):

    class Meta:
        model   = CustomerPayment
        fields  = ['amount', 'payment_date', 'payment_method', 'reference']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.receivable = kwargs.pop('receivable', None)
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['reference'].required                        = False
        self.fields['amount'].widget.attrs['placeholder']        = 'Amount being paid'
        self.fields['reference'].widget.attrs['placeholder']     = 'e.g. Transaction ID, cheque no.'
        self.fields['payment_date'].widget = forms.DateInput(
            attrs={
                'type' : 'date',
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400'
            }
        )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None:
            raise forms.ValidationError('Amount is required.')
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        if self.receivable:
            if amount > self.receivable.balance:
                raise forms.ValidationError(
                    f'Amount (UGX {amount:,.0f}) exceeds the outstanding '
                    f'balance (UGX {self.receivable.balance:,.0f}).'
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


# ── TRANSPORT OVERRIDE FORM ───────────────────────────────────
class TransportOverrideForm(forms.ModelForm):

    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=True
    )

    class Meta:
        model  = Invoice
        fields = ['transport_charge']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['transport_charge'].widget.attrs['placeholder'] = 'e.g. 30000'
        self.fields['reason'].widget.attrs['placeholder']           = 'Reason for overriding transport charge'

    def clean_transport_charge(self):
        charge = self.cleaned_data.get('transport_charge')
        if charge is None:
            raise forms.ValidationError('Transport charge is required.')
        if charge < 0:
            raise forms.ValidationError('Transport charge cannot be negative.')
        if charge > 500000:
            raise forms.ValidationError(
                'Transport charge seems unusually high. Maximum allowed is UGX 500,000.'
            )
        return charge

    def clean_reason(self):
        reason = self.cleaned_data.get('reason', '').strip()
        if not reason:
            raise forms.ValidationError('Please provide a reason for overriding the transport charge.')
        if len(reason) < 10:
            raise forms.ValidationError('Please provide a more detailed reason (at least 10 characters).')
        return reason