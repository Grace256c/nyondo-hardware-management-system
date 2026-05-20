from django.db import models
from django.contrib.auth.models import User
from stock.models import Product


class Customer(models.Model):

    CUSTOMER_TYPE_CHOICES = [
        ('retail',    'Retail'),
        ('wholesale', 'Wholesale'),
        ('walk_in',   'Walk In'),
    ]

    name          = models.CharField(max_length=100)
    phone         = models.CharField(max_length=20)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES, default='retail')
    address       = models.TextField(blank=True)
    distance_km   = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_active     = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_customer_type_display()})"


class Invoice(models.Model):

    PAYMENT_METHOD_CHOICES = [
        ('cash',          'Cash'),
        ('mobile_money',  'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque',        'Cheque'),
        ('scheme',        'Scheme'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('paid',    'Paid'),
        ('credit',  'Credit'),
        ('partial', 'Partial'),
    ]

    CUSTOMER_TYPE_CHOICES = [
        ('retail',    'Retail'),
        ('wholesale', 'Wholesale'),
        ('walk_in',   'Walk In'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    customer       = models.ForeignKey(Customer, null=True, blank=True,
                        on_delete=models.PROTECT)
    customer_name  = models.CharField(max_length=100, blank=True)
    customer_type  = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES,
                        default='retail')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES,
                        default='paid')
    transport_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal       = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance        = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sale_date      = models.DateField(auto_now_add=True)
    notes          = models.TextField(blank=True)
    served_by      = models.ForeignKey(User, on_delete=models.PROTECT)
    is_cancelled   = models.BooleanField(default=False)
    created_at     = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-generate invoice number
        if not self.invoice_number:
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last = Invoice.objects.filter(
                invoice_number__startswith=f'INV-{date_str}'
            ).count()
            self.invoice_number = f'INV-{date_str}-{str(last + 1).zfill(4)}'

        # Calculate transport
        from .utils import calculate_transport
        if self.customer and self.customer.distance_km:
            self.transport_charge = calculate_transport(
                self.customer.distance_km, self.subtotal
            )

        # Calculate total and balance
        self.total   = self.subtotal + self.transport_charge
        self.balance = self.total - self.amount_paid

        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number


class InvoiceItem(models.Model):
    invoice     = models.ForeignKey(Invoice, on_delete=models.CASCADE,
                    related_name='items')
    product     = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity    = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price  = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.quantity * self.unit_price

        # Check stock availability
        if self.quantity > self.product.quantity:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                f'Not enough stock for {self.product.name}. '
                f'Available: {self.product.quantity}'
            )

        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Deduct stock
        if is_new:
            self.product.quantity -= self.quantity
            self.product.save()

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.product.name}"


class Receivable(models.Model):

    STATUS_CHOICES = [
        ('unpaid',     'Unpaid'),
        ('partial',    'Partial'),
        ('paid',       'Paid'),
        ('written_off', 'Written Off'),
    ]

    invoice      = models.OneToOneField(Invoice, on_delete=models.PROTECT)
    customer     = models.ForeignKey(Customer, on_delete=models.PROTECT)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance      = models.DecimalField(max_digits=12, decimal_places=2)
    due_date     = models.DateField(null=True, blank=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid')
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receivable - {self.customer.name} - {self.balance}"


class CustomerPayment(models.Model):

    PAYMENT_METHOD_CHOICES = [
        ('cash',          'Cash'),
        ('mobile_money',  'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque',        'Cheque'),
    ]

    receivable     = models.ForeignKey(Receivable, on_delete=models.PROTECT,
                        related_name='payments')
    amount         = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date   = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference      = models.CharField(max_length=100, blank=True)
    recorded_by    = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at     = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        receivable = self.receivable
        receivable.amount_paid = sum(
            p.amount for p in receivable.payments.all()
        )
        receivable.balance = receivable.total_amount - receivable.amount_paid
        if receivable.balance <= 0:
            receivable.status = 'paid'
        elif receivable.amount_paid > 0:
            receivable.status = 'partial'
        receivable.save()

    def __str__(self):
        return f"Payment - {self.receivable.customer.name} - {self.amount}"