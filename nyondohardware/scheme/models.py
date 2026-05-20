from django.db import models
from django.contrib.auth.models import User
from stock.models import Product


class SchemeCustomer(models.Model):

    STATUS_CHOICES = [
        ('active',    'Active'),
        ('suspended', 'Suspended'),
    ]

    full_name        = models.CharField(max_length=100)
    nin              = models.CharField(max_length=14, unique=True)
    phone            = models.CharField(max_length=20)
    employer         = models.CharField(max_length=100, blank=True)
    employer_address = models.TextField(blank=True)
    registration_date = models.DateField(auto_now_add=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    registered_by    = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.full_name} - {self.nin}"


class Deposit(models.Model):

    PAYMENT_METHOD_CHOICES = [
        ('cash',         'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    customer       = models.ForeignKey(SchemeCustomer, on_delete=models.PROTECT,
                        related_name='deposits')
    amount         = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date   = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    recorded_by    = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at     = models.DateTimeField(auto_now_add=True)
    is_reversed    = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last = Deposit.objects.filter(
                receipt_number__startswith=f'RCPT-{date_str}'
            ).count()
            self.receipt_number = f'RCPT-{date_str}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.receipt_number} - {self.customer.full_name}"


class Pickup(models.Model):

    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('dispatched', 'Dispatched'),
        ('cancelled',  'Cancelled'),
    ]

    customer     = models.ForeignKey(SchemeCustomer, on_delete=models.PROTECT,
                    related_name='pickups')
    product      = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity     = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price   = models.DecimalField(max_digits=12, decimal_places=2)
    total_value  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pickup_date  = models.DateField()
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processed_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at   = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_value = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.full_name} - {self.product.name}"


class SchemeInvoice(models.Model):
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    pickup         = models.OneToOneField(Pickup, on_delete=models.PROTECT)
    customer       = models.ForeignKey(SchemeCustomer, on_delete=models.PROTECT)
    total_value    = models.DecimalField(max_digits=12, decimal_places=2)
    issue_date     = models.DateField(auto_now_add=True)
    printed        = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last = SchemeInvoice.objects.filter(
                invoice_number__startswith=f'SINV-{date_str}'
            ).count()
            self.invoice_number = f'SINV-{date_str}-{str(last + 1).zfill(4)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number