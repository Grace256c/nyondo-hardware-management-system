from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StockReceipt, SupplierCredit


@receiver(post_save, sender=StockReceipt)
def create_supplier_credit(sender, instance, created, **kwargs):
    if created and instance.payment_status == 'credit':
        SupplierCredit.objects.create(
            stock_receipt = instance,
            supplier      = instance.supplier,
            total_amount  = instance.total_cost,
            balance       = instance.total_cost,
        )