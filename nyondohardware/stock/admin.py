from django.contrib import admin
from .models import Category, StockReceipt, Supplier, Product, SupplierCredit, SupplierPayment


# Register your models here.
admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(StockReceipt)
admin.site.register(SupplierCredit)
admin.site.register(SupplierPayment)