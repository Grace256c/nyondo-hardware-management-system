from django.db.models import Sum


SCHEME_ALLOWED_CATEGORIES = ['Cement', 'Iron Bars', 'Iron Sheets']


def get_customer_balance(customer):
    total_deposits = customer.deposits.filter(
        is_reversed=False
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    total_pickups = customer.pickups.exclude(
        status='cancelled'
    ).aggregate(Sum('total_value'))['total_value__sum'] or 0

    return total_deposits - total_pickups


def get_scheme_products():
    from stock.models import Product
    return Product.objects.filter(
        category__name__in=SCHEME_ALLOWED_CATEGORIES,
        is_active=True
    )