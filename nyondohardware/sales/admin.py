from django.contrib import admin
from .models import Customer, Invoice, InvoiceItem, Receivable, CustomerPayment

admin.site.register(Customer)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)
admin.site.register(Receivable)
admin.site.register(CustomerPayment)