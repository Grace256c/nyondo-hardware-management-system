from django import forms
from .models import Customer, Invoice, InvoiceItem, Receivable, CustomerPayment
import re


def style_fields(form):
    for name, field in form.fields.items():
        widget_type = field.widget.__class__.__name__
        if widget_type == "Select":
            field.widget.attrs.update(
                {
                    "class": "w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white cursor-pointer"
                }
            )
        elif widget_type == "Textarea":
            field.widget.attrs.update(
                {
                    "class": "w-full border border-gray-300 rounded px-3 py-2 text-sm",
                    "rows": "3",
                }
            )
        else:
            field.widget.attrs.update(
                {"class": "w-full border border-gray-300 rounded px-3 py-2 text-sm"}
            )


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "customer_type", "address", "distance_km"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if not re.match(r"^(\+?256|0)[7][0-9]{8}$", phone):
            raise forms.ValidationError("Enter a valid Ugandan phone number.")
        return phone


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "customer",
            "customer_name",
            "customer_type",
            "payment_method",
            "payment_status",
            "amount_paid",
            "notes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields["customer"].required = False
        self.fields["customer_name"].required = False


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ["product", "quantity", "unit_price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        quantity = cleaned_data.get("quantity")

        if product and quantity:
            if quantity > product.quantity:
                raise forms.ValidationError(
                    f"Not enough stock for {product.name}. "
                    f"Available: {product.quantity}"
                )
        return cleaned_data


class ReceivableEditForm(forms.ModelForm):
    class Meta:
        model = Receivable
        fields = ["due_date", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class CustomerPaymentForm(forms.ModelForm):
    class Meta:
        model = CustomerPayment
        fields = ["amount", "payment_date", "payment_method", "reference"]

    def __init__(self, *args, **kwargs):
        self.receivable = kwargs.pop("receivable", None)
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields["payment_date"].widget = forms.DateInput(
            attrs={
                "type": "date",
                "class": "w-full border border-gray-300 rounded px-3 py-2 text-sm",
            }
        )

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if self.receivable and amount > self.receivable.balance:
            raise forms.ValidationError(
                f"Amount cannot exceed outstanding balance of {self.receivable.balance}."
            )
        return amount


class TransportOverrideForm(forms.ModelForm):
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=True)

    class Meta:
        model = Invoice
        fields = ["transport_charge"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
