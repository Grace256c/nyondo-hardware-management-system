from django.contrib import admin
from .models import SchemeCustomer, Deposit, Pickup, SchemeInvoice

admin.site.register(SchemeCustomer)
admin.site.register(Deposit)
admin.site.register(Pickup)
admin.site.register(SchemeInvoice)