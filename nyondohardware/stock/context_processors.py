from .models import Product
from django.db.models import F


def low_stock_count(request):
    if request.user.is_authenticated:
        count = Product.objects.filter(
            is_active=True,
            quantity__lte=F('reorder_level')
        ).count()
        return {'low_stock_count': count}
    return {'low_stock_count': 0}