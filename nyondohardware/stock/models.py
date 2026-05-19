from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class Supplier(models.Model):
    name       = models.CharField(max_length=100)
    phone      = models.CharField(max_length=20)
    address    = models.TextField()
    tin        = models.CharField(max_length=50, blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):

    UNIT_CHOICES = [
        ('bag',    'Bag'),
        ('kg',     'Kg'),
        ('piece',  'Piece'),
        ('roll',   'Roll'),
        ('sheet',  'Sheet'),
        ('pack',   'Pack'),
        ('length', 'Length'),
    ]

    name              = models.CharField(max_length=100)
    category          = models.ForeignKey(Category, on_delete=models.PROTECT)
    unit              = models.CharField(max_length=20, choices=UNIT_CHOICES)
    cost_price        = models.DecimalField(max_digits=12, decimal_places=2)
    retail_price      = models.DecimalField(max_digits=12, decimal_places=2)
    wholesale_price   = models.DecimalField(max_digits=12, decimal_places=2)
    quantity          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level     = models.DecimalField(max_digits=12, decimal_places=2, default=10)
    description       = models.TextField(blank=True)
    is_active         = models.BooleanField(default=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.retail_price <= self.cost_price:
            raise ValidationError('Retail price must be greater than cost price.')
        if self.wholesale_price <= self.cost_price:
            raise ValidationError('Wholesale price must be greater than cost price.')


class StockReceipt(models.Model):

    PAYMENT_CHOICES = [
        ('cash',   'Cash'),
        ('credit', 'Credit'),
    ]

    grn_number     = models.CharField(max_length=50, unique=True, blank=True)
    supplier       = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    product        = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity       = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost      = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost     = models.DecimalField(max_digits=12, decimal_places=2, blank=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    receipt_date   = models.DateField()
    notes          = models.TextField(blank=True)
    recorded_by    = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at     = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-generate GRN number
        if not self.grn_number:
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last = StockReceipt.objects.filter(
                grn_number__startswith=f'GRN-{date_str}'
            ).count()
            self.grn_number = f'GRN-{date_str}-{str(last + 1).zfill(4)}'

        # Auto-calculate total cost
        self.total_cost = self.quantity * self.unit_cost

        # Add quantity to product stock
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.product.quantity += self.quantity
            self.product.save()

    def __str__(self):
        return self.grn_number


class SupplierCredit(models.Model):

    STATUS_CHOICES = [
        ('unpaid',  'Unpaid'),
        ('partial', 'Partial'),
        ('paid',    'Paid'),
    ]

    stock_receipt = models.OneToOneField(StockReceipt, on_delete=models.PROTECT)
    supplier      = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    total_amount  = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance       = models.DecimalField(max_digits=12, decimal_places=2)
    due_date      = models.DateField(null=True, blank=True)
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Credit - {self.supplier.name} - {self.balance}"


class SupplierPayment(models.Model):

    PAYMENT_METHOD_CHOICES = [
        ('cash',          'Cash'),
        ('mobile_money',  'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque',        'Cheque'),
    ]

    credit         = models.ForeignKey(SupplierCredit, on_delete=models.PROTECT, related_name='payments')
    amount         = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date   = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference      = models.CharField(max_length=100, blank=True)
    recorded_by    = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at     = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update credit balance and status
        credit = self.credit
        credit.amount_paid = sum(
            p.amount for p in credit.payments.all()
        )
        credit.balance = credit.total_amount - credit.amount_paid
        if credit.balance <= 0:
            credit.status = 'paid'
        elif credit.amount_paid > 0:
            credit.status = 'partial'
        credit.save()

    def __str__(self):
        return f"Payment - {self.credit.supplier.name} - {self.amount}"