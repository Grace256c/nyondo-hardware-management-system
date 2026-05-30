from django import forms
from .models import Category, Supplier, Product, StockReceipt, SupplierCredit, SupplierPayment
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


# ── CATEGORY FORM ─────────────────────────────────────────────
class CategoryForm(forms.ModelForm):

    class Meta:
        model  = Category
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['name'].widget.attrs['placeholder']        = 'e.g. Cement'
        self.fields['description'].widget.attrs['placeholder'] = 'Optional description'

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Category name is required.')
        if len(name) < 2:
            raise forms.ValidationError('Category name must be at least 2 characters.')
        if len(name) > 100:
            raise forms.ValidationError('Category name cannot exceed 100 characters.')
        if Category.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f'A category named "{name}" already exists.')
        return name


# ── SUPPLIER FORM ─────────────────────────────────────────────
class SupplierForm(forms.ModelForm):

    class Meta:
        model  = Supplier
        fields = ['name', 'phone', 'address', 'tin']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['name'].widget.attrs['placeholder']    = 'e.g. Tororo Cement Ltd'
        self.fields['phone'].widget.attrs['placeholder']   = '0712345678 or +256712345678'
        self.fields['address'].widget.attrs['placeholder'] = 'Physical address'
        self.fields['tin'].widget.attrs['placeholder']     = '10-digit TIN (optional)'
        self.fields['tin'].required                        = False

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Supplier name is required.')
        if len(name) < 2:
            raise forms.ValidationError('Supplier name must be at least 2 characters.')
        if len(name) > 100:
            raise forms.ValidationError('Supplier name cannot exceed 100 characters.')
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

    def clean_address(self):
        address = self.cleaned_data.get('address', '').strip()
        if not address:
            raise forms.ValidationError('Address is required.')
        if len(address) < 5:
            raise forms.ValidationError('Please enter a more complete address.')
        return address

    def clean_tin(self):
        tin = self.cleaned_data.get('tin', '').strip()
        if tin:
            if not re.match(r'^\d{10}$', tin):
                raise forms.ValidationError(
                    'TIN must be exactly 10 digits (numbers only).'
                )
        return tin


# ── PRODUCT FORM ──────────────────────────────────────────────
class ProductForm(forms.ModelForm):

    class Meta:
        model  = Product
        fields = [
            'name', 'category', 'unit',
            'cost_price', 'retail_price', 'wholesale_price',
            'reorder_level', 'description'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['name'].widget.attrs['placeholder']        = 'e.g. Cement CEM IIN'
        self.fields['cost_price'].widget.attrs['placeholder']  = 'e.g. 28000'
        self.fields['retail_price'].widget.attrs['placeholder'] = 'e.g. 32000'
        self.fields['wholesale_price'].widget.attrs['placeholder'] = 'e.g. 30000'
        self.fields['reorder_level'].widget.attrs['placeholder']   = 'e.g. 50'
        self.fields['description'].widget.attrs['placeholder']     = 'Optional details'

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Product name is required.')
        if len(name) < 2:
            raise forms.ValidationError('Product name must be at least 2 characters.')
        if len(name) > 100:
            raise forms.ValidationError('Product name cannot exceed 100 characters.')
        return name

    def clean_cost_price(self):
        cost = self.cleaned_data.get('cost_price')
        if cost is None:
            raise forms.ValidationError('Cost price is required.')
        if cost <= 0:
            raise forms.ValidationError('Cost price must be greater than zero.')
        if cost > 999999999:
            raise forms.ValidationError('Cost price value is too large.')
        return cost

    def clean_retail_price(self):
        retail = self.cleaned_data.get('retail_price')
        if retail is None:
            raise forms.ValidationError('Retail price is required.')
        if retail <= 0:
            raise forms.ValidationError('Retail price must be greater than zero.')
        return retail

    def clean_wholesale_price(self):
        wholesale = self.cleaned_data.get('wholesale_price')
        if wholesale is None:
            raise forms.ValidationError('Wholesale price is required.')
        if wholesale <= 0:
            raise forms.ValidationError('Wholesale price must be greater than zero.')
        return wholesale

    def clean_reorder_level(self):
        level = self.cleaned_data.get('reorder_level')
        if level is None:
            raise forms.ValidationError('Reorder level is required.')
        if level < 0:
            raise forms.ValidationError('Reorder level cannot be negative.')
        return level

    def clean(self):
        cleaned_data    = super().clean()
        cost_price      = cleaned_data.get('cost_price')
        retail_price    = cleaned_data.get('retail_price')
        wholesale_price = cleaned_data.get('wholesale_price')

        if cost_price and retail_price:
            if retail_price <= cost_price:
                self.add_error(
                    'retail_price',
                    f'Retail price (UGX {retail_price:,.0f}) must be '
                    f'greater than cost price (UGX {cost_price:,.0f}).'
                )
        if cost_price and wholesale_price:
            if wholesale_price <= cost_price:
                self.add_error(
                    'wholesale_price',
                    f'Wholesale price (UGX {wholesale_price:,.0f}) must be '
                    f'greater than cost price (UGX {cost_price:,.0f}).'
                )
        return cleaned_data


# ── STOCK RECEIPT FORM ────────────────────────────────────────
class StockReceiptForm(forms.ModelForm):

    class Meta:
        model   = StockReceipt
        fields  = [
            'supplier', 'product', 'quantity',
            'unit_cost', 'payment_status', 'receipt_date', 'notes'
        ]
        widgets = {
            'receipt_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['quantity'].widget.attrs['placeholder']  = 'e.g. 100'
        self.fields['unit_cost'].widget.attrs['placeholder'] = 'e.g. 28000'
        self.fields['notes'].widget.attrs['placeholder']     = 'Optional notes'
        # Re-apply date after style_fields
        self.fields['receipt_date'].widget = forms.DateInput(
            attrs={
                'type' : 'date',
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400'
            }
        )

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is None:
            raise forms.ValidationError('Quantity is required.')
        if quantity <= 0:
            raise forms.ValidationError('Quantity must be greater than zero.')
        if quantity > 999999:
            raise forms.ValidationError('Quantity value is too large.')
        return quantity

    def clean_unit_cost(self):
        unit_cost = self.cleaned_data.get('unit_cost')
        if unit_cost is None:
            raise forms.ValidationError('Unit cost is required.')
        if unit_cost <= 0:
            raise forms.ValidationError('Unit cost must be greater than zero.')
        if unit_cost > 999999999:
            raise forms.ValidationError('Unit cost value is too large.')
        return unit_cost

    def clean_receipt_date(self):
        from django.utils import timezone
        date = self.cleaned_data.get('receipt_date')
        if not date:
            raise forms.ValidationError('Receipt date is required.')
        if date > timezone.now().date():
            raise forms.ValidationError('Receipt date cannot be in the future.')
        return date

    def clean(self):
        cleaned_data   = super().clean()
        supplier       = cleaned_data.get('supplier')
        product        = cleaned_data.get('product')
        unit_cost      = cleaned_data.get('unit_cost')
        payment_status = cleaned_data.get('payment_status')

        if not supplier:
            self.add_error('supplier', 'Please select a supplier.')
        if not product:
            self.add_error('product', 'Please select a product.')
        if not payment_status:
            self.add_error('payment_status', 'Please select a payment status.')

        # Warn if unit cost differs significantly from product cost price
        if product and unit_cost:
            if unit_cost < product.cost_price * 2 / 3:
                self.add_error(
                    'unit_cost',
                    f'Unit cost (UGX {unit_cost:,.0f}) seems unusually low '
                    f'compared to the product cost price (UGX {product.cost_price:,.0f}). '
                    f'Please verify.'
                )
        return cleaned_data


# ── SUPPLIER CREDIT EDIT FORM ─────────────────────────────────
class SupplierCreditEditForm(forms.ModelForm):

    class Meta:
        model  = SupplierCredit
        fields = ['due_date', 'notes']
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
        self.fields['due_date'].required        = False
        self.fields['notes'].widget.attrs['placeholder'] = 'Optional notes about this credit'

    def clean_due_date(self):
        from django.utils import timezone
        date = self.cleaned_data.get('due_date')
        if date and date < timezone.now().date():
            raise forms.ValidationError(
                'Due date is in the past. Please set a future date or leave blank.'
            )
        return date


# ── SUPPLIER PAYMENT FORM ─────────────────────────────────────
class SupplierPaymentForm(forms.ModelForm):

    class Meta:
        model   = SupplierPayment
        fields  = ['amount', 'payment_date', 'payment_method', 'reference']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.credit = kwargs.pop('credit', None)
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['amount'].widget.attrs['placeholder']    = 'Amount to pay'
        self.fields['reference'].widget.attrs['placeholder'] = 'e.g. Transaction ID, cheque number'
        self.fields['reference'].required                    = False
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
        if self.credit:
            if amount > self.credit.balance:
                raise forms.ValidationError(
                    f'Amount (UGX {amount:,.0f}) exceeds the outstanding '
                    f'balance (UGX {self.credit.balance:,.0f}).'
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