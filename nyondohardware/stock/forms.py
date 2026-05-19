from django import forms
from .models import Category, Supplier, Product, StockReceipt, SupplierCredit, SupplierPayment
import re


# ─── HELPER: adds Tailwind styling to all form fields ───────────
def style_fields(form):
    for field in form.fields.values():
        field.widget.attrs.update({
            'class': 'w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:border-orange-400'
        })


# ─── CATEGORY FORM ──────────────────────────────────────────────
class CategoryForm(forms.ModelForm):

    class Meta:
        model  = Category
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Category.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('A category with this name already exists.')
        return name


# ─── SUPPLIER FORM ──────────────────────────────────────────────
class SupplierForm(forms.ModelForm):

    class Meta:
        model  = Supplier
        fields = ['name', 'phone', 'address', 'tin']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^(\+?256|0)[7][0-9]{8}$', phone):
            raise forms.ValidationError('Enter a valid Ugandan phone number.')
        return phone


# ─── PRODUCT FORM ───────────────────────────────────────────────
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

    def clean(self):
        cleaned_data    = super().clean()
        cost_price      = cleaned_data.get('cost_price')
        retail_price    = cleaned_data.get('retail_price')
        wholesale_price = cleaned_data.get('wholesale_price')

        if cost_price and retail_price:
            if retail_price <= cost_price:
                raise forms.ValidationError('Retail price must be greater than cost price.')
        if cost_price and wholesale_price:
            if wholesale_price <= cost_price:
                raise forms.ValidationError('Wholesale price must be greater than cost price.')

        return cleaned_data


# ─── STOCK RECEIPT FORM ─────────────────────────────────────────
class StockReceiptForm(forms.ModelForm):

    class Meta:
        model  = StockReceipt
        fields = [
            'supplier', 'product', 'quantity',
            'unit_cost', 'payment_status', 'receipt_date', 'notes'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean(self):
        cleaned_data = super().clean()
        quantity     = cleaned_data.get('quantity')
        unit_cost    = cleaned_data.get('unit_cost')

        if quantity and quantity <= 0:
            raise forms.ValidationError('Quantity must be greater than zero.')
        if unit_cost and unit_cost <= 0:
            raise forms.ValidationError('Unit cost must be greater than zero.')

        return cleaned_data


# ─── SUPPLIER CREDIT EDIT FORM ──────────────────────────────────
class SupplierCreditEditForm(forms.ModelForm):

    class Meta:
        model  = SupplierCredit
        fields = ['due_date', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


# ─── SUPPLIER PAYMENT FORM ──────────────────────────────────────
class SupplierPaymentForm(forms.ModelForm):

    class Meta:
        model  = SupplierPayment
        fields = ['amount', 'payment_date', 'payment_method', 'reference']

    def __init__(self, *args, **kwargs):
        self.credit = kwargs.pop('credit', None)
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.credit and amount > self.credit.balance:
            raise forms.ValidationError(
                f'Amount cannot exceed outstanding balance of {self.credit.balance}.'
            )
        return amount