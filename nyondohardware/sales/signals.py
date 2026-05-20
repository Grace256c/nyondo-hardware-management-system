from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Invoice, Receivable


@receiver(post_save, sender=Invoice)
def create_receivable(sender, instance, created, **kwargs):
    if created and instance.payment_status in ['credit', 'partial']:
        if instance.customer:
            Receivable.objects.create(
                invoice      = instance,
                customer     = instance.customer,
                total_amount = instance.total,
                balance      = instance.balance,
            )